"""
RAG Routes - Complete multi-user RAG system
Backend handles: auth, access control, user tracking, preferences
Ingest service handles: pipeline, RAG, search (via HTTP)
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.dependencies.auth import get_current_user
from app.clients.ingest_service import IngestServiceClient
from app.models import User
from pydantic import BaseModel
from typing import Optional, List, Dict
from github import Github, GithubException
import os
import json

from google.cloud import storage as gcs

router = APIRouter(prefix="/rag", tags=["RAG"])

# HTTP client for ingest service
ingest_client = IngestServiceClient()

# GCP config (backend still needs these for user metadata)
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "otto-pm")
BUCKET_RAW = os.getenv("GCS_BUCKET_RAW", "otto-raw-repos")
BUCKET_PROCESSED = os.getenv("GCS_BUCKET_PROCESSED", "otto-processed-chunks")

# User access tracking (backend owns this - tied to auth)
from google.cloud import storage
_storage_client = storage.Client(project=PROJECT_ID)
_processed_bucket = _storage_client.bucket(BUCKET_PROCESSED)


# ==================== USER METADATA HELPERS ====================

def _get_shared_repo_path(repo_full_name: str) -> str:
    return f"repos/{repo_full_name}"

def _get_user_metadata_path(user_id: str, repo_full_name: str) -> str:
    return f"user_data/{user_id}/repos/{repo_full_name}"

def _record_user_access(user_id: str, repo_full_name: str, 
                        access_level: str, permissions: Dict):
    """Record user accessed a repo (stored in GCS)"""
    from datetime import datetime
    
    metadata_path = _get_user_metadata_path(user_id, repo_full_name)
    blob = _processed_bucket.blob(f"{metadata_path}/access_info.json")
    
    access_info = {
        'user_id': user_id,
        'repo': repo_full_name,
        'access_level': access_level,
        'github_permissions': permissions,
        'first_accessed': datetime.now().isoformat(),
        'last_accessed': datetime.now().isoformat(),
        'access_count': 1
    }
    
    if blob.exists():
        try:
            existing = json.loads(blob.download_as_text())
            access_info['first_accessed'] = existing.get('first_accessed', access_info['first_accessed'])
            access_info['access_count'] = existing.get('access_count', 0) + 1
        except Exception:
            pass
    
    blob.upload_from_string(json.dumps(access_info, indent=2))

def _get_access_info(user_id: str, repo_full_name: str) -> Optional[Dict]:
    """Get user's access info for a repo"""
    metadata_path = _get_user_metadata_path(user_id, repo_full_name)
    blob = _processed_bucket.blob(f"{metadata_path}/access_info.json")
    if blob.exists():
        return json.loads(blob.download_as_text())
    return None

def _get_user_repos(user_id: str) -> List[str]:
    """Get all repos a user has accessed"""
    prefix = f"user_data/{user_id}/repos/"
    all_blobs = list(_processed_bucket.list_blobs(prefix=prefix))
    repos = set()
    for blob in all_blobs:
        parts = blob.name.split('/')
        if len(parts) >= 6 and parts[5] == 'access_info.json':
            repos.add(f"{parts[3]}/{parts[4]}")
    return sorted(list(repos))

def _save_user_preferences(user_id: str, repo_full_name: str, preferences: Dict):
    """Save user preferences for a repo"""
    from datetime import datetime
    metadata_path = _get_user_metadata_path(user_id, repo_full_name)
    blob = _processed_bucket.blob(f"{metadata_path}/preferences.json")
    pref_data = {
        'preferred_doc_type': preferences.get('doc_type', 'api'),
        'preferred_chunk_size': preferences.get('chunk_size', 150),
        'auto_push_prs': preferences.get('auto_push', False),
        'favorite': preferences.get('favorite', False),
        'notifications': preferences.get('notifications', True),
        'updated_at': datetime.now().isoformat()
    }
    blob.upload_from_string(json.dumps(pref_data, indent=2))

def _get_user_preferences(user_id: str, repo_full_name: str) -> Dict:
    """Get user preferences for a repo"""
    metadata_path = _get_user_metadata_path(user_id, repo_full_name)
    blob = _processed_bucket.blob(f"{metadata_path}/preferences.json")
    if blob.exists():
        return json.loads(blob.download_as_text())
    return {
        'preferred_doc_type': 'api',
        'preferred_chunk_size': 150,
        'auto_push_prs': False,
        'favorite': False,
        'notifications': True
    }

def _get_commit_info(repo_full_name: str) -> Optional[Dict]:
    """Get last commit info from GCS"""
    repo_path = _get_shared_repo_path(repo_full_name)
    blob = _processed_bucket.blob(f"{repo_path}/commit_info.json")
    if blob.exists():
        try:
            return json.loads(blob.download_as_text())
        except Exception:
            return None
    return None

def _get_commit_history(repo_full_name: str, limit: int = 10) -> List[Dict]:
    """Get commit processing history"""
    repo_path = _get_shared_repo_path(repo_full_name)
    blob = _processed_bucket.blob(f"{repo_path}/commit_history.jsonl")
    if not blob.exists():
        return []
    try:
        content = blob.download_as_text()
        lines = content.strip().split('\n')
        history = [json.loads(line) for line in lines if line.strip()]
        history.reverse()
        return history[:limit]
    except Exception:
        return []


# ==================== AUTH HELPERS ====================

def get_user_github_token(user: User) -> str:
    github_token = user.get("github_access_token")
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token not found. Please re-authenticate."
        )
    return github_token

def verify_user_repo_access(user: User, repo_full_name: str) -> Dict:
    try:
        github_token = get_user_github_token(user)
        gh = Github(github_token)
        gh_repo = gh.get_repo(repo_full_name)
        return {
            'repo': gh_repo,
            'permissions': {
                'admin': gh_repo.permissions.admin,
                'push': gh_repo.permissions.push,
                'pull': gh_repo.permissions.pull
            }
        }
    except GithubException as e:
        if e.status == 404:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Repository not found or you don't have access"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify access: {str(e)}"
        )


# ==================== REQUEST/RESPONSE MODELS ====================

class IngestRepoRequest(BaseModel):
    repo_full_name: str
    branch: Optional[str] = None

class IngestRepoResponse(BaseModel):
    success: bool
    repo: str
    total_files: int
    message: str
    user: str
    was_cached: bool
    commit_sha: Optional[str] = None

class ProcessRepoRequest(BaseModel):
    repo_full_name: str
    chunk_size: int = 150
    overlap: int = 10

class ProcessRepoResponse(BaseModel):
    success: bool
    repo: str
    total_chunks: int
    message: str

class EmbedRepoRequest(BaseModel):
    repo_full_name: str
    force_reembed: bool = False

class EmbedRepoResponse(BaseModel):
    success: bool
    repo: str
    total_embedded: int
    message: str

class FullPipelineRequest(BaseModel):
    repo_full_name: str
    branch: Optional[str] = None
    chunk_size: int = 150
    overlap: int = 10
    force_reembed: bool = False

class FullPipelineResponse(BaseModel):
    success: bool
    repo: str
    total_files: int
    total_chunks: int
    total_embedded: int
    commit_sha: Optional[str] = None
    was_cached: bool
    message: str
    user: str

class AskQuestionRequest(BaseModel):
    repo_full_name: str
    question: str
    language: Optional[str] = None

class AskQuestionResponse(BaseModel):
    answer: str
    sources: List[Dict]
    chunks_used: int

class GenerateDocsRequest(BaseModel):
    repo_full_name: str
    target: str
    doc_type: str = "api"
    push_to_github: bool = False

class GenerateDocsResponse(BaseModel):
    documentation: str
    type: str
    files_referenced: int
    github_pr: Optional[str] = None
    github_branch: Optional[str] = None
    pushed_by: Optional[str] = None

class CompleteCodeRequest(BaseModel):
    repo_full_name: str
    code_context: str
    language: str = "python"
    target_file: Optional[str] = None
    push_to_github: bool = False

class CompleteCodeResponse(BaseModel):
    completion: str
    language: str
    confidence: str
    github_pr: Optional[str] = None
    pushed_by: Optional[str] = None

class EditCodeRequest(BaseModel):
    repo_full_name: str
    instruction: str
    target_file: str
    push_to_github: bool = False

class EditCodeResponse(BaseModel):
    modified_code: str
    file: str
    instruction: str
    chunks_analyzed: int
    github_pr: Optional[str] = None
    github_branch: Optional[str] = None
    pushed_by: Optional[str] = None

class SearchCodeRequest(BaseModel):
    repo_full_name: str
    query: str
    language: Optional[str] = None
    top_k: int = 10

class SearchCodeResponse(BaseModel):
    results: List[Dict]
    total_found: int

class UserPreferencesRequest(BaseModel):
    repo_full_name: str
    preferred_doc_type: Optional[str] = None
    preferred_chunk_size: Optional[int] = None
    auto_push_prs: Optional[bool] = None
    favorite: Optional[bool] = None
    notifications: Optional[bool] = None


# ==================== PIPELINE ENDPOINTS ====================

@router.post("/repos/pipeline", response_model=FullPipelineResponse)
async def run_full_pipeline(
    request: FullPipelineRequest,
    current_user: User = Depends(get_current_user)
) -> FullPipelineResponse:
    """Run full pipeline: ingest → chunk → embed via ingest-service."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    _record_user_access(
        user_id, request.repo_full_name,
        'write' if repo_access['permissions']['push'] else 'read',
        repo_access['permissions']
    )

    result = await ingest_client.run_full_pipeline(
        repo_full_name=request.repo_full_name,
        github_token=github_token,
        branch=request.branch,
        chunk_size=request.chunk_size,
        overlap=request.overlap,
        force_reembed=request.force_reembed
    )

    return FullPipelineResponse(
        **result,
        user=current_user.get('github_username', 'unknown')
    )


@router.post("/repos/ingest", status_code=status.HTTP_202_ACCEPTED, response_model=IngestRepoResponse)
async def ingest_repository(
    request: IngestRepoRequest,
    current_user: User = Depends(get_current_user)
) -> IngestRepoResponse:
    """Ingest repository via ingest-service."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    _record_user_access(
        user_id, request.repo_full_name,
        'write' if repo_access['permissions']['push'] else 'read',
        repo_access['permissions']
    )

    result = await ingest_client.ingest_repository(
        repo_full_name=request.repo_full_name,
        github_token=github_token,
        branch=request.branch
    )

    return IngestRepoResponse(
        success=result['success'],
        repo=result['repo'],
        total_files=result['total_files'],
        message=result['message'],
        user=current_user.get('github_username', 'unknown'),
        was_cached=result['was_cached'],
        commit_sha=result.get('commit_sha')
    )


@router.post("/repos/process", status_code=status.HTTP_202_ACCEPTED, response_model=ProcessRepoResponse)
async def process_repository(
    request: ProcessRepoRequest,
    current_user: User = Depends(get_current_user)
) -> ProcessRepoResponse:
    """Chunk repository via ingest-service."""
    verify_user_repo_access(current_user, request.repo_full_name)
    result = await ingest_client.chunk_repository(
        repo_full_name=request.repo_full_name,
        chunk_size=request.chunk_size,
        overlap=request.overlap
    )
    return ProcessRepoResponse(**result)


@router.post("/repos/embed", status_code=status.HTTP_202_ACCEPTED, response_model=EmbedRepoResponse)
async def embed_repository(
    request: EmbedRepoRequest,
    current_user: User = Depends(get_current_user)
) -> EmbedRepoResponse:
    """Embed repository via ingest-service."""
    verify_user_repo_access(current_user, request.repo_full_name)
    result = await ingest_client.embed_repository(
        repo_full_name=request.repo_full_name,
        force_reembed=request.force_reembed
    )
    return EmbedRepoResponse(**result)


# ==================== RAG SERVICE ENDPOINTS ====================

@router.post("/ask", response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_user)
) -> AskQuestionResponse:
    """Ask a question about the codebase."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    _record_user_access(
        user_id, request.repo_full_name,
        'write' if repo_access['permissions']['push'] else 'read',
        repo_access['permissions']
    )

    result = await ingest_client.ask_question(
        repo_full_name=request.repo_full_name,
        question=request.question,
        github_token=github_token,
        language=request.language
    )

    return AskQuestionResponse(**result)


@router.post("/docs/generate", response_model=GenerateDocsResponse)
async def generate_documentation(
    request: GenerateDocsRequest,
    current_user: User = Depends(get_current_user)
) -> GenerateDocsResponse:
    """Generate documentation."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    if request.push_to_github and not repo_access['permissions']['push']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have push access to this repository"
        )

    valid_doc_types = ['api', 'user_guide', 'technical', 'readme']
    if request.doc_type not in valid_doc_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid doc_type. Must be one of: {valid_doc_types}"
        )

    _record_user_access(
        user_id, request.repo_full_name,
        'write' if repo_access['permissions']['push'] else 'read',
        repo_access['permissions']
    )

    result = await ingest_client.generate_docs(
        repo_full_name=request.repo_full_name,
        target=request.target,
        github_token=github_token,
        doc_type=request.doc_type,
        push_to_github=request.push_to_github
    )

    return GenerateDocsResponse(
        documentation=result['documentation'],
        type=result['type'],
        files_referenced=result['files_referenced'],
        github_pr=result.get('github_pr'),
        github_branch=result.get('github_branch'),
        pushed_by=current_user.get('github_username') if request.push_to_github else None
    )


@router.post("/code/complete", response_model=CompleteCodeResponse)
async def complete_code(
    request: CompleteCodeRequest,
    current_user: User = Depends(get_current_user)
) -> CompleteCodeResponse:
    """Get code completion."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    if request.push_to_github and not repo_access['permissions']['push']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have push access to this repository"
        )

    _record_user_access(user_id, request.repo_full_name, 'read', repo_access['permissions'])

    result = await ingest_client.complete_code(
        repo_full_name=request.repo_full_name,
        code_context=request.code_context,
        github_token=github_token,
        language=request.language,
        target_file=request.target_file,
        push_to_github=request.push_to_github
    )

    return CompleteCodeResponse(
        completion=result['completion'],
        language=result['language'],
        confidence=result['confidence'],
        github_pr=result.get('github_pr'),
        pushed_by=current_user.get('github_username') if request.push_to_github else None
    )


@router.post("/code/edit", response_model=EditCodeResponse)
async def edit_code(
    request: EditCodeRequest,
    current_user: User = Depends(get_current_user)
) -> EditCodeResponse:
    """Edit code based on instructions."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    if request.push_to_github and not repo_access['permissions']['push']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have push access to this repository"
        )

    _record_user_access(
        user_id, request.repo_full_name,
        'write' if repo_access['permissions']['push'] else 'read',
        repo_access['permissions']
    )

    result = await ingest_client.edit_code(
        repo_full_name=request.repo_full_name,
        instruction=request.instruction,
        target_file=request.target_file,
        github_token=github_token,
        push_to_github=request.push_to_github
    )

    return EditCodeResponse(
        modified_code=result['modified_code'],
        file=result['file'],
        instruction=result['instruction'],
        chunks_analyzed=result['chunks_analyzed'],
        github_pr=result.get('github_pr'),
        github_branch=result.get('github_branch'),
        pushed_by=current_user.get('github_username') if request.push_to_github else None
    )


@router.post("/search", response_model=SearchCodeResponse)
async def search_code(
    request: SearchCodeRequest,
    current_user: User = Depends(get_current_user)
) -> SearchCodeResponse:
    """Search code."""
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    _record_user_access(user_id, request.repo_full_name, 'read', repo_access['permissions'])

    result = await ingest_client.search_code(
        repo_full_name=request.repo_full_name,
        query=request.query,
        language=request.language,
        top_k=request.top_k
    )

    return SearchCodeResponse(**result)


# ==================== STREAMING ENDPOINTS ====================
# Note: Streaming goes directly to ingest-service via proxy
# Backend adds auth then forwards the stream

@router.post("/ask/stream")
async def ask_question_stream(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_user)
):
    """Ask question with streaming response."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    _record_user_access(user_id, request.repo_full_name, 'read', repo_access['permissions'])

    import httpx
    from app.clients.ingest_service import INGEST_SERVICE_URL

    async def generate():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{INGEST_SERVICE_URL}/pipeline/ask/stream",
                    json={
                        "repo_full_name": request.repo_full_name,
                        "question": request.question,
                        "github_token": github_token,
                        "language": request.language
                    },
                    timeout=300.0
                ) as response:
                    async for chunk in response.aiter_text():
                        yield chunk
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/docs/generate/stream")
async def generate_docs_stream(
    request: GenerateDocsRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate documentation with streaming."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    if request.push_to_github and not repo_access['permissions']['push']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No push access")

    _record_user_access(user_id, request.repo_full_name, 'read', repo_access['permissions'])

    import httpx
    from app.clients.ingest_service import INGEST_SERVICE_URL

    async def generate():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{INGEST_SERVICE_URL}/pipeline/docs/generate/stream",
                    json={
                        "repo_full_name": request.repo_full_name,
                        "target": request.target,
                        "doc_type": request.doc_type,
                        "github_token": github_token,
                        "push_to_github": request.push_to_github
                    },
                    timeout=300.0
                ) as response:
                    async for chunk in response.aiter_text():
                        yield chunk
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/code/edit/stream")
async def edit_code_stream(
    request: EditCodeRequest,
    current_user: User = Depends(get_current_user)
):
    """Edit code with streaming."""
    github_token = get_user_github_token(current_user)
    repo_access = verify_user_repo_access(current_user, request.repo_full_name)
    user_id = current_user.get('id')

    if request.push_to_github and not repo_access['permissions']['push']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No push access")

    _record_user_access(
        user_id, request.repo_full_name,
        'write' if repo_access['permissions']['push'] else 'read',
        repo_access['permissions']
    )

    import httpx
    from app.clients.ingest_service import INGEST_SERVICE_URL

    async def generate():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{INGEST_SERVICE_URL}/pipeline/code/edit/stream",
                    json={
                        "repo_full_name": request.repo_full_name,
                        "instruction": request.instruction,
                        "target_file": request.target_file,
                        "github_token": github_token,
                        "push_to_github": request.push_to_github
                    },
                    timeout=300.0
                ) as response:
                    async for chunk in response.aiter_text():
                        yield chunk
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ==================== USER REPOSITORY MANAGEMENT ====================

@router.get("/repos/user/history")
async def get_user_repo_history(
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """Get user's repository access history with status."""
    try:
        user_id = current_user.get('id')
        user_repos = _get_user_repos(user_id)

        results = []

        for repo in user_repos:
            access_info = _get_access_info(user_id, repo)

            # Check chunk status
            repo_path = _get_shared_repo_path(repo)
            chunks_blob = _processed_bucket.blob(f"{repo_path}/chunks.jsonl")

            indexed = chunks_blob.exists()
            chunk_count = 0
            has_embeddings = False

            if indexed:
                content = chunks_blob.download_as_text()
                chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
                chunk_count = len(chunks)
                has_embeddings = all(c.get('embedding') for c in chunks) if chunks else False

            commit_info = _get_commit_info(repo)
            preferences = _get_user_preferences(user_id, repo)

            results.append({
                'repo': repo,
                'indexed': indexed,
                'total_chunks': chunk_count,
                'has_embeddings': has_embeddings,
                'ready_for_rag': indexed and has_embeddings,
                'access_level': access_info.get('access_level', 'read') if access_info else 'read',
                'permissions': access_info.get('github_permissions', {}) if access_info else {},
                'first_accessed': access_info.get('first_accessed') if access_info else None,
                'last_accessed': access_info.get('last_accessed') if access_info else None,
                'access_count': access_info.get('access_count', 0) if access_info else 0,
                'last_commit_sha': commit_info.get('commit_sha', '')[:8] if commit_info else None,
                'last_commit_author': commit_info.get('author') if commit_info else None,
                'last_updated': commit_info.get('processed_at') if commit_info else None,
                'favorite': preferences.get('favorite', False),
                'auto_push': preferences.get('auto_push_prs', False)
            })

        results.sort(key=lambda x: x.get('last_accessed', ''), reverse=True)
        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )


@router.get("/repos/user/all")
async def list_user_github_repos(
    indexed_only: bool = False,
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """List ALL user's GitHub repositories with index status."""
    try:
        github_token = get_user_github_token(current_user)
        gh = Github(github_token)
        user = gh.get_user()

        repos = []

        for gh_repo in user.get_repos():
            repo_path = _get_shared_repo_path(gh_repo.full_name)
            chunks_blob = _processed_bucket.blob(f"{repo_path}/chunks.jsonl")

            is_indexed = chunks_blob.exists()

            if indexed_only and not is_indexed:
                continue

            chunk_count = 0
            has_embeddings = False

            if is_indexed:
                content = chunks_blob.download_as_text()
                chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
                chunk_count = len(chunks)
                has_embeddings = all(c.get('embedding') for c in chunks) if chunks else False

            repos.append({
                'full_name': gh_repo.full_name,
                'name': gh_repo.name,
                'owner': gh_repo.owner.login,
                'description': gh_repo.description,
                'private': gh_repo.private,
                'default_branch': gh_repo.default_branch,
                'language': gh_repo.language,
                'url': gh_repo.html_url,
                'indexed': is_indexed,
                'total_chunks': chunk_count,
                'has_embeddings': has_embeddings,
                'ready_for_rag': is_indexed and has_embeddings
            })

        return repos

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list repositories: {str(e)}"
        )


# ==================== REPO STATUS & HISTORY ====================

@router.get("/repos/{owner}/{repo}/status")
async def get_repository_status(
    owner: str, repo: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get detailed repository status."""
    result = await ingest_client.get_repo_status(owner, repo)

    # Add user access info
    user_id = current_user.get('id')
    repo_full_name = f"{owner}/{repo}"
    access_info = _get_access_info(user_id, repo_full_name)
    if access_info:
        result['user_access'] = {
            'access_level': access_info.get('access_level'),
            'first_accessed': access_info.get('first_accessed'),
            'last_accessed': access_info.get('last_accessed'),
            'access_count': access_info.get('access_count', 0)
        }

    return result


@router.get("/repos/{owner}/{repo}/commit-history")
async def get_repo_commit_history(
    owner: str, repo: str, limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """Get processing history for a repository."""
    repo_full_name = f"{owner}/{repo}"
    return _get_commit_history(repo_full_name, limit)


@router.get("/repos/{owner}/{repo}/access")
async def check_repo_access(
    owner: str, repo: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Check user's access to a repository."""
    repo_full_name = f"{owner}/{repo}"
    try:
        repo_access = verify_user_repo_access(current_user, repo_full_name)
        return {
            'has_access': True,
            'repo': repo_full_name,
            'permissions': repo_access['permissions'],
            'private': repo_access['repo'].private,
            'can_ingest': True,
            'can_push': repo_access['permissions']['push'] or repo_access['permissions']['admin'],
            'message': 'User has access to this repository'
        }
    except HTTPException as e:
        return {
            'has_access': False,
            'repo': repo_full_name,
            'message': str(e.detail),
            'can_ingest': False,
            'can_push': False
        }


@router.get("/repos/indexed")
async def list_indexed_repos(
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """List all indexed repositories."""
    try:
        repos = []
        all_blobs = _processed_bucket.list_blobs(prefix='repos/')

        for blob in all_blobs:
            if blob.name.endswith('chunks.jsonl'):
                parts = blob.name.split('/')
                if len(parts) >= 4:
                    repo_full_name = f"{parts[1]}/{parts[2]}"
                    try:
                        content = blob.download_as_text()
                        chunk_count = len([l for l in content.split('\n') if l.strip()])
                        commit_info = _get_commit_info(repo_full_name)
                        repos.append({
                            'repo': repo_full_name,
                            'total_chunks': chunk_count,
                            'storage_path': f"repos/{repo_full_name}",
                            'last_commit': commit_info.get('commit_sha', '')[:8] if commit_info else None,
                            'last_updated': commit_info.get('processed_at') if commit_info else None,
                            'last_author': commit_info.get('author') if commit_info else None
                        })
                    except Exception as e:
                        print(f"⚠️  Error processing {repo_full_name}: {e}")

        return repos

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list repos: {str(e)}"
        )


# ==================== USER PREFERENCES ====================

@router.post("/repos/user/preferences")
async def save_user_preferences(
    request: UserPreferencesRequest,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Save user's preferences for a repository."""
    user_id = current_user.get('id')
    preferences = {}
    if request.preferred_doc_type:
        preferences['doc_type'] = request.preferred_doc_type
    if request.preferred_chunk_size:
        preferences['chunk_size'] = request.preferred_chunk_size
    if request.auto_push_prs is not None:
        preferences['auto_push'] = request.auto_push_prs
    if request.favorite is not None:
        preferences['favorite'] = request.favorite
    if request.notifications is not None:
        preferences['notifications'] = request.notifications

    _save_user_preferences(user_id, request.repo_full_name, preferences)
    return {'success': True, 'message': 'Preferences saved', 'repo': request.repo_full_name}


@router.get("/repos/{owner}/{repo}/preferences")
async def get_user_preferences_endpoint(
    owner: str, repo: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get user's preferences for a repository."""
    user_id = current_user.get('id')
    repo_full_name = f"{owner}/{repo}"
    preferences = _get_user_preferences(user_id, repo_full_name)
    return {'repo': repo_full_name, 'preferences': preferences}


# ==================== HEALTH & STATS ====================

@router.get("/health")
async def rag_health() -> Dict:
    """Check RAG service health including ingest-service."""
    ingest_health = await ingest_client.health_check()
    return {
        "status": "healthy",
        "project_id": PROJECT_ID,
        "ingest_service": ingest_health,
        "features": {
            "ingestion": True, "chunking": True, "embedding": True,
            "qa": True, "documentation": True, "code_completion": True,
            "code_editing": True, "github_push": True, "streaming": True,
            "commit_tracking": True, "smart_caching": True,
            "multi_user": True, "user_preferences": True
        }
    }


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get system statistics."""
    try:
        total_repos = 0
        total_chunks = 0
        repos_found = set()

        all_blobs = _processed_bucket.list_blobs(prefix='repos/')
        for blob in all_blobs:
            if blob.name.endswith('chunks.jsonl'):
                parts = blob.name.split('/')
                if len(parts) >= 4:
                    repo_full_name = f"{parts[1]}/{parts[2]}"
                    repos_found.add(repo_full_name)
                    try:
                        content = blob.download_as_text()
                        total_chunks += len([l for l in content.split('\n') if l.strip()])
                    except Exception:
                        pass

        user_blobs = _processed_bucket.list_blobs(prefix='user_data/', delimiter='/')
        total_users = sum(1 for _ in user_blobs.prefixes)

        return {
            'total_indexed_repos': len(repos_found),
            'indexed_repos': sorted(list(repos_found)),
            'total_chunks': total_chunks,
            'total_users_accessed': total_users,
            'storage_architecture': 'shared',
            'project_id': PROJECT_ID
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
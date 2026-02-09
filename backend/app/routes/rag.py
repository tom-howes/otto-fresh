"""
RAG Routes - AI-powered code intelligence for Otto
Uses logged-in user's GitHub token for all operations
Supports: Private repos, User attribution, GitHub push, Local save, Streaming
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.dependencies.auth import get_current_user
from app.models import User
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import sys
import json

# Add ingest-service to path
INGEST_SERVICE_PATH = os.path.join(os.path.dirname(__file__), '../../../ingest-service')
sys.path.insert(0, INGEST_SERVICE_PATH)

from src.rag.rag_services import RAGServices
from src.ingestion.github_ingester import GitHubIngester
from src.chunking.enhanced_chunker import EnhancedCodeChunker
from src.chunking.embedder import ChunkEmbedder
from src.github.github_client import GitHubClient

router = APIRouter(prefix="/rag", tags=["RAG"])

# Configuration (shared settings only, no user tokens!)
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "otto-486221")
BUCKET_RAW = os.getenv("GCS_BUCKET_RAW", "otto-raw-repos")
BUCKET_PROCESSED = os.getenv("GCS_BUCKET_PROCESSED", "otto-processed-chunks")


# ==================== HELPER FUNCTIONS ====================

def get_user_github_token(user: User) -> str:
    """
    Extract GitHub token from authenticated user
    
    Args:
        user: Authenticated user from session
        
    Returns:
        User's GitHub access token
        
    Raises:
        HTTPException: If token not found or expired
    """
    github_token = user.get("github_access_token")
    
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token not found. Please re-authenticate."
        )
    
    return github_token


def get_rag_service(user: User) -> RAGServices:
    """
    Initialize RAG service with user's GitHub token
    
    This ensures:
    - User can only access repos they have permission for
    - PRs are created under user's account
    - Private repos are accessible
    
    Args:
        user: Authenticated user
        
    Returns:
        RAGServices instance configured for this user
    """
    try:
        github_token = get_user_github_token(user)
        
        rag = RAGServices(
            PROJECT_ID, 
            BUCKET_PROCESSED,
            enable_github=True,
            enable_local_save=True
        )
        
        # Override GitHub client to use USER'S token
        rag.github_client = GitHubClient(github_token)
        
        print(f"✓ RAG initialized for user: {user.get('github_username', 'unknown')}")
        
        return rag
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize RAG service: {str(e)}"
        )


def get_user_ingester(user: User) -> GitHubIngester:
    """
    Create ingester with user's GitHub token
    
    Args:
        user: Authenticated user
        
    Returns:
        GitHubIngester configured for this user
    """
    github_token = get_user_github_token(user)
    return GitHubIngester(PROJECT_ID, BUCKET_RAW, github_token)


# ==================== REQUEST/RESPONSE MODELS ====================

class IngestRepoRequest(BaseModel):
    """Request to ingest a repository"""
    repo_full_name: str
    branch: Optional[str] = None


class IngestRepoResponse(BaseModel):
    """Response after ingesting repository"""
    success: bool
    repo: str
    total_files: int
    message: str
    user: str


class ProcessRepoRequest(BaseModel):
    """Request to process (chunk) a repository"""
    repo_full_name: str
    chunk_size: int = 150
    overlap: int = 10


class ProcessRepoResponse(BaseModel):
    """Response after processing repository"""
    success: bool
    repo: str
    total_chunks: int
    message: str


class EmbedRepoRequest(BaseModel):
    """Request to generate embeddings"""
    repo_full_name: str
    force_reembed: bool = False


class EmbedRepoResponse(BaseModel):
    """Response after embedding generation"""
    success: bool
    repo: str
    total_embedded: int
    message: str


class AskQuestionRequest(BaseModel):
    """Request to ask a question"""
    repo_full_name: str
    question: str
    language: Optional[str] = None


class AskQuestionResponse(BaseModel):
    """Response with answer"""
    answer: str
    sources: List[Dict]
    chunks_used: int


class GenerateDocsRequest(BaseModel):
    """Request to generate documentation"""
    repo_full_name: str
    target: str
    doc_type: str = "api"
    push_to_github: bool = False
    save_local: bool = True


class GenerateDocsResponse(BaseModel):
    """Response with generated documentation"""
    documentation: str
    type: str
    files_referenced: int
    local_file: Optional[str] = None
    github_pr: Optional[str] = None
    github_branch: Optional[str] = None
    pushed_by: Optional[str] = None


class CompleteCodeRequest(BaseModel):
    """Request for code completion"""
    repo_full_name: str
    code_context: str
    language: str = "python"
    target_file: Optional[str] = None
    push_to_github: bool = False
    save_local: bool = False


class CompleteCodeResponse(BaseModel):
    """Response with code completion"""
    completion: str
    language: str
    confidence: str
    local_file: Optional[str] = None
    github_pr: Optional[str] = None
    pushed_by: Optional[str] = None


class EditCodeRequest(BaseModel):
    """Request to edit code"""
    repo_full_name: str
    instruction: str
    target_file: str
    push_to_github: bool = False
    save_local: bool = True


class EditCodeResponse(BaseModel):
    """Response with edited code"""
    modified_code: str
    file: str
    instruction: str
    chunks_analyzed: int
    local_file: Optional[str] = None
    github_pr: Optional[str] = None
    github_branch: Optional[str] = None
    pushed_by: Optional[str] = None


class SearchCodeRequest(BaseModel):
    """Request to search code"""
    repo_full_name: str
    query: str
    language: Optional[str] = None
    top_k: int = 10


class SearchCodeResponse(BaseModel):
    """Response with search results"""
    results: List[Dict]
    total_found: int


# ==================== PIPELINE ENDPOINTS ====================

@router.post("/repos/ingest", status_code=status.HTTP_202_ACCEPTED, response_model=IngestRepoResponse)
async def ingest_repository(
    request: IngestRepoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> IngestRepoResponse:
    """
    Ingest a GitHub repository using the logged-in user's access token
    
    Benefits:
    - Can access user's private repositories
    - Respects user's repository permissions
    - No shared GitHub token needed
    
    Args:
        request: Repository details
        current_user: Authenticated user (token from OAuth)
        
    Returns:
        Ingestion status with user attribution
    """
    try:
        ingester = get_user_ingester(current_user)
        metadata = ingester.ingest_repository(request.repo_full_name, request.branch)
        
        return IngestRepoResponse(
            success=True,
            repo=metadata['repo'],
            total_files=metadata['total_files'],
            message=f"Successfully ingested {metadata['total_files']} files",
            user=current_user.get('github_username', 'unknown')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.post("/repos/process", status_code=status.HTTP_202_ACCEPTED, response_model=ProcessRepoResponse)
async def process_repository(
    request: ProcessRepoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> ProcessRepoResponse:
    """
    Process repository into intelligent chunks
    
    Step 2: Chunks code with enhanced context extraction
    
    Args:
        request: Processing parameters
        current_user: Authenticated user
        
    Returns:
        Processing status
    """
    try:
        chunker = EnhancedCodeChunker(PROJECT_ID, BUCKET_RAW, BUCKET_PROCESSED)
        chunker.chunk_size = request.chunk_size
        chunker.overlap_lines = request.overlap
        
        chunks = chunker.process_repository(request.repo_full_name)
        
        return ProcessRepoResponse(
            success=True,
            repo=request.repo_full_name,
            total_chunks=len(chunks),
            message=f"Successfully created {len(chunks)} chunks"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.post("/repos/embed", status_code=status.HTTP_202_ACCEPTED, response_model=EmbedRepoResponse)
async def embed_repository(
    request: EmbedRepoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> EmbedRepoResponse:
    """
    Generate embeddings for repository chunks
    
    Step 3: Creates vector embeddings for semantic search
    
    Args:
        request: Embedding parameters
        current_user: Authenticated user
        
    Returns:
        Embedding status
    """
    try:
        embedder = ChunkEmbedder(PROJECT_ID, BUCKET_PROCESSED)
        stats = embedder.embed_repository(request.repo_full_name, request.force_reembed)
        
        return EmbedRepoResponse(
            success=True,
            repo=request.repo_full_name,
            total_embedded=stats.get('newly_embedded', 0),
            message=f"Successfully embedded {stats.get('newly_embedded', 0)} chunks"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding failed: {str(e)}"
        )


# ==================== RAG SERVICE ENDPOINTS ====================

@router.post("/ask", status_code=status.HTTP_200_OK, response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_user)
) -> AskQuestionResponse:
    """
    Ask a question about the codebase
    
    Uses user's token to access their repositories
    
    Args:
        request: Question and repository
        current_user: Authenticated user
        
    Returns:
        Answer with source references
    """
    rag = get_rag_service(current_user)
    
    try:
        result = rag.answer_question(
            question=request.question,
            repo_path=request.repo_full_name,
            language=request.language,
            stream=False
        )
        
        return AskQuestionResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}"
        )


@router.post("/docs/generate", status_code=status.HTTP_200_OK, response_model=GenerateDocsResponse)
async def generate_documentation(
    request: GenerateDocsRequest,
    current_user: User = Depends(get_current_user)
) -> GenerateDocsResponse:
    """
    Generate documentation
    
    When push_to_github=true:
    - Creates branch under user's account
    - Creates PR attributed to the user
    - Uses user's permissions
    
    Args:
        request: Documentation parameters
        current_user: Authenticated user
        
    Returns:
        Generated documentation with optional PR link
    """
    rag = get_rag_service(current_user)
    
    valid_doc_types = ['api', 'user_guide', 'technical', 'readme']
    if request.doc_type not in valid_doc_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid doc_type. Must be one of: {valid_doc_types}"
        )
    
    try:
        result = rag.generate_documentation(
            target=request.target,
            repo_path=request.repo_full_name,
            doc_type=request.doc_type,
            stream=False,
            push_to_github=request.push_to_github,
            save_local=request.save_local
        )
        
        response_data = {
            'documentation': result['documentation'],
            'type': result['type'],
            'files_referenced': result['files_referenced'],
            'local_file': result.get('local_file'),
            'github_pr': result.get('github', {}).get('pr_url'),
            'github_branch': result.get('github', {}).get('branch'),
            'pushed_by': current_user.get('github_username') if request.push_to_github else None
        }
        
        return GenerateDocsResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate documentation: {str(e)}"
        )


@router.post("/code/complete", status_code=status.HTTP_200_OK, response_model=CompleteCodeResponse)
async def complete_code(
    request: CompleteCodeRequest,
    current_user: User = Depends(get_current_user)
) -> CompleteCodeResponse:
    """
    Get intelligent code completion
    
    Args:
        request: Code context and options
        current_user: Authenticated user
        
    Returns:
        Code completion with optional GitHub PR
    """
    rag = get_rag_service(current_user)
    
    try:
        result = rag.complete_code(
            code_context=request.code_context,
            cursor_position="",
            repo_path=request.repo_full_name,
            language=request.language,
            stream=False,
            push_to_github=request.push_to_github,
            save_local=request.save_local,
            target_file=request.target_file
        )
        
        response_data = {
            'completion': result['completion'],
            'language': result['language'],
            'confidence': result['confidence'],
            'local_file': result.get('local_file'),
            'github_pr': result.get('github', {}).get('pr_url'),
            'pushed_by': current_user.get('github_username') if request.push_to_github else None
        }
        
        return CompleteCodeResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate completion: {str(e)}"
        )


@router.post("/code/edit", status_code=status.HTTP_200_OK, response_model=EditCodeResponse)
async def edit_code(
    request: EditCodeRequest,
    current_user: User = Depends(get_current_user)
) -> EditCodeResponse:
    """
    Edit code based on instructions
    
    When push_to_github=true:
    - Creates branch under user's account
    - Commits with user's identity
    - Creates PR from user's account
    
    Args:
        request: Edit instruction and options
        current_user: Authenticated user
        
    Returns:
        Modified code with optional PR link
    """
    rag = get_rag_service(current_user)
    
    try:
        result = rag.edit_code(
            instruction=request.instruction,
            target_file=request.target_file,
            repo_path=request.repo_full_name,
            stream=False,
            push_to_github=request.push_to_github,
            save_local=request.save_local
        )
        
        if result.get('error'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['error']
            )
        
        response_data = {
            'modified_code': result['modified_code'],
            'file': result['file'],
            'instruction': result['instruction'],
            'chunks_analyzed': result['chunks_analyzed'],
            'local_file': result.get('local_file'),
            'github_pr': result.get('github', {}).get('pr_url'),
            'github_branch': result.get('github', {}).get('branch'),
            'pushed_by': current_user.get('github_username') if request.push_to_github else None
        }
        
        return EditCodeResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit code: {str(e)}"
        )


@router.post("/search", status_code=status.HTTP_200_OK, response_model=SearchCodeResponse)
async def search_code(
    request: SearchCodeRequest,
    current_user: User = Depends(get_current_user)
) -> SearchCodeResponse:
    """
    Search code using semantic or keyword search
    
    Args:
        request: Search query
        current_user: Authenticated user
        
    Returns:
        Relevant code chunks
    """
    rag = get_rag_service(current_user)
    
    try:
        chunks = rag.search.search(
            query=request.query,
            repo_path=request.repo_full_name,
            top_k=request.top_k,
            filter_language=request.language
        )
        
        results = [
            {
                'file_path': chunk['file_path'],
                'chunk_type': chunk['chunk_type'],
                'language': chunk['language'],
                'lines': f"{chunk['start_line']}-{chunk['end_line']}",
                'content': chunk['content'][:500],
                'summary': chunk.get('summary', '')
            }
            for chunk in chunks
        ]
        
        return SearchCodeResponse(
            results=results,
            total_found=len(results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# ==================== STREAMING ENDPOINTS ====================

@router.post("/ask/stream")
async def ask_question_stream(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_user)
):
    """Ask question with streaming response"""
    rag = get_rag_service(current_user)
    
    async def generate():
        try:
            result = rag.answer_question(
                question=request.question,
                repo_path=request.repo_full_name,
                language=request.language,
                stream=True
            )
            
            for chunk in result['answer_stream']:
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'sources', 'sources': result['sources']})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/docs/generate/stream")
async def generate_documentation_stream(
    request: GenerateDocsRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate documentation with streaming response"""
    rag = get_rag_service(current_user)
    
    async def generate():
        try:
            result = rag.generate_documentation(
                target=request.target,
                repo_path=request.repo_full_name,
                doc_type=request.doc_type,
                stream=True,
                push_to_github=False,
                save_local=False
            )
            
            full_response = []
            
            for chunk in result['documentation_stream']:
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            complete_doc = ''.join(full_response)
            
            if request.save_local:
                local_path = rag.doc_manager.save_documentation(
                    complete_doc, request.target, request.doc_type, request.repo_full_name
                )
                yield f"data: {json.dumps({'type': 'saved', 'path': local_path})}\n\n"
            
            if request.push_to_github:
                github_result = rag.github_client.push_documentation(
                    request.repo_full_name, complete_doc, request.target, 
                    request.doc_type, create_pr=True
                )
                if github_result.get('success'):
                    yield f"data: {json.dumps({'type': 'pushed', 'pr_url': github_result.get('pr_url'), 'branch': github_result.get('branch'), 'user': current_user.get('github_username')})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/code/edit/stream")
async def edit_code_stream(
    request: EditCodeRequest,
    current_user: User = Depends(get_current_user)
):
    """Edit code with streaming response"""
    rag = get_rag_service(current_user)
    
    async def generate():
        try:
            result = rag.edit_code(
                instruction=request.instruction,
                target_file=request.target_file,
                repo_path=request.repo_full_name,
                stream=True,
                push_to_github=False,
                save_local=False
            )
            
            full_response = []
            
            for chunk in result['modified_code_stream']:
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            complete_code = ''.join(full_response)
            code_content = rag._extract_code_from_response(complete_code)
            
            if request.save_local:
                local_path = rag.doc_manager.save_edited_code(
                    code_content, request.target_file, request.repo_full_name, request.instruction
                )
                yield f"data: {json.dumps({'type': 'saved', 'path': local_path})}\n\n"
            
            if request.push_to_github:
                github_result = rag.github_client.create_branch_and_push_code(
                    request.repo_full_name, request.target_file, code_content, request.instruction
                )
                if github_result.get('success'):
                    yield f"data: {json.dumps({'type': 'pushed', 'pr_url': github_result.get('pr_url'), 'branch': github_result.get('branch'), 'user': current_user.get('github_username')})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ==================== REPOSITORY MANAGEMENT ====================

@router.get("/repos/user", status_code=status.HTTP_200_OK)
async def list_user_repos(
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """
    List all repositories accessible to the current user
    
    Shows both indexed and non-indexed repos
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List of user's repositories with index status
    """
    from github import Github
    
    try:
        github_token = get_user_github_token(current_user)
        github_client = Github(github_token)
        
        user = github_client.get_user()
        repos = []
        
        # Check GCS for indexed repos
        from google.cloud import storage
        gcs_client = storage.Client(project=PROJECT_ID)
        bucket = gcs_client.bucket(BUCKET_PROCESSED)
        
        for gh_repo in user.get_repos():
            repo_path = gh_repo.full_name
            chunks_blob = bucket.blob(f"{repo_path}/chunks.jsonl")
            
            is_indexed = chunks_blob.exists()
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


@router.get("/repos/{owner}/{repo}/status", status_code=status.HTTP_200_OK)
async def get_repository_status(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Check repository index status
    
    Returns pipeline completion status:
    - Ingested (files in GCS)
    - Chunked (intelligent chunks created)
    - Embedded (vector embeddings ready)
    
    Args:
        owner: Repository owner
        repo: Repository name
        current_user: Authenticated user
        
    Returns:
        Detailed pipeline status
    """
    from google.cloud import storage
    
    repo_path = f"{owner}/{repo}"
    client = storage.Client(project=PROJECT_ID)
    
    status_info = {
        'repo': repo_path,
        'ingested': False,
        'chunked': False,
        'embedded': False,
        'ready_for_rag': False,
        'total_files': 0,
        'total_chunks': 0,
        'chunks_with_embeddings': 0,
        'pipeline_progress': 0  # 0-100%
    }
    
    try:
        # Check ingestion
        raw_bucket = client.bucket(BUCKET_RAW)
        metadata_blob = raw_bucket.blob(f"{repo_path}/metadata.json")
        
        if metadata_blob.exists():
            status_info['ingested'] = True
            status_info['pipeline_progress'] = 33
            metadata = json.loads(metadata_blob.download_as_text())
            status_info['total_files'] = metadata.get('total_files', 0)
        
        # Check chunking
        processed_bucket = client.bucket(BUCKET_PROCESSED)
        chunks_blob = processed_bucket.blob(f"{repo_path}/chunks.jsonl")
        
        if chunks_blob.exists():
            status_info['chunked'] = True
            status_info['pipeline_progress'] = 66
            content = chunks_blob.download_as_text()
            chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
            status_info['total_chunks'] = len(chunks)
            
            # Check embeddings
            chunks_with_emb = sum(1 for c in chunks if c.get('embedding'))
            status_info['chunks_with_embeddings'] = chunks_with_emb
            
            if chunks_with_emb == len(chunks) and len(chunks) > 0:
                status_info['embedded'] = True
                status_info['pipeline_progress'] = 100
                status_info['ready_for_rag'] = True
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check status: {str(e)}"
        )


@router.get("/repos/{owner}/{repo}/access", status_code=status.HTTP_200_OK)
async def check_repo_access(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Check if user has access to a repository
    
    Verifies user's permissions before ingestion
    
    Args:
        owner: Repository owner
        repo: Repository name
        current_user: Authenticated user
        
    Returns:
        Access permissions and capabilities
    """
    from github import Github, GithubException
    
    try:
        github_token = get_user_github_token(current_user)
        github_client = Github(github_token)
        
        gh_repo = github_client.get_repo(f"{owner}/{repo}")
        permissions = gh_repo.permissions
        
        return {
            'has_access': True,
            'repo': f"{owner}/{repo}",
            'permissions': {
                'admin': permissions.admin,
                'push': permissions.push,
                'pull': permissions.pull
            },
            'private': gh_repo.private,
            'can_ingest': True,
            'can_push': permissions.push or permissions.admin,
            'message': 'User has access to this repository'
        }
        
    except GithubException as e:
        if e.status == 404:
            return {
                'has_access': False,
                'repo': f"{owner}/{repo}",
                'message': 'Repository not found or no access',
                'can_ingest': False,
                'can_push': False
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check access: {str(e)}"
        )


@router.get("/repos/indexed", status_code=status.HTTP_200_OK)
async def list_indexed_repos(
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """
    List all indexed repositories in the system
    
    Args:
        current_user: Authenticated user
        
    Returns:
        All indexed repositories (system-wide)
    """
    from google.cloud import storage
    
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(BUCKET_PROCESSED)
        
        blobs = bucket.list_blobs(delimiter='/')
        repos = []
        
        for prefix in blobs.prefixes:
            repo_path = prefix.rstrip('/')
            chunks_blob = bucket.blob(f"{repo_path}/chunks.jsonl")
            
            if chunks_blob.exists():
                content = chunks_blob.download_as_text()
                chunk_count = len([line for line in content.split('\n') if line.strip()])
                
                repos.append({
                    'repo': repo_path,
                    'total_chunks': chunk_count,
                    'storage_url': f"gs://{BUCKET_PROCESSED}/{repo_path}/chunks.jsonl"
                })
        
        return repos
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list repos: {str(e)}"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def rag_health() -> Dict:
    """
    Check RAG service health
    
    Returns:
        Health status and available features
    """
    try:
        from google.cloud import storage
        client = storage.Client(project=PROJECT_ID)
        
        return {
            "status": "healthy",
            "project_id": PROJECT_ID,
            "buckets": {
                "raw": BUCKET_RAW,
                "processed": BUCKET_PROCESSED
            },
            "features": {
                "ingestion": True,
                "chunking": True,
                "embedding": True,
                "qa": True,
                "documentation": True,
                "code_completion": True,
                "code_editing": True,
                "github_push": True,
                "local_save": True,
                "streaming": True,
                "user_tokens": True,
                "private_repos": True
            },
            "authentication": "User OAuth tokens from session"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
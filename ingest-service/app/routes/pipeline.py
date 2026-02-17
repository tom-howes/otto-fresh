"""
Pipeline routes - Ingest, Chunk, Embed, and full pipeline orchestration
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
import json

from src.ingestion.github_ingester import GitHubIngester
from src.chunking.enhanced_chunker import EnhancedCodeChunker
from src.chunking.embedder import ChunkEmbedder
from src.rag.rag_services import RAGServices
from src.rag.vector_search import VectorSearch
from src.github.github_client import GitHubClient
from src.utils.storage_utils import get_shared_repo_path
from src.utils.commit_tracker import CommitTracker

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "otto-pm")
BUCKET_RAW = os.getenv("GCS_BUCKET_RAW", "otto-raw-repos")
BUCKET_PROCESSED = os.getenv("GCS_BUCKET_PROCESSED", "otto-processed-chunks")

# Initialize shared components
commit_tracker = CommitTracker(PROJECT_ID, BUCKET_PROCESSED)


# ==================== REQUEST/RESPONSE MODELS ====================

class IngestRequest(BaseModel):
    repo_full_name: str
    branch: Optional[str] = None
    github_token: str


class IngestResponse(BaseModel):
    success: bool
    repo: str
    total_files: int
    commit_sha: Optional[str] = None
    message: str
    was_cached: bool


class ChunkRequest(BaseModel):
    repo_full_name: str
    chunk_size: int = 150
    overlap: int = 10


class ChunkResponse(BaseModel):
    success: bool
    repo: str
    total_chunks: int
    message: str


class EmbedRequest(BaseModel):
    repo_full_name: str
    force_reembed: bool = False


class EmbedResponse(BaseModel):
    success: bool
    repo: str
    total_embedded: int
    message: str


class FullPipelineRequest(BaseModel):
    """Run the complete pipeline: ingest → chunk → embed"""
    repo_full_name: str
    branch: Optional[str] = None
    github_token: str
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


class AskRequest(BaseModel):
    repo_full_name: str
    question: str
    language: Optional[str] = None
    github_token: str


class AskResponse(BaseModel):
    answer: str
    sources: List[Dict]
    chunks_used: int


class GenerateDocsRequest(BaseModel):
    repo_full_name: str
    target: str
    doc_type: str = "api"
    github_token: str
    push_to_github: bool = False
    save_local: bool = False


class GenerateDocsResponse(BaseModel):
    documentation: str
    type: str
    files_referenced: int
    github_pr: Optional[str] = None
    github_branch: Optional[str] = None


class CodeCompleteRequest(BaseModel):
    repo_full_name: str
    code_context: str
    language: str = "python"
    target_file: Optional[str] = None
    github_token: str
    push_to_github: bool = False


class CodeCompleteResponse(BaseModel):
    completion: str
    language: str
    confidence: str
    github_pr: Optional[str] = None


class CodeEditRequest(BaseModel):
    repo_full_name: str
    instruction: str
    target_file: str
    github_token: str
    push_to_github: bool = False
    save_local: bool = False


class CodeEditResponse(BaseModel):
    modified_code: str
    file: str
    instruction: str
    chunks_analyzed: int
    github_pr: Optional[str] = None
    github_branch: Optional[str] = None


class SearchRequest(BaseModel):
    repo_full_name: str
    query: str
    language: Optional[str] = None
    top_k: int = 10


class SearchResponse(BaseModel):
    results: List[Dict]
    total_found: int


class RepoStatusResponse(BaseModel):
    repo: str
    ingested: bool
    chunked: bool
    embedded: bool
    ready_for_rag: bool
    total_files: int
    total_chunks: int
    pipeline_progress: int
    commit_info: Optional[Dict] = None


# ==================== PIPELINE ENDPOINTS ====================

@router.post("/ingest", response_model=IngestResponse)
async def ingest_repository(request: IngestRequest):
    """
    Step 1: Ingest repository from GitHub into GCS.
    Checks commit tracker for smart caching.
    """
    try:
        repo_path = get_shared_repo_path(request.repo_full_name)

        # Check if update needed
        from github import Github
        gh = Github(request.github_token)
        gh_repo = gh.get_repo(request.repo_full_name)
        branch = request.branch or gh_repo.default_branch
        current_sha = gh_repo.get_branch(branch).commit.sha

        needs_update, reason = commit_tracker.needs_update(
            request.repo_full_name, current_sha
        )

        if not needs_update:
            return IngestResponse(
                success=True,
                repo=request.repo_full_name,
                total_files=0,
                commit_sha=current_sha[:8],
                message=f"Already up to date. {reason}",
                was_cached=True
            )

        # Run ingestion
        ingester = GitHubIngester(PROJECT_ID, BUCKET_RAW, request.github_token)
        metadata = ingester.ingest_repository(request.repo_full_name, request.branch)

        # Save commit info
        commit = gh_repo.get_branch(branch).commit
        commit_tracker.save_commit_info(
            request.repo_full_name,
            current_sha,
            branch,
            commit.author.login if commit.author else "unknown",
            commit.commit.message.split('\n')[0] if commit.commit else None
        )

        return IngestResponse(
            success=True,
            repo=request.repo_full_name,
            total_files=metadata['total_files'],
            commit_sha=current_sha[:8],
            message=f"Ingested {metadata['total_files']} files. {reason}",
            was_cached=False
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.post("/chunk", response_model=ChunkResponse)
async def chunk_repository(request: ChunkRequest):
    """Step 2: Chunk ingested repository code into semantic pieces."""
    try:
        repo_path = get_shared_repo_path(request.repo_full_name)

        chunker = EnhancedCodeChunker(PROJECT_ID, BUCKET_RAW, BUCKET_PROCESSED)
        chunker.chunk_size = request.chunk_size
        chunker.overlap_lines = request.overlap

        chunks = chunker.process_repository(repo_path)

        return ChunkResponse(
            success=True,
            repo=request.repo_full_name,
            total_chunks=len(chunks),
            message=f"Created {len(chunks)} chunks"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunking failed: {str(e)}"
        )


@router.post("/embed", response_model=EmbedResponse)
async def embed_repository(request: EmbedRequest):
    """Step 3: Generate embeddings for chunked code."""
    try:
        repo_path = get_shared_repo_path(request.repo_full_name)

        embedder = ChunkEmbedder(PROJECT_ID, BUCKET_PROCESSED)
        stats = embedder.embed_repository(repo_path, request.force_reembed)

        return EmbedResponse(
            success=True,
            repo=request.repo_full_name,
            total_embedded=stats.get('newly_embedded', 0),
            message=f"Embedded {stats.get('newly_embedded', 0)} chunks"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding failed: {str(e)}"
        )


@router.post("/run", response_model=FullPipelineResponse)
async def run_full_pipeline(request: FullPipelineRequest):
    """
    Run the complete pipeline: Ingest → Chunk → Embed
    
    This is the main endpoint called by:
    - Backend when user triggers indexing
    - Webhook handler on push events
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 FULL PIPELINE: {request.repo_full_name}")
        print(f"{'='*60}")

        # ---- Step 1: Ingest ----
        print(f"\n📥 Step 1/3: Ingesting...")
        ingest_result = await ingest_repository(IngestRequest(
            repo_full_name=request.repo_full_name,
            branch=request.branch,
            github_token=request.github_token
        ))

        if ingest_result.was_cached:
            # Check if chunks and embeddings already exist
            repo_path = get_shared_repo_path(request.repo_full_name)
            from google.cloud import storage
            client = storage.Client(project=PROJECT_ID)
            bucket = client.bucket(BUCKET_PROCESSED)
            chunks_blob = bucket.blob(f"{repo_path}/chunks.jsonl")

            if chunks_blob.exists():
                content = chunks_blob.download_as_text()
                chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
                has_embeddings = all(c.get('embedding') for c in chunks) if chunks else False

                if has_embeddings:
                    return FullPipelineResponse(
                        success=True,
                        repo=request.repo_full_name,
                        total_files=0,
                        total_chunks=len(chunks),
                        total_embedded=len(chunks),
                        commit_sha=ingest_result.commit_sha,
                        was_cached=True,
                        message="Repository already fully indexed and up to date"
                    )

        # ---- Step 2: Chunk ----
        print(f"\n🔪 Step 2/3: Chunking...")
        chunk_result = await chunk_repository(ChunkRequest(
            repo_full_name=request.repo_full_name,
            chunk_size=request.chunk_size,
            overlap=request.overlap
        ))

        # ---- Step 3: Embed ----
        print(f"\n🧮 Step 3/3: Embedding...")
        embed_result = await embed_repository(EmbedRequest(
            repo_full_name=request.repo_full_name,
            force_reembed=request.force_reembed
        ))

        print(f"\n{'='*60}")
        print(f"✅ PIPELINE COMPLETE")
        print(f"   Files: {ingest_result.total_files}")
        print(f"   Chunks: {chunk_result.total_chunks}")
        print(f"   Embedded: {embed_result.total_embedded}")
        print(f"{'='*60}\n")

        return FullPipelineResponse(
            success=True,
            repo=request.repo_full_name,
            total_files=ingest_result.total_files,
            total_chunks=chunk_result.total_chunks,
            total_embedded=embed_result.total_embedded,
            commit_sha=ingest_result.commit_sha,
            was_cached=False,
            message="Pipeline complete"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {str(e)}"
        )


# ==================== RAG SERVICE ENDPOINTS ====================

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask a question about the codebase using RAG."""
    try:
        rag = RAGServices(PROJECT_ID, BUCKET_PROCESSED,
                         enable_github=True, enable_local_save=False)
        rag.github_client = GitHubClient(request.github_token)

        repo_path = get_shared_repo_path(request.repo_full_name)
        result = rag.answer_question(
            question=request.question,
            repo_path=repo_path,
            language=request.language,
            stream=False
        )

        return AskResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A failed: {str(e)}"
        )


@router.post("/docs/generate", response_model=GenerateDocsResponse)
async def generate_docs(request: GenerateDocsRequest):
    """Generate documentation for a codebase."""
    try:
        rag = RAGServices(PROJECT_ID, BUCKET_PROCESSED,
                         enable_github=True, enable_local_save=False)
        rag.github_client = GitHubClient(request.github_token)

        repo_path = get_shared_repo_path(request.repo_full_name)
        result = rag.generate_documentation(
            target=request.target,
            repo_path=repo_path,
            doc_type=request.doc_type,
            stream=False,
            push_to_github=request.push_to_github,
            save_local=False
        )

        return GenerateDocsResponse(
            documentation=result['documentation'],
            type=result['type'],
            files_referenced=result['files_referenced'],
            github_pr=result.get('github', {}).get('pr_url'),
            github_branch=result.get('github', {}).get('branch')
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Documentation generation failed: {str(e)}"
        )


@router.post("/code/complete", response_model=CodeCompleteResponse)
async def complete_code(request: CodeCompleteRequest):
    """Get intelligent code completion."""
    try:
        rag = RAGServices(PROJECT_ID, BUCKET_PROCESSED,
                         enable_github=True, enable_local_save=False)
        rag.github_client = GitHubClient(request.github_token)

        repo_path = get_shared_repo_path(request.repo_full_name)
        result = rag.complete_code(
            code_context=request.code_context,
            cursor_position="",
            repo_path=repo_path,
            language=request.language,
            stream=False,
            push_to_github=request.push_to_github,
            save_local=False,
            target_file=request.target_file
        )

        return CodeCompleteResponse(
            completion=result['completion'],
            language=result['language'],
            confidence=result['confidence'],
            github_pr=result.get('github', {}).get('pr_url')
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code completion failed: {str(e)}"
        )


@router.post("/code/edit", response_model=CodeEditResponse)
async def edit_code(request: CodeEditRequest):
    """Edit code based on instructions."""
    try:
        rag = RAGServices(PROJECT_ID, BUCKET_PROCESSED,
                         enable_github=True, enable_local_save=False)
        rag.github_client = GitHubClient(request.github_token)

        repo_path = get_shared_repo_path(request.repo_full_name)
        result = rag.edit_code(
            instruction=request.instruction,
            target_file=request.target_file,
            repo_path=repo_path,
            stream=False,
            push_to_github=request.push_to_github,
            save_local=False
        )

        if result.get('error'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['error']
            )

        return CodeEditResponse(
            modified_code=result['modified_code'],
            file=result['file'],
            instruction=result['instruction'],
            chunks_analyzed=result['chunks_analyzed'],
            github_pr=result.get('github', {}).get('pr_url'),
            github_branch=result.get('github', {}).get('branch')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code edit failed: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_code(request: SearchRequest):
    """Search code using vector similarity."""
    try:
        search = VectorSearch(PROJECT_ID, BUCKET_PROCESSED)
        repo_path = get_shared_repo_path(request.repo_full_name)

        chunks = search.search(
            query=request.query,
            repo_path=repo_path,
            top_k=request.top_k,
            filter_language=request.language
        )

        results = [
            {
                'file_path': c['file_path'],
                'chunk_type': c['chunk_type'],
                'language': c['language'],
                'lines': f"{c['start_line']}-{c['end_line']}",
                'content': c['content'][:500],
                'summary': c.get('summary', '')
            }
            for c in chunks
        ]

        return SearchResponse(results=results, total_found=len(results))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# ==================== STATUS ENDPOINTS ====================

@router.get("/repos/{owner}/{repo}/status", response_model=RepoStatusResponse)
async def get_repo_status(owner: str, repo: str):
    """Get pipeline status for a repository."""
    from google.cloud import storage

    repo_full_name = f"{owner}/{repo}"
    repo_path = get_shared_repo_path(repo_full_name)

    status_info = {
        'repo': repo_full_name,
        'ingested': False,
        'chunked': False,
        'embedded': False,
        'ready_for_rag': False,
        'total_files': 0,
        'total_chunks': 0,
        'pipeline_progress': 0,
        'commit_info': None
    }

    try:
        client = storage.Client(project=PROJECT_ID)

        # Check ingestion
        raw_bucket = client.bucket(BUCKET_RAW)
        metadata_blob = raw_bucket.blob(f"{repo_path}/metadata.json")

        if metadata_blob.exists():
            status_info['ingested'] = True
            status_info['pipeline_progress'] = 33
            metadata = json.loads(metadata_blob.download_as_text())
            status_info['total_files'] = metadata.get('total_files', 0)

        # Check chunks
        processed_bucket = client.bucket(BUCKET_PROCESSED)
        chunks_blob = processed_bucket.blob(f"{repo_path}/chunks.jsonl")

        if chunks_blob.exists():
            status_info['chunked'] = True
            status_info['pipeline_progress'] = 66
            content = chunks_blob.download_as_text()
            chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
            status_info['total_chunks'] = len(chunks)

            embedded_count = sum(1 for c in chunks if c.get('embedding'))
            if embedded_count == len(chunks) and len(chunks) > 0:
                status_info['embedded'] = True
                status_info['pipeline_progress'] = 100
                status_info['ready_for_rag'] = True

        # Commit info
        commit_info = commit_tracker.get_last_commit(repo_full_name)
        if commit_info:
            status_info['commit_info'] = {
                'sha': commit_info.get('commit_sha', '')[:8],
                'author': commit_info.get('author'),
                'message': commit_info.get('commit_message'),
                'processed_at': commit_info.get('processed_at')
            }

        return RepoStatusResponse(**status_info)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )
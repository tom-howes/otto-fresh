"""
HTTP client for calling the Ingest Service API.
Replaces direct imports from ingest-service.
"""
import httpx
import os
from typing import Dict, Optional, List
from fastapi import HTTPException, status

INGEST_SERVICE_URL = os.getenv("INGEST_SERVICE_URL", "http://localhost:8081")
TIMEOUT = 300.0  # 5 min timeout for pipeline operations


class IngestServiceClient:
    """
    HTTP client for the ingest-service API.
    
    All RAG pipeline operations go through this client.
    The backend no longer imports from ingest-service directly.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or INGEST_SERVICE_URL

    async def health_check(self) -> Dict:
        """Check if ingest service is running."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health", timeout=10.0)
                return response.json()
            except httpx.ConnectError:
                return {"status": "unreachable", "url": self.base_url}

    # ==================== PIPELINE ====================

    async def run_full_pipeline(self, repo_full_name: str, github_token: str,
                                branch: Optional[str] = None,
                                chunk_size: int = 150, overlap: int = 10,
                                force_reembed: bool = False) -> Dict:
        """Run full pipeline: ingest → chunk → embed"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/run",
                    json={
                        "repo_full_name": repo_full_name,
                        "branch": branch,
                        "github_token": github_token,
                        "chunk_size": chunk_size,
                        "overlap": overlap,
                        "force_reembed": force_reembed
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def ingest_repository(self, repo_full_name: str, github_token: str,
                                branch: Optional[str] = None) -> Dict:
        """Step 1: Ingest only"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/ingest",
                    json={
                        "repo_full_name": repo_full_name,
                        "branch": branch,
                        "github_token": github_token
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def chunk_repository(self, repo_full_name: str,
                               chunk_size: int = 150, overlap: int = 10) -> Dict:
        """Step 2: Chunk only"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/chunk",
                    json={
                        "repo_full_name": repo_full_name,
                        "chunk_size": chunk_size,
                        "overlap": overlap
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def embed_repository(self, repo_full_name: str,
                               force_reembed: bool = False) -> Dict:
        """Step 3: Embed only"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/embed",
                    json={
                        "repo_full_name": repo_full_name,
                        "force_reembed": force_reembed
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    # ==================== RAG SERVICES ====================

    async def ask_question(self, repo_full_name: str, question: str,
                           github_token: str, language: Optional[str] = None) -> Dict:
        """Ask a question about the codebase."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/ask",
                    json={
                        "repo_full_name": repo_full_name,
                        "question": question,
                        "github_token": github_token,
                        "language": language
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def generate_docs(self, repo_full_name: str, target: str,
                            github_token: str, doc_type: str = "api",
                            push_to_github: bool = False) -> Dict:
        """Generate documentation."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/docs/generate",
                    json={
                        "repo_full_name": repo_full_name,
                        "target": target,
                        "doc_type": doc_type,
                        "github_token": github_token,
                        "push_to_github": push_to_github
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def complete_code(self, repo_full_name: str, code_context: str,
                            github_token: str, language: str = "python",
                            target_file: Optional[str] = None,
                            push_to_github: bool = False) -> Dict:
        """Get code completion."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/code/complete",
                    json={
                        "repo_full_name": repo_full_name,
                        "code_context": code_context,
                        "language": language,
                        "target_file": target_file,
                        "github_token": github_token,
                        "push_to_github": push_to_github
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def edit_code(self, repo_full_name: str, instruction: str,
                        target_file: str, github_token: str,
                        push_to_github: bool = False) -> Dict:
        """Edit code based on instructions."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/code/edit",
                    json={
                        "repo_full_name": repo_full_name,
                        "instruction": instruction,
                        "target_file": target_file,
                        "github_token": github_token,
                        "push_to_github": push_to_github
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def search_code(self, repo_full_name: str, query: str,
                          language: Optional[str] = None, top_k: int = 10) -> Dict:
        """Search code."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/search",
                    json={
                        "repo_full_name": repo_full_name,
                        "query": query,
                        "language": language,
                        "top_k": top_k
                    },
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )

    async def get_repo_status(self, owner: str, repo: str) -> Dict:
        """Get pipeline status for a repo."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/pipeline/repos/{owner}/{repo}/status",
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", str(e))
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ingest service is unavailable"
                )
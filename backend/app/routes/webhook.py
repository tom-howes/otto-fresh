# backend/app/routes/webhook.py
"""
GitHub Webhook handler for auto-updating RAG embeddings on push events.

Flow:
1. GitHub sends push event to /webhook/github
2. We verify the HMAC signature
3. Check if the repo is indexed AND the pushing user is logged in
4. Kick off async re-ingestion pipeline (ingest → chunk → embed)
5. Return 200 immediately so GitHub doesn't timeout
"""
import hashlib
import hmac
import json
from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from typing import Dict, Optional
from datetime import datetime

from app.config import GITHUB_WEBHOOK_SECRET

router = APIRouter(prefix="/webhook", tags=["Webhooks"])

# In-memory tracker for active sessions (user_id -> github_username mapping)
# This gets populated when users log in and cleared on logout
_active_sessions: Dict[str, dict] = {}


def register_active_user(user_id: str, github_username: str, github_access_token: str, 
                         installation_id: Optional[str] = None):
    """
    Register a user as active (logged in) so webhooks can trigger for their repos.
    
    Call this from your auth flow after successful login.
    
    Args:
        user_id: Firebase user ID
        github_username: GitHub username
        github_access_token: User's OAuth token for re-ingestion
        installation_id: GitHub App installation ID (if available)
    """
    _active_sessions[github_username.lower()] = {
        'user_id': user_id,
        'github_username': github_username,
        'github_access_token': github_access_token,
        'installation_id': installation_id,
        'logged_in_at': datetime.now().isoformat()
    }
    print(f"✓ Registered active user for webhooks: {github_username}")


def unregister_active_user(github_username: str):
    """Remove user from active sessions on logout."""
    key = github_username.lower()
    if key in _active_sessions:
        del _active_sessions[key]
        print(f"✓ Unregistered user from webhooks: {github_username}")


def get_active_user_for_repo(repo_owner: str) -> Optional[dict]:
    """
    Check if the repo owner (or a collaborator) has an active session.
    
    Args:
        repo_owner: GitHub username or org that owns the repo
        
    Returns:
        Active session dict if found, None otherwise
    """
    # Direct match - repo owner is logged in
    key = repo_owner.lower()
    if key in _active_sessions:
        return _active_sessions[key]
    
    # For org repos, check if any active user might have access
    # (In production, you'd check collaborator lists)
    return None


def verify_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verify GitHub webhook HMAC-SHA256 signature.
    
    GitHub sends the signature in the X-Hub-Signature-256 header.
    We compute our own HMAC using the shared secret and compare.
    
    Args:
        payload_body: Raw request body bytes
        signature_header: Value of X-Hub-Signature-256 header
        
    Returns:
        True if signature is valid
    """
    if not GITHUB_WEBHOOK_SECRET:
        print("⚠️  No webhook secret configured - skipping verification")
        return True
    
    if not signature_header:
        return False
    
    expected_signature = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)


# In webhook.py, replace the run_rag_update_pipeline function:

async def run_rag_update_pipeline(
    repo_full_name: str,
    branch: str,
    commit_sha: str,
    commit_message: str,
    commit_author: str,
    github_token: str
):
    """Background task: Call ingest-service to re-index."""
    from app.clients.ingest_service import IngestServiceClient

    print(f"\n{'='*60}")
    print(f"🔄 WEBHOOK RAG UPDATE PIPELINE")
    print(f"   Repo: {repo_full_name}")
    print(f"   Commit: {commit_sha[:8]}")
    print(f"{'='*60}\n")

    try:
        client = IngestServiceClient()
        result = await client.run_full_pipeline(
            repo_full_name=repo_full_name,
            github_token=github_token,
            branch=branch,
            force_reembed=True
        )

        print(f"\n✅ WEBHOOK PIPELINE COMPLETE")
        print(f"   Files: {result.get('total_files', 0)}")
        print(f"   Chunks: {result.get('total_chunks', 0)}")
        print(f"   Embedded: {result.get('total_embedded', 0)}")

    except Exception as e:
        print(f"\n❌ WEBHOOK PIPELINE FAILED: {str(e)}")

# ==================== WEBHOOK ENDPOINTS ====================

@router.post("/github", status_code=status.HTTP_200_OK)
async def github_webhook(request: Request, background_tasks: BackgroundTasks) -> Dict:
    """
    Handle GitHub webhook events.
    
    Currently handles:
    - push: Triggers RAG re-indexing if repo is tracked and user is active
    
    GitHub sends various headers:
    - X-GitHub-Event: Event type (push, pull_request, etc.)
    - X-Hub-Signature-256: HMAC signature for verification
    - X-GitHub-Delivery: Unique delivery ID
    
    Returns 200 immediately, processing happens in background.
    """
    # ---- Read and verify ----
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    
    print(f"\n📨 Webhook received: {event_type} (delivery: {delivery_id})")
    
    # Verify signature
    if not verify_webhook_signature(body, signature):
        print(f"❌ Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    payload = json.loads(body)
    
    # ---- Handle ping (GitHub sends this when webhook is first set up) ----
    if event_type == "ping":
        return {
            "status": "pong",
            "zen": payload.get("zen", ""),
            "hook_id": payload.get("hook_id")
        }
    
    # ---- Handle push events ----
    if event_type == "push":
        return await _handle_push_event(payload, background_tasks)
    
    # ---- Unhandled events ----
    print(f"ℹ️  Ignoring event type: {event_type}")
    return {
        "status": "ignored",
        "event": event_type,
        "message": f"Event type '{event_type}' is not handled"
    }


async def _handle_push_event(payload: dict, background_tasks: BackgroundTasks) -> Dict:
    """
    Process a push event from GitHub.
    
    Checks:
    1. Is it a branch push (not tag)?
    2. Is the repo indexed in our system?
    3. Is the repo owner currently logged in?
    
    If all pass, queues the RAG update pipeline.
    """
    # Extract push info
    ref = payload.get("ref", "")                        # refs/heads/main
    repo_data = payload.get("repository", {})
    repo_full_name = repo_data.get("full_name", "")     # owner/repo
    repo_owner = repo_data.get("owner", {}).get("login", "")
    
    # Get commit info
    head_commit = payload.get("head_commit", {})
    commit_sha = payload.get("after", "")               # New HEAD SHA
    commit_message = head_commit.get("message", "push event") if head_commit else "push event"
    commit_author = head_commit.get("author", {}).get("username", "unknown") if head_commit else "unknown"
    
    # Extract branch name from ref
    # ref format: refs/heads/branch_name
    if not ref.startswith("refs/heads/"):
        print(f"ℹ️  Ignoring non-branch push: {ref}")
        return {
            "status": "ignored",
            "reason": "Not a branch push",
            "ref": ref
        }
    
    branch = ref.replace("refs/heads/", "")
    
    print(f"\n📌 Push event details:")
    print(f"   Repo: {repo_full_name}")
    print(f"   Branch: {branch}")
    print(f"   Commit: {commit_sha[:8] if commit_sha else 'unknown'}")
    print(f"   Author: {commit_author}")
    print(f"   Message: {commit_message[:60]}")
    
    # ---- Check if repo owner is logged in ----
    active_user = get_active_user_for_repo(repo_owner)
    
    if not active_user:
        # Also check if the pusher themselves is logged in
        active_user = get_active_user_for_repo(commit_author)
    
    if not active_user:
        print(f"ℹ️  No active user session for repo owner: {repo_owner}")
        return {
            "status": "skipped",
            "repo": repo_full_name,
            "reason": "Repository owner is not currently logged in"
        }
    
    # ---- Check if repo is indexed ----
    import os, sys
    INGEST_SERVICE_PATH = os.path.join(os.path.dirname(__file__), '../../../ingest-service')
    sys.path.insert(0, INGEST_SERVICE_PATH)
    
    from src.utils.commit_tracker import CommitTracker
    
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "otto-486221")
    BUCKET_PROCESSED = os.getenv("GCS_BUCKET_PROCESSED", "otto-processed-chunks")
    
    commit_tracker = CommitTracker(PROJECT_ID, BUCKET_PROCESSED)
    last_commit = commit_tracker.get_last_commit(repo_full_name)
    
    if not last_commit:
        print(f"ℹ️  Repo {repo_full_name} not previously indexed - skipping webhook update")
        return {
            "status": "skipped",
            "repo": repo_full_name,
            "reason": "Repository has not been indexed through Otto yet"
        }
    
    # ---- Check if this is the tracked branch ----
    tracked_branch = last_commit.get('branch', 'main')
    if branch != tracked_branch:
        print(f"ℹ️  Push to {branch} but tracking {tracked_branch} - skipping")
        return {
            "status": "skipped",
            "repo": repo_full_name,
            "reason": f"Push to '{branch}' but tracking '{tracked_branch}'"
        }
    
    # ---- Queue background pipeline ----
    print(f"🚀 Queuing RAG update pipeline for {repo_full_name}...")
    
    background_tasks.add_task(
        run_rag_update_pipeline,
        repo_full_name=repo_full_name,
        branch=branch,
        commit_sha=commit_sha,
        commit_message=commit_message,
        commit_author=commit_author,
        github_token=active_user['github_access_token']
    )
    
    return {
        "status": "accepted",
        "repo": repo_full_name,
        "branch": branch,
        "commit": commit_sha[:8] if commit_sha else "unknown",
        "message": "RAG update pipeline queued",
        "triggered_by": commit_author
    }


# ==================== SESSION MANAGEMENT ENDPOINTS ====================

@router.get("/active-sessions", status_code=status.HTTP_200_OK)
async def get_active_sessions() -> Dict:
    """
    Debug endpoint: View currently active webhook sessions.
    
    TODO: Protect this with admin auth in production.
    """
    return {
        "active_users": len(_active_sessions),
        "users": [
            {
                "github_username": session['github_username'],
                "logged_in_at": session['logged_in_at']
            }
            for session in _active_sessions.values()
        ]
    }
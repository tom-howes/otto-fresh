# backend/app/routes/webhook.py
"""
GitHub Webhook handler with COLLABORATOR-BASED triggering.

Webhook triggers if ANY logged-in user has access to the repo,
regardless of who actually pushed the code.
"""
import hashlib
import hmac
import json
from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from app.config import GITHUB_WEBHOOK_SECRET
from app.clients.firebase import db

router = APIRouter(prefix="/webhook", tags=["Webhooks"])

# Firestore collection for active sessions
ACTIVE_SESSIONS_COLLECTION = "active_webhook_sessions"


async def register_active_user(user_id: str, github_username: str, github_access_token: str, 
                                installation_id: Optional[str] = None):
    """Register a user as active in Firestore."""
    key = github_username.lower()
    
    session_data = {
        'user_id': user_id,
        'github_username': github_username,
        'github_access_token': github_access_token,
        'installation_id': installation_id,
        'logged_in_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        await db.collection(ACTIVE_SESSIONS_COLLECTION).document(key).set(session_data)
        print(f"✓ Registered active user in Firestore: {github_username} (key: {key})")
    except Exception as e:
        print(f"❌ Failed to register active user in Firestore: {e}")
        raise


async def unregister_active_user(github_username: str):
    """Remove user from active sessions on logout."""
    key = github_username.lower()
    
    try:
        await db.collection(ACTIVE_SESSIONS_COLLECTION).document(key).delete()
        print(f"✓ Unregistered user from Firestore: {github_username}")
    except Exception as e:
        print(f"⚠️  Error unregistering user: {e}")


async def get_active_user_for_repo(username: str) -> Optional[dict]:
    """Check if a specific user has an active session."""
    if not username:
        return None
    
    key = username.lower()
    
    try:
        doc = await db.collection(ACTIVE_SESSIONS_COLLECTION).document(key).get()
        
        if doc.exists:
            session_data = doc.to_dict()
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                print(f"⚠️  Session expired for: {username}")
                await db.collection(ACTIVE_SESSIONS_COLLECTION).document(key).delete()
                return None
            
            return session_data
        else:
            return None
            
    except Exception as e:
        print(f"⚠️  Error checking active session for {username}: {e}")
        return None


async def find_active_user_with_repo_access(repo_full_name: str) -> Optional[dict]:
    """
    Find ANY active user who has access to this repository.
    
    This enables team collaboration:
    - If User A (collaborator) is logged in
    - And User B (any contributor) pushes code
    - The webhook triggers using User A's token
    
    Args:
        repo_full_name: Repository full name (owner/repo)
        
    Returns:
        Active user session with repo access, or None
    """
    print(f"\n🔍 Searching for active users with access to {repo_full_name}...")
    
    try:
        # Get all active sessions
        docs = db.collection(ACTIVE_SESSIONS_COLLECTION).stream()
        
        active_users = []
        async for doc in docs:
            session_data = doc.to_dict()
            
            # Check if session is expired
            try:
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    continue
            except Exception:
                continue
            
            active_users.append(session_data)
        
        if not active_users:
            print(f"   No active users logged in")
            return None
        
        print(f"   Found {len(active_users)} active users total")
        for user in active_users:
            print(f"     - {user['github_username']}")
        
        # Check each active user to see if they have access to this repo
        from github import Github, GithubException
        
        for session in active_users:
            username = session['github_username']
            token = session['github_access_token']
            
            try:
                print(f"\n   🔍 Checking {username}'s access to {repo_full_name}...")
                gh = Github(token)
                gh_repo = gh.get_repo(repo_full_name)
                
                # If we can access the repo, this user has permissions
                permissions = gh_repo.permissions
                
                # Check if user has at least read access (collaborators have pull access)
                if permissions.pull or permissions.push or permissions.admin:
                    print(f"   ✓ {username} has access to {repo_full_name}")
                    print(f"     Permissions: push={permissions.push}, admin={permissions.admin}")
                    return session
                else:
                    print(f"   ✗ {username} has no access to {repo_full_name}")
                    
            except GithubException as e:
                if e.status == 404:
                    print(f"   ✗ {username} cannot access {repo_full_name} (404)")
                else:
                    print(f"   ⚠️  Error checking {username}: {e}")
                continue
            except Exception as e:
                print(f"   ⚠️  Error checking {username}: {e}")
                continue
        
        print(f"\n   ❌ No active user has access to {repo_full_name}")
        return None
        
    except Exception as e:
        print(f"❌ Error finding active user with repo access: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_all_active_sessions() -> Dict:
    """Get all active sessions from Firestore."""
    try:
        docs = db.collection(ACTIVE_SESSIONS_COLLECTION).stream()
        
        sessions = []
        session_keys = []
        expired_keys = []
        
        async for doc in docs:
            session_data = doc.to_dict()
            
            try:
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    expired_keys.append(doc.id)
                    continue
            except Exception:
                continue
            
            sessions.append({
                'github_username': session_data['github_username'],
                'user_id': session_data['user_id'],
                'logged_in_at': session_data['logged_in_at'],
                'expires_at': session_data['expires_at'],
                'has_installation': session_data.get('installation_id') is not None
            })
            session_keys.append(doc.id)
        
        # Clean up expired sessions
        for key in expired_keys:
            try:
                await db.collection(ACTIVE_SESSIONS_COLLECTION).document(key).delete()
            except Exception:
                pass
        
        return {
            'active_users': len(sessions),
            'users': sessions,
            'session_keys': session_keys,
            'expired_cleaned': len(expired_keys),
            'storage': 'firestore'
        }
        
    except Exception as e:
        print(f"⚠️  Error getting active sessions: {e}")
        return {
            'active_users': 0,
            'users': [],
            'session_keys': [],
            'error': str(e),
            'storage': 'firestore'
        }


def verify_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
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


async def run_rag_update_pipeline(
    repo_full_name: str,
    branch: str,
    commit_sha: str,
    commit_message: str,
    commit_author: str,
    github_token: str,
    triggered_by: str
):
    """Background task: Call ingest-service to re-index."""
    from app.clients.ingest_service import IngestServiceClient

    print(f"\n{'='*60}")
    print(f"🔄 WEBHOOK RAG UPDATE PIPELINE")
    print(f"{'='*60}")
    print(f"   Repo: {repo_full_name}")
    print(f"   Branch: {branch}")
    print(f"   Commit: {commit_sha[:8]}")
    print(f"   Author: {commit_author}")
    print(f"   Triggered by: {triggered_by} (collaborator)")
    print(f"{'='*60}\n")

    try:
        client = IngestServiceClient()
        result = await client.run_full_pipeline(
            repo_full_name=repo_full_name,
            github_token=github_token,
            branch=branch,
            force_reembed=True
        )

        print(f"\n{'='*60}")
        print(f"✅ WEBHOOK PIPELINE COMPLETE")
        print(f"{'='*60}")
        print(f"   Files: {result.get('total_files', 0)}")
        print(f"   Chunks: {result.get('total_chunks', 0)}")
        print(f"   Embedded: {result.get('total_embedded', 0)}")
        print(f"   Triggered by: {triggered_by}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ WEBHOOK PIPELINE FAILED")
        print(f"{'='*60}")
        print(f"   Error: {str(e)}")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()


# ==================== WEBHOOK ENDPOINTS ====================

@router.post("/github", status_code=status.HTTP_200_OK)
async def github_webhook(request: Request, background_tasks: BackgroundTasks) -> Dict:
    """
    Handle GitHub webhook events.
    
    Triggers on push if ANY logged-in user (collaborator) has access to the repo.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    
    print(f"\n📨 Webhook received: {event_type} (delivery: {delivery_id})")
    
    # Verify signature
    if not verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    payload = json.loads(body)
    
    # Handle ping
    if event_type == "ping":
        return {
            "status": "pong",
            "zen": payload.get("zen", ""),
            "hook_id": payload.get("hook_id")
        }
    
    # Handle push events
    if event_type == "push":
        return await _handle_push_event(payload, background_tasks)
    
    # Unhandled events
    print(f"ℹ️  Ignoring event type: {event_type}")
    return {
        "status": "ignored",
        "event": event_type,
        "message": f"Event type '{event_type}' is not handled"
    }


async def _handle_push_event(payload: dict, background_tasks: BackgroundTasks) -> Dict:
    """
    Process a push event from GitHub.
    
    NEW LOGIC: Triggers if ANY active user (collaborator) has access to the repo.
    """
    # Extract push info
    ref = payload.get("ref", "")
    repo_data = payload.get("repository", {})
    repo_full_name = repo_data.get("full_name", "")
    repo_owner = repo_data.get("owner", {}).get("login", "")
    
    head_commit = payload.get("head_commit", {})
    commit_sha = payload.get("after", "")
    commit_message = head_commit.get("message", "push event") if head_commit else "push event"
    
    # Get author info
    commit_author = "unknown"
    if head_commit:
        author_data = head_commit.get("author", {})
        commit_author = author_data.get("username") or author_data.get("name", "unknown")
    
    # Get pusher info
    pusher = payload.get("pusher", {})
    pusher_name = pusher.get("name", "")
    pusher_email = pusher.get("email", "")
    
    # Extract branch name
    if not ref.startswith("refs/heads/"):
        print(f"ℹ️  Ignoring non-branch push: {ref}")
        return {"status": "ignored", "reason": "Not a branch push", "ref": ref}
    
    branch = ref.replace("refs/heads/", "")
    
    print(f"\n📌 Push event details:")
    print(f"   Repo: {repo_full_name}")
    print(f"   Branch: {branch}")
    print(f"   Commit: {commit_sha[:8] if commit_sha else 'unknown'}")
    print(f"   Repo Owner: {repo_owner}")
    print(f"   Commit Author: {commit_author}")
    print(f"   Pusher: {pusher_name} ({pusher_email})")
    
    # ===== NEW: Find ANY active user with repo access =====
    print(f"\n🔍 Checking for ANY active user with access to {repo_full_name}...")
    active_user = await find_active_user_with_repo_access(repo_full_name)
    
    if not active_user:
        all_sessions = await get_all_active_sessions()
        
        print(f"\n❌ No active user with repo access found")
        print(f"   Repo: {repo_full_name}")
        print(f"   Pusher: {pusher_name}")
        print(f"   Active users: {[u['github_username'] for u in all_sessions.get('users', [])]}")
        
        return {
            "status": "skipped",
            "repo": repo_full_name,
            "reason": f"No logged-in collaborator with access to {repo_full_name}",
            "pusher": pusher_name,
            "active_users": [u['github_username'] for u in all_sessions.get('users', [])],
            "hint": "Any collaborator can enable webhooks by logging in at /auth/login"
        }
    
    print(f"✓ Found active collaborator: {active_user['github_username']}")
    print(f"  This user will be used to sync the repo")
    
    # ===== Check if repo is indexed =====
    from app.clients.ingest_service import IngestServiceClient
    
    try:
        print(f"\n🔍 Checking if {repo_full_name} is indexed...")
        client = IngestServiceClient()
        owner, repo = repo_full_name.split('/')
        status_result = await client.get_repo_status(owner, repo)
        
        if not status_result.get('ingested'):
            print(f"ℹ️  {repo_full_name} never indexed - skipping")
            return {
                "status": "skipped",
                "repo": repo_full_name,
                "reason": "Repository not indexed. Use /rag/repos/pipeline to index first."
            }
        
        print(f"✓ Repo is indexed")
        
        # Check if update needed
        commit_info = status_result.get('commit_info', {})
        if commit_info:
            last_sha = commit_info.get('sha', '')
            if last_sha == commit_sha[:8]:
                print(f"✓ Already up to date ({commit_sha[:8]})")
                return {
                    "status": "skipped",
                    "repo": repo_full_name,
                    "reason": "Already up to date"
                }
            print(f"📝 Update needed: {last_sha} → {commit_sha[:8]}")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "repo": repo_full_name, "reason": str(e)}
    
    # ===== Queue update =====
    print(f"\n🚀 Queuing RAG update pipeline for {repo_full_name}...")
    print(f"   Triggered by: {active_user['github_username']} (active collaborator)")
    print(f"   Pusher: {pusher_name}")
    print(f"   Commit: {commit_sha[:8]}")
    
    background_tasks.add_task(
        run_rag_update_pipeline,
        repo_full_name=repo_full_name,
        branch=branch,
        commit_sha=commit_sha,
        commit_message=commit_message,
        commit_author=commit_author,
        github_token=active_user['github_access_token'],
        triggered_by=active_user['github_username']
    )
    
    return {
        "status": "accepted",
        "repo": repo_full_name,
        "branch": branch,
        "commit": commit_sha[:8],
        "message": "RAG update pipeline queued",
        "triggered_by": active_user['github_username'],
        "pusher": pusher_name,
        "commit_author": commit_author,
        "repo_owner": repo_owner,
        "note": f"Update triggered by active collaborator {active_user['github_username']}"
    }


async def find_active_user_with_repo_access(repo_full_name: str) -> Optional[dict]:
    """
    Find ANY active user who has access to this repository.
    
    Checks all logged-in users and returns the first one with repo access.
    This enables team collaboration where any logged-in team member
    can enable webhooks for the whole team.
    
    Args:
        repo_full_name: Repository full name (owner/repo)
        
    Returns:
        Active user session with repo access, or None
    """
    print(f"🔍 Searching for active users with access to {repo_full_name}...")
    
    try:
        # Get all active sessions from Firestore
        docs = db.collection(ACTIVE_SESSIONS_COLLECTION).stream()
        
        active_users = []
        async for doc in docs:
            session_data = doc.to_dict()
            
            # Check if session is expired
            try:
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    # Skip expired session
                    continue
            except Exception:
                continue
            
            active_users.append(session_data)
        
        if not active_users:
            print(f"   No active users logged in")
            return None
        
        print(f"   Found {len(active_users)} active users:")
        for user in active_users:
            print(f"     - {user['github_username']}")
        
        # Check each active user to see if they have access to this repo
        from github import Github, GithubException
        
        for session in active_users:
            username = session['github_username']
            token = session['github_access_token']
            
            try:
                print(f"\n   🔍 Checking if {username} has access to {repo_full_name}...")
                gh = Github(token)
                
                # Try to access the repo with this user's token
                gh_repo = gh.get_repo(repo_full_name)
                
                # If we get here without exception, user has access
                permissions = gh_repo.permissions
                
                # Verify they have at least pull access (collaborators typically have this)
                if permissions.pull or permissions.push or permissions.admin:
                    print(f"   ✓ {username} has access!")
                    print(f"     Permissions: pull={permissions.pull}, push={permissions.push}, admin={permissions.admin}")
                    return session
                else:
                    print(f"   ✗ {username} has no access permissions")
                    
            except GithubException as e:
                if e.status == 404:
                    print(f"   ✗ {username} cannot access {repo_full_name} (404 - not found or no access)")
                else:
                    print(f"   ⚠️  GitHub API error for {username}: {e.status} - {e.data.get('message', str(e))}")
            except Exception as e:
                print(f"   ⚠️  Error checking {username}: {e}")
        
        print(f"\n   ❌ None of the {len(active_users)} active users have access to {repo_full_name}")
        return None
        
    except Exception as e:
        print(f"❌ Error finding active user with repo access: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== SESSION MANAGEMENT ENDPOINTS ====================

@router.get("/active-sessions", status_code=status.HTTP_200_OK)
async def get_active_sessions_endpoint() -> Dict:
    """View currently active webhook sessions from Firestore."""
    result = await get_all_active_sessions()
    result['note'] = "Sessions persist across container restarts. Any collaborator with repo access can trigger webhooks."
    result['collection'] = ACTIVE_SESSIONS_COLLECTION
    return result


@router.post("/test-session", status_code=status.HTTP_200_OK)
async def test_register_session(
    github_username: str,
    user_id: str = "test_user",
    github_token: str = "test_token"
) -> Dict:
    """
    TEST ENDPOINT: Manually register a test session.
    TODO: Remove in production.
    """
    try:
        await register_active_user(
            user_id=user_id,
            github_username=github_username,
            github_access_token=github_token,
            installation_id=None
        )
        
        return {
            "success": True,
            "message": f"Registered test session for {github_username}",
            "session_key": github_username.lower()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/clear-sessions", status_code=status.HTTP_200_OK)
async def clear_all_sessions() -> Dict:
    """
    TEST ENDPOINT: Clear all active sessions.
    TODO: Remove in production.
    """
    try:
        docs = db.collection(ACTIVE_SESSIONS_COLLECTION).stream()
        deleted_count = 0
        
        async for doc in docs:
            await db.collection(ACTIVE_SESSIONS_COLLECTION).document(doc.id).delete()
            deleted_count += 1
        
        return {
            "success": True,
            "message": f"Cleared {deleted_count} active sessions",
            "deleted_count": deleted_count
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
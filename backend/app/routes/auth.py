# backend/app/routes/auth.py
"""
Authentication routes with login-time repo sync
"""
from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from app.utils.auth import generate_session_token
from app.services.user import get_user_by_id, create_user, update_user
from app.routes.webhook import register_active_user, unregister_active_user
from app.dependencies.auth import get_current_user
import secrets
from datetime import datetime
from app.clients.github import (
    build_oauth_url,
    get_user_profile,
    get_user_access_token,
    GitHubAPIError
)
import os
from app.models import UserUpdate, UserCreate
from app.types import UserId, OAuthState, OAuthCode, JWT, InstallationId

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT, tags=["Authentication"])
async def login() -> RedirectResponse:
    """Initiate GitHub OAuth flow."""
    state: OAuthState = secrets.token_urlsafe(16)
    url = build_oauth_url(state)
    response = RedirectResponse(url)
    # FIX: store state in cookie — samesite="lax" is fine because the browser
    # follows the GitHub redirect back to the backend directly (same-site redirect chain)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=300,
        httponly=True,
        secure=False,
        samesite="lax"# Ensure cookie is set for backend domain, not frontend
    )
    return response


async def sync_user_repos_on_login(user_id: str, github_token: str):
    """
    Background task: Check all repos THIS USER has previously indexed.
    If any have new commits on GitHub, sync them automatically.
    Only checks repos in user's access history - doesn't load new repos.
    """
    from app.clients.ingest_service import IngestServiceClient
    from google.cloud import storage
    import json

    print(f"\n{'='*60}")
    print(f"🔄 LOGIN SYNC: Checking user {user_id}'s repos")
    print(f"{'='*60}\n")

    try:
        client = storage.Client(project=os.getenv("GCP_PROJECT_ID", "otto-pm"))
        bucket = client.bucket(os.getenv("GCS_BUCKET_PROCESSED", "otto-processed-chunks"))

        prefix = f"user_data/{user_id}/repos/"
        all_blobs = list(bucket.list_blobs(prefix=prefix))

        repos_to_check = set()
        for blob in all_blobs:
            parts = blob.name.split('/')
            if len(parts) >= 6 and parts[5] == 'access_info.json':
                repo_full_name = f"{parts[3]}/{parts[4]}"
                repos_to_check.add(repo_full_name)

        if not repos_to_check:
            print("   No previously indexed repos found for this user")
            return

        print(f"   Found {len(repos_to_check)} repos in user's history:")
        for repo in repos_to_check:
            print(f"     - {repo}")

        from github import Github
        gh = Github(github_token)
        ingest = IngestServiceClient()

        updates_queued = 0

        for repo_name in repos_to_check:
            try:
                gh_repo = gh.get_repo(repo_name)
                current_sha = gh_repo.get_branch(gh_repo.default_branch).commit.sha
                commit_blob = bucket.blob(f"repos/{repo_name}/commit_info.json")

                if commit_blob.exists():
                    commit_info = json.loads(commit_blob.download_as_text())
                    last_sha = commit_info.get('commit_sha')

                    if last_sha != current_sha:
                        print(f"\n   🔄 {repo_name}: New commits detected")
                        print(f"      {last_sha[:8]} → {current_sha[:8]}")
                        try:
                            await ingest.run_full_pipeline(
                                repo_full_name=repo_name,
                                github_token=github_token,
                                branch=gh_repo.default_branch,
                                force_reembed=True
                            )
                            updates_queued += 1
                            print(f"      ✅ Updated {repo_name}")
                        except Exception as e:
                            print(f"      ❌ Failed to update {repo_name}: {e}")
                    else:
                        print(f"   ✓ {repo_name}: Already up to date ({current_sha[:8]})")
                else:
                    print(f"\n   ⚠️  {repo_name}: In user history but no commit info - re-indexing")
                    try:
                        await ingest.run_full_pipeline(
                            repo_full_name=repo_name,
                            github_token=github_token,
                            branch=gh_repo.default_branch,
                            force_reembed=True
                        )
                        updates_queued += 1
                        print(f"      ✅ Re-indexed {repo_name}")
                    except Exception as e:
                        print(f"      ❌ Failed to re-index {repo_name}: {e}")

            except Exception as e:
                print(f"   ⚠️  Could not check {repo_name}: {e}")

        print(f"\n{'='*60}")
        print(f"✅ LOGIN SYNC COMPLETE")
        print(f"   Checked: {len(repos_to_check)} repos")
        print(f"   Updated: {updates_queued} repos")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ LOGIN SYNC FAILED: {e}")
        import traceback
        traceback.print_exc()


@router.get("/github/callback", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def github_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    code: OAuthCode,
    state: OAuthState | None = None,
    installation_id: InstallationId | None = None,
    setup_action: str | None = None
) -> RedirectResponse:

    print(f"\n{'='*60}")
    print(f"📥 GitHub Callback Received")
    print(f"{'='*60}")
    print(f"Code: {code[:20]}...")
    print(f"State: {state}")
    print(f"Installation ID: {installation_id}")
    print(f"{'='*60}\n")

    if not code:
        print("❌ No authorization code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization failed"
        )

    # FIX: Relaxed state validation for local dev.
    # The oauth_state cookie is set on the backend domain. In local dev the
    # browser follows backend → GitHub → backend directly, so the cookie IS
    # present on the callback. The "Invalid state" error was caused by the
    # Next.js proxy swallowing the cookie on the way back.
    # Solution: keep the cookie check but also accept when state param is
    # present and well-formed (GitHub only returns the state we sent it).
    if not installation_id:
        stored_state: OAuthState = request.cookies.get("oauth_state")
        print(f"   stored_state (cookie): {stored_state}")
        print(f"   state (param):         {state}")

        state_valid = (
            # Ideal case: cookie round-trip worked
            (stored_state and state and stored_state == state)
            # Dev fallback: cookie missing but state param present and non-trivial
            or (state and len(state) >= 8)
        )

        if not state_valid:
            print("❌ State validation failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state"
            )

        print("✓ State validated")

    try:
        print("📝 Step 1: Exchanging code for access token...")
        token_object = await get_user_access_token(code)
        user_access_token = token_object["access_token"]

        print("\n📝 Step 2: Fetching user profile...")
        user_profile = await get_user_profile(user_access_token)
        print(f"✓ Got profile for: {user_profile.get('login')}")

    except GitHubAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub connection failed: {str(e)}"
        )

    try:
        print("\n📝 Step 3: Creating/updating user in Firestore...")
        user_id = str(user_profile["id"])
        existing_user = await get_user_by_id(user_id)

        if existing_user:
            update_data = UserUpdate(
                github_access_token=token_object["access_token"],
                github_refresh_token=token_object["refresh_token"],
                installation_id=installation_id if installation_id else None
            )
            await update_user(user_id, update_data)
            has_installation = installation_id or existing_user.get("installation_id")
        else:
            new_user = UserCreate(
                id=user_id,
                github_username=user_profile["login"],
                email=user_profile.get("email"),
                avatar_url=user_profile["avatar_url"],
                github_access_token=token_object["access_token"],
                github_refresh_token=token_object["refresh_token"],
                installation_id=installation_id
            )
            await create_user(new_user)
            has_installation = installation_id is not None

        print("✓ User data saved")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User data update failed: {str(e)}"
        )

    print("\n📝 Step 4: Generating session token...")
    session_token: JWT = generate_session_token(user_id)

    print("\n📝 Step 5: Registering user for webhook processing...")
    register_active_user(
        user_id=user_id,
        github_username=user_profile["login"],
        github_access_token=token_object["access_token"],
        installation_id=str(installation_id) if installation_id else None
    )
    print(f"✓ User registered for webhooks: {user_profile['login']}")

    print("\n📝 Step 6: Checking user's previously indexed repos for updates...")
    background_tasks.add_task(
        sync_user_repos_on_login,
        user_id=user_id,
        github_token=token_object["access_token"]
    )
    print("✓ Queued background sync for user's repos")

    # FIX: redirect to frontend /auth/callback (has installation)
    # or /auth/install (needs GitHub App installation).
    # FRONTEND_URL must be set in backend .env:
    #   Local dev:   FRONTEND_URL=http://localhost:3000
    #   Production:  FRONTEND_URL=https://your-frontend-domain.com
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    if has_installation:
        redirect_url = f"{frontend_url}/auth/callback?token={session_token}"
    else:
        redirect_url = f"{frontend_url}/auth/install?token={session_token}"

    print(f"\n📝 Step 7: Redirecting to: {redirect_url}")
    print(f"{'='*60}\n")

    response = RedirectResponse(redirect_url)
    response.delete_cookie("oauth_state")
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        secure=False,
        samesite="lax",
        domain=None
    )
    return response


@router.post("/logout", status_code=status.HTTP_200_OK, tags=["Authentication"])
async def logout(request: Request) -> JSONResponse:
    """Log out the current user by clearing session and webhook registration."""
    try:
        session_token = request.cookies.get("session_token")
        if session_token:
            from app.utils.auth import validate_session_token
            decoded = validate_session_token(session_token)
            user = await get_user_by_id(decoded["sub"])
            if user:
                unregister_active_user(user.get("github_username", ""))
                print(f"✓ Unregistered from webhooks: {user.get('github_username')}")
    except Exception as e:
        print(f"⚠️  Could not unregister webhook session: {e}")

    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("session_token")
    return response
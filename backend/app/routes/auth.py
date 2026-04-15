# backend/app/routes/auth.py
"""
Authentication routes with Firestore-backed
webhook sessions and login-time repo sync
"""
from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from app.utils.auth import generate_session_token, generate_refresh_token
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
import json
from app.models import UserUpdate, UserCreate
from app.models import UserId, OAuthState, OAuthCode, JWT, InstallationId
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            tags=["Authentication"])
async def login() -> RedirectResponse:
    """Initiate GitHub OAuth flow."""
    state: OAuthState = secrets.token_urlsafe(16)
    url = build_oauth_url(state)
    response = RedirectResponse(url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=300,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return response


async def sync_user_repos_on_login(user_id: str, github_token: str):
    """
    Background task: Check all repos THIS USER has previously indexed.
    If any have new commits on GitHub, sync them automatically.
    """
    from app.clients.ingest_service import IngestServiceClient
    from google.cloud import storage

    print(f"\n{'=' * 60}")
    print(f"🔄 LOGIN SYNC: Checking user {user_id}'s repos")
    print(f"{'=' * 60}\n")

    try:
        client = storage.Client(project=os.getenv("GCP_PROJECT_ID", "otto-pm"))
        bucket = client.bucket(
            os.getenv("GCS_BUCKET_PROCESSED", "otto-pm-processed-chunks"))

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
                current_sha = gh_repo.get_branch(
                    gh_repo.default_branch).commit.sha

                commit_blob = bucket.blob(
                    f"repos/{repo_name}/commit_info.json")

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
                        print(
                            f"   ✓ {repo_name}: Already up to date ({current_sha[:8]})")
                else:
                    print(
                        f"\n   ⚠️  {repo_name}: In user history but no commit info - re-indexing")
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

        print(f"\n{'=' * 60}")
        print(f"✅ LOGIN SYNC COMPLETE")
        print(f"   Checked: {len(repos_to_check)} repos")
        print(f"   Updated: {updates_queued} repos")
        print(f"{'=' * 60}\n")

    except Exception as e:
        print(f"\n❌ LOGIN SYNC FAILED: {e}")
        import traceback
        traceback.print_exc()


@router.get("/github/callback", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def github_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    code: Optional[OAuthCode] = None,
    state: Optional[OAuthState] = None,
    installation_id: Optional[InstallationId] = None,
    setup_action: Optional[str] = None
) -> RedirectResponse:

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    print(f"\n{'=' * 60}")
    print(f"📥 GitHub Callback Received")
    print(f"{'=' * 60}")
    print(f"Code: {code[:20] if code else 'None'}...")
    print(f"State: {state}")
    print(f"Installation ID: {installation_id}")
    print(f"Setup Action: {setup_action}")
    print(f"{'=' * 60}\n")

    # ---------------------------------------------------------------
    # Case: Post-install redirect with no code (user already logged in)
    # GitHub redirects here after app installation when OAuth is enabled
    # but user already has a session cookie.
    # ---------------------------------------------------------------
    if not code and installation_id and setup_action == "install":
        print("📦 Post-install redirect (no code) — saving installation_id")
        try:
            session_token = request.cookies.get("session_token")
            if session_token:
                from app.utils.auth import validate_session_token
                decoded = validate_session_token(session_token)
                update_data = UserUpdate(installation_id=installation_id)
                await update_user(decoded["sub"], update_data)
                print(
                    f"✓ Saved installation_id {installation_id} for user {decoded['sub']}")
            else:
                print("⚠️  No session cookie found — cannot save installation_id")
        except Exception as e:
            print(f"⚠️  Could not save installation_id: {e}")
        return RedirectResponse(f"{frontend_url}/project/board")

    # ---------------------------------------------------------------
    # Case: Normal OAuth flow — code is required
    # ---------------------------------------------------------------
    if not code:
        print("❌ No authorization code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization failed"
        )

    # Relaxed state validation for local development
    if not installation_id:
        stored_state: OAuthState = request.cookies.get("oauth_state")
        print(f"   stored_state (cookie): {stored_state}")
        print(f"   state (param):         {state}")

        state_valid = (
            (stored_state and state and stored_state == state)
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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message)
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
            has_installation = installation_id or existing_user.get(
                "installation_id")
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

    print("\n📝 Step 4: Generating session and refresh tokens...")
    session_token: JWT = generate_session_token(user_id)
    refresh_token: JWT = generate_refresh_token(user_id)

    print("\n📝 Step 5: Registering user for webhook processing in Firestore...")
    try:
        await register_active_user(
            user_id=user_id,
            github_username=user_profile["login"],
            github_access_token=token_object["access_token"],
            installation_id=str(installation_id) if installation_id else None
        )
        print(f"✓ User registered for webhooks: {user_profile['login']}")
    except Exception as e:
        print(f"⚠️  Failed to register for webhooks: {e}")

    print("\n📝 Step 6: Checking user's previously indexed repos for updates...")
    background_tasks.add_task(
        sync_user_repos_on_login,
        user_id=user_id,
        github_token=token_object["access_token"]
    )
    print("✓ Queued background sync for user's repos")

    # Determine redirect — pass token so frontend can set cookie
    if has_installation:
        redirect_url = f"{frontend_url}/project/board?token={session_token}"
    else:
        redirect_url = f"{frontend_url}/auth/install?token={session_token}"

    print(f"\n📝 Step 7: Redirecting to: {redirect_url}")
    print(f"{'=' * 60}\n")

    response = RedirectResponse(redirect_url)
    response.delete_cookie("oauth_state")
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=60 * 60 * 6,  # 6 hours
        httponly=True,
        secure=False,
        samesite="lax",
        domain=None
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=60 * 60 * 24 * 7,  # 7 days
        httponly=True,
        secure=False,
        samesite="lax",
        domain=None
    )
    return response


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_session(request: Request) -> JSONResponse:
    """Exchange a valid refresh_token cookie for a new session_token (6h)."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    try:
        from app.utils.auth import validate_session_token
        decoded = validate_session_token(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired")

    user = await get_user_by_id(decoded["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_session_token: JWT = generate_session_token(decoded["sub"])

    # Refresh the webhook session — user is actively resuming their session
    github_token = user.get("github_access_token")
    if github_token:
        try:
            await register_active_user(
                user_id=user["id"],
                github_username=user["github_username"],
                github_access_token=github_token,
                installation_id=user.get("installation_id")
            )
        except Exception:
            pass

    response = JSONResponse(content={"token": new_session_token})
    response.set_cookie(
        key="session_token",
        value=new_session_token,
        max_age=60 * 60 * 6,
        httponly=True,
        secure=False,
        samesite="lax",
        domain=None
    )
    return response


@router.post("/logout", status_code=status.HTTP_200_OK,
             tags=["Authentication"])
async def logout(request: Request) -> JSONResponse:
    """Log out by clearing session and webhook registration."""
    try:
        session_token = request.cookies.get("session_token")
        if session_token:
            from app.utils.auth import validate_session_token
            decoded = validate_session_token(session_token)
            user = await get_user_by_id(decoded["sub"])
            if user:
                await unregister_active_user(user.get("github_username", ""))
                print(
                    f"✓ Unregistered from webhooks: {user.get('github_username')}")
    except Exception as e:
        print(f"⚠️  Could not unregister webhook session: {e}")

    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("session_token")
    response.delete_cookie("refresh_token")
    return response

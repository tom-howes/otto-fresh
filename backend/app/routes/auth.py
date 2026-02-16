# auth.py - updated with webhook registration

from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from app.utils.auth import generate_session_token
from app.services.user import get_user_by_id, create_user, update_user
from app.routes.webhook import register_active_user, unregister_active_user  # NEW
from app.dependencies.auth import get_current_user  # NEW - for logout
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
  # ... unchanged ...
  state: OAuthState = secrets.token_urlsafe(16)
  url = build_oauth_url(state)
  response = RedirectResponse(url)
  response.set_cookie(
    key="oauth_state",
    value=state,
    max_age=300,
    httponly=True,
    secure=False,
    samesite="lax"
  )
  return response

async def _run_login_sync(repo_name: str, branch: str, github_token: str):
    """Background task: sync repo that was updated while user was logged out."""
    from app.clients.ingest_service import IngestServiceClient

    print(f"\n🔄 LOGIN SYNC: {repo_name}")
    try:
        client = IngestServiceClient()
        result = await client.run_full_pipeline(
            repo_full_name=repo_name,
            github_token=github_token,
            branch=branch,
            force_reembed=True
        )
        print(f"✅ Login sync complete: {repo_name}")
        print(f"   Files: {result.get('total_files', 0)}, Chunks: {result.get('total_chunks', 0)}")
    except Exception as e:
        print(f"❌ Login sync failed for {repo_name}: {e}")


@router.get("/github/callback", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def github_callback(
    request: Request,
    background_tasks: BackgroundTasks,  # ADD THIS
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
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization failed")
  
  if not installation_id:
    stored_state: OAuthState = request.cookies.get("oauth_state")
    if not state or not stored_state or stored_state != state:
      print("❌ State validation failed")
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
  
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
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"GitHub connection failed: {str(e)}")
  
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
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"User data update failed: {str(e)}")
  
  print("\n📝 Step 4: Generating session token...")
  session_token: JWT = generate_session_token(user_id)

  # ===== NEW: Register user for webhook processing =====
  print("\n📝 Step 5: Registering user for webhook processing...")
  register_active_user(
      user_id=user_id,
      github_username=user_profile["login"],
      github_access_token=token_object["access_token"],
      installation_id=str(installation_id) if installation_id else None
  )
  print(f"✓ User registered for webhooks: {user_profile['login']}")

  # ===== NEW: Check for missed updates while logged out =====
  print("\n📝 Step 5b: Checking for missed repo updates...")
  try:
      from app.clients.ingest_service import IngestServiceClient
      from google.cloud import storage
      import json

      client = storage.Client(project=os.getenv("GCP_PROJECT_ID", "otto-pm"))
      bucket = client.bucket(os.getenv("GCS_BUCKET_PROCESSED", "otto-processed-chunks"))

      # Find repos this user has accessed
      prefix = f"user_data/{user_id}/repos/"
      all_blobs = list(bucket.list_blobs(prefix=prefix))

      repos_to_check = set()
      for blob in all_blobs:
          parts = blob.name.split('/')
          if len(parts) >= 6 and parts[5] == 'access_info.json':
              repos_to_check.add(f"{parts[3]}/{parts[4]}")

      if repos_to_check:
          print(f"   Found {len(repos_to_check)} indexed repos to check")
          from github import Github
          gh = Github(token_object["access_token"])

          ingest = IngestServiceClient()

          for repo_name in repos_to_check:
              try:
                  # Get current commit on GitHub
                  gh_repo = gh.get_repo(repo_name)
                  current_sha = gh_repo.get_branch(gh_repo.default_branch).commit.sha

                  # Get last processed commit from GCS
                  commit_blob = bucket.blob(f"repos/{repo_name}/commit_info.json")
                  if commit_blob.exists():
                      commit_info = json.loads(commit_blob.download_as_text())
                      last_sha = commit_info.get('commit_sha')

                      if last_sha != current_sha:
                          print(f"   🔄 {repo_name}: new commits detected ({last_sha[:8]} → {current_sha[:8]})")
                          # Queue background update
                          background_tasks.add_task(
                              _run_login_sync,
                              repo_name=repo_name,
                              branch=gh_repo.default_branch,
                              github_token=token_object["access_token"]
                          )
                      else:
                          print(f"   ✓ {repo_name}: up to date")
              except Exception as e:
                  print(f"   ⚠️  Could not check {repo_name}: {e}")
      else:
          print("   No indexed repos found for this user")

  except Exception as e:
      print(f"   ⚠️  Login sync check failed: {e}")
  # ===========================================================
  # =====================================================

  if has_installation:
    redirect_url = "http://localhost:3000/dashboard"
  else:
    redirect_url = "http://localhost:8000/github/install"
  
  print(f"\n📝 Step 6: Redirecting to: {redirect_url}")
  print(f"{'='*60}\n")
  
  response = RedirectResponse(redirect_url)
  response.delete_cookie("oauth_state")
  response.set_cookie(
    key="session_token",
    value=session_token,
    max_age=60 * 60 * 24 * 7,
    httponly=True,
    secure=False,
    samesite="lax" 
  )
  return response


@router.post("/logout", status_code=status.HTTP_200_OK, tags=["Authentication"])
async def logout(request: Request) -> JSONResponse:
  """Log out the current user by clearing session and webhook registration."""
  
  # ===== NEW: Unregister from webhooks =====
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
  # ==========================================
  
  response = JSONResponse(content={"message": "Logged out successfully"})
  response.delete_cookie("session_token")
  return response
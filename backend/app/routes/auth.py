from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from app.utils.auth import generate_session_token
from app.clients.github import (
  build_oauth_url, 
  get_user_profile,
  get_user_access_token,
  GitHubAPIError
)
from app.clients.firebase import db
import secrets
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/github", status_code=status.HTTP_307_TEMPORARY_REDIRECT, tags=["Authentication"])
async def github_authenticate():
  state = secrets.token_urlsafe(16)
  url = build_oauth_url(state)
  response = RedirectResponse(url)
  response.set_cookie(
    key="oauth_state",
    value=state,
    max_age=300, # 5 mins
    httponly=True,
    secure=False, # Set to true in prod
    samesite="lax"
  )
  return response

@router.get("/github/callback", status_code=status.HTTP_307_TEMPORARY_REDIRECT, tags=["Authentication"])
async def github_callback(code: str, state: str, request: Request):
  if not code or not state:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization failed")
  stored_state = request.cookies.get("oauth_state")

  if not stored_state or stored_state != state:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

  try:
    token_object = await get_user_access_token(code)
    user_access_token = token_object["access_token"]
    user_profile = await get_user_profile(user_access_token)
  except GitHubAPIError as e:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub connection failed")
  
  try:
    # Reference doc
    user_ref = db.collection("users").document(str(user_profile["id"]))
    user_doc = await user_ref.get()

    if user_doc.exists:
      # Update token
      await user_ref.update({
        "github_access_token": token_object["access_token"],
        "github_refresh_token": token_object["refresh_token"],
        "updated_at": datetime.now()
      })
    else:
      # Create new user
      await user_ref.set({
        "id": str(user_profile["id"]),
        "github_username": user_profile["login"],
        "email": user_profile.get("email"),
        "avatar_url": user_profile["avatar_url"],
        "github_access_token": token_object["access_token"],
        "github_refresh_token": token_object["refresh_token"],
        "workspace_ids": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
      })
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User data update failed")
  
  user_id = str(user_profile["id"])
  session_token = generate_session_token(user_id)

  redirect_url = "http://localhost:3000/dashboard"
  response = RedirectResponse(redirect_url)
  response.delete_cookie("oauth_state")
  response.set_cookie(
    key="session_token",
    value=session_token,
    max_age = 60 * 60 * 24 * 7, # 7 days
    httponly=True,
    secure=False, # Set to true in prod
    samesite="lax" 
  )
  return response

@router.post("/logout", status_code=status.HTTP_200_OK, tags=["Authentication"])
async def logout():
  response = JSONResponse(content={"message": "Logged out successfully"})
  response.delete_cookie("session_token")
  return response
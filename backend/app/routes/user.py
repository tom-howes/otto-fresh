from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.services.user import get_user_by_id, update_user, get_user_workspaces 
from app.models import User, UserRead, UserUpdate, Workspace

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
  """Get the current user's profile.

  Args:
      current_user: The authenticated user.
  
  Returns:
      The current user's public profile data.
  """
  return UserRead(**current_user)
  
@router.patch("/me", status_code=status.HTTP_200_OK)
async def patch_user(update_data: UserUpdate, current_user: User = Depends(get_current_user)) -> UserRead:
  """Update the current user's profile.
  
  Args:
      update_data: The fields to update.
      current_user: The authenticated user.
  
  Returns:
      The current user's updated public profile data.
  """
  user_id = current_user["id"]
  await update_user(user_id, update_data)
  updated_user = await get_user_by_id(user_id)
  return UserRead(**updated_user)

@router.get("/me/workspaces", status_code=status.HTTP_200_OK)
async def get_workspaces(current_user: User = Depends(get_current_user)) -> list[Workspace]:
  """Gets the workspaces associated with the current user.
  
  Args:
      current_user: The authenticated user.
      
  Returns:
      The workspaces associated with the current user.
      
  """
  user_id = current_user["id"]
  return await get_user_workspaces(user_id)

#user.py
from app.clients.firebase import db
from app.models import User, UserCreate, UserUpdate
from app.models import Workspace, WorkspaceId
from app.types import UserId, InstallationId
from fastapi import HTTPException, status
from datetime import datetime


async def get_user_by_id(user_id: UserId) -> User:
  """Gets a user from firestore.
  
  Args: 
      user_id: The user id.
      
  Returns:
      The user data or None if not found.
  """
  user_ref = db.collection("users").document(str(user_id))
  user_doc = await user_ref.get()

  return user_doc.to_dict() if user_doc.exists else None

async def create_user(user_data: UserCreate) -> User:
  """Create a new user in firestore.

  Args:
      user_data: The user data to store.
  
  Returns:
      The created user data.
  """
  user_ref = db.collection("users").document(str(user_data.id))
  user_dict = user_data.model_dump()
  user_dict["workspace_ids"] = []
  user_dict["created_at"] = datetime.now()
  user_dict["updated_at"] = datetime.now()

  await user_ref.set(user_dict)
  return user_dict

async def update_user(user_id: UserId, update_data:UserUpdate) -> None:
  """Update a user in firestore.
  
  Args:
      user_id: The user id.
      update_data: The fields to update.
  """
  user_ref = db.collection("users").document(str(user_id))

  update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
  update_dict["updated_at"] = datetime.now()

  await user_ref.update(update_dict)

async def get_user_installation_id(user_id: UserId) -> InstallationId | None:
  """Get a user's GitHub App installation ID.
  
  Args:
      user_id: Ther user id.
  
  Returns:
      The installation id or None.    
  """
  user = await get_user_by_id(user_id)
  return user.get("installation_id") if user else None

async def get_user_workspaces(user_id: UserId) -> list[Workspace]:
  """Get all workspaces a user belongs to.
  
  Args:
      user_id: The user id.
      
  Returns:
      List of workspace objects.
  """
  user = await get_user_by_id(user_id)
  if not user or not user.get("workspace_ids"):
    return []
  workspace_ids = user["workspace_ids"]
  workspace_refs = [db.collection("workspaces").document(workspace_id) for workspace_id in workspace_ids]
  workspace_docs = await db.get_all(workspace_refs)
  
  return [doc.to_dict() for doc in workspace_docs if doc.exists]

async def add_workspace_to_user(user_id: UserId, workspace_id: WorkspaceId) -> None:
  """Add a workspace to a user.
  
  Args:
      user_id: The user id.
      workspace_id: The workspace id.
  """
  user = await get_user_by_id(user_id)
  if not user:
    return
  workspace_ids = user.get("workspace_ids", [])
  workspace_ids.append(workspace_id)
  update_data = UserUpdate(
    workspace_ids = workspace_ids
  )
  await update_user(user_id, update_data)

async def remove_workspace_from_user(user_id: UserId, workspace_id: WorkspaceId) -> None:
  """Remove a workspace from a user.
  
  Args:
      user_id: The user id.
      workspace_id: The workspace id.
  """
  user = await get_user_by_id(user_id)
  if not user:
    return
  workspace_ids = user.get("workspace_ids", [])
  
  if workspace_id not in workspace_ids:
    return
  
  workspace_ids.remove(workspace_id)

  update_data = UserUpdate(
    workspace_ids = workspace_ids
  )
  await update_user(user_id, update_data)

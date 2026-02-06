from app.clients.firebase import db
from app.models import User, UserCreate, UserUpdate
from app.models import Workspace
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

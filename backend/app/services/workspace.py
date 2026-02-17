from app.clients.firebase import db
from app.models import WorkspaceId, WorkspaceCreate, Workspace
from fastapi import HTTPException, status
from datetime import datetime
import secrets
import string

def generate_join_code(length: int = 8) -> str:
  """Generate a unique join code for a workspace."""
  alphabet = string.ascii_uppercase + string.digits
  return ''.join(secrets.choice(alphabet) for _ in range(length))

async def create_workspace(workspace_data: WorkspaceCreate) -> Workspace:
  """Create a new workspace in firestore.

  Args:
      workspace_data: The workspace data to store.
  
  Returns:
      The created workspace data.
  """
  workspace_ref = db.collection("workspaces").document(str(workspace_data.id))
  workspace_dict = workspace_data.model_dump()
  workspace_dict["created_at"] = datetime.now()
  workspace_dict["updated_at"] = datetime.now()

  await workspace_ref.set(workspace_dict)
  return workspace_dict
  
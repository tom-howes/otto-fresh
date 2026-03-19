"""Workspace CRUD and membership. Keeps user.workspace_ids in sync with workspace.member_ids."""
from app.clients.firebase import db
from app.models import WorkspaceCreate, WorkspaceUpdate
from app.models.github import UserId
from app.models.workspace import WorkspaceId
from app.services.user import add_workspace_to_user, remove_workspace_from_user
from fastapi import HTTPException, status
from datetime import datetime
import secrets
import string


def generate_join_code(length: int = 8) -> str:
    """Generate a unique join code for a workspace."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def create_workspace(data: WorkspaceCreate, creator_id: UserId) -> dict:
    """
    Create a new workspace with auto-generated id and join_code.
    Adds creator to member_ids and to user's workspace_ids.
    """
    col_ref = db.collection("workspaces")
    doc_ref = col_ref.document()
    workspace_id = doc_ref.id
    join_code = generate_join_code()
    now = datetime.now()
    workspace_dict = {
        "id": workspace_id,
        "name": data.name,
        "join_code": join_code,
        "member_ids": [creator_id],
        "repos": data.model_dump().get("repos", []) or [],
        "created_by": creator_id,
        "created_at": now,
        "updated_at": now,
    }
    await doc_ref.set(workspace_dict)
    await add_workspace_to_user(creator_id, workspace_id)
    return workspace_dict


async def get_workspace(workspace_id: str) -> dict | None:
    """Get a workspace by id. Returns None if not found."""
    doc_ref = db.collection("workspaces").document(workspace_id)
    doc = await doc_ref.get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    d["id"] = doc.id
    return d


async def update_workspace(workspace_id: str, data: WorkspaceUpdate) -> None:
    """Update workspace. Only non-None fields are updated. Raises 404 if not found."""
    doc_ref = db.collection("workspaces").document(workspace_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        return
    update_dict["updated_at"] = datetime.now()
    await doc_ref.update(update_dict)


async def get_workspace_by_join_code(join_code: str) -> dict | None:
    """Find a workspace by join_code. Returns None if not found."""
    ref = db.collection("workspaces").where("join_code", "==", join_code).limit(1)
    snapshot = ref.stream()
    async for doc in snapshot:
        d = doc.to_dict()
        d["id"] = doc.id
        return d
    return None


async def add_member(workspace_id: WorkspaceId, user_id: UserId) -> None:
    """Add a user to the workspace (member_ids and user's workspace_ids). Raises 404 if workspace not found."""
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    member_ids = list(workspace.get("member_ids") or [])
    if user_id in member_ids:
        return
    member_ids.append(user_id)
    doc_ref = db.collection("workspaces").document(workspace_id)
    await doc_ref.update(
        {"member_ids": member_ids, "updated_at": datetime.now()}
    )
    await add_workspace_to_user(user_id, workspace_id)


async def remove_member(workspace_id: WorkspaceId, user_id: UserId) -> None:
    """Remove a user from the workspace (member_ids and user's workspace_ids). Raises 404 if workspace not found."""
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    member_ids = list(workspace.get("member_ids") or [])
    if user_id not in member_ids:
        return
    member_ids.remove(user_id)
    doc_ref = db.collection("workspaces").document(workspace_id)
    await doc_ref.update(
        {"member_ids": member_ids, "updated_at": datetime.now()}
    )
    await remove_workspace_from_user(user_id, workspace_id)

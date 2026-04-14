"""Workspace CRUD and join-by-code. All routes require auth; member-only for get/patch."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.services.workspace import (
    create_workspace,
    get_workspace,
    update_workspace,
    get_workspace_by_join_code,
    add_member,
)
from app.services.user import get_user_by_id
from app.models import User, WorkspaceCreate, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class JoinWorkspaceRequest(BaseModel):
    """Body for POST /workspaces/join."""
    join_code: str


@router.post("", status_code=status.HTTP_201_CREATED)
async def post_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new workspace. Creator is set as the only member and added to user.workspace_ids."""
    workspace = await create_workspace(data, creator_id=current_user["id"])
    return workspace


@router.post("/join", status_code=status.HTTP_200_OK)
async def join_workspace(
    body: JoinWorkspaceRequest,
    current_user: User = Depends(get_current_user),
):
    """Join a workspace by join_code. Adds current user to workspace and to user.workspace_ids."""
    workspace = await get_workspace_by_join_code(body.join_code)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No workspace found with this join code",
        )
    await add_member(workspace["id"], current_user["id"])
    updated = await get_workspace(workspace["id"])
    return updated


@router.get("/{workspace_id}", status_code=status.HTTP_200_OK)
async def get_workspace_route(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Get a workspace by id. Only members can access."""
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


@router.get("/{workspace_id}/members", status_code=status.HTTP_200_OK)
async def get_workspace_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Get member profiles for a workspace. Only members can access."""
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    members = []
    for user_id in workspace.get("member_ids", []):
        user = await get_user_by_id(user_id)
        if user:
            members.append({
                "id": user["id"],
                "github_username": user["github_username"],
                "avatar_url": user.get("avatar_url", ""),
            })
    return members


@router.patch("/{workspace_id}", status_code=status.HTTP_200_OK)
async def patch_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Update a workspace. Only provided fields are updated. Only members can update."""
    await update_workspace(workspace_id, data)
    workspace = await get_workspace(workspace_id)
    return workspace

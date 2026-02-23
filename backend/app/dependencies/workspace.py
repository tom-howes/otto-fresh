"""Workspace-scoped dependencies: require current user to be a member of the workspace."""
from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models import User


async def require_workspace_member(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Ensure the current user is a member of the given workspace.
    Use as a dependency on routes that take workspace_id.

    Raises:
        HTTPException: 403 if user is not a member of the workspace.
    """
    workspace_ids = current_user.get("workspace_ids") or []
    if workspace_id not in workspace_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace",
        )

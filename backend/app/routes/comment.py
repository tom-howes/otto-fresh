"""Comment CRUD API. All routes are scoped to a workspace and an issue; require workspace membership."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.services.comment import (
    get_comments,
    get_comment,
    create_comment,
    update_comment,
    delete_comment,
    is_comment_author,
)
from app.services.issue import get_issue
from app.models import User, CommentCreate, CommentUpdate

router = APIRouter(prefix="/workspaces", tags=["Comments"])


@router.get("/{workspace_id}/issues/{issue_id}/comments", status_code=status.HTTP_200_OK)
async def list_comments(
    workspace_id: str,
    issue_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """List all comments on an issue."""
    if await get_issue(workspace_id, issue_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    items = await get_comments(workspace_id, issue_id)
    return {"comments": items}


@router.post("/{workspace_id}/issues/{issue_id}/comments", status_code=status.HTTP_201_CREATED)
async def post_comment(
    workspace_id: str,
    issue_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Add a comment to an issue. Author is set to current user."""
    if await get_issue(workspace_id, issue_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    comment = await create_comment(
        workspace_id=workspace_id,
        issue_id=issue_id,
        data=data,
        author_id=current_user["id"],
    )
    return comment


@router.get("/{workspace_id}/issues/{issue_id}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def get_comment_route(
    workspace_id: str,
    issue_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Get a single comment by id."""
    comment = await get_comment(workspace_id, issue_id, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


@router.patch("/{workspace_id}/issues/{issue_id}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def patch_comment(
    workspace_id: str,
    issue_id: str,
    comment_id: str,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Update a comment. Only the author may update (optional enforcement)."""
    comment = await get_comment(workspace_id, issue_id, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    author_ok = await is_comment_author(workspace_id, issue_id, comment_id, current_user["id"])
    if not author_ok:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the comment author can update it")
    await update_comment(workspace_id, issue_id, comment_id, data)
    updated = await get_comment(workspace_id, issue_id, comment_id)
    return updated


@router.delete("/{workspace_id}/issues/{issue_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_route(
    workspace_id: str,
    issue_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Delete a comment. Only the author may delete (optional enforcement)."""
    comment = await get_comment(workspace_id, issue_id, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    author_ok = await is_comment_author(workspace_id, issue_id, comment_id, current_user["id"])
    if not author_ok:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the comment author can delete it")
    await delete_comment(workspace_id, issue_id, comment_id)

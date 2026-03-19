"""Issue CRUD API. All routes are scoped to a workspace and require membership."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.services.issue import (
    get_issues,
    get_issue,
    create_issue,
    update_issue,
    delete_issue,
)
from app.models import User, IssueCreate, IssueUpdate

router = APIRouter(prefix="/workspaces", tags=["Issues"])


@router.get("/{workspace_id}/issues", status_code=status.HTTP_200_OK)
async def list_issues(
    workspace_id: str,
    section_id: str | None = Query(None, description="Filter by section"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """List issues in the workspace, optionally filtered by section_id."""
    items = await get_issues(workspace_id, section_id=section_id)
    return {"issues": items}


@router.post("/{workspace_id}/issues", status_code=status.HTTP_201_CREATED)
async def post_issue(
    workspace_id: str,
    data: IssueCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Create a new issue in the workspace. Reporter is set to current user."""
    issue = await create_issue(
        workspace_id=workspace_id,
        data=data,
        reporter_id=current_user["id"],
    )
    return issue


@router.get("/{workspace_id}/issues/{issue_id}", status_code=status.HTTP_200_OK)
async def get_issue_route(
    workspace_id: str,
    issue_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Get a single issue by id."""
    issue = await get_issue(workspace_id, issue_id)
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return issue


@router.patch("/{workspace_id}/issues/{issue_id}", status_code=status.HTTP_200_OK)
async def patch_issue(
    workspace_id: str,
    issue_id: str,
    data: IssueUpdate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Update an issue. Only provided fields are updated."""
    await update_issue(workspace_id, issue_id, data)
    issue = await get_issue(workspace_id, issue_id)
    return issue


@router.delete("/{workspace_id}/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue_route(
    workspace_id: str,
    issue_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_workspace_member),
):
    """Delete an issue."""
    await delete_issue(workspace_id, issue_id)

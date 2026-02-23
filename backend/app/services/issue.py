"""Issue CRUD scoped to a workspace. Issues live in workspaces/{workspace_id}/issues."""
from app.clients.firebase import db
from app.models import Issue, IssueCreate, IssueUpdate
from app.models.enums import Priority
from app.models.github import UserId
from fastapi import HTTPException, status
from datetime import datetime


def _issues_ref(workspace_id: str):
    return db.collection("workspaces").document(workspace_id).collection("issues")


async def get_issues(workspace_id: str, section_id: str | None = None) -> list[dict]:
    """List issues in a workspace, optionally filtered by section_id. Ordered by position."""
    ref = _issues_ref(workspace_id)
    snapshot = ref.stream()
    issues = []
    async for doc in snapshot:
        d = doc.to_dict()
        d["id"] = doc.id
        if section_id is None or d.get("section_id") == section_id:
            issues.append(d)
    issues.sort(key=lambda x: (x.get("position", 0), x.get("created_at", "")))
    return issues


async def get_issue(workspace_id: str, issue_id: str) -> dict | None:
    """Get a single issue by id. Returns None if not found."""
    doc_ref = _issues_ref(workspace_id).document(issue_id)
    doc = await doc_ref.get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    d["id"] = doc.id
    return d


async def _next_position_in_section(workspace_id: str, section_id: str) -> int:
    """Return the next position value for a new issue in the given section."""
    issues = await get_issues(workspace_id, section_id=section_id)
    if not issues:
        return 0
    return max(i.get("position", 0) for i in issues) + 1


async def create_issue(
    workspace_id: str,
    data: IssueCreate,
    reporter_id: UserId,
) -> dict:
    """Create a new issue. Sets reporter_id, position, and default priority."""
    col_ref = _issues_ref(workspace_id)
    doc_ref = col_ref.document()
    position = await _next_position_in_section(workspace_id, data.section_id)
    now = datetime.now()
    issue_dict = {
        "id": doc_ref.id,
        "title": data.title,
        "description": None,
        "section_id": data.section_id,
        "assignee_id": None,
        "reporter_id": reporter_id,
        "position": position,
        "priority": Priority.MEDIUM.value,
        "branch": None,
        "branch_url": None,
        "created_at": now,
        "updated_at": now,
    }
    await doc_ref.set(issue_dict)
    return issue_dict


async def update_issue(
    workspace_id: str,
    issue_id: str,
    data: IssueUpdate,
) -> None:
    """Update an issue. Only non-None fields are updated. Raises 404 if not found."""
    doc_ref = _issues_ref(workspace_id).document(issue_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        return
    update_dict["updated_at"] = datetime.now()
    await doc_ref.update(update_dict)


async def delete_issue(workspace_id: str, issue_id: str) -> None:
    """Delete an issue. Raises 404 if not found."""
    doc_ref = _issues_ref(workspace_id).document(issue_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )
    await doc_ref.delete()

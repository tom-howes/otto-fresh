"""Comment CRUD scoped to an issue. Comments live in workspaces/{wid}/issues/{issue_id}/comments."""
from app.clients.firebase import db
from app.models import CommentCreate, CommentUpdate
from app.models.github import UserId
from fastapi import HTTPException, status
from datetime import datetime


def _comments_ref(workspace_id: str, issue_id: str):
    return (
        db.collection("workspaces")
        .document(workspace_id)
        .collection("issues")
        .document(issue_id)
        .collection("comments")
    )


async def get_comments(workspace_id: str, issue_id: str) -> list[dict]:
    """List all comments on an issue, ordered by created_at."""
    ref = _comments_ref(workspace_id, issue_id)
    snapshot = ref.stream()
    comments = []
    async for doc in snapshot:
        d = doc.to_dict()
        d["id"] = doc.id
        comments.append(d)
    comments.sort(key=lambda x: x.get("created_at", ""))
    return comments


async def get_comment(
    workspace_id: str,
    issue_id: str,
    comment_id: str,
) -> dict | None:
    """Get a single comment by id. Returns None if not found."""
    doc_ref = _comments_ref(workspace_id, issue_id).document(comment_id)
    doc = await doc_ref.get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    d["id"] = doc.id
    return d


async def create_comment(
    workspace_id: str,
    issue_id: str,
    data: CommentCreate,
    author_id: UserId,
) -> dict:
    """Create a new comment. Sets author_id from current user."""
    col_ref = _comments_ref(workspace_id, issue_id)
    doc_ref = col_ref.document()
    now = datetime.now()
    comment_dict = {
        "id": doc_ref.id,
        "content": data.content,
        "author_id": author_id,
        "created_at": now,
        "updated_at": now,
    }
    await doc_ref.set(comment_dict)
    return comment_dict


async def update_comment(
    workspace_id: str,
    issue_id: str,
    comment_id: str,
    data: CommentUpdate,
) -> None:
    """Update a comment. Only non-None fields are updated. Raises 404 if not found."""
    doc_ref = _comments_ref(workspace_id, issue_id).document(comment_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        return
    update_dict["updated_at"] = datetime.now()
    await doc_ref.update(update_dict)


async def delete_comment(
    workspace_id: str,
    issue_id: str,
    comment_id: str,
) -> None:
    """Delete a comment. Raises 404 if not found."""
    doc_ref = _comments_ref(workspace_id, issue_id).document(comment_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    await doc_ref.delete()


async def is_comment_author(
    workspace_id: str,
    issue_id: str,
    comment_id: str,
    user_id: UserId,
) -> bool:
    """Return True if the given user is the author of the comment."""
    comment = await get_comment(workspace_id, issue_id, comment_id)
    return comment is not None and comment.get("author_id") == user_id

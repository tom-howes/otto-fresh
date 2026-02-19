from app.models.base import BaseModel, datetime
from app.models.github import UserId, GitHubRepo
from typing import TypeAlias

WorkspaceId: TypeAlias = str
"""Unique identifier for a workspace."""

class Workspace(BaseModel):
    """Complete workspace data returned from the API.

    Attributes:
        id: Unique identifier for the workspace.
        name: Display name of the workspace.
        join_code: Unique code for users to join this workspace.
        member_ids: List of user IDs who belong to this workspace.
        repos: List of repositories that belong to this workspace.
        created_by: User ID of the workspace creator.
        created_at: Timestamp when the workspace was created.
        updated_at: Timestamp when the workspace was last modified.
    """
    id: WorkspaceId
    name: str
    join_code: str
    member_ids: list[UserId]
    repos: list[GitHubRepo]
    created_by: UserId
    created_at: datetime
    updated_at: datetime


class WorkspaceCreate(BaseModel):
    """Data required to create a new workspace.

    The first repository can be connected immediately after creation
    via a separate call, or the workspace can start empty.

    Attributes:
        name: Display name for the workspace.
        repos: List of repositories that belong to this workspace.
    """
    name: str
    repos: list[GitHubRepo]


class WorkspaceUpdate(BaseModel):
    """Data for updating an existing workspace. All fields are optional.

    Attributes:
        name: New display name for the workspace.
        member_ids: List of user IDs who belong to this workspace.
    """
    name: str | None = None
    member_ids: list[UserId]
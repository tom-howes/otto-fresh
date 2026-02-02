from app.models.base import BaseModel, datetime

class UserRead(BaseModel):
  """User data safe to return to clients"""
  id: str
  github_username: str
  email: str | None
  avatar_url: str
  workspace_ids: list[str]
  created_at: datetime
  updated_at: datetime

class User(UserRead):
  """Full user data for internal use"""
  github_access_token: str
  github_refresh_token: str | None
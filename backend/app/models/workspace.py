from app.models.base import BaseModel, datetime

class WorkspaceRead(BaseModel):
  id: str
  name: str
  join_code: str
  repo_owner: str
  repo_name: str
  repo_full_name: str
  repo_default_branch: str
  member_ids: list[str]
  created_by: str
  created_at: datetime
  updated_at: datetime

class WorkspaceCreate(BaseModel):
  repo_full_name: str

class WorkspaceUpdate(BaseModel):
  name: str | None
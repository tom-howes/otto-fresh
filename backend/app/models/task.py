from app.models.base import BaseModel, datetime
from app.models.enums import Priority

class TaskRead(BaseModel):
  id: str
  title: str
  description: str | None
  section_id: str
  assignee_id: str | None
  reporter_id: str
  position: int
  priority: Priority
  branch: str | None
  branch_url: str | None
  created_at: datetime
  updated_at: datetime

class TaskCreate(BaseModel):
  title: str
  section_id: str

class TaskUpdate(BaseModel):
  title: str | None
  description: str | None
  section_id: str | None
  position: int | None
  assignee_id: str | None
  reporter_id: str | None
  priority: Priority | None
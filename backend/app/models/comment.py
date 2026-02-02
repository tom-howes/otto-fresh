from app.models.base import BaseModel, datetime

class CommentRead(BaseModel):
  id: str
  content: str
  author_id: str
  created_at: datetime
  updated_at: datetime

class CommentCreate(BaseModel):
  content: str

class CommentUpdate(BaseModel):
  content: str | None
from app.models.base import BaseModel, datetime

class SectionRead(BaseModel):
  id: str
  title: str
  position: int
  created_at: datetime
  updated_at: datetime

class SectionCreate(BaseModel):
  title: str

class SectionUpdate(BaseModel):
  title: str | None
  position: int | None
from pydantic import BaseModel
from datetime import datetime

class FileResponse(BaseModel):
    id: int
    original_name: str
    file_size: int
    mime_type: str | None
    is_encrypted: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True
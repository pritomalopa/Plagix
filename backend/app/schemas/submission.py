from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class SubmissionResponse(BaseModel):
    id: UUID
    evaluation_id: UUID
    student_label: str
    student_id: Optional[str] = None
    original_filename: str
    file_hash: str
    extraction_status: str
    language: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    submissions: List[SubmissionResponse]
    total: int

    class Config:
        from_attributes = True

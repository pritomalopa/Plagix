from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# --- Rubric Criteria Schemas ---

class RubricCriterionCreate(BaseModel):
    criterion: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_points: int = Field(..., ge=0)
    weight: float = Field(1.0, ge=0.0)
    expected_evidence: Optional[str] = None
    order: int = Field(0, ge=0)


class RubricCriterionUpdate(BaseModel):
    criterion: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    max_points: Optional[int] = Field(None, ge=0)
    weight: Optional[float] = Field(None, ge=0.0)
    expected_evidence: Optional[str] = None
    order: Optional[int] = Field(None, ge=0)


class RubricCriterionResponse(BaseModel):
    id: UUID
    question_id: UUID
    criterion: str
    description: Optional[str] = None
    max_points: int
    weight: float
    expected_evidence: Optional[str] = None
    order: int

    class Config:
        from_attributes = True


# --- Question Schemas ---

class QuestionCreate(BaseModel):
    order: int = Field(0, ge=0)
    prompt: str = Field(..., min_length=1)
    instructions: Optional[str] = None
    reference_answer: Optional[str] = None
    expected_concepts: Optional[Dict[str, Any]] = None
    citation_policy: Optional[str] = Field("none", max_length=100)
    rubric_criteria: Optional[List[RubricCriterionCreate]] = []


class QuestionUpdate(BaseModel):
    order: Optional[int] = Field(None, ge=0)
    prompt: Optional[str] = Field(None, min_length=1)
    instructions: Optional[str] = None
    reference_answer: Optional[str] = None
    expected_concepts: Optional[Dict[str, Any]] = None
    citation_policy: Optional[str] = Field(None, max_length=100)


class QuestionResponse(BaseModel):
    id: UUID
    evaluation_id: UUID
    order: int
    prompt: str
    instructions: Optional[str] = None
    reference_answer: Optional[str] = None
    expected_concepts: Optional[Dict[str, Any]] = None
    citation_policy: Optional[str] = None
    created_at: datetime
    rubric_criteria: List[RubricCriterionResponse] = []

    class Config:
        from_attributes = True


# --- Evaluation Schemas ---

class EvaluationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    language: str = Field("en", min_length=2, max_length=10)
    max_marks: int = Field(..., gt=0)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    questions: Optional[List[QuestionCreate]] = []


class EvaluationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    max_marks: Optional[int] = Field(None, gt=0)
    settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=50)


class EvaluationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    owner_id: UUID
    title: str
    language: str
    max_marks: int
    settings: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    evaluations: List[EvaluationResponse]
    total: int
    page: int
    per_page: int

    class Config:
        from_attributes = True

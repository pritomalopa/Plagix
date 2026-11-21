from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    role: str = "teacher"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: str = Field(..., min_length=2, description="Teacher / User full name")
    tenant_name: Optional[str] = Field(None, description="Organization / Institution name (optional during registration)")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TenantResponse(BaseModel):
    id: UUID
    name: str
    plan: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    role: str
    status: str
    created_at: datetime
    tenant: Optional[TenantResponse] = None

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

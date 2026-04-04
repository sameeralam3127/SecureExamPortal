from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    role: UserRole = UserRole.student


class BulkUserCreate(BaseModel):
    users: list[UserCreate] = Field(min_length=1)


class StudentRegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20)


class UserRead(BaseModel):
    id: int
    full_name: str
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=72)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

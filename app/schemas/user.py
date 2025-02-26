from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any, Union, Literal

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    roles: Optional[List[int]] = []

class UserOut(UserBase):
    id: int
    roles: List[Dict[str, Any]] = []
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    roles: Optional[List[int]] = None

class UserPasswordChange(BaseModel):
    username: str
    password: str
    password_confirmation: str

    @field_validator('password_confirmation')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedUserResponse(BaseModel):
    items: List[UserOut]
    total: int
    page: int
    pageSize: int
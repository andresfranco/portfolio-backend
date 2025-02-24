from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    roles: Optional[List[int]] = []

class UserOut(UserBase):
    id: int
    roles: List[int] = []
    class Config:
        from_attributes = True  # Pydantic V2 compatibility

class UserUpdate(BaseModel):  # No inheritance from UserBase
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
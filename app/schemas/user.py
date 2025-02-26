from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any  # Added Any import

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    roles: Optional[List[int]] = []

class UserOut(UserBase):
    id: int
    roles: List[Dict[str, Any]] = []  # Changed 'any' to 'Any'
    class Config:
        from_attributes = True  # Pydantic V2 compatibility

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    roles: Optional[List[int]] = None  # Now will accept just a roles array

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
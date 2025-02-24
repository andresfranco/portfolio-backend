from pydantic import BaseModel, EmailStr
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
    password: str
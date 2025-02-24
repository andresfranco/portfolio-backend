from pydantic import BaseModel

class RoleBase(BaseModel):
    name: str
    description: str  # Add description field

class RoleOut(RoleBase):
    id: int

    class Config:
        from_attributes = True  # Use from_attributes instead of orm_mode

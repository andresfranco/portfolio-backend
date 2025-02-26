from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal, Any, ClassVar

class PermissionBase(BaseModel):
    name: str
    description: str

class PermissionCreate(PermissionBase):
    pass

class PermissionOut(PermissionBase):
    id: int

    model_config = {
        "from_attributes": True
    }

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PaginatedPermissionResponse(BaseModel):
    items: List[PermissionOut]
    total: int
    page: int
    pageSize: int

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal['eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'contains', 'startswith', 'endswith']
    
    # Define valid fields as a class variable
    valid_fields: ClassVar[List[str]] = ['name', 'description', 'id']
    
    @field_validator('field')
    @classmethod
    def validate_field(cls, field):
        if field not in cls.valid_fields:
            raise ValueError(f"Invalid field: {field}. Valid fields are {cls.valid_fields}")
        return field
    
    @classmethod
    def from_params(cls, field: str, value: str, operator: str):
        return cls(field=field, value=value, operator=operator)
from pydantic import BaseModel
from typing import List, Optional, Literal

class RoleBase(BaseModel):
    name: str
    description: str
    permissions: List[str] = []  # List of permission names

class RoleOut(BaseModel):
    id: int
    name: str
    description: str
    permissions: List[str] = []
    users_count: int = 0  # Count of users with this role

    class Config:
        from_attributes = True

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleFilter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "RoleFilter":
        # Validate that field is a valid field name
        valid_fields = ["name", "description", "permission"]
        if field not in valid_fields and field != "permissions":  # Allow "permissions" for backward compatibility
            raise ValueError(f"Invalid filter field: {field}. Valid fields are: {valid_fields}")
            
        # Convert "permissions" to "permission" for consistency
        if field == "permissions":
            field = "permission"
            
        return cls(field=field, value=value, operator=operator)

class PaginatedRoleResponse(BaseModel):
    items: List[RoleOut]
    total: int
    page: int
    pageSize: int

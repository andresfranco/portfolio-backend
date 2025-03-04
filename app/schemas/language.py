from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal

class LanguageBase(BaseModel):
    code: str
    name: str
    image: str
    is_default: bool = False

class LanguageCreate(LanguageBase):
    pass

class LanguageUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    image: Optional[str] = None
    is_default: Optional[bool] = None

class LanguageOut(LanguageBase):
    id: int
    
    class Config:
        from_attributes = True

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedLanguageResponse(BaseModel):
    items: List[LanguageOut]
    total: int
    page: int
    pageSize: int

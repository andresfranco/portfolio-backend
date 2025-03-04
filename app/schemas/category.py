from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal

class CategoryTextBase(BaseModel):
    language_id: int
    name: str
    description: str

class CategoryTextCreate(CategoryTextBase):
    pass

class CategoryTextUpdate(BaseModel):
    language_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryTextOut(CategoryTextBase):
    id: int
    language: Dict[str, Any]
    
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    code: str
    type: str  # e.g., "skill", "project"

class CategoryCreate(CategoryBase):
    category_texts: List[CategoryTextCreate]
    skills: Optional[List[int]] = []

class CategoryUpdate(BaseModel):
    code: Optional[str] = None
    type: Optional[str] = None
    category_texts: Optional[List[CategoryTextCreate]] = None
    skills: Optional[List[int]] = None

class CategoryOut(CategoryBase):
    id: int
    category_texts: List[CategoryTextOut] = []
    skills: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedCategoryResponse(BaseModel):
    items: List[CategoryOut]
    total: int
    page: int
    pageSize: int

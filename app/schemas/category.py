from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal
from app.schemas.language import LanguageOut
from app.schemas.category_type import CategoryType

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
    language: LanguageOut
    
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    code: str
    type_code: str

class CategoryCreate(CategoryBase):
    category_texts: List[CategoryTextCreate]

class CategoryUpdate(BaseModel):
    code: Optional[str] = None
    type_code: Optional[str] = None
    category_texts: Optional[List[CategoryTextCreate]] = None
    removed_language_ids: Optional[List[int]] = None

class Category(CategoryBase):
    id: int
    category_texts: List[CategoryTextOut] = []
    skills: List[Dict[str, Any]] = []
    category_type: Optional[CategoryType] = None
    
    class Config:
        from_attributes = True

class CategoryOut(Category):
    pass

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedCategoryResponse(BaseModel):
    items: List[Category]
    total: int
    page: int
    pageSize: int

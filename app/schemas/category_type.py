from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal
from app.schemas.language import LanguageOut

class CategoryTypeBase(BaseModel):
    code: str
    name: str

class CategoryTypeCreate(CategoryTypeBase):
    pass

class CategoryTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class CategoryType(CategoryTypeBase):
    class Config:
        from_attributes = True

class CategoryTypeOut(CategoryType):
    pass

class Filter(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class PaginatedCategoryTypeResponse(BaseModel):
    items: List[CategoryType]
    total: int
    page: int
    pageSize: int

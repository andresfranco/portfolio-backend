from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal

class TranslationBase(BaseModel):
    identifier: str
    text: str

class TranslationCreate(TranslationBase):
    languages: List[int]

class TranslationUpdate(BaseModel):
    identifier: Optional[str] = None
    text: Optional[str] = None
    languages: Optional[List[int]] = None

class TranslationOut(TranslationBase):
    id: int
    languages: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedTranslationResponse(BaseModel):
    items: List[TranslationOut]
    total: int
    page: int
    pageSize: int

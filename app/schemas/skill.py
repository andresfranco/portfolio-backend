from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal

class SkillTextBase(BaseModel):
    language_id: int
    name: str
    description: str

class SkillTextCreate(SkillTextBase):
    pass

class SkillTextUpdate(BaseModel):
    language_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None

class SkillTextOut(SkillTextBase):
    id: int
    language: Dict[str, Any]
    
    class Config:
        from_attributes = True

class SkillBase(BaseModel):
    type: str  # e.g., "soft", "hard", "technical"

class SkillCreate(SkillBase):
    skill_texts: List[SkillTextCreate]
    categories: Optional[List[int]] = []

class SkillUpdate(BaseModel):
    type: Optional[str] = None
    skill_texts: Optional[List[SkillTextCreate]] = None
    categories: Optional[List[int]] = None

class SkillOut(SkillBase):
    id: int
    skill_texts: List[SkillTextOut] = []
    categories: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedSkillResponse(BaseModel):
    items: List[SkillOut]
    total: int
    page: int
    pageSize: int

# Added UniqueCheckResponse for the check-unique endpoint
class UniqueCheckResponse(BaseModel):
    exists: bool
    name: str
    language_id: int

from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal

class ExperienceTextBase(BaseModel):
    language_id: int
    name: str
    description: str

class ExperienceTextCreate(ExperienceTextBase):
    pass

class ExperienceTextUpdate(BaseModel):
    language_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None

class ExperienceTextOut(ExperienceTextBase):
    id: int
    language: Dict[str, Any]
    
    class Config:
        from_attributes = True

class ExperienceBase(BaseModel):
    years: int

class ExperienceCreate(ExperienceBase):
    experience_texts: List[ExperienceTextCreate]

class ExperienceUpdate(BaseModel):
    years: Optional[int] = None
    experience_texts: Optional[List[ExperienceTextCreate]] = None

class ExperienceOut(ExperienceBase):
    id: int
    experience_texts: List[ExperienceTextOut] = []
    
    class Config:
        from_attributes = True

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedExperienceResponse(BaseModel):
    items: List[ExperienceOut]
    total: int
    page: int
    pageSize: int

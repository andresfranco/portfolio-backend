from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal

class ProjectTextBase(BaseModel):
    language_id: int
    name: str
    description: str

class ProjectTextCreate(ProjectTextBase):
    pass

class ProjectTextUpdate(BaseModel):
    language_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectTextOut(ProjectTextBase):
    id: int
    language: Dict[str, Any]
    
    class Config:
        from_attributes = True

class ProjectImageBase(BaseModel):
    image_path: str
    category: str  # e.g., "diagram", "main", "gallery"

class ProjectImageCreate(ProjectImageBase):
    pass

class ProjectImageUpdate(BaseModel):
    image_path: Optional[str] = None
    category: Optional[str] = None

class ProjectImageOut(ProjectImageBase):
    id: int
    
    class Config:
        from_attributes = True

class ProjectAttachmentBase(BaseModel):
    file_path: str
    file_name: str

class ProjectAttachmentCreate(ProjectAttachmentBase):
    pass

class ProjectAttachmentUpdate(BaseModel):
    file_path: Optional[str] = None
    file_name: Optional[str] = None

class ProjectAttachmentOut(ProjectAttachmentBase):
    id: int
    
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    repository_url: Optional[str] = None
    website_url: Optional[str] = None

class ProjectCreate(ProjectBase):
    project_texts: List[ProjectTextCreate]
    images: Optional[List[ProjectImageCreate]] = []
    attachments: Optional[List[ProjectAttachmentCreate]] = []
    categories: Optional[List[int]] = []
    skills: Optional[List[int]] = []

class ProjectUpdate(BaseModel):
    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    project_texts: Optional[List[ProjectTextCreate]] = None
    categories: Optional[List[int]] = None
    skills: Optional[List[int]] = None

class ProjectOut(ProjectBase):
    id: int
    project_texts: List[ProjectTextOut] = []
    images: List[ProjectImageOut] = []
    attachments: List[ProjectAttachmentOut] = []
    categories: List[Dict[str, Any]] = []
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

class PaginatedProjectResponse(BaseModel):
    items: List[ProjectOut]
    total: int
    page: int
    pageSize: int

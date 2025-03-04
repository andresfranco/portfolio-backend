from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal

class PortfolioImageBase(BaseModel):
    image_path: str

class PortfolioImageCreate(PortfolioImageBase):
    pass

class PortfolioImageUpdate(BaseModel):
    image_path: Optional[str] = None

class PortfolioImageOut(PortfolioImageBase):
    id: int
    
    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    name: str
    description: str

class PortfolioCreate(PortfolioBase):
    categories: Optional[List[int]] = []
    experiences: Optional[List[int]] = []
    projects: Optional[List[int]] = []
    sections: Optional[List[int]] = []
    images: Optional[List[PortfolioImageCreate]] = []

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[int]] = None
    experiences: Optional[List[int]] = None
    projects: Optional[List[int]] = None
    sections: Optional[List[int]] = None

class PortfolioOut(PortfolioBase):
    id: int
    categories: List[Dict[str, Any]] = []
    experiences: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    sections: List[Dict[str, Any]] = []
    images: List[PortfolioImageOut] = []
    
    class Config:
        from_attributes = True

class Filter(BaseModel):
    field: str
    value: str
    operator: Literal["contains", "equals", "startsWith", "endsWith"] = "contains"

    @classmethod
    def from_params(cls, field: str, value: str, operator: str = "contains") -> "Filter":
        return cls(field=field, value=value, operator=operator)

class PaginatedPortfolioResponse(BaseModel):
    items: List[PortfolioOut]
    total: int
    page: int
    pageSize: int

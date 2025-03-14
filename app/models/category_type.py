from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class CategoryType(Base):
    __tablename__ = "category_types"
    code = Column(String(5), primary_key=True, index=True)
    name = Column(String)
    
    # Timestamp and user tracking fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String)  # user id who created the record
    updated_by = Column(String)  # user id who last updated the record

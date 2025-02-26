from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.permission import role_permissions

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)
    
    # Back-reference to users via the association table
    users = relationship("User", secondary="user_roles", back_populates="roles")
    # Add permissions relationship
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

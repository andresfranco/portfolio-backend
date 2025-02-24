from sqlalchemy import Column, Integer, String, DateTime  # added DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # added func for timestamp defaults
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)  # new description field
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # new timestamp
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # new timestamp
    created_by = Column(Integer)  # new user field for creator
    updated_by = Column(Integer)  # new user field for updater
    # Back-reference to users via the association table
    users = relationship("User", secondary="user_roles", back_populates="roles")

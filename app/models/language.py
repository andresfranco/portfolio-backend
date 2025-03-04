from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.translation import translation_languages

class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, unique=True, index=True)
    image = Column(String)  # Path to flag icon
    is_default = Column(Boolean, default=False)
    
    # Timestamp and user tracking fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)  # user id who created the record
    updated_by = Column(Integer)  # user id who last updated the record
    
    # Relationships
    translations = relationship("Translation", secondary=translation_languages, back_populates="language")
    section_texts = relationship("SectionText", back_populates="language")
    project_texts = relationship("ProjectText", back_populates="language")
    experience_texts = relationship("ExperienceText", back_populates="language")
    category_texts = relationship("CategoryText", back_populates="language")
    skill_texts = relationship("SkillText", back_populates="language")

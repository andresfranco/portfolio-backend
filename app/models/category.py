from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association table for many-to-many relationship between categories and skills
category_skills = Table(
    "category_skills",
    Base.metadata,
    Column("category_id", Integer, ForeignKey("categories.id")),
    Column("skill_id", Integer, ForeignKey("skills.id"))
)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    type = Column(String)  # e.g., "skill", "project"
    
    # Timestamp and user tracking fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)  # user id who created the record
    updated_by = Column(Integer)  # user id who last updated the record
    
    # Relationships
    portfolios = relationship("Portfolio", secondary="portfolio_categories", back_populates="categories")
    projects = relationship("Project", secondary="project_categories", back_populates="categories")
    skills = relationship("Skill", secondary=category_skills, back_populates="categories")
    category_texts = relationship("CategoryText", back_populates="category")


class CategoryText(Base):
    __tablename__ = "category_texts"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    language_id = Column(Integer, ForeignKey("languages.id"))
    name = Column(String)
    description = Column(Text)
    
    # Timestamp and user tracking fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)  # user id who created the record
    updated_by = Column(Integer)  # user id who last updated the record
    
    # Relationships
    category = relationship("Category", back_populates="category_texts")
    language = relationship("Language", back_populates="category_texts")

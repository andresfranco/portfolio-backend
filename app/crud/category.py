from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.category import Category, CategoryText
from app.models.skill import Skill
from app.models.language import Language
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryTextCreate, Filter
from typing import List, Optional, Tuple
import logging
import sys

# Use Uvicorn's logger for consistency
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# CRUD Functions
def get_category(db: Session, category_id: int):
    logger.debug(f"Fetching category with ID {category_id}")
    return db.query(Category).filter(Category.id == category_id).first()

def get_category_by_code(db: Session, code: str):
    logger.debug(f"Fetching category by code: {code}")
    return db.query(Category).filter(Category.code == code).first()

def create_category(db: Session, category: CategoryCreate):
    logger.debug(f"Starting category creation for {category.code}")
    
    # Create the category
    db_category = Category(
        code=category.code,
        type=category.type
    )
    db.add(db_category)
    db.flush()  # Flush to get the category ID
    
    # Add skills if provided
    if category.skills:
        skills = db.query(Skill).filter(Skill.id.in_(category.skills)).all()
        if len(skills) != len(category.skills):
            missing_skills = set(category.skills) - {skill.id for skill in skills}
            logger.error(f"Invalid skill IDs: {missing_skills}")
            raise ValueError(f"Invalid skill IDs: {missing_skills}")
        db_category.skills = skills
    
    # Create category texts
    for text_data in category.category_texts:
        # Verify language exists
        language = db.query(Language).filter(Language.id == text_data.language_id).first()
        if not language:
            logger.error(f"Invalid language ID: {text_data.language_id}")
            raise ValueError(f"Invalid language ID: {text_data.language_id}")
        
        db_category_text = CategoryText(
            category_id=db_category.id,
            language_id=text_data.language_id,
            name=text_data.name,
            description=text_data.description
        )
        db.add(db_category_text)
    
    logger.debug("Category added to session")
    return db_category

def update_category(db: Session, category_id: int, category: CategoryUpdate):
    logger.debug(f"Updating category with ID {category_id}")
    db_category = get_category(db, category_id)
    
    if not db_category:
        return None
    
    # Update fields if provided
    if category.code is not None:
        db_category.code = category.code
    
    if category.type is not None:
        db_category.type = category.type
    
    # Update skills if provided
    if category.skills is not None:
        skills = db.query(Skill).filter(Skill.id.in_(category.skills)).all()
        if len(skills) != len(category.skills):
            missing_skills = set(category.skills) - {skill.id for skill in skills}
            logger.error(f"Invalid skill IDs: {missing_skills}")
            raise ValueError(f"Invalid skill IDs: {missing_skills}")
        db_category.skills = skills
    
    # Update category texts if provided
    if category.category_texts is not None:
        # First, remove existing texts
        db.query(CategoryText).filter(CategoryText.category_id == category_id).delete()
        
        # Then add new texts
        for text_data in category.category_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Invalid language ID: {text_data.language_id}")
            
            db_category_text = CategoryText(
                category_id=db_category.id,
                language_id=text_data.language_id,
                name=text_data.name,
                description=text_data.description
            )
            db.add(db_category_text)
    
    return db_category

def delete_category(db: Session, category_id: int):
    logger.debug(f"Deleting category with ID {category_id}")
    db_category = get_category(db, category_id)
    
    if not db_category:
        return None
    
    # Delete associated texts
    db.query(CategoryText).filter(CategoryText.category_id == category_id).delete()
    
    # Delete the category
    db.delete(db_category)
    return db_category

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching categories with skip={skip}, limit={limit}")
    return db.query(Category).offset(skip).limit(limit).all()

def get_categories_by_type(db: Session, category_type: str, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching categories of type {category_type} with skip={skip}, limit={limit}")
    return db.query(Category).filter(Category.type == category_type).offset(skip).limit(limit).all()

def get_categories_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Category], int]:
    query = db.query(Category)
    
    # Separate skill and text filters from other filters
    skill_filter_values = []
    text_filters = []
    other_filters = []
    
    if filters:
        for filter_item in filters:
            if filter_item.field == "skill" or filter_item.field == "skills":
                logger.debug(f"Found skill filter with value: {filter_item.value}")
                skill_filter_values.append(filter_item.value)
            elif filter_item.field == "name" or filter_item.field == "description":
                text_filters.append(filter_item)
            elif hasattr(Category, filter_item.field):
                column = getattr(Category, filter_item.field)
                if filter_item.operator == "contains":
                    other_filters.append(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    other_filters.append(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    other_filters.append(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    other_filters.append(column.ilike(f"%{filter_item.value}"))
    
    if other_filters:
        query = query.filter(*other_filters)
    
    # Apply skill filters
    if skill_filter_values:
        logger.debug(f"Filtering by skills: {skill_filter_values}")
        conditions = [Skill.id == int(skill_id) for skill_id in skill_filter_values]
        query = query.join(Category.skills).filter(or_(*conditions)).distinct()
    
    # Apply text filters
    if text_filters:
        for filter_item in text_filters:
            # Join with CategoryText to filter by name or description
            query = query.join(CategoryText)
            column = getattr(CategoryText, filter_item.field)
            if filter_item.operator == "contains":
                query = query.filter(column.ilike(f"%{filter_item.value}%"))
            elif filter_item.operator == "equals":
                query = query.filter(column == filter_item.value)
            elif filter_item.operator == "startsWith":
                query = query.filter(column.ilike(f"{filter_item.value}%"))
            elif filter_item.operator == "endsWith":
                query = query.filter(column.ilike(f"%{filter_item.value}"))
            query = query.distinct()
    
    total = query.count()
    
    if sort_field:
        if hasattr(Category, sort_field):
            sort_func = asc if sort_order == "asc" else desc
            query = query.order_by(sort_func(getattr(Category, sort_field)))
        elif sort_field in ["name", "description"]:
            # Sort by name or description in the default language
            default_language = db.query(Language).filter(Language.is_default == True).first()
            if default_language:
                query = query.join(CategoryText).filter(CategoryText.language_id == default_language.id)
                sort_func = asc if sort_order == "asc" else desc
                query = query.order_by(sort_func(getattr(CategoryText, sort_field)))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

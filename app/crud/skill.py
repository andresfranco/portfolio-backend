from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.skill import Skill, SkillText
from app.models.category import Category
from app.models.language import Language
from app.schemas.skill import SkillCreate, SkillUpdate, SkillTextCreate, Filter
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
def get_skill(db: Session, skill_id: int):
    logger.debug(f"Fetching skill with ID {skill_id}")
    return db.query(Skill).filter(Skill.id == skill_id).first()

# Added function to get skill by name and language
def get_skill_by_name_and_language(db: Session, name: str, language_id: int):
    """
    Get a skill by name in a specific language
    """
    logger.debug(f"Fetching skill with name '{name}' for language ID {language_id}")
    return db.query(Skill).join(SkillText).filter(
        SkillText.name == name,
        SkillText.language_id == language_id
    ).first()

def create_skill(db: Session, skill: SkillCreate):
    logger.debug(f"Starting skill creation with type {skill.type}")
    
    # Create the skill
    db_skill = Skill(type=skill.type)
    db.add(db_skill)
    db.flush()  # Flush to get the skill ID
    
    # Add categories if provided
    if skill.categories:
        categories = db.query(Category).filter(Category.id.in_(skill.categories)).all()
        if len(categories) != len(skill.categories):
            missing_categories = set(skill.categories) - {cat.id for cat in categories}
            logger.error(f"Invalid category IDs: {missing_categories}")
            raise ValueError(f"Invalid category IDs: {missing_categories}")
        db_skill.categories = categories
    
    # Create skill texts
    for text_data in skill.skill_texts:
        # Verify language exists
        language = db.query(Language).filter(Language.id == text_data.language_id).first()
        if not language:
            logger.error(f"Invalid language ID: {text_data.language_id}")
            raise ValueError(f"Invalid language ID: {text_data.language_id}")
        
        db_skill_text = SkillText(
            skill_id=db_skill.id,
            language_id=text_data.language_id,
            name=text_data.name,
            description=text_data.description
        )
        db.add(db_skill_text)
    
    logger.debug("Skill added to session")
    return db_skill

def update_skill(db: Session, skill_id: int, skill: SkillUpdate):
    logger.debug(f"Updating skill with ID {skill_id}")
    db_skill = get_skill(db, skill_id)
    
    if not db_skill:
        return None
    
    # Update type if provided
    if skill.type is not None:
        db_skill.type = skill.type
    
    # Update categories if provided
    if skill.categories is not None:
        categories = db.query(Category).filter(Category.id.in_(skill.categories)).all()
        if len(categories) != len(skill.categories):
            missing_categories = set(skill.categories) - {cat.id for cat in categories}
            logger.error(f"Invalid category IDs: {missing_categories}")
            raise ValueError(f"Invalid category IDs: {missing_categories}")
        db_skill.categories = categories
    
    # Update skill texts if provided
    if skill.skill_texts is not None:
        # First, remove existing texts
        db.query(SkillText).filter(SkillText.skill_id == skill_id).delete()
        
        # Then add new texts
        for text_data in skill.skill_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Invalid language ID: {text_data.language_id}")
            
            db_skill_text = SkillText(
                skill_id=db_skill.id,
                language_id=text_data.language_id,
                name=text_data.name,
                description=text_data.description
            )
            db.add(db_skill_text)
    
    return db_skill

def delete_skill(db: Session, skill_id: int):
    logger.debug(f"Deleting skill with ID {skill_id}")
    db_skill = get_skill(db, skill_id)
    
    if not db_skill:
        return None
    
    # Delete associated texts
    db.query(SkillText).filter(SkillText.skill_id == skill_id).delete()
    
    # Delete the skill
    db.delete(db_skill)
    return db_skill

def get_skills(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching skills with skip={skip}, limit={limit}")
    return db.query(Skill).offset(skip).limit(limit).all()

def get_skills_by_type(db: Session, skill_type: str, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching skills of type {skill_type} with skip={skip}, limit={limit}")
    return db.query(Skill).filter(Skill.type == skill_type).offset(skip).limit(limit).all()

def get_skills_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc",
    type_filter: str = None,
    name_filter: str = None
) -> Tuple[List[Skill], int]:
    logger.debug(f"Getting paginated skills with filters: type={type_filter}, name={name_filter}")
    query = db.query(Skill)
    
    # Separate category and text filters from other filters
    category_filter_values = []
    text_filters = []
    other_filters = []
    
    if filters:
        for filter_item in filters:
            if filter_item.field == "category" or filter_item.field == "categories":
                logger.debug(f"Found category filter with value: {filter_item.value}")
                category_filter_values.append(filter_item.value)
            elif filter_item.field == "name" or filter_item.field == "description":
                text_filters.append(filter_item)
            elif hasattr(Skill, filter_item.field):
                column = getattr(Skill, filter_item.field)
                if filter_item.operator == "contains":
                    other_filters.append(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    other_filters.append(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    other_filters.append(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    other_filters.append(column.ilike(f"%{filter_item.value}"))
    
    # Apply direct type filter if provided
    if type_filter:
        logger.debug(f"Applying direct type filter: {type_filter}")
        other_filters.append(Skill.type.ilike(f"%{type_filter}%"))
    
    # Apply direct name filter if provided
    if name_filter:
        logger.debug(f"Applying direct name filter: {name_filter}")
        query = query.join(SkillText)
        query = query.filter(SkillText.name.ilike(f"%{name_filter}%"))
        query = query.distinct()
    
    if other_filters:
        query = query.filter(*other_filters)
    
    # Apply category filters
    if category_filter_values:
        logger.debug(f"Filtering by categories: {category_filter_values}")
        conditions = [Category.id == int(cat_id) for cat_id in category_filter_values]
        query = query.join(Skill.categories).filter(or_(*conditions)).distinct()
    
    # Apply text filters
    if text_filters:
        for filter_item in text_filters:
            # Join with SkillText to filter by name or description
            query = query.join(SkillText)
            column = getattr(SkillText, filter_item.field)
            if filter_item.operator == "contains":
                query = query.filter(column.ilike(f"%{filter_item.value}%"))
            elif filter_item.operator == "equals":
                query = query.filter(column == filter_item.value)
            elif filter_item.operator == "startsWith":
                query = query.filter(column.ilike(f"{filter_item.value}%"))
            elif filter_item.operator == "endsWith":
                query = query.filter(column.ilike(f"%{filter_item.value}"))
            query = query.distinct()
    
    # Get the total count before applying pagination
    total = query.count()
    logger.debug(f"Total matching skills: {total}")
    
    # Apply sorting if specified
    if sort_field:
        if hasattr(Skill, sort_field):
            sort_func = asc if sort_order == "asc" else desc
            query = query.order_by(sort_func(getattr(Skill, sort_field)))
        elif sort_field in ["name", "description"]:
            # Sort by name or description in the default language
            default_language = db.query(Language).filter(Language.is_default == True).first()
            if default_language:
                query = query.join(SkillText).filter(SkillText.language_id == default_language.id)
                sort_func = asc if sort_order == "asc" else desc
                query = query.order_by(sort_func(getattr(SkillText, sort_field)))
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

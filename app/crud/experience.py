from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.experience import Experience, ExperienceText
from app.models.language import Language
from app.schemas.experience import ExperienceCreate, ExperienceUpdate, ExperienceTextCreate, Filter
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
def get_experience(db: Session, experience_id: int):
    logger.debug(f"Fetching experience with ID {experience_id}")
    return db.query(Experience).filter(Experience.id == experience_id).first()

def create_experience(db: Session, experience: ExperienceCreate):
    logger.debug(f"Starting experience creation with {len(experience.experience_texts)} texts")
    
    # Create the experience
    db_experience = Experience(years=experience.years)
    db.add(db_experience)
    db.flush()  # Flush to get the experience ID
    
    # Create experience texts
    for text_data in experience.experience_texts:
        # Verify language exists
        language = db.query(Language).filter(Language.id == text_data.language_id).first()
        if not language:
            logger.error(f"Invalid language ID: {text_data.language_id}")
            raise ValueError(f"Invalid language ID: {text_data.language_id}")
        
        db_experience_text = ExperienceText(
            experience_id=db_experience.id,
            language_id=text_data.language_id,
            name=text_data.name,
            description=text_data.description
        )
        db.add(db_experience_text)
    
    logger.debug("Experience added to session")
    return db_experience

def update_experience(db: Session, experience_id: int, experience: ExperienceUpdate):
    logger.debug(f"Updating experience with ID {experience_id}")
    db_experience = get_experience(db, experience_id)
    
    if not db_experience:
        return None
    
    # Update years if provided
    if experience.years is not None:
        db_experience.years = experience.years
    
    # Update experience texts if provided
    if experience.experience_texts is not None:
        # First, remove existing texts
        db.query(ExperienceText).filter(ExperienceText.experience_id == experience_id).delete()
        
        # Then add new texts
        for text_data in experience.experience_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Invalid language ID: {text_data.language_id}")
            
            db_experience_text = ExperienceText(
                experience_id=db_experience.id,
                language_id=text_data.language_id,
                name=text_data.name,
                description=text_data.description
            )
            db.add(db_experience_text)
    
    return db_experience

def delete_experience(db: Session, experience_id: int):
    logger.debug(f"Deleting experience with ID {experience_id}")
    db_experience = get_experience(db, experience_id)
    
    if not db_experience:
        return None
    
    # Delete associated texts
    db.query(ExperienceText).filter(ExperienceText.experience_id == experience_id).delete()
    
    # Delete the experience
    db.delete(db_experience)
    return db_experience

def get_experiences(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching experiences with skip={skip}, limit={limit}")
    return db.query(Experience).offset(skip).limit(limit).all()

def get_experiences_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Experience], int]:
    query = db.query(Experience)
    
    # Handle text-based filtering through the ExperienceText table
    if filters:
        for filter_item in filters:
            if filter_item.field == "name" or filter_item.field == "description":
                # Join with ExperienceText to filter by name or description
                query = query.join(ExperienceText)
                column = getattr(ExperienceText, filter_item.field)
                if filter_item.operator == "contains":
                    query = query.filter(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    query = query.filter(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    query = query.filter(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    query = query.filter(column.ilike(f"%{filter_item.value}"))
                query = query.distinct()
            elif hasattr(Experience, filter_item.field):
                column = getattr(Experience, filter_item.field)
                if filter_item.operator == "contains":
                    query = query.filter(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    query = query.filter(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    query = query.filter(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    query = query.filter(column.ilike(f"%{filter_item.value}"))
    
    total = query.count()
    
    if sort_field:
        if hasattr(Experience, sort_field):
            sort_func = asc if sort_order == "asc" else desc
            query = query.order_by(sort_func(getattr(Experience, sort_field)))
        elif sort_field in ["name", "description"]:
            # Sort by name or description in the default language
            default_language = db.query(Language).filter(Language.is_default == True).first()
            if default_language:
                query = query.join(ExperienceText).filter(ExperienceText.language_id == default_language.id)
                sort_func = asc if sort_order == "asc" else desc
                query = query.order_by(sort_func(getattr(ExperienceText, sort_field)))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

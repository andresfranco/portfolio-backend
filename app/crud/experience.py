from sqlalchemy.orm import Session, joinedload
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
    return db.query(Experience).options(
        joinedload(Experience.experience_texts).joinedload(ExperienceText.language)
    ).filter(Experience.id == experience_id).first()

def get_experience_by_code(db: Session, code: str):
    logger.debug(f"Fetching experience by code: {code}")
    return db.query(Experience).options(
        joinedload(Experience.experience_texts).joinedload(ExperienceText.language)
    ).filter(Experience.code == code).first()

def create_experience(db: Session, experience: ExperienceCreate):
    logger.debug(f"Starting experience creation with code {experience.code} and {len(experience.experience_texts)} texts")
    
    # Create the experience
    db_experience = Experience(
        code=experience.code,
        years=experience.years,
        # Set default values for user tracking fields
        created_by=1,  # Default user ID
        updated_by=1   # Default user ID
    )
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
            description=text_data.description,
            # Set default values for user tracking fields
            created_by=1,  # Default user ID
            updated_by=1   # Default user ID
        )
        db.add(db_experience_text)
    
    logger.debug("Experience added to session")
    db.commit()
    db.refresh(db_experience)
    return db_experience

def update_experience(db: Session, experience_id: int, experience: ExperienceUpdate):
    logger.debug(f"Updating experience with ID {experience_id}")
    
    # Get the existing experience
    db_experience = get_experience(db, experience_id)
    if not db_experience:
        logger.error(f"Experience with ID {experience_id} not found")
        return None
    
    # Update experience fields
    if experience.code is not None:
        db_experience.code = experience.code
    if experience.years is not None:
        db_experience.years = experience.years
    
    # Update user tracking fields
    db_experience.updated_by = 1  # Default user ID
    
    # Handle removed languages if provided
    if experience.removed_language_ids:
        logger.debug(f"Removing languages with IDs: {experience.removed_language_ids}")
        for lang_id in experience.removed_language_ids:
            # Find and delete experience_texts for this language
            texts_to_delete = db.query(ExperienceText).filter(
                ExperienceText.experience_id == experience_id,
                ExperienceText.language_id == lang_id
            ).all()
            
            for text in texts_to_delete:
                logger.debug(f"Deleting experience_text with ID {text.id} for language {lang_id}")
                db.delete(text)
    
    # Update experience texts if provided
    if experience.experience_texts:
        # Get existing texts
        existing_texts = {text.language_id: text for text in db_experience.experience_texts}
        
        # Process each text in the update
        for text_data in experience.experience_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Invalid language ID: {text_data.language_id}")
            
            # If the text has an ID, try to find it directly
            if text_data.id:
                existing_text = db.query(ExperienceText).filter(ExperienceText.id == text_data.id).first()
                if existing_text:
                    # Update existing text
                    if text_data.name is not None:
                        existing_text.name = text_data.name
                    if text_data.description is not None:
                        existing_text.description = text_data.description
                    existing_text.updated_by = 1  # Default user ID
                    continue
            
            # Check if text for this language already exists
            if text_data.language_id in existing_texts:
                # Update existing text
                existing_text = existing_texts[text_data.language_id]
                if text_data.name is not None:
                    existing_text.name = text_data.name
                if text_data.description is not None:
                    existing_text.description = text_data.description
                existing_text.updated_by = 1  # Default user ID
            else:
                # Create new text
                db_experience_text = ExperienceText(
                    experience_id=db_experience.id,
                    language_id=text_data.language_id,
                    name=text_data.name or "",
                    description=text_data.description or "",
                    created_by=1,  # Default user ID
                    updated_by=1   # Default user ID
                )
                db.add(db_experience_text)
    
    db.commit()
    db.refresh(db_experience)
    return db_experience

def delete_experience(db: Session, experience_id: int):
    logger.debug(f"Deleting experience with ID {experience_id}")
    
    # Get the existing experience
    db_experience = get_experience(db, experience_id)
    if not db_experience:
        logger.error(f"Experience with ID {experience_id} not found")
        return None
    
    # Delete associated texts first
    for text in db_experience.experience_texts:
        db.delete(text)
    
    # Delete the experience
    db.delete(db_experience)
    db.commit()
    return db_experience

def get_experiences(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching experiences with skip={skip}, limit={limit}")
    return db.query(Experience).options(
        joinedload(Experience.experience_texts).joinedload(ExperienceText.language)
    ).offset(skip).limit(limit).all()

def check_code_exists(db: Session, code: str, exclude_id: Optional[int] = None):
    """Check if a code already exists, optionally excluding a specific experience ID."""
    query = db.query(Experience).filter(Experience.code == code)
    if exclude_id:
        query = query.filter(Experience.id != exclude_id)
    return query.first() is not None

def get_experiences_paginated(
    db: Session, 
    page: int = 1, 
    page_size: int = 10,
    filters: Optional[List[Filter]] = None,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    code_filter: Optional[str] = None,
    name_filter: Optional[str] = None,
    description_filter: Optional[str] = None,
    language_filter_values: Optional[List[str]] = None
) -> Tuple[List[Experience], int]:
    logger.debug(f"Fetching paginated experiences with page={page}, page_size={page_size}, filters={filters}, sort_field={sort_field}, sort_order={sort_order}")
    
    # Start with base query
    query = db.query(Experience).options(
        joinedload(Experience.experience_texts).joinedload(ExperienceText.language)
    )
    
    # Apply filters if provided
    if filters:
        for filter_item in filters:
            if filter_item.field == "code" and filter_item.value:
                query = query.filter(Experience.code.ilike(f"%{filter_item.value}%"))
            elif filter_item.field == "name" and filter_item.value:
                query = query.join(ExperienceText).filter(
                    ExperienceText.name.ilike(f"%{filter_item.value}%")
                )
            elif filter_item.field == "description" and filter_item.value:
                query = query.join(ExperienceText).filter(
                    ExperienceText.description.ilike(f"%{filter_item.value}%")
                )
            elif filter_item.field == "years" and filter_item.value:
                try:
                    years_value = int(filter_item.value)
                    query = query.filter(Experience.years == years_value)
                except ValueError:
                    logger.warning(f"Invalid years value for filtering: {filter_item.value}")
    
    # Apply direct filters if provided
    if code_filter:
        query = query.filter(Experience.code.ilike(f"%{code_filter}%"))
    
    if name_filter:
        query = query.join(ExperienceText).filter(
            ExperienceText.name.ilike(f"%{name_filter}%")
        )
    
    if description_filter:
        query = query.join(ExperienceText).filter(
            ExperienceText.description.ilike(f"%{description_filter}%")
        )
    
    if language_filter_values:
        language_ids = []
        for lang_id in language_filter_values:
            try:
                language_ids.append(int(lang_id))
            except ValueError:
                logger.warning(f"Invalid language ID for filtering: {lang_id}")
        
        if language_ids:
            query = query.join(ExperienceText).filter(
                ExperienceText.language_id.in_(language_ids)
            )
    
    # Apply sorting
    if sort_field:
        if sort_field == "code":
            order_func = asc if sort_order.lower() == "asc" else desc
            query = query.order_by(order_func(Experience.code))
        elif sort_field == "years":
            order_func = asc if sort_order.lower() == "asc" else desc
            query = query.order_by(order_func(Experience.years))
        elif sort_field == "name":
            order_func = asc if sort_order.lower() == "asc" else desc
            query = query.join(ExperienceText).order_by(order_func(ExperienceText.name))
        elif sort_field == "created_at":
            order_func = asc if sort_order.lower() == "asc" else desc
            query = query.order_by(order_func(Experience.created_at))
        elif sort_field == "updated_at":
            order_func = asc if sort_order.lower() == "asc" else desc
            query = query.order_by(order_func(Experience.updated_at))
    else:
        # Default sorting by ID
        query = query.order_by(asc(Experience.id))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    experiences = query.all()
    
    # Ensure all experiences have a code value
    for experience in experiences:
        if experience.code is None:
            # Set a default code value
            experience.code = f"EXP-{experience.id}"
            db.add(experience)
    
    # Commit any changes
    db.commit()
    
    return experiences, total

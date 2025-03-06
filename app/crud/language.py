from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.language import Language
from app.schemas.language import LanguageCreate, LanguageUpdate, Filter
from typing import List, Optional, Tuple
import logging
import sys
import os
from app.utils.file_utils import delete_file

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
def get_language(db: Session, language_id: int):
    logger.debug(f"Fetching language with ID {language_id}")
    return db.query(Language).filter(Language.id == language_id).first()

def get_language_by_code(db: Session, code: str):
    logger.debug(f"Fetching language by code: {code}")
    return db.query(Language).filter(Language.code == code).first()

def get_default_language(db: Session):
    logger.debug("Fetching default language")
    return db.query(Language).filter(Language.is_default == True).first()

def create_language(db: Session, language: LanguageCreate, image_path: str = None):
    logger.debug(f"Starting language creation for {language.code}")
    
    # If this language is set as default, unset any existing default language
    if language.is_default:
        current_default = get_default_language(db)
        if current_default:
            current_default.is_default = False
            db.flush()  # Flush to ensure the change is applied
    
    db_language = Language(
        code=language.code,
        name=language.name,
        image=image_path or "",  # Use the uploaded image path or empty string
        is_default=language.is_default
    )
    
    db.add(db_language)
    db.flush()  # Flush to get the ID assigned by the database
    db.refresh(db_language)  # Refresh to ensure we have all fields populated
    logger.debug(f"Language added to session with ID: {db_language.id}")
    return db_language

def update_language(db: Session, language_id: int, language: LanguageUpdate, image_path: str = None):
    logger.debug(f"Updating language with ID {language_id}")
    db_language = get_language(db, language_id)
    
    if not db_language:
        return None
    
    # Store old image path in case we need to delete it
    old_image_path = db_language.image if image_path else None
    
    # Update fields if provided
    if language.code is not None:
        db_language.code = language.code
    
    if language.name is not None:
        db_language.name = language.name
    
    # Update image if a new one is provided
    if image_path:
        db_language.image = image_path
    
    # Handle default language logic
    if language.is_default is not None and language.is_default and not db_language.is_default:
        # Unset any existing default language
        current_default = get_default_language(db)
        if current_default and current_default.id != language_id:
            current_default.is_default = False
        db_language.is_default = True
    elif language.is_default is not None:
        db_language.is_default = language.is_default
    
    db.flush()  # Flush to ensure changes are applied
    
    # Delete old image if it was replaced
    if old_image_path and old_image_path != db_language.image:
        try:
            delete_file(old_image_path)
            logger.debug(f"Deleted old image file: {old_image_path}")
        except Exception as e:
            logger.error(f"Error deleting old image file: {str(e)}")
    
    return db_language

def delete_language(db: Session, language_id: int):
    logger.debug(f"Deleting language with ID {language_id}")
    db_language = get_language(db, language_id)
    
    if not db_language:
        return None
    
    # Don't allow deleting the default language
    if db_language.is_default:
        raise ValueError("Cannot delete the default language")
    
    # Store image path to delete after removing from database
    image_path = db_language.image
    
    db.delete(db_language)
    db.flush()
    
    # Delete the image file if it exists
    if image_path:
        try:
            delete_file(image_path)
            logger.debug(f"Deleted image file during language deletion: {image_path}")
        except Exception as e:
            logger.error(f"Error deleting image file during language deletion: {str(e)}")
    
    return db_language

def get_languages(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching languages with skip={skip}, limit={limit}")
    return db.query(Language).offset(skip).limit(limit).all()

def get_languages_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Language], int]:
    query = db.query(Language)
    
    if filters:
        for filter_item in filters:
            if hasattr(Language, filter_item.field):
                column = getattr(Language, filter_item.field)
                if filter_item.operator == "contains":
                    query = query.filter(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    query = query.filter(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    query = query.filter(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    query = query.filter(column.ilike(f"%{filter_item.value}"))
    
    total = query.count()
    
    if sort_field and hasattr(Language, sort_field):
        sort_func = asc if sort_order == "asc" else desc
        query = query.order_by(sort_func(getattr(Language, sort_field)))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

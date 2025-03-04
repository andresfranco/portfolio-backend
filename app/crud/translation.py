from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.translation import Translation
from app.models.language import Language
from app.schemas.translation import TranslationCreate, TranslationUpdate, Filter
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
def get_translation(db: Session, translation_id: int):
    logger.debug(f"Fetching translation with ID {translation_id}")
    return db.query(Translation).filter(Translation.id == translation_id).first()

def get_translation_by_identifier(db: Session, identifier: str):
    logger.debug(f"Fetching translation by identifier: {identifier}")
    return db.query(Translation).filter(Translation.identifier == identifier).first()

def create_translation(db: Session, translation: TranslationCreate):
    logger.debug(f"Starting translation creation for {translation.identifier}")
    
    # Fetch the languages
    languages = db.query(Language).filter(Language.id.in_(translation.languages)).all()
    if len(languages) != len(translation.languages):
        missing_languages = set(translation.languages) - {lang.id for lang in languages}
        logger.error(f"Invalid language IDs: {missing_languages}")
        raise ValueError(f"Invalid language IDs: {missing_languages}")
    
    db_translation = Translation(
        identifier=translation.identifier,
        text=translation.text,
        language=languages
    )
    
    db.add(db_translation)
    logger.debug("Translation added to session")
    return db_translation

def update_translation(db: Session, translation_id: int, translation: TranslationUpdate):
    logger.debug(f"Updating translation with ID {translation_id}")
    db_translation = get_translation(db, translation_id)
    
    if not db_translation:
        return None
    
    # Update fields if provided
    if translation.identifier is not None:
        db_translation.identifier = translation.identifier
    
    if translation.text is not None:
        db_translation.text = translation.text
    
    # Update languages if provided
    if translation.languages is not None:
        languages = db.query(Language).filter(Language.id.in_(translation.languages)).all()
        if len(languages) != len(translation.languages):
            missing_languages = set(translation.languages) - {lang.id for lang in languages}
            logger.error(f"Invalid language IDs: {missing_languages}")
            raise ValueError(f"Invalid language IDs: {missing_languages}")
        db_translation.language = languages
    
    return db_translation

def delete_translation(db: Session, translation_id: int):
    logger.debug(f"Deleting translation with ID {translation_id}")
    db_translation = get_translation(db, translation_id)
    
    if not db_translation:
        return None
    
    db.delete(db_translation)
    return db_translation

def get_translations(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching translations with skip={skip}, limit={limit}")
    return db.query(Translation).offset(skip).limit(limit).all()

def get_translations_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Translation], int]:
    query = db.query(Translation)
    
    # Separate language filters from other filters
    language_filter_values = []
    other_filters = []
    
    if filters:
        for filter_item in filters:
            if filter_item.field == "language" or filter_item.field == "languages":
                logger.debug(f"Found language filter with value: {filter_item.value}")
                language_filter_values.append(filter_item.value)
            elif hasattr(Translation, filter_item.field):
                column = getattr(Translation, filter_item.field)
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
    
    if language_filter_values:
        logger.debug(f"Filtering by languages: {language_filter_values}")
        # Join with languages and apply OR logic: include translations that have any of the selected languages
        conditions = [Language.id == int(lang_id) for lang_id in language_filter_values]
        query = query.join(Translation.language).filter(or_(*conditions)).distinct()
    
    total = query.count()
    
    if sort_field and hasattr(Translation, sort_field):
        sort_func = asc if sort_order == "asc" else desc
        query = query.order_by(sort_func(getattr(Translation, sort_field)))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

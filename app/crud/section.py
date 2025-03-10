from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc, or_
from app.models.section import Section, SectionText
from app.models.language import Language
from app.schemas.section import SectionCreate, SectionUpdate, SectionTextCreate, Filter
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
def get_section(db: Session, section_id: int):
    logger.debug(f"Fetching section with ID {section_id}")
    return db.query(Section).options(
        joinedload(Section.section_texts).joinedload(SectionText.language)
    ).filter(Section.id == section_id).first()

def get_section_by_code(db: Session, code: str):
    logger.debug(f"Fetching section by code: {code}")
    return db.query(Section).options(
        joinedload(Section.section_texts).joinedload(SectionText.language)
    ).filter(Section.code == code).first()

def create_section(db: Session, section: SectionCreate):
    logger.debug(f"Starting section creation for {section.code}")
    
    # Create the section
    db_section = Section(
        code=section.code,
        # Set default values for user tracking fields
        created_by=1,  # Default user ID
        updated_by=1   # Default user ID
    )
    db.add(db_section)
    db.flush()  # Flush to get the section ID
    
    # Create section texts
    for text_data in section.section_texts:
        # Verify language exists
        language = db.query(Language).filter(Language.id == text_data.language_id).first()
        if not language:
            logger.error(f"Invalid language ID: {text_data.language_id}")
            raise ValueError(f"Language with ID {text_data.language_id} not found")
        
        section_text = SectionText(
            section_id=db_section.id,
            language_id=text_data.language_id,
            text=text_data.text
        )
        db.add(section_text)
    
    return db_section

def update_section(db: Session, section_id: int, section: SectionUpdate):
    logger.debug(f"Starting section update for ID {section_id}")
    
    # Get the section
    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        logger.error(f"Section with ID {section_id} not found")
        return None
    
    # Update section fields
    if section.code is not None:
        db_section.code = section.code
    
    # Update user tracking
    db_section.updated_by = 1  # Default user ID
    
    # Update section texts
    if section.section_texts is not None:  # Check if section_texts is provided (even if empty)
        # Get existing texts
        existing_texts = db.query(SectionText).filter(SectionText.section_id == section_id).all()
        existing_texts_by_lang = {text.language_id: text for text in existing_texts}
        
        # Track which languages are in the update
        updated_language_ids = set()
        
        for text_data in section.section_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Language with ID {text_data.language_id} not found")
            
            # Add to set of updated languages
            updated_language_ids.add(text_data.language_id)
            
            # Update existing or create new
            if text_data.language_id in existing_texts_by_lang:
                logger.debug(f"Updating text for language ID {text_data.language_id}")
                existing_texts_by_lang[text_data.language_id].text = text_data.text
            else:
                logger.debug(f"Creating new text for language ID {text_data.language_id}")
                new_text = SectionText(
                    section_id=section_id,
                    language_id=text_data.language_id,
                    text=text_data.text
                )
                db.add(new_text)
        
        # Remove texts for languages that are not in the update
        for lang_id, text in existing_texts_by_lang.items():
            if lang_id not in updated_language_ids:
                logger.debug(f"Removing text for language ID {lang_id}")
                db.delete(text)
    
    return db_section

def delete_section(db: Session, section_id: int):
    logger.debug(f"Deleting section with ID {section_id}")
    
    # Get the section
    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        logger.error(f"Section with ID {section_id} not found")
        return None
    
    # Delete associated section texts
    db.query(SectionText).filter(SectionText.section_id == section_id).delete()
    
    # Delete the section
    db.delete(db_section)
    
    return db_section

def get_sections(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Getting sections with skip={skip}, limit={limit}")
    return db.query(Section).offset(skip).limit(limit).all()

def get_sections_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc",
    code_filter: str = None,
    text_filter: str = None,
    language_filter_values: List[str] = None
) -> Tuple[List[Section], int]:
    logger.debug(f"Getting paginated sections with page={page}, page_size={page_size}")
    
    query = db.query(Section).options(
        joinedload(Section.section_texts).joinedload(SectionText.language)
    )
    
    # Apply direct filters
    if code_filter:
        logger.debug(f"Applying code filter: {code_filter}")
        query = query.filter(Section.code.ilike(f"%{code_filter}%"))
    
    # Apply text filter to search in section texts
    if text_filter:
        logger.debug(f"Applying text filter: {text_filter}")
        query = query.join(Section.section_texts, isouter=True).filter(SectionText.text.ilike(f"%{text_filter}%")).distinct()
    
    if language_filter_values:
        logger.debug(f"Applying language filters: {language_filter_values}")
        # Convert string IDs to integers and validate
        language_ids = []
        for lang_id in language_filter_values:
            try:
                language_ids.append(int(lang_id))
            except (ValueError, TypeError):
                logger.warning(f"Invalid language ID: {lang_id}")
                continue
        
        if language_ids:
            # Join with the section_texts and filter by language_id
            # Use distinct to avoid duplicate results when joining
            query = query.join(Section.section_texts).filter(SectionText.language_id.in_(language_ids)).distinct()
    
    # Apply generic filters
    if filters:
        for filter_item in filters:
            if hasattr(Section, filter_item.field):
                column = getattr(Section, filter_item.field)
                if filter_item.operator == "contains":
                    query = query.filter(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    query = query.filter(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    query = query.filter(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    query = query.filter(column.ilike(f"%{filter_item.value}"))
    
    # Get total count before pagination
    # Use a separate count query to avoid issues with distinct and joins
    count_query = db.query(Section.id)
    
    # Apply the same filters to the count query
    if code_filter:
        count_query = count_query.filter(Section.code.ilike(f"%{code_filter}%"))
    
    if text_filter:
        count_query = count_query.join(Section.section_texts, isouter=True).filter(SectionText.text.ilike(f"%{text_filter}%")).distinct()
    
    if language_filter_values and language_ids:
        count_query = count_query.join(Section.section_texts, isouter=True).filter(SectionText.language_id.in_(language_ids)).distinct()
    
    # Apply generic filters to count query
    if filters:
        for filter_item in filters:
            if hasattr(Section, filter_item.field):
                column = getattr(Section, filter_item.field)
                if filter_item.operator == "contains":
                    count_query = count_query.filter(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    count_query = count_query.filter(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    count_query = count_query.filter(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    count_query = count_query.filter(column.ilike(f"%{filter_item.value}"))
    
    total = count_query.distinct().count()
    logger.debug(f"Total sections found: {total}")
    
    # Apply sorting
    if sort_field:
        logger.debug(f"Sorting by {sort_field} {sort_order}")
        if sort_field == 'language':
            # Sort by the language name
            query = query.join(Section.section_texts, isouter=True).join(SectionText.language, isouter=True).order_by(
                desc(Language.name) if sort_order == 'desc' else asc(Language.name)
            ).distinct()
        else:
            sort_column = getattr(Section, sort_field, None)
            if sort_column is not None:
                query = query.order_by(desc(sort_column) if sort_order == 'desc' else asc(sort_column))
    else:
        # Default sorting by id
        query = query.order_by(Section.id)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    sections = query.all()
    logger.debug(f"Returning {len(sections)} sections for page {page}")
    
    return sections, total

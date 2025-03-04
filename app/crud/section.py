from sqlalchemy.orm import Session
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
    return db.query(Section).filter(Section.id == section_id).first()

def get_section_by_code(db: Session, code: str):
    logger.debug(f"Fetching section by code: {code}")
    return db.query(Section).filter(Section.code == code).first()

def create_section(db: Session, section: SectionCreate):
    logger.debug(f"Starting section creation for {section.code}")
    
    # Create the section
    db_section = Section(code=section.code)
    db.add(db_section)
    db.flush()  # Flush to get the section ID
    
    # Create section texts
    for text_data in section.section_texts:
        # Verify language exists
        language = db.query(Language).filter(Language.id == text_data.language_id).first()
        if not language:
            logger.error(f"Invalid language ID: {text_data.language_id}")
            raise ValueError(f"Invalid language ID: {text_data.language_id}")
        
        db_section_text = SectionText(
            section_id=db_section.id,
            language_id=text_data.language_id,
            text=text_data.text
        )
        db.add(db_section_text)
    
    logger.debug("Section added to session")
    return db_section

def update_section(db: Session, section_id: int, section: SectionUpdate):
    logger.debug(f"Updating section with ID {section_id}")
    db_section = get_section(db, section_id)
    
    if not db_section:
        return None
    
    # Update code if provided
    if section.code is not None:
        db_section.code = section.code
    
    # Update section texts if provided
    if section.section_texts is not None:
        # First, remove existing texts
        db.query(SectionText).filter(SectionText.section_id == section_id).delete()
        
        # Then add new texts
        for text_data in section.section_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Invalid language ID: {text_data.language_id}")
            
            db_section_text = SectionText(
                section_id=db_section.id,
                language_id=text_data.language_id,
                text=text_data.text
            )
            db.add(db_section_text)
    
    return db_section

def delete_section(db: Session, section_id: int):
    logger.debug(f"Deleting section with ID {section_id}")
    db_section = get_section(db, section_id)
    
    if not db_section:
        return None
    
    # Delete associated texts
    db.query(SectionText).filter(SectionText.section_id == section_id).delete()
    
    # Delete the section
    db.delete(db_section)
    return db_section

def get_sections(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching sections with skip={skip}, limit={limit}")
    return db.query(Section).offset(skip).limit(limit).all()

def get_sections_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Section], int]:
    query = db.query(Section)
    
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
    
    total = query.count()
    
    if sort_field and hasattr(Section, sort_field):
        sort_func = asc if sort_order == "asc" else desc
        query = query.order_by(sort_func(getattr(Section, sort_field)))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

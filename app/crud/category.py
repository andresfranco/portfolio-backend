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
        type_code=category.type_code
    )
    db.add(db_category)
    db.flush()  # Flush to get the category ID
    
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
    
    # Commit the transaction to ensure data is saved to the database
    db.commit()
    logger.debug(f"Category created successfully with ID: {db_category.id}")
    
    # Refresh the category object to ensure all relationships are loaded
    db.refresh(db_category)
    
    return db_category

def update_category(db: Session, category_id: int, category: CategoryUpdate):
    logger.debug(f"Updating category with ID {category_id}")
    db_category = get_category(db, category_id)
    
    if not db_category:
        return None
    
    # Update fields if provided
    if category.code is not None:
        db_category.code = category.code
    if category.type_code is not None:
        db_category.type_code = category.type_code
    
    # Update category texts if provided
    if category.category_texts is not None:
        # First, get existing texts to determine which ones to remove
        existing_texts = db.query(CategoryText).filter(CategoryText.category_id == category_id).all()
        existing_lang_ids = {text.language_id for text in existing_texts}
        
        # Process removed language IDs
        if category.removed_language_ids:
            for lang_id in category.removed_language_ids:
                db.query(CategoryText).filter(
                    CategoryText.category_id == category_id,
                    CategoryText.language_id == lang_id
                ).delete()
        
        # Process new or updated texts
        for text_data in category.category_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Invalid language ID: {text_data.language_id}")
            
            # Check if text for this language already exists
            existing_text = db.query(CategoryText).filter(
                CategoryText.category_id == category_id,
                CategoryText.language_id == text_data.language_id
            ).first()
            
            if existing_text:
                # Update existing text
                if text_data.name is not None:
                    existing_text.name = text_data.name
                if text_data.description is not None:
                    existing_text.description = text_data.description
            else:
                # Create new text
                new_text = CategoryText(
                    category_id=category_id,
                    language_id=text_data.language_id,
                    name=text_data.name,
                    description=text_data.description
                )
                db.add(new_text)
    
    db.commit()
    db.refresh(db_category)
    logger.debug(f"Category updated successfully: {category_id}")
    
    return db_category

def delete_category(db: Session, category_id: int):
    logger.debug(f"Deleting category with ID {category_id}")
    db_category = get_category(db, category_id)
    
    if not db_category:
        return None
    
    # Delete the category (cascade will handle texts)
    db.delete(db_category)
    db.commit()
    
    logger.debug(f"Category deleted successfully: {category_id}")
    return db_category

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Category).offset(skip).limit(limit).all()

def get_categories_by_type(db: Session, category_type: str, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching categories with type {category_type}")
    return db.query(Category).filter(Category.type_code == category_type).offset(skip).limit(limit).all()

def get_categories_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Category], int]:
    """
    Get paginated list of categories with optional filtering and sorting.
    
    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        filters: List of filter conditions
        sort_field: Field to sort by
        sort_order: Sort direction ("asc" or "desc")
        
    Returns:
        Tuple of (list of categories, total count)
    """
    logger.debug(f"Getting paginated categories with page={page}, page_size={page_size}, filters={filters}, sort_field={sort_field}, sort_order={sort_order}")
    
    # Start with base query
    query = db.query(Category)
    
    # Apply filters if provided
    if filters:
        for filter_item in filters:
            if filter_item.field == "code":
                if filter_item.operator == "contains":
                    query = query.filter(Category.code.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    query = query.filter(Category.code == filter_item.value)
                elif filter_item.operator == "startsWith":
                    query = query.filter(Category.code.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    query = query.filter(Category.code.ilike(f"%{filter_item.value}"))
            elif filter_item.field == "type":
                if filter_item.operator == "contains":
                    query = query.filter(Category.type_code.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    query = query.filter(Category.type_code == filter_item.value)
                elif filter_item.operator == "startsWith":
                    query = query.filter(Category.type_code.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    query = query.filter(Category.type_code.ilike(f"%{filter_item.value}"))
            elif filter_item.field == "name" or filter_item.field == "description":
                # These fields are in the texts table, so we need to join
                query = query.join(CategoryText)
                
                if filter_item.operator == "contains":
                    if filter_item.field == "name":
                        query = query.filter(CategoryText.name.ilike(f"%{filter_item.value}%"))
                    else:  # description
                        query = query.filter(CategoryText.description.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    if filter_item.field == "name":
                        query = query.filter(CategoryText.name == filter_item.value)
                    else:  # description
                        query = query.filter(CategoryText.description == filter_item.value)
            elif filter_item.field == "language_id":
                # Filter by language ID
                query = query.join(CategoryText)
                query = query.filter(CategoryText.language_id == filter_item.value)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting if provided
    if sort_field:
        if sort_field == "code":
            sort_column = Category.code
        elif sort_field == "type":
            sort_column = Category.type_code
        elif sort_field == "name":
            # Join with texts table if not already joined
            if not any(isinstance(join, tuple) and join[0] == CategoryText for join in query._joins):
                query = query.join(CategoryText)
            sort_column = CategoryText.name
        elif sort_field == "description":
            # Join with texts table if not already joined
            if not any(isinstance(join, tuple) and join[0] == CategoryText for join in query._joins):
                query = query.join(CategoryText)
            sort_column = CategoryText.description
        else:
            # Default to id if sort field is not recognized
            sort_column = Category.id
        
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    else:
        # Default sort by id
        query = query.order_by(asc(Category.id))
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    categories = query.all()
    
    logger.debug(f"Retrieved {len(categories)} categories out of {total} total")
    return categories, total

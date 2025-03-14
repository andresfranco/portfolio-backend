from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from app.models.category_type import CategoryType
from app.schemas.category_type import CategoryTypeCreate, CategoryTypeUpdate, Filter
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
def get_category_type(db: Session, code: str):
    logger.debug(f"Fetching category type with code {code}")
    return db.query(CategoryType).filter(CategoryType.code == code).first()

def get_category_type_by_code(db: Session, code: str):
    logger.debug(f"Fetching category type by code: {code}")
    return db.query(CategoryType).filter(CategoryType.code == code).first()

def create_category_type(db: Session, category_type: CategoryTypeCreate):
    logger.debug(f"Starting category type creation for {category_type.code}")
    
    # Create the category type
    db_category_type = CategoryType(
        code=category_type.code,
        name=category_type.name
    )
    db.add(db_category_type)
    
    # Commit the transaction to ensure data is saved to the database
    db.commit()
    logger.debug(f"Category type created successfully with code: {db_category_type.code}")
    
    # Refresh the category type object
    db.refresh(db_category_type)
    
    return db_category_type

def update_category_type(db: Session, code: str, category_type: CategoryTypeUpdate):
    logger.debug(f"Updating category type with code {code}")
    db_category_type = get_category_type(db, code)
    
    if not db_category_type:
        return None
    
    # Update fields if provided
    if category_type.code is not None and category_type.code != code:
        # This would require changing the primary key, which is complex
        # For simplicity, we'll disallow this operation
        logger.error(f"Cannot change category type code from {code} to {category_type.code}")
        raise ValueError("Cannot change category type code as it is the primary key")
    
    # Update name if provided
    if category_type.name is not None:
        db_category_type.name = category_type.name
    
    db.commit()
    db.refresh(db_category_type)
    logger.debug(f"Category type updated successfully: {code}")
    
    return db_category_type

def delete_category_type(db: Session, code: str):
    logger.debug(f"Deleting category type with code {code}")
    db_category_type = get_category_type(db, code)
    
    if not db_category_type:
        return None
    
    # Delete the category type
    db.delete(db_category_type)
    db.commit()
    
    logger.debug(f"Category type deleted successfully: {code}")
    return db_category_type

def get_category_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CategoryType).offset(skip).limit(limit).all()

def get_category_types_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: Optional[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[CategoryType], int]:
    """
    Get paginated list of category types with optional filtering and sorting.
    
    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        filters: Filter conditions
        sort_field: Field to sort by
        sort_order: Sort direction ("asc" or "desc")
        
    Returns:
        Tuple of (list of category types, total count)
    """
    logger.debug(f"Getting paginated category types with page={page}, page_size={page_size}, filters={filters}, sort_field={sort_field}, sort_order={sort_order}")
    
    # Start with base query
    query = db.query(CategoryType)
    
    # Apply filters if provided
    if filters:
        if filters.code:
            query = query.filter(CategoryType.code.ilike(f"%{filters.code}%"))
        if filters.name:
            query = query.filter(CategoryType.name.ilike(f"%{filters.name}%"))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting if provided
    if sort_field:
        if sort_field == "code":
            sort_column = CategoryType.code
        elif sort_field == "name":
            sort_column = CategoryType.name
        else:
            # Default to code if sort field is not recognized
            sort_column = CategoryType.code
        
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    else:
        # Default sort by code
        query = query.order_by(asc(CategoryType.code))
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    category_types = query.all()
    
    logger.debug(f"Retrieved {len(category_types)} category types out of {total} total")
    return category_types, total

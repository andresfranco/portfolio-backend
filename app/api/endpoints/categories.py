from fastapi import APIRouter, Depends, HTTPException, Query, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app import models, schemas
from app.api import deps
from app.crud import category as category_crud
import logging
import sys

router = APIRouter()

# Set up logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

@router.get("/", response_model=schemas.PaginatedResponse[schemas.category.Category])
def read_categories(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.category.Filter]] = None,
) -> Any:
    """
    Retrieve categories with pagination.
    """
    
    categories, total = category_crud.get_categories_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": categories,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/full", response_model=schemas.category.PaginatedCategoryResponse)
def read_categories_full(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get paginated list of categories with full details.
    """
    logger.debug(f"Fetching categories with page={page}, pageSize={pageSize}, filters={filterField}, values={filterValue}, operators={filterOperator}, sort={sortField} {sortOrder}")
    
    parsed_filters = []
    if filterField and filterValue:
        # Zip the filter parameters together, using 'contains' as default operator if not provided
        operators = filterOperator if filterOperator else ['contains'] * len(filterField)
        for field, value, operator in zip(filterField, filterValue, operators):
            try:
                parsed_filters.append(schemas.category.Filter.from_params(field=field, value=value, operator=operator))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    categories, total = category_crud.get_categories_paginated(
        db,
        page=page,
        page_size=pageSize,
        filters=parsed_filters or None,
        sort_field=sortField,
        sort_order=sortOrder
    )
    
    # Ensure all categories have a valid type_code
    for category in categories:
        if category.type_code is None:
            category.type_code = "GEN"
    
    response = {
        "items": categories,
        "total": total,
        "page": page,
        "pageSize": pageSize
    }
    
    logger.debug(f"Categories fetched: {total} items")
    return response

@router.get("/by-type/{category_type}", response_model=List[schemas.category.Category])
def read_categories_by_type(
    *,
    db: Session = Depends(deps.get_db),
    category_type: str,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve categories by type.
    """
    
    categories = category_crud.get_categories_by_type(
        db, category_type=category_type, skip=skip, limit=limit
    )
    
    return categories

@router.post("/", response_model=schemas.category.Category)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    category_in: schemas.category.CategoryCreate,
) -> Any:
    """
    Create new category.
    """
    logger.debug(f"Creating category with data: {category_in}")
    
    # Check if category with this code already exists
    category = category_crud.get_category_by_code(db, code=category_in.code)
    if category:
        raise HTTPException(
            status_code=400,
            detail="The category with this code already exists in the system.",
        )
    
    try:
        category = category_crud.create_category(db, category=category_in)
        logger.debug(f"Category created successfully with ID: {category.id}")
        return category
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating category: {str(e)}",
        )

@router.get("/check-code/{code}", response_model=dict)
def check_code_exists(
    *,
    db: Session = Depends(deps.get_db),
    code: str,
    category_id: Optional[int] = None,
) -> Any:
    """
    Check if a category code already exists.
    """
    category = category_crud.get_category_by_code(db, code=code)
    
    # If we're checking for an update, exclude the current category
    if category and category_id and category.id == category_id:
        return {"exists": False}
    
    return {"exists": bool(category)}

@router.get("/{category_id}", response_model=schemas.category.Category)
def read_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: int,
) -> Any:
    """
    Get category by ID.
    """
    
    category = category_crud.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )
    return category

@router.put("/{category_id}", response_model=schemas.category.Category)
def update_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: int,
    category_in: schemas.category.CategoryUpdate,
) -> Any:
    """
    Update a category.
    """
    logger.debug(f"Updating category {category_id} with data: {category_in}")
    
    category = category_crud.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )
    
    # If updating code, check it doesn't conflict with existing categories
    if category_in.code and category_in.code != category.code:
        existing_category = category_crud.get_category_by_code(db, code=category_in.code)
        if existing_category and existing_category.id != category_id:
            raise HTTPException(
                status_code=400,
                detail="The category with this code already exists in the system.",
            )
    
    try:
        category = category_crud.update_category(db, category_id=category_id, category=category_in)
        logger.debug(f"Category updated successfully: {category.id}")
        return category
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating category: {str(e)}",
        )

@router.delete("/{category_id}", response_model=schemas.category.Category)
def delete_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: int,
) -> Any:
    """
    Delete a category.
    """
    
    category = category_crud.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )
    
    try:
        category = category_crud.delete_category(db, category_id=category_id)
        logger.debug(f"Category deleted successfully: {category_id}")
        return category
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting category: {str(e)}",
        )

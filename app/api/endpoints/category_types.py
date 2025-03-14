from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app import models, schemas
from app.api import deps
from app.crud import category_type as category_type_crud
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

@router.get("/full", response_model=schemas.category_type.PaginatedCategoryTypeResponse)
def read_category_types_full(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    code: Optional[str] = None,
    name: Optional[str] = None,
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get paginated list of category types with full details.
    """
    logger.debug(f"Fetching category types with page={page}, pageSize={pageSize}, filters={filterField}, values={filterValue}, operators={filterOperator}, code={code}, name={name}, sort={sortField} {sortOrder}")
    
    filters = None
    
    # Handle both direct parameters and filter parameters
    if filterField and filterValue:
        # Create a Filter object from the filter parameters
        filters = schemas.category_type.Filter()
        
        # Zip the filter parameters together, using 'contains' as default operator if not provided
        operators = filterOperator if filterOperator else ['contains'] * len(filterField)
        for field, value, operator in zip(filterField, filterValue, operators):
            if field == 'code':
                filters.code = value
            elif field == 'name':
                filters.name = value
    # Fall back to direct parameters if no filter parameters are provided
    elif code or name:
        filters = schemas.category_type.Filter(code=code, name=name)
    
    category_types, total = category_type_crud.get_category_types_paginated(
        db,
        page=page,
        page_size=pageSize,
        filters=filters,
        sort_field=sortField,
        sort_order=sortOrder
    )
    
    response = {
        "items": category_types,
        "total": total,
        "page": page,
        "pageSize": pageSize
    }
    
    logger.debug(f"Category types fetched: {total} items")
    return response

@router.post("/", response_model=schemas.category_type.CategoryType)
def create_category_type(
    *,
    db: Session = Depends(deps.get_db),
    category_type_in: schemas.category_type.CategoryTypeCreate,
) -> Any:
    """
    Create new category type.
    """
    logger.debug(f"Creating category type with data: {category_type_in}")
    
    # Check if category type with this code already exists
    category_type = category_type_crud.get_category_type_by_code(db, code=category_type_in.code)
    if category_type:
        raise HTTPException(
            status_code=400,
            detail="The category type with this code already exists in the system.",
        )
    
    try:
        category_type = category_type_crud.create_category_type(db, category_type=category_type_in)
        logger.debug(f"Category type created successfully with code: {category_type.code}")
        return category_type
    except Exception as e:
        logger.error(f"Error creating category type: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating category type: {str(e)}",
        )

@router.get("/check-code/{code}", response_model=dict)
def check_code_exists(
    *,
    db: Session = Depends(deps.get_db),
    code: str,
) -> Any:
    """
    Check if a category type code already exists.
    """
    category_type = category_type_crud.get_category_type_by_code(db, code=code)
    return {"exists": bool(category_type)}

@router.get("/{code}", response_model=schemas.category_type.CategoryType)
def read_category_type(
    *,
    db: Session = Depends(deps.get_db),
    code: str,
) -> Any:
    """
    Get category type by code.
    """
    
    category_type = category_type_crud.get_category_type(db, code=code)
    if not category_type:
        raise HTTPException(
            status_code=404,
            detail="Category type not found",
        )
    return category_type

@router.put("/{code}", response_model=schemas.category_type.CategoryType)
def update_category_type(
    *,
    db: Session = Depends(deps.get_db),
    code: str,
    category_type_in: schemas.category_type.CategoryTypeUpdate,
) -> Any:
    """
    Update a category type.
    """
    logger.debug(f"Updating category type {code} with data: {category_type_in}")
    
    category_type = category_type_crud.get_category_type(db, code=code)
    if not category_type:
        raise HTTPException(
            status_code=404,
            detail="Category type not found",
        )
    
    try:
        category_type = category_type_crud.update_category_type(db, code=code, category_type=category_type_in)
        logger.debug(f"Category type updated successfully: {code}")
        return category_type
    except ValueError as e:
        logger.error(f"Error updating category type: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating category type: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating category type: {str(e)}",
        )

@router.delete("/{code}", response_model=schemas.category_type.CategoryType)
def delete_category_type(
    *,
    db: Session = Depends(deps.get_db),
    code: str,
) -> Any:
    """
    Delete a category type.
    """
    logger.debug(f"Deleting category type with code {code}")
    
    category_type = category_type_crud.get_category_type(db, code=code)
    if not category_type:
        raise HTTPException(
            status_code=404,
            detail="Category type not found",
        )
    
    try:
        category_type = category_type_crud.delete_category_type(db, code=code)
        logger.debug(f"Category type deleted successfully: {code}")
        return category_type
    except Exception as e:
        logger.error(f"Error deleting category type: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting category type: {str(e)}",
        )

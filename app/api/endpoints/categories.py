from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import crud, models, schemas
from app.api import deps
from app.utils import check_admin_access

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Category])
def read_categories(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.category.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve categories with pagination.
    """
    check_admin_access(current_user)
    
    categories, total = crud.category.get_categories_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": categories,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/by-type/{category_type}", response_model=List[schemas.Category])
def read_categories_by_type(
    *,
    db: Session = Depends(deps.get_db),
    category_type: str,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve categories by type.
    """
    check_admin_access(current_user)
    
    categories = crud.category.get_categories_by_type(
        db, category_type=category_type, skip=skip, limit=limit
    )
    
    return categories


@router.post("/", response_model=schemas.Category)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    category_in: schemas.CategoryCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new category.
    """
    check_admin_access(current_user)
    
    # Check if category with this code already exists
    category = crud.category.get_category_by_code(db, code=category_in.code)
    if category:
        raise HTTPException(
            status_code=400,
            detail="The category with this code already exists in the system.",
        )
    
    category = crud.category.create_category(db, category=category_in)
    return category


@router.get("/{category_id}", response_model=schemas.Category)
def read_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get category by ID.
    """
    check_admin_access(current_user)
    
    category = crud.category.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )
    return category


@router.put("/{category_id}", response_model=schemas.Category)
def update_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: int,
    category_in: schemas.CategoryUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a category.
    """
    check_admin_access(current_user)
    
    category = crud.category.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )
    
    # If updating code, check it doesn't conflict with existing categories
    if category_in.code and category_in.code != category.code:
        existing_category = crud.category.get_category_by_code(db, code=category_in.code)
        if existing_category:
            raise HTTPException(
                status_code=400,
                detail="The category with this code already exists in the system.",
            )
    
    category = crud.category.update_category(db, category_id=category_id, category=category_in)
    return category


@router.delete("/{category_id}", response_model=schemas.Category)
def delete_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a category.
    """
    check_admin_access(current_user)
    
    category = crud.category.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )
    
    category = crud.category.delete_category(db, category_id=category_id)
    return category

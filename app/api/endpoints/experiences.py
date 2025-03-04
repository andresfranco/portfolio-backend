from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import crud, models, schemas
from app.api import deps
from app.utils import check_admin_access

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Experience])
def read_experiences(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.experience.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve experiences with pagination.
    """
    check_admin_access(current_user)
    
    experiences, total = crud.experience.get_experiences_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": experiences,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=schemas.Experience)
def create_experience(
    *,
    db: Session = Depends(deps.get_db),
    experience_in: schemas.ExperienceCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new experience.
    """
    check_admin_access(current_user)
    
    experience = crud.experience.create_experience(db, experience=experience_in)
    return experience


@router.get("/{experience_id}", response_model=schemas.Experience)
def read_experience(
    *,
    db: Session = Depends(deps.get_db),
    experience_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get experience by ID.
    """
    check_admin_access(current_user)
    
    experience = crud.experience.get_experience(db, experience_id=experience_id)
    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )
    return experience


@router.put("/{experience_id}", response_model=schemas.Experience)
def update_experience(
    *,
    db: Session = Depends(deps.get_db),
    experience_id: int,
    experience_in: schemas.ExperienceUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an experience.
    """
    check_admin_access(current_user)
    
    experience = crud.experience.get_experience(db, experience_id=experience_id)
    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )
    
    experience = crud.experience.update_experience(db, experience_id=experience_id, experience=experience_in)
    return experience


@router.delete("/{experience_id}", response_model=schemas.Experience)
def delete_experience(
    *,
    db: Session = Depends(deps.get_db),
    experience_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an experience.
    """
    check_admin_access(current_user)
    
    experience = crud.experience.get_experience(db, experience_id=experience_id)
    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )
    
    experience = crud.experience.delete_experience(db, experience_id=experience_id)
    return experience

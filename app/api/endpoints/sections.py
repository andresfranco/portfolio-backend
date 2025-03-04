from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import crud, models, schemas
from app.api import deps
from app.utils import check_admin_access

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Section])
def read_sections(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.section.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve sections with pagination.
    """
    check_admin_access(current_user)
    
    sections, total = crud.section.get_sections_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": sections,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=schemas.Section)
def create_section(
    *,
    db: Session = Depends(deps.get_db),
    section_in: schemas.SectionCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new section.
    """
    check_admin_access(current_user)
    
    # Check if section with this code already exists
    section = crud.section.get_section_by_code(db, code=section_in.code)
    if section:
        raise HTTPException(
            status_code=400,
            detail="The section with this code already exists in the system.",
        )
    
    section = crud.section.create_section(db, section=section_in)
    return section


@router.get("/{section_id}", response_model=schemas.Section)
def read_section(
    *,
    db: Session = Depends(deps.get_db),
    section_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get section by ID.
    """
    check_admin_access(current_user)
    
    section = crud.section.get_section(db, section_id=section_id)
    if not section:
        raise HTTPException(
            status_code=404,
            detail="Section not found",
        )
    return section


@router.put("/{section_id}", response_model=schemas.Section)
def update_section(
    *,
    db: Session = Depends(deps.get_db),
    section_id: int,
    section_in: schemas.SectionUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a section.
    """
    check_admin_access(current_user)
    
    section = crud.section.get_section(db, section_id=section_id)
    if not section:
        raise HTTPException(
            status_code=404,
            detail="Section not found",
        )
    
    # If updating code, check it doesn't conflict with existing sections
    if section_in.code and section_in.code != section.code:
        existing_section = crud.section.get_section_by_code(db, code=section_in.code)
        if existing_section:
            raise HTTPException(
                status_code=400,
                detail="The section with this code already exists in the system.",
            )
    
    section = crud.section.update_section(db, section_id=section_id, section=section_in)
    return section


@router.delete("/{section_id}", response_model=schemas.Section)
def delete_section(
    *,
    db: Session = Depends(deps.get_db),
    section_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a section.
    """
    check_admin_access(current_user)
    
    section = crud.section.get_section(db, section_id=section_id)
    if not section:
        raise HTTPException(
            status_code=404,
            detail="Section not found",
        )
    
    section = crud.section.delete_section(db, section_id=section_id)
    return section

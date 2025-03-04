from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import crud, models, schemas
from app.api import deps
from app.utils import check_admin_access

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Translation])
def read_translations(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.translation.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve translations with pagination.
    """
    check_admin_access(current_user)
    
    translations, total = crud.translation.get_translations_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": translations,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=schemas.Translation)
def create_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_in: schemas.TranslationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new translation.
    """
    check_admin_access(current_user)
    
    # Check if translation with this identifier already exists
    translation = crud.translation.get_translation_by_identifier(db, identifier=translation_in.identifier)
    if translation:
        raise HTTPException(
            status_code=400,
            detail="The translation with this identifier already exists in the system.",
        )
    
    translation = crud.translation.create_translation(db, translation=translation_in)
    return translation


@router.get("/{translation_id}", response_model=schemas.Translation)
def read_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get translation by ID.
    """
    check_admin_access(current_user)
    
    translation = crud.translation.get_translation(db, translation_id=translation_id)
    if not translation:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )
    return translation


@router.put("/{translation_id}", response_model=schemas.Translation)
def update_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_id: int,
    translation_in: schemas.TranslationUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a translation.
    """
    check_admin_access(current_user)
    
    translation = crud.translation.get_translation(db, translation_id=translation_id)
    if not translation:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )
    
    # If updating identifier, check it doesn't conflict with existing translations
    if translation_in.identifier and translation_in.identifier != translation.identifier:
        existing_translation = crud.translation.get_translation_by_identifier(db, identifier=translation_in.identifier)
        if existing_translation:
            raise HTTPException(
                status_code=400,
                detail="The translation with this identifier already exists in the system.",
            )
    
    translation = crud.translation.update_translation(db, translation_id=translation_id, translation=translation_in)
    return translation


@router.delete("/{translation_id}", response_model=schemas.Translation)
def delete_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a translation.
    """
    check_admin_access(current_user)
    
    translation = crud.translation.get_translation(db, translation_id=translation_id)
    if not translation:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )
    
    translation = crud.translation.delete_translation(db, translation_id=translation_id)
    return translation

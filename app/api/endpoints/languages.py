from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import crud, models, schemas
from app.api import deps
from app.core.security import get_password_hash
from app.utils import check_admin_access

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Language])
def read_languages(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.language.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve languages with pagination.
    """
    check_admin_access(current_user)
    
    languages, total = crud.language.get_languages_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": languages,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=schemas.Language)
def create_language(
    *,
    db: Session = Depends(deps.get_db),
    language_in: schemas.LanguageCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new language.
    """
    check_admin_access(current_user)
    
    # Check if language with this code already exists
    language = crud.language.get_language_by_code(db, code=language_in.code)
    if language:
        raise HTTPException(
            status_code=400,
            detail="The language with this code already exists in the system.",
        )
    
    language = crud.language.create_language(db, language=language_in)
    return language


@router.get("/{language_id}", response_model=schemas.Language)
def read_language(
    *,
    db: Session = Depends(deps.get_db),
    language_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get language by ID.
    """
    check_admin_access(current_user)
    
    language = crud.language.get_language(db, language_id=language_id)
    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )
    return language


@router.put("/{language_id}", response_model=schemas.Language)
def update_language(
    *,
    db: Session = Depends(deps.get_db),
    language_id: int,
    language_in: schemas.LanguageUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a language.
    """
    check_admin_access(current_user)
    
    language = crud.language.get_language(db, language_id=language_id)
    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )
    
    # If updating code, check it doesn't conflict with existing languages
    if language_in.code and language_in.code != language.code:
        existing_language = crud.language.get_language_by_code(db, code=language_in.code)
        if existing_language:
            raise HTTPException(
                status_code=400,
                detail="The language with this code already exists in the system.",
            )
    
    language = crud.language.update_language(db, language_id=language_id, language=language_in)
    return language


@router.delete("/{language_id}", response_model=schemas.Language)
def delete_language(
    *,
    db: Session = Depends(deps.get_db),
    language_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a language.
    """
    check_admin_access(current_user)
    
    language = crud.language.get_language(db, language_id=language_id)
    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )
    
    # Check if it's the default language
    if language.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the default language",
        )
    
    language = crud.language.delete_language(db, language_id=language_id)
    return language

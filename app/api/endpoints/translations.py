from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app.crud import translation as translation_crud
from app.api import deps
from app.schemas.translation import TranslationOut as Translation, PaginatedTranslationResponse, TranslationCreate, TranslationUpdate
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


@router.get("/", response_model=List[str])
def list_translation_identifiers(
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get list of all translation identifiers.
    """
    logger.debug("Fetching all translation identifiers")
    translations = translation_crud.get_translations(db)
    return [trans.identifier for trans in translations]


@router.get("/full", response_model=PaginatedTranslationResponse)
def read_translations(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    identifier: Optional[str] = None,
    text: Optional[str] = None,
    language_id: Optional[List[str]] = Query(None),
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get paginated list of translations with full details.
    Supports both direct parameters (identifier, text, language_id) and 
    filter parameters (filterField, filterValue, filterOperator).
    """
    logger.debug(f"Fetching translations with page={page}, pageSize={pageSize}, identifier={identifier}, text={text}, language_id={language_id}, filterField={filterField}, filterValue={filterValue}, sort={sortField} {sortOrder}")
    
    # Process filter parameters if they exist
    identifier_filter = identifier
    text_filter = text
    language_filter_values = language_id
    
    # If filter parameters are provided, use them instead of direct parameters
    if filterField and filterValue:
        for i, field in enumerate(filterField):
            if i < len(filterValue):
                if field == 'identifier' and not identifier_filter:
                    identifier_filter = filterValue[i]
                elif field == 'text' and not text_filter:
                    text_filter = filterValue[i]
                elif field == 'language_id':
                    if not language_filter_values:
                        language_filter_values = []
                    language_filter_values.append(filterValue[i])
    
    try:
        translations, total = translation_crud.get_translations_paginated(
            db=db,
            page=page,
            page_size=pageSize,
            identifier_filter=identifier_filter,
            text_filter=text_filter,
            language_filter_values=language_filter_values,
            sort_field=sortField,
            sort_order=sortOrder
        )
        
        logger.debug(f"Successfully fetched {len(translations)} translations with total={total}")
        
        return {
            "items": translations,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
    except Exception as e:
        logger.error(f"Error getting translations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting translations: {str(e)}"
        )


@router.post("/", response_model=Translation)
def create_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_in: TranslationCreate,
) -> Any:
    """
    Create new translation.
    """
    logger.debug(f"Creating translation with identifier: {translation_in.identifier}")
    
    # Check if translation with this identifier already exists
    existing_translation = translation_crud.get_translation_by_identifier(db, identifier=translation_in.identifier)
    if existing_translation:
        raise HTTPException(
            status_code=400,
            detail="The translation with this identifier already exists in the system.",
        )
    
    new_translation = translation_crud.create_translation(db, translation=translation_in)
    db.commit()
    db.refresh(new_translation)
    logger.debug(f"Translation created successfully with ID: {new_translation.id}")
    return new_translation


@router.get("/{translation_id}", response_model=Translation)
def read_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_id: int,
) -> Any:
    """
    Get translation by ID.
    """
    logger.debug(f"Fetching translation with ID: {translation_id}")
    
    translation_obj = translation_crud.get_translation(db, translation_id=translation_id)
    if not translation_obj:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )
    return translation_obj


@router.put("/{translation_id}", response_model=Translation)
def update_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_id: int,
    translation_in: TranslationUpdate,
) -> Any:
    """
    Update a translation.
    """
    logger.debug(f"Updating translation with ID: {translation_id}")
    
    translation_obj = translation_crud.get_translation(db, translation_id=translation_id)
    if not translation_obj:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )
    
    # If updating identifier, check it doesn't conflict with existing translations
    if translation_in.identifier and translation_in.identifier != translation_obj.identifier:
        existing_translation = translation_crud.get_translation_by_identifier(db, identifier=translation_in.identifier)
        if existing_translation:
            raise HTTPException(
                status_code=400,
                detail="The translation with this identifier already exists in the system.",
            )
    
    updated_translation = translation_crud.update_translation(db, translation_id=translation_id, translation=translation_in)
    db.commit()
    db.refresh(updated_translation)
    logger.debug(f"Translation updated successfully: {updated_translation.id}")
    return updated_translation


@router.delete("/{translation_id}", response_model=Translation)
def delete_translation(
    *,
    db: Session = Depends(deps.get_db),
    translation_id: int,
) -> Any:
    """
    Delete a translation.
    """
    logger.debug(f"Deleting translation with ID: {translation_id}")
    
    translation_obj = translation_crud.get_translation(db, translation_id=translation_id)
    if not translation_obj:
        raise HTTPException(
            status_code=404,
            detail="Translation not found",
        )
    
    deleted_translation = translation_crud.delete_translation(db, translation_id=translation_id)
    db.commit()
    logger.debug(f"Translation deleted successfully: {translation_id}")
    return deleted_translation

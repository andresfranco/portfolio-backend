from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.language import (LanguageCreate, PaginatedLanguageResponse, Filter, LanguageOut as Language, LanguageUpdate)
from app.crud import language as crud_language
from app.api import deps
from typing import Optional, List, Any
import logging
import sys
import json
from app.utils.file_utils import save_upload_file, LANGUAGE_IMAGES_DIR, get_file_url

router = APIRouter()
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

@router.get("/",response_model=List[str])
def list_languages(
    db: Session =Depends(get_db)
):
    """Get list of all language codes as per the API spec"""
    logger.debug("Fetching all language codes")
    languages = crud_language.get_languages(db)
    return [lang.code for lang in languages]


@router.get("/full",response_model=PaginatedLanguageResponse)
def read_languages(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get paginated list of languages with full details"""
    logger.debug(f"Fetching languages with page={page}, pageSize={pageSize}, filters={filterField}, values={filterValue}, operators={filterOperator}, sort={sortField} {sortOrder}")
    
    parsed_filters = []
    if filterField and filterValue:
        # Zip the filter parameters together, using 'contains' as default operator if not provided
        operators = filterOperator if filterOperator else ['contains'] * len(filterField)
        for field, value, operator in zip(filterField, filterValue, operators):
            try:
                parsed_filters.append(Filter.from_params(field=field, value=value, operator=operator))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    languages, total = crud_language.get_languages_paginated(
        db,
        page=page,
        page_size=pageSize,
        filters=parsed_filters or None,
        sort_field=sortField,
        sort_order=sortOrder
    )
    
    response = {
        "items": languages,
        "total": total,
        "page": page,
        "pageSize": pageSize
    }
    
    logger.debug(f"Languages fetched: {response}")
    return response

@router.post("/", response_model=Language)
async def create_language(
    code: str = Form(...),
    name: str = Form(...),
    is_default: bool = Form(False),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Create a new language with an optional image upload"""
    logger.debug(f"Creating language with code: {code}")
    
    # First check if language already exists
    existing_language = crud_language.get_language_by_code(db, code)
    if existing_language:
        logger.warning(f"Language with code {code} already exists")
        raise HTTPException(status_code=400, detail="Language already exists")
    
    # Create language schema object
    language_data = LanguageCreate(
        code=code,
        name=name,
        is_default=is_default
    )
    
    # Handle image upload if provided
    image_path = None
    if image and image.filename:
        # Validate image file type
        valid_image_types = ["image/jpeg", "image/png", "image/gif", "image/svg+xml"]
        if image.content_type not in valid_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type. Supported types: {', '.join(valid_image_types)}"
            )
        
        # Save the image
        try:
            image_path = await save_upload_file(image, LANGUAGE_IMAGES_DIR)
            logger.debug(f"Image saved at: {image_path}")
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save image")
    
    # Create the language
    db_language = crud_language.create_language(db, language_data, image_path)
    db.commit()
    db.refresh(db_language)
    logger.debug(f"Language created successfully with ID: {db_language.id}")
    return db_language


@router.get("/{language_id}", response_model=Language)
def read_language(
    *,
    db: Session = Depends(deps.get_db),
    language_id: int,
) -> Any:
    """
    Get language by ID.
    """
    
    language = crud_language.get_language(db, language_id=language_id)
    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )
    return language


@router.put("/{language_id}", response_model=Language)
async def update_language(
    *,
    db: Session = Depends(deps.get_db),
    language_id: int,
    code: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    is_default: Optional[bool] = Form(None),
    image: UploadFile = File(None),
) -> Any:
    """
    Update a language with optional image upload.
    """
    
    language = crud_language.get_language(db, language_id=language_id)
    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found",
        )
    
    # Create update data
    language_update = LanguageUpdate(
        code=code,
        name=name,
        is_default=is_default
    )
    
    # If updating code, check it doesn't conflict with existing languages
    if code and code != language.code:
        existing_language = crud_language.get_language_by_code(db, code=code)
        if existing_language:
            raise HTTPException(
                status_code=400,
                detail="The language with this code already exists in the system.",
            )
    
    # Handle image upload if provided
    image_path = None
    if image and image.filename:
        # Validate image file type
        valid_image_types = ["image/jpeg", "image/png", "image/gif", "image/svg+xml"]
        if image.content_type not in valid_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type. Supported types: {', '.join(valid_image_types)}"
            )
        
        # Save the image
        try:
            image_path = await save_upload_file(image, LANGUAGE_IMAGES_DIR)
            logger.debug(f"Image saved at: {image_path}")
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save image")
    
    # Update the language
    language = crud_language.update_language(db, language_id=language_id, language=language_update, image_path=image_path)
    db.commit()
    db.refresh(language)
    logger.debug(f"Language updated successfully: {language.id}")
    return language


@router.delete("/{language_id}", response_model=Language)
def delete_language(
    *,
    db: Session = Depends(deps.get_db),
    language_id: int,
) -> Any:
    """
    Delete a language.
    """
    
    language = crud_language.get_language(db, language_id=language_id)
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
    
    language = crud_language.delete_language(db, language_id=language_id)
    db.commit()
    logger.debug(f"Language {language_id} deleted successfully")
    return language

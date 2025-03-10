from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
import sqlalchemy as sa

from app import models, schemas
from app.api import deps
from app.crud import experience as experience_crud
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


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Experience])
def read_experiences(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.experience.Filter]] = None,
) -> Any:
    """
    Retrieve experiences with pagination.
    """
    
    experiences, total = experience_crud.get_experiences_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": experiences,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/full", response_model=schemas.experience.PaginatedExperienceResponse)
def read_experiences_full(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    code: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    language_id: Optional[List[str]] = Query(None),
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get paginated list of experiences with full details.
    Supports both direct parameters (code, name, description, language_id) and 
    filter parameters (filterField, filterValue, filterOperator).
    """
    logger.debug(f"Fetching experiences with page={page}, pageSize={pageSize}, code={code}, name={name}, description={description}, language_id={language_id}, filterField={filterField}, filterValue={filterValue}, sort={sortField} {sortOrder}")
    
    # Process filter parameters if they exist
    code_filter = code
    name_filter = name
    description_filter = description
    language_filter_values = language_id
    
    # If filter parameters are provided, use them instead of direct parameters
    if filterField and filterValue:
        for i, field in enumerate(filterField):
            if i < len(filterValue):
                if field == 'code' and not code_filter:
                    code_filter = filterValue[i]
                elif field == 'name' and not name_filter:
                    name_filter = filterValue[i]
                elif field == 'description' and not description_filter:
                    description_filter = filterValue[i]
                elif field == 'language_id':
                    if not language_filter_values:
                        language_filter_values = []
                    language_filter_values.append(filterValue[i])
    
    try:
        # First, ensure all experiences have a code value
        db.execute(sa.text(
            """
            UPDATE experiences 
            SET code = 'EXP-' || id 
            WHERE code IS NULL
            """
        ))
        db.commit()
        
        experiences, total = experience_crud.get_experiences_paginated(
            db=db,
            page=page,
            page_size=pageSize,
            code_filter=code_filter,
            name_filter=name_filter,
            description_filter=description_filter,
            language_filter_values=language_filter_values,
            sort_field=sortField,
            sort_order=sortOrder
        )
        
        # Double-check that all experiences have a code value
        for experience in experiences:
            if experience.code is None:
                experience.code = f"EXP-{experience.id}"
        
        db.commit()
        
        return {
            "items": experiences,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
    except Exception as e:
        logger.error(f"Error fetching experiences: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching experiences: {str(e)}"
        )


@router.get("/check-code/{code}", response_model=schemas.experience.UniqueCheckResponse)
def check_code(
    code: str,
    experience_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Check if a code already exists.
    """
    exists = experience_crud.check_code_exists(db, code, exclude_id=experience_id)
    return {"exists": exists, "code": code}


@router.post("/", response_model=schemas.Experience)
def create_experience(
    *,
    db: Session = Depends(deps.get_db),
    experience_in: schemas.ExperienceCreate,
) -> Any:
    """
    Create new experience.
    """
    
    # Check if code already exists
    if experience_crud.check_code_exists(db, experience_in.code):
        raise HTTPException(
            status_code=400,
            detail=f"Experience with code '{experience_in.code}' already exists"
        )
    
    experience = experience_crud.create_experience(db, experience=experience_in)
    return experience


@router.get("/{experience_id}", response_model=schemas.Experience)
def read_experience(
    *,
    db: Session = Depends(deps.get_db),
    experience_id: int,
) -> Any:
    """
    Get experience by ID.
    """
    
    experience = experience_crud.get_experience(db, experience_id=experience_id)
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
) -> Any:
    """
    Update an experience.
    """
    
    experience = experience_crud.get_experience(db, experience_id=experience_id)
    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )
    
    # Check if code already exists (if code is being updated)
    if experience_in.code is not None and experience_in.code != experience.code:
        if experience_crud.check_code_exists(db, experience_in.code, exclude_id=experience_id):
            raise HTTPException(
                status_code=400,
                detail=f"Experience with code '{experience_in.code}' already exists"
            )
    
    experience = experience_crud.update_experience(db, experience_id=experience_id, experience=experience_in)
    return experience


@router.delete("/{experience_id}", response_model=schemas.Experience)
def delete_experience(
    *,
    db: Session = Depends(deps.get_db),
    experience_id: int,
) -> Any:
    """
    Delete an experience.
    """
    
    experience = experience_crud.get_experience(db, experience_id=experience_id)
    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found",
        )
    
    experience = experience_crud.delete_experience(db, experience_id=experience_id)
    return experience

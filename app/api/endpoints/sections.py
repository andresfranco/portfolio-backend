from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import models, schemas
from app.api import deps
from app.crud import section as section_crud
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


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Section])
def read_sections(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.section.Filter]] = None,
) -> Any:
    """
    Retrieve sections with pagination.
    """
    
    sections, total = section_crud.get_sections_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": sections,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/full", response_model=schemas.section.PaginatedSectionResponse)
def read_sections_full(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    code: Optional[str] = None,
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
    Get paginated list of sections with full details.
    Supports both direct parameters (code, text, language_id) and 
    filter parameters (filterField, filterValue, filterOperator).
    """
    logger.debug(f"Fetching sections with page={page}, pageSize={pageSize}, code={code}, text={text}, language_id={language_id}, filterField={filterField}, filterValue={filterValue}, sort={sortField} {sortOrder}")
    
    # Process filter parameters if they exist
    code_filter = code
    text_filter = text
    language_filter_values = language_id
    
    # If filter parameters are provided, use them instead of direct parameters
    if filterField and filterValue:
        for i, field in enumerate(filterField):
            if i < len(filterValue):
                if field == 'code' and not code_filter:
                    code_filter = filterValue[i]
                elif field == 'text' and not text_filter:
                    text_filter = filterValue[i]
                elif field == 'language_id':
                    if not language_filter_values:
                        language_filter_values = []
                    language_filter_values.append(filterValue[i])
    
    try:
        sections, total = section_crud.get_sections_paginated(
            db=db,
            page=page,
            page_size=pageSize,
            code_filter=code_filter,
            text_filter=text_filter,
            language_filter_values=language_filter_values,
            sort_field=sortField,
            sort_order=sortOrder
        )
        
        logger.debug(f"Successfully fetched {len(sections)} sections with total={total}")
        
        return {
            "items": sections,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
    except Exception as e:
        logger.error(f"Error getting sections: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting sections: {str(e)}"
        )


@router.get("/check-unique", response_model=schemas.section.UniqueCheckResponse)
def check_section_code_unique(
    code: str = Query(..., description="Section code to check for uniqueness"),
    exclude_id: Optional[int] = Query(None, description="Section ID to exclude from the check"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Check if a section code is unique.
    """
    
    # Get section by code
    section = section_crud.get_section_by_code(db, code=code)
    
    # If section exists and it's not the one we're excluding, it's not unique
    exists = section is not None and (exclude_id is None or section.id != exclude_id)
    
    return {
        "exists": exists,
        "code": code
    }


@router.post("/", response_model=schemas.Section)
def create_section(
    *,
    db: Session = Depends(deps.get_db),
    section_in: schemas.SectionCreate,
) -> Any:
    """
    Create new section.
    """
    
    # Check if section with this code already exists
    section = section_crud.get_section_by_code(db, code=section_in.code)
    if section:
        raise HTTPException(
            status_code=400,
            detail="The section with this code already exists in the system.",
        )
    
    section = section_crud.create_section(db, section=section_in)
    db.commit()
    db.refresh(section)
    return section


@router.get("/{section_id}", response_model=schemas.Section)
def read_section(
    *,
    db: Session = Depends(deps.get_db),
    section_id: int,
) -> Any:
    """
    Get section by ID.
    """
    
    section = section_crud.get_section(db, section_id=section_id)
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
) -> Any:
    """
    Update a section.
    """
    
    section = section_crud.get_section(db, section_id=section_id)
    if not section:
        raise HTTPException(
            status_code=404,
            detail="Section not found",
        )
    
    # If updating code, check it doesn't conflict with existing sections
    if section_in.code and section_in.code != section.code:
        existing_section = section_crud.get_section_by_code(db, code=section_in.code)
        if existing_section and existing_section.id != section_id:
            raise HTTPException(
                status_code=400,
                detail="The section with this code already exists in the system.",
            )
    
    section = section_crud.update_section(db, section_id=section_id, section=section_in)
    db.commit()
    db.refresh(section)
    return section


@router.delete("/{section_id}", response_model=schemas.Section)
def delete_section(
    *,
    db: Session = Depends(deps.get_db),
    section_id: int,
) -> Any:
    """
    Delete a section.
    """
    
    section = section_crud.get_section(db, section_id=section_id)
    if not section:
        raise HTTPException(
            status_code=404,
            detail="Section not found",
        )
    
    section = section_crud.delete_section(db, section_id=section_id)
    db.commit()
    return section

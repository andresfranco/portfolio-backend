from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app import models, schemas
from app.api import deps
from app.crud import skill as skill_crud  # Fixed import to match section implementation
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

@router.get("/", response_model=schemas.PaginatedResponse[schemas.Skill])
def read_skills(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.skill.Filter]] = None,
) -> Any:
    """
    Retrieve skills with pagination.
    """
    
    skills, total = skill_crud.get_skills_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": skills,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/full", response_model=schemas.skill.PaginatedSkillResponse)
def read_skills_full(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    type: Optional[str] = None,
    name: Optional[str] = None,
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get paginated list of skills with full details.
    Supports both direct parameters (type, name) and 
    filter parameters (filterField, filterValue, filterOperator).
    """
    logger.debug(f"Fetching skills with page={page}, pageSize={pageSize}, type={type}, name={name}, filterField={filterField}, filterValue={filterValue}, sort={sortField} {sortOrder}")
    
    # Process filter parameters if they exist
    type_filter = type
    name_filter = name
    
    # If filter parameters are provided, use them instead of direct parameters
    if filterField and filterValue:
        operators = filterOperator if filterOperator else ['contains'] * len(filterField)
        parsed_filters = []
        for i, field in enumerate(filterField):
            if i < len(filterValue):
                try:
                    parsed_filters.append(schemas.skill.Filter.from_params(
                        field=field, 
                        value=filterValue[i],
                        operator=operators[i] if i < len(operators) else "contains"
                    ))
                    if field == 'type' and not type_filter:
                        type_filter = filterValue[i]
                    elif field == 'name' and not name_filter:
                        name_filter = filterValue[i]
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))
    
    try:
        skills, total = skill_crud.get_skills_paginated(
            db=db,
            page=page,
            page_size=pageSize,
            type_filter=type_filter,
            name_filter=name_filter,
            sort_field=sortField,
            sort_order=sortOrder
        )
        
        logger.debug(f"Successfully fetched {len(skills)} skills with total={total}")
        
        return {
            "items": skills,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting skills: {str(e)}"
        )

@router.get("/check-unique", response_model=schemas.skill.UniqueCheckResponse)
def check_skill_name_unique(
    name: str = Query(..., description="Skill name to check for uniqueness"),
    language_id: int = Query(..., description="Language ID for the name"),
    exclude_id: Optional[int] = Query(None, description="Skill ID to exclude from the check"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Check if a skill name is unique for a given language.
    """
    
    # Get skill by name and language
    skill = skill_crud.get_skill_by_name_and_language(db, name=name, language_id=language_id)
    
    # If skill exists and it's not the one we're excluding, it's not unique
    exists = skill is not None and (exclude_id is None or skill.id != exclude_id)
    
    return {
        "exists": exists,
        "name": name,
        "language_id": language_id
    }

@router.get("/by-type/{skill_type}", response_model=List[schemas.Skill])
def read_skills_by_type(
    *,
    db: Session = Depends(deps.get_db),
    skill_type: str,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve skills by type.
    """
    
    skills = skill_crud.get_skills_by_type(
        db, skill_type=skill_type, skip=skip, limit=limit
    )
    
    return skills

@router.post("/", response_model=schemas.Skill)
def create_skill(
    *,
    db: Session = Depends(deps.get_db),
    skill_in: schemas.SkillCreate,
) -> Any:
    """
    Create new skill.
    """
    
    skill = skill_crud.create_skill(db, skill=skill_in)
    db.commit()
    db.refresh(skill)
    return skill

@router.get("/{skill_id}", response_model=schemas.Skill)
def read_skill(
    *,
    db: Session = Depends(deps.get_db),
    skill_id: int,
) -> Any:
    """
    Get skill by ID.
    """
    
    skill = skill_crud.get_skill(db, skill_id=skill_id)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )
    return skill

@router.put("/{skill_id}", response_model=schemas.Skill)
def update_skill(
    *,
    db: Session = Depends(deps.get_db),
    skill_id: int,
    skill_in: schemas.SkillUpdate,
) -> Any:
    """
    Update a skill.
    """
    
    skill = skill_crud.get_skill(db, skill_id=skill_id)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )
    
    skill = skill_crud.update_skill(db, skill_id=skill_id, skill=skill_in)
    db.commit()
    db.refresh(skill)
    return skill

@router.delete("/{skill_id}", response_model=schemas.Skill)
def delete_skill(
    *,
    db: Session = Depends(deps.get_db),
    skill_id: int,
) -> Any:
    """
    Delete a skill.
    """
    
    skill = skill_crud.get_skill(db, skill_id=skill_id)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )
    
    skill = skill_crud.delete_skill(db, skill_id=skill_id)
    db.commit()
    return skill

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import crud, models, schemas
from app.api import deps
from app.utils import check_admin_access

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Skill])
def read_skills(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.skill.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve skills with pagination.
    """
    check_admin_access(current_user)
    
    skills, total = crud.skill.get_skills_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": skills,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/by-type/{skill_type}", response_model=List[schemas.Skill])
def read_skills_by_type(
    *,
    db: Session = Depends(deps.get_db),
    skill_type: str,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve skills by type.
    """
    check_admin_access(current_user)
    
    skills = crud.skill.get_skills_by_type(
        db, skill_type=skill_type, skip=skip, limit=limit
    )
    
    return skills


@router.post("/", response_model=schemas.Skill)
def create_skill(
    *,
    db: Session = Depends(deps.get_db),
    skill_in: schemas.SkillCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new skill.
    """
    check_admin_access(current_user)
    
    skill = crud.skill.create_skill(db, skill=skill_in)
    return skill


@router.get("/{skill_id}", response_model=schemas.Skill)
def read_skill(
    *,
    db: Session = Depends(deps.get_db),
    skill_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get skill by ID.
    """
    check_admin_access(current_user)
    
    skill = crud.skill.get_skill(db, skill_id=skill_id)
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
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a skill.
    """
    check_admin_access(current_user)
    
    skill = crud.skill.get_skill(db, skill_id=skill_id)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )
    
    skill = crud.skill.update_skill(db, skill_id=skill_id, skill=skill_in)
    return skill


@router.delete("/{skill_id}", response_model=schemas.Skill)
def delete_skill(
    *,
    db: Session = Depends(deps.get_db),
    skill_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a skill.
    """
    check_admin_access(current_user)
    
    skill = crud.skill.get_skill(db, skill_id=skill_id)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )
    
    skill = crud.skill.delete_skill(db, skill_id=skill_id)
    return skill

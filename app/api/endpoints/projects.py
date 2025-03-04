from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any, List, Optional
import os
import uuid
from datetime import datetime

from app import crud, models, schemas
from app.api import deps
from app.utils import check_admin_access
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Project])
def read_projects(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.project.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve projects with pagination.
    """
    check_admin_access(current_user)
    
    projects, total = crud.project.get_projects_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": projects,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=schemas.Project)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new project.
    """
    check_admin_access(current_user)
    
    project = crud.project.create_project(db, project=project_in)
    return project


@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get project by ID.
    """
    check_admin_access(current_user)
    
    project = crud.project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    return project


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: schemas.ProjectUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a project.
    """
    check_admin_access(current_user)
    
    project = crud.project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    
    project = crud.project.update_project(db, project_id=project_id, project=project_in)
    return project


@router.delete("/{project_id}", response_model=schemas.Project)
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a project.
    """
    check_admin_access(current_user)
    
    project = crud.project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    
    project = crud.project.delete_project(db, project_id=project_id)
    return project


@router.post("/{project_id}/images", response_model=schemas.ProjectImage)
async def upload_project_image(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    category: str = Query(..., description="Image category"),
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload an image for a project.
    """
    check_admin_access(current_user)
    
    project = crud.project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.STATIC_DIR, "uploads", "projects", str(project_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the file
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Create relative path for database
    relative_path = os.path.join("uploads", "projects", str(project_id), unique_filename)
    
    # Create project image in database
    project_image = crud.project.add_project_image(
        db, 
        project_id=project_id, 
        image=schemas.ProjectImageCreate(
            image_path=relative_path,
            category=category
        )
    )
    
    return project_image


@router.delete("/{project_id}/images/{image_id}", response_model=schemas.ProjectImage)
def delete_project_image(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    image_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a project image.
    """
    check_admin_access(current_user)
    
    project = crud.project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    
    project_image = crud.project.delete_project_image(db, image_id=image_id)
    if not project_image:
        raise HTTPException(
            status_code=404,
            detail="Project image not found",
        )
    
    # Delete the file if it exists
    if project_image.image_path:
        file_path = os.path.join(settings.STATIC_DIR, project_image.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return project_image


@router.post("/{project_id}/attachments", response_model=schemas.ProjectAttachment)
async def upload_project_attachment(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload an attachment for a project.
    """
    check_admin_access(current_user)
    
    project = crud.project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.STATIC_DIR, "uploads", "projects", str(project_id), "attachments")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the file
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Create relative path for database
    relative_path = os.path.join("uploads", "projects", str(project_id), "attachments", unique_filename)
    
    # Create project attachment in database
    project_attachment = crud.project.add_project_attachment(
        db, 
        project_id=project_id, 
        attachment=schemas.ProjectAttachmentCreate(
            file_path=relative_path,
            file_name=file.filename
        )
    )
    
    return project_attachment


@router.delete("/{project_id}/attachments/{attachment_id}", response_model=schemas.ProjectAttachment)
def delete_project_attachment(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    attachment_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a project attachment.
    """
    check_admin_access(current_user)
    
    project = crud.project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    
    project_attachment = crud.project.delete_project_attachment(db, attachment_id=attachment_id)
    if not project_attachment:
        raise HTTPException(
            status_code=404,
            detail="Project attachment not found",
        )
    
    # Delete the file if it exists
    if project_attachment.file_path:
        file_path = os.path.join(settings.STATIC_DIR, project_attachment.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return project_attachment

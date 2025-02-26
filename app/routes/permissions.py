from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
    PermissionOut,
    PaginatedPermissionResponse,
    Filter
)
from app.crud import permission as crud_permission
from typing import Optional, List
import logging
import sys

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

@router.post("/", response_model=PermissionOut)
def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db)
):
    logger.debug(f"Creating permission with name: {permission.name}")
    db_permission = crud_permission.get_permission_by_name(db, permission.name)
    if db_permission:
        logger.warning(f"Permission with name {permission.name} already exists")
        raise HTTPException(status_code=400, detail="Permission already exists")
    
    return crud_permission.create_permission(db, permission)

@router.get("/", response_model=List[str])
def list_permissions(
    db: Session = Depends(get_db)
):
    """Get list of all permission names as per the API spec"""
    logger.debug("Fetching all permission names")
    permissions = crud_permission.get_permissions(db)
    return [perm.name for perm in permissions]

@router.get("/full", response_model=PaginatedPermissionResponse)
def read_permissions(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get paginated list of permissions with full details"""
    logger.debug(f"Fetching permissions with page={page}, pageSize={pageSize}, filters={filterField}, values={filterValue}, operators={filterOperator}, sort={sortField} {sortOrder}")
    
    parsed_filters = []
    if filterField and filterValue:
        # Zip the filter parameters together, using 'contains' as default operator if not provided
        operators = filterOperator if filterOperator else ['contains'] * len(filterField)
        for field, value, operator in zip(filterField, filterValue, operators):
            try:
                parsed_filters.append(Filter.from_params(field=field, value=value, operator=operator))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    permissions, total = crud_permission.get_permissions_paginated(
        db,
        page=page,
        page_size=pageSize,
        filters=parsed_filters or None,
        sort_field=sortField,
        sort_order=sortOrder
    )
    
    response = {
        "items": permissions,
        "total": total,
        "page": page,
        "pageSize": pageSize
    }
    
    logger.debug(f"Permissions fetched: {response}")
    return response

@router.get("/{permission_id}", response_model=PermissionOut)
def read_permission(
    permission_id: int,
    db: Session = Depends(get_db)
):
    logger.debug(f"Fetching permission with id: {permission_id}")
    permission = crud_permission.get_permission(db, permission_id)
    if not permission:
        logger.warning(f"Permission with id {permission_id} not found")
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission

@router.put("/{permission_id}", response_model=PermissionOut)
def update_permission(
    permission_id: int,
    permission: PermissionUpdate,
    db: Session = Depends(get_db)
):
    logger.debug(f"Updating permission {permission_id} with data: {permission}")
    
    # Check name uniqueness if name is being updated
    if permission.name is not None:
        existing = crud_permission.get_permission_by_name(db, permission.name)
        if existing and existing.id != permission_id:
            logger.warning(f"Permission name {permission.name} already exists")
            raise HTTPException(status_code=400, detail="Permission name already exists")
    
    updated = crud_permission.update_permission(db, permission_id, permission)
    if not updated:
        logger.warning(f"Permission with id {permission_id} not found")
        raise HTTPException(status_code=404, detail="Permission not found")
    
    logger.debug(f"Permission updated successfully: {updated.name}")
    return updated

@router.delete("/{permission_id}", response_model=dict)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db)
):
    logger.debug(f"Deleting permission with id: {permission_id}")
    permission = crud_permission.get_permission(db, permission_id)
    if not permission:
        logger.warning(f"Permission with id {permission_id} not found")
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Check if permission is assigned to any roles before deletion
    if permission.roles:
        logger.error(f"Cannot delete permission {permission_id} as it is assigned to roles")
        raise HTTPException(
            status_code=400,
            detail="Cannot delete permission as it is assigned to roles"
        )
    
    crud_permission.delete_permission(db, permission_id)
    logger.debug(f"Permission {permission_id} deleted successfully")
    return {"detail": "Permission deleted"}
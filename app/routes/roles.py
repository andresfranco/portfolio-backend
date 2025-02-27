from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.role import RoleBase, RoleOut, PaginatedRoleResponse, RoleFilter, RoleUpdate
from app.crud import role as crud_role
from typing import Optional, List
import logging
import sys
from app.models.role import Role  # Import the Role model

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

@router.post("/", response_model=RoleOut)
def create_role_endpoint(role: RoleBase, db: Session = Depends(get_db)):
    logger.debug(f"Creating role with name: {role.name}")
    db_role = crud_role.get_role_by_name(db, role.name)
    if db_role:
        logger.warning(f"Role with name {role.name} already exists")
        raise HTTPException(status_code=400, detail="Role already exists")
    
    created_role = crud_role.create_role(db, role.name, role.description, role.permissions)
    logger.debug(f"Role created successfully: {created_role['name']}")
    return created_role

@router.get("/", response_model=List[str])
def list_roles(
    db: Session = Depends(get_db)
):
    """Get list of all role names"""
    logger.debug("Fetching all role names")
    roles = crud_role.get_roles(db)
    return [role["name"] for role in roles]

@router.get("/full", response_model=PaginatedRoleResponse)
def read_roles(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get paginated list of roles with full details"""
    logger.debug(f"Fetching roles with page={page}, pageSize={pageSize}, filters={filterField}, values={filterValue}, operators={filterOperator}, sort={sortField} {sortOrder}")
    
    parsed_filters = []
    if filterField and filterValue:
        # Zip the filter parameters together, using 'contains' as default operator if not provided
        operators = filterOperator if filterOperator else ['contains'] * len(filterField)
        for field, value, operator in zip(filterField, filterValue, operators):
            try:
                # Handle permission filter specially
                if field == 'permission':
                    parsed_filters.append(RoleFilter.from_params(field='permission', value=value, operator=operator))
                elif field == 'permissions':
                    # This is the old way, but we'll handle it for backward compatibility
                    parsed_filters.append(RoleFilter.from_params(field='permission', value=value, operator=operator))
                else:
                    parsed_filters.append(RoleFilter.from_params(field=field, value=value, operator=operator))
            except ValueError as e:
                logger.error(f"Invalid filter parameters: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
    
    roles, total = crud_role.get_roles_paginated(
        db,
        page=page,
        page_size=pageSize,
        filters=parsed_filters or None,
        sort_field=sortField,
        sort_order=sortOrder
    )
    
    # The roles are already in dictionary format with permissions as strings
    response = {
        "items": roles,
        "total": total,
        "page": page,
        "pageSize": pageSize
    }
    
    logger.debug(f"Roles fetched: {response}")
    return response

@router.get("/{role_id}", response_model=RoleOut)
def read_role(role_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Fetching role with id: {role_id}")
    db_role = crud_role.get_role(db, role_id)
    if not db_role:
        logger.warning(f"Role with id {role_id} not found")
        raise HTTPException(status_code=404, detail="Role not found")
    
    # The role is already in dictionary format with permissions as strings and users_count
    return db_role

@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    logger.debug(f"Updating role {role_id} with data: {role}")
    
    # Check for name uniqueness if name is being updated
    if role.name is not None:
        existing_role = crud_role.get_role_by_name(db, role.name)
        if existing_role and existing_role["id"] != role_id:
            logger.warning(f"Role name {role.name} already exists")
            raise HTTPException(status_code=400, detail="Role name already exists")
    
    updated_role = crud_role.update_role(db, role_id, role)
    if not updated_role:
        logger.warning(f"Role with id {role_id} not found")
        raise HTTPException(status_code=404, detail="Role not found")
    
    # The role is already in dictionary format with permissions as strings and users_count
    logger.debug(f"Role updated successfully: {updated_role['name']}")
    return updated_role

@router.delete("/{role_id}", response_model=dict)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Deleting role with id: {role_id}")
    db_role = crud_role.get_role(db, role_id)
    if not db_role:
        logger.warning(f"Role with id {role_id} not found")
        raise HTTPException(status_code=404, detail="Role not found")
    
    # We need to get the actual role object from the database for deletion
    role_obj = db.query(Role).filter(Role.id == role_id).first()
    
    # Check if role is assigned to any users before deletion
    if role_obj.users:
        logger.error(f"Cannot delete role {role_id} as it is assigned to users")
        raise HTTPException(status_code=400, detail="Cannot delete role as it is assigned to users")
    
    db.delete(role_obj)
    db.commit()
    logger.debug(f"Role {role_id} deleted successfully")
    return {"detail": "Role deleted"}

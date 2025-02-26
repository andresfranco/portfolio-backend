from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from app.models.role import Role
from app.models.permission import Permission
from app.schemas.role import RoleFilter, RoleUpdate
from app.crud import permission as permission_crud
from typing import List, Tuple, Optional
from fastapi import HTTPException

def get_role(db: Session, role_id: int):
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        return None
        
    # Ensure role object has permissions as strings for serialization
    role_dict = {
        "id": db_role.id,
        "name": db_role.name,
        "description": db_role.description,
        "permissions": [p.name for p in db_role.permissions] if db_role.permissions else [],
        "users_count": len(db_role.users) if db_role.users else 0
    }
    
    return role_dict

def get_role_by_name(db: Session, name: str):
    db_role = db.query(Role).filter(Role.name == name).first()
    if not db_role:
        return None
        
    # Ensure role object has permissions as strings for serialization
    role_dict = {
        "id": db_role.id,
        "name": db_role.name,
        "description": db_role.description,
        "permissions": [p.name for p in db_role.permissions] if db_role.permissions else [],
        "users_count": len(db_role.users) if db_role.users else 0
    }
    
    return role_dict

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    roles = db.query(Role).offset(skip).limit(limit).all()
    
    # Convert roles to dictionaries with permissions as strings
    role_dicts = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": [p.name for p in role.permissions] if role.permissions else [],
            "users_count": len(role.users) if role.users else 0
        }
        role_dicts.append(role_dict)
    
    return role_dicts

def create_role(db: Session, name: str, description: str, permissions: List[str] = None):
    # Check name uniqueness
    existing = get_role_by_name(db, name)
    if existing:
        raise HTTPException(status_code=400, detail="Role name already exists")

    # Create the role
    role = Role(name=name, description=description)
    if permissions:
        db_permissions = permission_crud.get_permissions_by_names(db, permissions)
        if len(db_permissions) != len(permissions):
            existing_perms = {p.name for p in db_permissions}
            invalid_perms = set(permissions) - existing_perms
            raise ValueError(f"Invalid permissions: {invalid_perms}")
        role.permissions = db_permissions

    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Ensure role object has permissions as strings for serialization
    role_dict = {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": [p.name for p in role.permissions] if role.permissions else [],
        "users_count": len(role.users) if role.users else 0
    }
    
    return role_dict

def update_role(db: Session, role_id: int, role: RoleUpdate):
    # Get the actual role object from the database
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        return None
        
    if role.name is not None:
        db_role.name = role.name
    if role.description is not None:
        db_role.description = role.description
    
    # Update permissions if provided
    if role.permissions is not None:
        db_permissions = permission_crud.get_permissions_by_names(db, role.permissions)
        if len(db_permissions) != len(role.permissions):
            existing_perms = {p.name for p in db_permissions}
            invalid_perms = set(role.permissions) - existing_perms
            raise ValueError(f"Invalid permissions: {invalid_perms}")
        db_role.permissions = db_permissions
    
    db.commit()
    db.refresh(db_role)
    
    # Ensure role object has permissions as strings for serialization
    role_dict = {
        "id": db_role.id,
        "name": db_role.name,
        "description": db_role.description,
        "permissions": [p.name for p in db_role.permissions] if db_role.permissions else [],
        "users_count": len(db_role.users) if db_role.users else 0
    }
    
    return role_dict

def get_roles_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[RoleFilter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[dict], int]:
    query = db.query(Role)
    
    # Apply multiple filters if specified
    if filters:
        filter_conditions = []
        for filter_item in filters:
            if hasattr(Role, filter_item.field):
                column = getattr(Role, filter_item.field)
                if filter_item.operator == "contains":
                    filter_conditions.append(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    filter_conditions.append(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    filter_conditions.append(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    filter_conditions.append(column.ilike(f"%{filter_item.value}"))
        
        if filter_conditions:
            query = query.filter(*filter_conditions)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting if specified
    if sort_field and hasattr(Role, sort_field):
        sort_func = asc if sort_order == "asc" else desc
        query = query.order_by(sort_func(getattr(Role, sort_field)))
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    roles = query.all()
    
    # Convert roles to dictionaries with permissions as strings
    role_dicts = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": [p.name for p in role.permissions] if role.permissions else [],
            "users_count": len(role.users) if role.users else 0
        }
        role_dicts.append(role_dict)
    
    return role_dicts, total

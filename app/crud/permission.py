from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_, and_, cast, String
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, Filter
from typing import List, Tuple, Optional

def get_permission(db: Session, permission_id: int):
    return db.query(Permission).filter(Permission.id == permission_id).first()

def get_permission_by_name(db: Session, name: str):
    return db.query(Permission).filter(Permission.name == name).first()

def get_permissions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Permission).offset(skip).limit(limit).all()

def get_permissions_by_names(db: Session, names: List[str]) -> List[Permission]:
    return db.query(Permission).filter(Permission.name.in_(names)).all()

def create_permission(db: Session, permission: PermissionCreate):
    db_permission = Permission(**permission.model_dump())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def update_permission(db: Session, permission_id: int, permission: PermissionUpdate):
    db_permission = get_permission(db, permission_id)
    if not db_permission:
        return None
        
    # Update only provided fields
    for field, value in permission.model_dump(exclude_unset=True).items():
        setattr(db_permission, field, value)
    
    db.commit()
    db.refresh(db_permission)
    return db_permission

def delete_permission(db: Session, permission_id: int):
    db_permission = get_permission(db, permission_id)
    if db_permission:
        db.delete(db_permission)
        db.commit()
    return db_permission

def apply_filter_conditions(query, filters: List[Filter]):
    """Apply filter conditions to the query"""
    if not filters:
        return query
        
    filter_conditions = []
    for filter in filters:
        model_attr = getattr(Permission, filter.field)
        
        # Handle different operators
        if filter.operator == 'eq':
            # For ID field, no need to cast to string
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = model_attr == value
                except ValueError:
                    condition = False  # Invalid ID value
            else:
                condition = model_attr == filter.value
        elif filter.operator == 'neq':
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = model_attr != value
                except ValueError:
                    condition = True  # Invalid ID will never equal any ID
            else:
                condition = model_attr != filter.value
        elif filter.operator == 'gt':
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = model_attr > value
                except ValueError:
                    condition = False
            else:
                condition = model_attr > filter.value
        elif filter.operator == 'gte':
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = model_attr >= value
                except ValueError:
                    condition = False
            else:
                condition = model_attr >= filter.value
        elif filter.operator == 'lt':
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = model_attr < value
                except ValueError:
                    condition = False
            else:
                condition = model_attr < filter.value
        elif filter.operator == 'lte':
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = model_attr <= value
                except ValueError:
                    condition = False
            else:
                condition = model_attr <= filter.value
        elif filter.operator == 'contains':
            # Cast to string for contains operations on non-string fields
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = cast(model_attr, String).contains(str(value))
                except ValueError:
                    condition = False
            else:
                condition = model_attr.contains(filter.value)
        elif filter.operator == 'startswith':
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = cast(model_attr, String).startswith(str(value))
                except ValueError:
                    condition = False
            else:
                condition = model_attr.startswith(filter.value)
        elif filter.operator == 'endswith':
            if filter.field == 'id':
                try:
                    value = int(filter.value)
                    condition = cast(model_attr, String).endswith(str(value))
                except ValueError:
                    condition = False
            else:
                condition = model_attr.endswith(filter.value)
        
        filter_conditions.append(condition)
    
    # Combine all conditions with AND
    return query.filter(and_(*filter_conditions))

def get_permissions_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Permission], int]:
    query = db.query(Permission)
    
    # Apply filters if any
    if filters:
        query = apply_filter_conditions(query, filters)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting if specified
    if sort_field and hasattr(Permission, sort_field):
        sort_func = asc if sort_order == "asc" else desc
        query = query.order_by(sort_func(getattr(Permission, sort_field)))
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

# Core permissions initialization
CORE_PERMISSIONS = [
    {"name": "CREATE_USER", "description": "Allows creating new users"},
    {"name": "EDIT_USER", "description": "Allows editing user details"},
    {"name": "DELETE_USER", "description": "Allows deleting users"},
    {"name": "VIEW_USER", "description": "Allows viewing user details"},
    {"name": "CREATE_ROLE", "description": "Allows creating new roles"},
    {"name": "EDIT_ROLE", "description": "Allows editing role details"},
    {"name": "DELETE_ROLE", "description": "Allows deleting roles"},
    {"name": "VIEW_ROLE", "description": "Allows viewing role details"},
]

def initialize_core_permissions(db: Session):
    """Initialize core permissions if they don't exist."""
    for perm in CORE_PERMISSIONS:
        if not get_permission_by_name(db, perm["name"]):
            db_permission = Permission(**perm)
            db.add(db_permission)
    db.commit()
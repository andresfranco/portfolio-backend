from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, Filter
from passlib.context import CryptContext
from typing import List, Optional, Tuple
import logging
import sys

# Use Uvicorn's logger for consistency
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CRUD Functions
def get_user(db: Session, user_id: int):
    logger.debug(f"Fetching user with ID {user_id}")
    print(f"DEBUG: Fetching user with ID {user_id}", file=sys.stderr)
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    logger.debug(f"Fetching user by username: {username}")
    print(f"DEBUG: Fetching user by username: {username}", file=sys.stderr)
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    logger.debug(f"Starting user creation for {user.username}")
    print(f"DEBUG: Starting user creation for {user.username}", file=sys.stderr)
    
    db_user = User(username=user.username, email=user.email)
    db_user.hashed_password = pwd_context.hash(user.password)
    if user.roles:
        logger.debug(f"Fetching roles: {user.roles}")
        print(f"DEBUG: Fetching roles: {user.roles}", file=sys.stderr)
        roles = db.query(Role).filter(Role.id.in_(user.roles)).all()
        if len(roles) != len(user.roles):
            missing_roles = set(user.roles) - {role.id for role in roles}
            logger.error(f"Invalid role IDs: {missing_roles}")
            print(f"ERROR: Invalid role IDs: {missing_roles}", file=sys.stderr)
            raise ValueError(f"Invalid role IDs: {missing_roles}")
        db_user.roles = roles
    db.add(db_user)
    logger.debug("User added to session")
    print("DEBUG: User added to session", file=sys.stderr)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching users with skip={skip}, limit={limit}")
    print(f"DEBUG: Fetching users with skip={skip}, limit={limit}", file=sys.stderr)
    return db.query(User).offset(skip).limit(limit).all()

def get_users_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[User], int]:
    query = db.query(User)
    
    # Apply multiple filters if specified
    if filters:
        filter_conditions = []
        for filter_item in filters:
            if hasattr(User, filter_item.field):
                column = getattr(User, filter_item.field)
                if filter_item.operator == "contains":
                    filter_conditions.append(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    filter_conditions.append(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    filter_conditions.append(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    filter_conditions.append(column.ilike(f"%{filter_item.value}"))
        
        if filter_conditions:
            # Combine all filters with AND operation
            query = query.filter(*filter_conditions)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting if specified
    if sort_field and hasattr(User, sort_field):
        sort_func = asc if sort_order == "asc" else desc
        query = query.order_by(sort_func(getattr(User, sort_field)))
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total
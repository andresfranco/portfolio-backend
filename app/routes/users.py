from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate, UserPasswordChange
from app.crud import user as crud_user
from app.models.role import Role
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

logger.debug("Users router initialized")
print("DEBUG: Users router initialized", file=sys.stderr)

@router.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.debug(f"Starting user creation for {user.username}")
    print(f"DEBUG: Starting user creation for {user.username}", file=sys.stderr)
    
    db_user = crud_user.get_user_by_username(db, user.username)
    if db_user:
        logger.warning(f"Username {user.username} already registered")
        print(f"WARN: Username {user.username} already registered", file=sys.stderr)
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = crud_user.create_user(db, user)
    logger.debug("Committing user to database")
    print("DEBUG: Committing user to database", file=sys.stderr)
    db.commit()
    
    logger.debug("Refreshing user object")
    print("DEBUG: Refreshing user object", file=sys.stderr)
    db.refresh(new_user)
    
    logger.debug(f"Raw roles after refresh: {new_user.roles}")
    print(f"DEBUG: Raw roles after refresh: {new_user.roles}", file=sys.stderr)
    
    new_user_roles = []
    if new_user.roles is not None:
        new_user_roles = [role.id for role in new_user.roles]
    logger.debug(f"Converted roles: {new_user_roles}")
    print(f"DEBUG: Converted roles: {new_user_roles}", file=sys.stderr)
    
    response = {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "roles": new_user_roles
    }
    logger.debug(f"Response prepared: {response}")
    print(f"DEBUG: Response prepared: {response}", file=sys.stderr)
    
    return response

@router.get("/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    roles = [role.id for role in db_user.roles] if db_user.roles else []
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email, "roles": roles}

@router.get("/", response_model=list[UserOut])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.debug(f"Fetching users with skip={skip}, limit={limit}")
    print(f"DEBUG: Fetching users with skip={skip}, limit={limit}", file=sys.stderr)
    
    users = crud_user.get_users(db, skip=skip, limit=limit)
    response = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": [role.id for role in user.roles] if user.roles else []
        }
        for user in users
    ]
    logger.debug(f"Users fetched: {response}")
    print(f"DEBUG: Users fetched: {response}", file=sys.stderr)
    return response

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    logger.debug(f"Updating user {user_id} with data: {user}")
    print(f"DEBUG: Updating user {user_id} with data: {user}", file=sys.stderr)
    
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    if user.username is not None:
        db_user.username = user.username
        logger.debug(f"Updated username to {user.username}")
        print(f"DEBUG: Updated username to {user.username}", file=sys.stderr)
    
    if user.email is not None:
        db_user.email = user.email
        logger.debug(f"Updated email to {user.email}")
        print(f"DEBUG: Updated email to {user.email}", file=sys.stderr)
    
    if user.roles is not None:  # Allow empty list to clear roles
        roles = db.query(Role).filter(Role.id.in_(user.roles)).all()
        if len(roles) != len(user.roles):
            missing_roles = set(user.roles) - {role.id for role in roles}
            logger.error(f"Invalid role IDs: {missing_roles}")
            print(f"ERROR: Invalid role IDs: {missing_roles}", file=sys.stderr)
            raise HTTPException(status_code=400, detail=f"Invalid role IDs: {missing_roles}")
        db_user.roles = roles
        logger.debug(f"Updated roles to {[role.id for role in roles]}")
        print(f"DEBUG: Updated roles to {[role.id for role in roles]}", file=sys.stderr)
    
    db.commit()
    db.refresh(db_user)
    db_user_roles = [role.id for role in db_user.roles] if db_user.roles else []
    
    response = {"id": db_user.id, "username": db_user.username, "email": db_user.email, "roles": db_user_roles}
    logger.debug(f"User updated: {response}")
    print(f"DEBUG: User updated: {response}", file=sys.stderr)
    return response

@router.put("/{user_id}/password", response_model=UserOut)
def change_user_password(user_id: int, user: UserPasswordChange, db: Session = Depends(get_db)):
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.set_password(user.password)
    db.commit()
    db.refresh(db_user)
    roles = [role.id for role in db_user.roles] if db_user.roles else []
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email, "roles": roles}

@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}
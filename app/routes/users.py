from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate, UserPasswordChange, ForgotPasswordRequest
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
    
    # Check if username already exists
    db_user = crud_user.get_user_by_username(db, user.username)
    if db_user:
        logger.warning(f"Username {user.username} already registered")
        print(f"WARN: Username {user.username} already registered", file=sys.stderr)
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Validate role IDs if provided
    if user.roles:
        roles = db.query(Role).filter(Role.id.in_(user.roles)).all()
        if len(roles) != len(user.roles):
            existing_role_ids = {role.id for role in roles}
            invalid_role_ids = set(user.roles) - existing_role_ids
            logger.error(f"Invalid role IDs: {invalid_role_ids}")
            print(f"ERROR: Invalid role IDs: {invalid_role_ids}", file=sys.stderr)
            raise HTTPException(status_code=400, detail=f"Invalid role IDs: {invalid_role_ids}")
    
    new_user = crud_user.create_user(db, user)
    logger.debug("User created, committing to database")
    db.commit()
    db.refresh(new_user)
    
    roles_response = [{"id": role.id, "name": role.name} for role in new_user.roles] if new_user.roles else []
    
    response = {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "roles": roles_response
    }
    logger.debug(f"Response prepared: {response}")
    print(f"DEBUG: Response prepared: {response}", file=sys.stderr)
    
    return response

@router.get("/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    roles = [{"id": role.id, "name": role.name} for role in db_user.roles] if db_user.roles else []
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
            "roles": [{"id": role.id, "name": role.name} for role in user.roles] if user.roles else []
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
    
    # Update username if provided
    if user.username is not None:
        db_user.username = user.username
        logger.debug(f"Updated username to {user.username}")
        print(f"DEBUG: Updated username to {user.username}", file=sys.stderr)
    
    # Update email if provided
    if user.email is not None:
        db_user.email = user.email
        logger.debug(f"Updated email to {user.email}")
        print(f"DEBUG: Updated email to {user.email}", file=sys.stderr)
    
    # Update roles if provided
    if user.roles is not None:
        # Allow empty list to clear roles
        if user.roles:
            roles = db.query(Role).filter(Role.id.in_(user.roles)).all()
            if len(roles) != len(user.roles):
                existing_role_ids = {role.id for role in roles}
                invalid_role_ids = set(user.roles) - existing_role_ids
                logger.error(f"Invalid role IDs: {invalid_role_ids}")
                print(f"ERROR: Invalid role IDs: {invalid_role_ids}", file=sys.stderr)
                raise HTTPException(status_code=400, detail=f"Invalid role IDs: {invalid_role_ids}")
            db_user.roles = roles
        else:
            db_user.roles = []
        logger.debug(f"Updated roles to {[role.id for role in db_user.roles]}")
        print(f"DEBUG: Updated roles to {[role.id for role in db_user.roles]}", file=sys.stderr)
    
    db.commit()
    db.refresh(db_user)
    
    # Fix: Return roles with both id and name to match UserOut schema
    roles_response = [{"id": role.id, "name": role.name} for role in db_user.roles] if db_user.roles else []
    response = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "roles": roles_response
    }
    logger.debug(f"User updated: {response}")
    print(f"DEBUG: User updated: {response}", file=sys.stderr)
    return response

@router.post("/change-password", response_model=UserOut)
def change_user_password(user: UserPasswordChange, db: Session = Depends(get_db)):
    logger.debug(f"Password change request for username: {user.username}")
    
    # Validate that the username exists
    db_user = crud_user.get_user_by_username(db, user.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="Username not found")
    
    # Password confirmation is already validated by Pydantic
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

@router.post("/forgot-password", response_model=dict)
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    logger.debug(f"Forgot password request for email: {req.email}")
    
    from app.models.user import User
    db_user = db.query(User).filter(User.email == req.email).first()
    if db_user:
        return {"detail": "Email is valid"}
    
    raise HTTPException(status_code=404, detail="Email is invalid")
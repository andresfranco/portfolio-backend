from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.role import RoleBase, RoleOut
from app.crud import role as crud_role

router = APIRouter()

@router.post("/", response_model=RoleOut)
def create_role_endpoint(role: RoleBase, db: Session = Depends(get_db)):
    db_role = crud_role.get_role_by_name(db, role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    return crud_role.create_role(db, role.name, role.description)

@router.get("/{role_id}", response_model=RoleOut)
def read_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud_role.get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/", response_model=list[RoleOut])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_role.get_roles(db, skip=skip, limit=limit)

@router.delete("/{role_id}", response_model=dict)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud_role.get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(db_role)
    db.commit()
    return {"detail": "Role deleted"}

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


@router.get("/", response_model=schemas.PaginatedResponse[schemas.Portfolio])
def read_portfolios(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    filters: Optional[List[schemas.portfolio.Filter]] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve portfolios with pagination.
    """
    check_admin_access(current_user)
    
    portfolios, total = crud.portfolio.get_portfolios_paginated(
        db, page=page, page_size=page_size, filters=filters, 
        sort_field=sort_field, sort_order=sort_order
    )
    
    return {
        "items": portfolios,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=schemas.Portfolio)
def create_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_in: schemas.PortfolioCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new portfolio.
    """
    check_admin_access(current_user)
    
    portfolio = crud.portfolio.create_portfolio(db, portfolio=portfolio_in)
    return portfolio


@router.get("/{portfolio_id}", response_model=schemas.Portfolio)
def read_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get portfolio by ID.
    """
    check_admin_access(current_user)
    
    portfolio = crud.portfolio.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    return portfolio


@router.put("/{portfolio_id}", response_model=schemas.Portfolio)
def update_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    portfolio_in: schemas.PortfolioUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a portfolio.
    """
    check_admin_access(current_user)
    
    portfolio = crud.portfolio.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    
    portfolio = crud.portfolio.update_portfolio(db, portfolio_id=portfolio_id, portfolio=portfolio_in)
    return portfolio


@router.delete("/{portfolio_id}", response_model=schemas.Portfolio)
def delete_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a portfolio.
    """
    check_admin_access(current_user)
    
    portfolio = crud.portfolio.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    
    portfolio = crud.portfolio.delete_portfolio(db, portfolio_id=portfolio_id)
    return portfolio


@router.post("/{portfolio_id}/images", response_model=schemas.PortfolioImage)
async def upload_portfolio_image(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    category: str = Query(..., description="Image category"),
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload an image for a portfolio.
    """
    check_admin_access(current_user)
    
    portfolio = crud.portfolio.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.STATIC_DIR, "uploads", "portfolios", str(portfolio_id))
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
    relative_path = os.path.join("uploads", "portfolios", str(portfolio_id), unique_filename)
    
    # Create portfolio image in database
    portfolio_image = crud.portfolio.add_portfolio_image(
        db, 
        portfolio_id=portfolio_id, 
        image=schemas.PortfolioImageCreate(
            image_path=relative_path,
            category=category
        )
    )
    
    return portfolio_image


@router.delete("/{portfolio_id}/images/{image_id}", response_model=schemas.PortfolioImage)
def delete_portfolio_image(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    image_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a portfolio image.
    """
    check_admin_access(current_user)
    
    portfolio = crud.portfolio.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    
    portfolio_image = crud.portfolio.delete_portfolio_image(db, image_id=image_id)
    if not portfolio_image:
        raise HTTPException(
            status_code=404,
            detail="Portfolio image not found",
        )
    
    # Delete the file if it exists
    if portfolio_image.image_path:
        file_path = os.path.join(settings.STATIC_DIR, portfolio_image.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return portfolio_image

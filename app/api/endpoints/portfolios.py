from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any, List, Optional
import os
import uuid
from datetime import datetime
from app.crud import portfolio as portfolio_crud
from app.schemas.portfolio import PortfolioOut as Portfolio,PaginatedPortfolioResponse,PortfolioCreate,PortfolioUpdate,PortfolioImageOut
from app.models.portfolio import Portfolio as PortfolioModel
from app.api import deps
from app.core.config import settings
import logging
import sys

router = APIRouter()
# Set up logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)



@router.get("/", response_model=List[str])
def list_portfolio_names(
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get list of all portfolios.
    """
    logger.debug("Fetching all portfolio names")
    portfolios = portfolio_crud.get_portfolios(db)
    return [portfolio.name for portfolio in portfolios]


@router.post("/", response_model=Portfolio)
def create_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_in: PortfolioCreate,
) -> Any:
    """
    Create new portfolio.
    """
    portfolio = portfolio_crud.create_portfolio(db, portfolio=portfolio_in)
    return portfolio


@router.get("/full", response_model=PaginatedPortfolioResponse)
def read_portfolios_full(
    page: int = Query(1, gt=0),
    pageSize: int = Query(10, gt=0, le=100),
    name: Optional[str] = None,
    description: Optional[str] = None,
    filterField: Optional[List[str]] = Query(None),
    filterValue: Optional[List[str]] = Query(None),
    filterOperator: Optional[List[str]] = Query(None),
    sortField: Optional[str] = None,
    sortOrder: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get paginated list of portfolios with full details.
    Supports both direct parameters (name, description) and 
    filter parameters (filterField, filterValue, filterOperator).
    """
    # Process filter parameters if they exist
    name_filter = name
    description_filter = description
    
    # If filter parameters are provided, use them instead of direct parameters
    if filterField and filterValue:
        for i, field in enumerate(filterField):
            if i < len(filterValue):
                if field == 'name' and not name_filter:
                    name_filter = filterValue[i]
                elif field == 'description' and not description_filter:
                    description_filter = filterValue[i]
    
    try:
        filters = []
        
        if name_filter:
            filters.append(schemas.portfolio.Filter(field="name", value=name_filter, operator="contains"))
        
        if description_filter:
            filters.append(schemas.portfolio.Filter(field="description", value=description_filter, operator="contains"))
        
        portfolios, total = portfolio_crud.get_portfolios_paginated(
            db=db,
            page=page,
            page_size=pageSize,
            filters=filters,
            sort_field=sortField,
            sort_order=sortOrder
        )
        
        return {
            "items": portfolios,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting portfolios: {str(e)}"
        )




@router.get("/{portfolio_id}", response_model=Portfolio)
def read_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
) -> Any:
    """
    Get portfolio by ID.
    """
    portfolio = crud.portfolio.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    return portfolio


@router.put("/{portfolio_id}", response_model=Portfolio)
def update_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    portfolio_in: PortfolioUpdate,
) -> Any:
    """
    Update a portfolio.
    """
    portfolio = portfolio_crud.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    
    portfolio = portfolio_crud.update_portfolio(db, portfolio_id=portfolio_id, portfolio=portfolio_in)
    return portfolio


@router.delete("/{portfolio_id}", response_model=Portfolio)
def delete_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
) -> Any:
    """
    Delete a portfolio.
    """
    portfolio = portfolio_crud.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    
    portfolio = portfolio_crud.delete_portfolio(db, portfolio_id=portfolio_id)
    return portfolio


@router.post("/{portfolio_id}/images", response_model=PortfolioImageOut)
async def upload_portfolio_image(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    category: str = Query(..., description="Image category"),
    file: UploadFile = File(...),
) -> Any:
    """
    Upload an image for a portfolio.
    """
    portfolio = portfolio_crud.get_portfolio(db, portfolio_id=portfolio_id)
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


@router.delete("/{portfolio_id}/images/{image_id}", response_model=PortfolioImageOut)
def delete_portfolio_image(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    image_id: int,
) -> Any:
    """
    Delete a portfolio image.
    """
    portfolio = portfolio_crud.get_portfolio(db, portfolio_id=portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    
    portfolio_image = portfolio_crud.delete_portfolio_image(db, image_id=image_id)
    if not portfolio_image:
        raise HTTPException(
            status_code=404,
            detail="Portfolio image not found",
        )
    
    # Delete the file from the filesystem
    if portfolio_image.image_path:
        file_path = os.path.join(settings.STATIC_DIR, portfolio_image.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return portfolio_image

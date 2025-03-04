from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.portfolio import Portfolio, PortfolioImage
from app.models.language import Language
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate, PortfolioImageCreate, Filter
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

# CRUD Functions
def get_portfolio(db: Session, portfolio_id: int):
    logger.debug(f"Fetching portfolio with ID {portfolio_id}")
    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

def create_portfolio(db: Session, portfolio: PortfolioCreate):
    logger.debug(f"Starting portfolio creation with name {portfolio.name}")
    
    # Create the portfolio
    db_portfolio = Portfolio(
        name=portfolio.name,
        description=portfolio.description
    )
    db.add(db_portfolio)
    db.flush()  # Flush to get the portfolio ID
    
    # Create portfolio images if provided
    if portfolio.images:
        for image_data in portfolio.images:
            db_portfolio_image = PortfolioImage(
                portfolio_id=db_portfolio.id,
                image_path=image_data.image_path,
                category=image_data.category
            )
            db.add(db_portfolio_image)
    
    logger.debug("Portfolio added to session")
    return db_portfolio

def update_portfolio(db: Session, portfolio_id: int, portfolio: PortfolioUpdate):
    logger.debug(f"Updating portfolio with ID {portfolio_id}")
    db_portfolio = get_portfolio(db, portfolio_id)
    
    if not db_portfolio:
        return None
    
    # Update fields if provided
    if portfolio.name is not None:
        db_portfolio.name = portfolio.name
    
    if portfolio.description is not None:
        db_portfolio.description = portfolio.description
    
    return db_portfolio

def delete_portfolio(db: Session, portfolio_id: int):
    logger.debug(f"Deleting portfolio with ID {portfolio_id}")
    db_portfolio = get_portfolio(db, portfolio_id)
    
    if not db_portfolio:
        return None
    
    # Delete associated images
    db.query(PortfolioImage).filter(PortfolioImage.portfolio_id == portfolio_id).delete()
    
    # Delete the portfolio
    db.delete(db_portfolio)
    return db_portfolio

def add_portfolio_image(db: Session, portfolio_id: int, image: PortfolioImageCreate):
    logger.debug(f"Adding image to portfolio with ID {portfolio_id}")
    db_portfolio = get_portfolio(db, portfolio_id)
    
    if not db_portfolio:
        return None
    
    db_portfolio_image = PortfolioImage(
        portfolio_id=portfolio_id,
        image_path=image.image_path,
        category=image.category
    )
    db.add(db_portfolio_image)
    db.flush()
    
    return db_portfolio_image

def delete_portfolio_image(db: Session, image_id: int):
    logger.debug(f"Deleting portfolio image with ID {image_id}")
    db_image = db.query(PortfolioImage).filter(PortfolioImage.id == image_id).first()
    
    if not db_image:
        return None
    
    db.delete(db_image)
    return db_image

def get_portfolios(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching portfolios with skip={skip}, limit={limit}")
    return db.query(Portfolio).offset(skip).limit(limit).all()

def get_portfolios_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Portfolio], int]:
    query = db.query(Portfolio)
    
    if filters:
        for filter_item in filters:
            if hasattr(Portfolio, filter_item.field):
                column = getattr(Portfolio, filter_item.field)
                if filter_item.operator == "contains":
                    query = query.filter(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    query = query.filter(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    query = query.filter(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    query = query.filter(column.ilike(f"%{filter_item.value}"))
    
    total = query.count()
    
    if sort_field and hasattr(Portfolio, sort_field):
        sort_func = asc if sort_order == "asc" else desc
        query = query.order_by(sort_func(getattr(Portfolio, sort_field)))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

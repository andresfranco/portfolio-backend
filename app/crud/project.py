from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models.project import Project, ProjectText, ProjectImage, ProjectAttachment
from app.models.category import Category
from app.models.skill import Skill
from app.models.language import Language
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectTextCreate, ProjectImageCreate, ProjectAttachmentCreate, Filter
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
def get_project(db: Session, project_id: int):
    logger.debug(f"Fetching project with ID {project_id}")
    return db.query(Project).filter(Project.id == project_id).first()

def create_project(db: Session, project: ProjectCreate):
    logger.debug(f"Starting project creation with {len(project.project_texts)} texts")
    
    # Create the project
    db_project = Project(
        repository_url=project.repository_url,
        website_url=project.website_url
    )
    db.add(db_project)
    db.flush()  # Flush to get the project ID
    
    # Add categories if provided
    if project.categories:
        categories = db.query(Category).filter(Category.id.in_(project.categories)).all()
        if len(categories) != len(project.categories):
            missing_categories = set(project.categories) - {cat.id for cat in categories}
            logger.error(f"Invalid category IDs: {missing_categories}")
            raise ValueError(f"Invalid category IDs: {missing_categories}")
        db_project.categories = categories
    
    # Add skills if provided
    if project.skills:
        skills = db.query(Skill).filter(Skill.id.in_(project.skills)).all()
        if len(skills) != len(project.skills):
            missing_skills = set(project.skills) - {skill.id for skill in skills}
            logger.error(f"Invalid skill IDs: {missing_skills}")
            raise ValueError(f"Invalid skill IDs: {missing_skills}")
        db_project.skills = skills
    
    # Create project texts
    for text_data in project.project_texts:
        # Verify language exists
        language = db.query(Language).filter(Language.id == text_data.language_id).first()
        if not language:
            logger.error(f"Invalid language ID: {text_data.language_id}")
            raise ValueError(f"Invalid language ID: {text_data.language_id}")
        
        db_project_text = ProjectText(
            project_id=db_project.id,
            language_id=text_data.language_id,
            name=text_data.name,
            description=text_data.description
        )
        db.add(db_project_text)
    
    # Create project images if provided
    if project.images:
        for image_data in project.images:
            db_project_image = ProjectImage(
                project_id=db_project.id,
                image_path=image_data.image_path,
                category=image_data.category
            )
            db.add(db_project_image)
    
    # Create project attachments if provided
    if project.attachments:
        for attachment_data in project.attachments:
            db_project_attachment = ProjectAttachment(
                project_id=db_project.id,
                file_path=attachment_data.file_path,
                file_name=attachment_data.file_name
            )
            db.add(db_project_attachment)
    
    logger.debug("Project added to session")
    return db_project

def update_project(db: Session, project_id: int, project: ProjectUpdate):
    logger.debug(f"Updating project with ID {project_id}")
    db_project = get_project(db, project_id)
    
    if not db_project:
        return None
    
    # Update fields if provided
    if project.repository_url is not None:
        db_project.repository_url = project.repository_url
    
    if project.website_url is not None:
        db_project.website_url = project.website_url
    
    # Update categories if provided
    if project.categories is not None:
        categories = db.query(Category).filter(Category.id.in_(project.categories)).all()
        if len(categories) != len(project.categories):
            missing_categories = set(project.categories) - {cat.id for cat in categories}
            logger.error(f"Invalid category IDs: {missing_categories}")
            raise ValueError(f"Invalid category IDs: {missing_categories}")
        db_project.categories = categories
    
    # Update skills if provided
    if project.skills is not None:
        skills = db.query(Skill).filter(Skill.id.in_(project.skills)).all()
        if len(skills) != len(project.skills):
            missing_skills = set(project.skills) - {skill.id for skill in skills}
            logger.error(f"Invalid skill IDs: {missing_skills}")
            raise ValueError(f"Invalid skill IDs: {missing_skills}")
        db_project.skills = skills
    
    # Update project texts if provided
    if project.project_texts is not None:
        # First, remove existing texts
        db.query(ProjectText).filter(ProjectText.project_id == project_id).delete()
        
        # Then add new texts
        for text_data in project.project_texts:
            # Verify language exists
            language = db.query(Language).filter(Language.id == text_data.language_id).first()
            if not language:
                logger.error(f"Invalid language ID: {text_data.language_id}")
                raise ValueError(f"Invalid language ID: {text_data.language_id}")
            
            db_project_text = ProjectText(
                project_id=db_project.id,
                language_id=text_data.language_id,
                name=text_data.name,
                description=text_data.description
            )
            db.add(db_project_text)
    
    return db_project

def delete_project(db: Session, project_id: int):
    logger.debug(f"Deleting project with ID {project_id}")
    db_project = get_project(db, project_id)
    
    if not db_project:
        return None
    
    # Delete associated texts, images, and attachments
    db.query(ProjectText).filter(ProjectText.project_id == project_id).delete()
    db.query(ProjectImage).filter(ProjectImage.project_id == project_id).delete()
    db.query(ProjectAttachment).filter(ProjectAttachment.project_id == project_id).delete()
    
    # Delete the project
    db.delete(db_project)
    return db_project

def add_project_image(db: Session, project_id: int, image: ProjectImageCreate):
    logger.debug(f"Adding image to project with ID {project_id}")
    db_project = get_project(db, project_id)
    
    if not db_project:
        return None
    
    db_project_image = ProjectImage(
        project_id=project_id,
        image_path=image.image_path,
        category=image.category
    )
    db.add(db_project_image)
    db.flush()
    
    return db_project_image

def delete_project_image(db: Session, image_id: int):
    logger.debug(f"Deleting project image with ID {image_id}")
    db_image = db.query(ProjectImage).filter(ProjectImage.id == image_id).first()
    
    if not db_image:
        return None
    
    db.delete(db_image)
    return db_image

def add_project_attachment(db: Session, project_id: int, attachment: ProjectAttachmentCreate):
    logger.debug(f"Adding attachment to project with ID {project_id}")
    db_project = get_project(db, project_id)
    
    if not db_project:
        return None
    
    db_project_attachment = ProjectAttachment(
        project_id=project_id,
        file_path=attachment.file_path,
        file_name=attachment.file_name
    )
    db.add(db_project_attachment)
    db.flush()
    
    return db_project_attachment

def delete_project_attachment(db: Session, attachment_id: int):
    logger.debug(f"Deleting project attachment with ID {attachment_id}")
    db_attachment = db.query(ProjectAttachment).filter(ProjectAttachment.id == attachment_id).first()
    
    if not db_attachment:
        return None
    
    db.delete(db_attachment)
    return db_attachment

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    logger.debug(f"Fetching projects with skip={skip}, limit={limit}")
    return db.query(Project).offset(skip).limit(limit).all()

def get_projects_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    filters: List[Filter] = None,
    sort_field: str = None,
    sort_order: str = "asc"
) -> Tuple[List[Project], int]:
    query = db.query(Project)
    
    # Separate category, skill, and text filters from other filters
    category_filter_values = []
    skill_filter_values = []
    text_filters = []
    other_filters = []
    
    if filters:
        for filter_item in filters:
            if filter_item.field == "category" or filter_item.field == "categories":
                logger.debug(f"Found category filter with value: {filter_item.value}")
                category_filter_values.append(filter_item.value)
            elif filter_item.field == "skill" or filter_item.field == "skills":
                logger.debug(f"Found skill filter with value: {filter_item.value}")
                skill_filter_values.append(filter_item.value)
            elif filter_item.field == "name" or filter_item.field == "description":
                text_filters.append(filter_item)
            elif hasattr(Project, filter_item.field):
                column = getattr(Project, filter_item.field)
                if filter_item.operator == "contains":
                    other_filters.append(column.ilike(f"%{filter_item.value}%"))
                elif filter_item.operator == "equals":
                    other_filters.append(column == filter_item.value)
                elif filter_item.operator == "startsWith":
                    other_filters.append(column.ilike(f"{filter_item.value}%"))
                elif filter_item.operator == "endsWith":
                    other_filters.append(column.ilike(f"%{filter_item.value}"))
    
    if other_filters:
        query = query.filter(*other_filters)
    
    # Apply category filters
    if category_filter_values:
        logger.debug(f"Filtering by categories: {category_filter_values}")
        conditions = [Category.id == int(cat_id) for cat_id in category_filter_values]
        query = query.join(Project.categories).filter(or_(*conditions)).distinct()
    
    # Apply skill filters
    if skill_filter_values:
        logger.debug(f"Filtering by skills: {skill_filter_values}")
        conditions = [Skill.id == int(skill_id) for skill_id in skill_filter_values]
        query = query.join(Project.skills).filter(or_(*conditions)).distinct()
    
    # Apply text filters
    if text_filters:
        for filter_item in text_filters:
            # Join with ProjectText to filter by name or description
            query = query.join(ProjectText)
            column = getattr(ProjectText, filter_item.field)
            if filter_item.operator == "contains":
                query = query.filter(column.ilike(f"%{filter_item.value}%"))
            elif filter_item.operator == "equals":
                query = query.filter(column == filter_item.value)
            elif filter_item.operator == "startsWith":
                query = query.filter(column.ilike(f"{filter_item.value}%"))
            elif filter_item.operator == "endsWith":
                query = query.filter(column.ilike(f"%{filter_item.value}"))
            query = query.distinct()
    
    total = query.count()
    
    if sort_field:
        if hasattr(Project, sort_field):
            sort_func = asc if sort_order == "asc" else desc
            query = query.order_by(sort_func(getattr(Project, sort_field)))
        elif sort_field in ["name", "description"]:
            # Sort by name or description in the default language
            default_language = db.query(Language).filter(Language.is_default == True).first()
            if default_language:
                query = query.join(ProjectText).filter(ProjectText.language_id == default_language.id)
                sort_func = asc if sort_order == "asc" else desc
                query = query.order_by(sort_func(getattr(ProjectText, sort_field)))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    return query.all(), total

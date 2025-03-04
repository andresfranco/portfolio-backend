from fastapi import APIRouter

from app.api.endpoints import (
    users,
    roles,
    permissions,
    languages,
    translations,
    portfolios,
    sections,
    experiences,
    projects,
    categories,
    skills,
    email
)

api_router = APIRouter()

# User management
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(email.router, prefix="/email", tags=["Email"])

# Content management
api_router.include_router(languages.router, prefix="/languages", tags=["Languages"])
api_router.include_router(translations.router, prefix="/translations", tags=["Translations"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(sections.router, prefix="/sections", tags=["Sections"])

# Portfolio content
api_router.include_router(experiences.router, prefix="/experiences", tags=["Experiences"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(skills.router, prefix="/skills", tags=["Skills"])

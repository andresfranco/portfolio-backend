import sys
import os
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware  # Add CORS middleware
from sqlalchemy.exc import SQLAlchemyError

from app.routes import users, roles, permissions
from app.core.database import SessionLocal
from app.crud.permission import initialize_core_permissions

# Print sys.path for debugging
print(f"sys.path: {sys.path}", file=sys.stderr)

# Ensure app directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
print(f"Added to sys.path: {os.path.abspath(os.path.join(os.path.dirname(__file__), 'app'))}", file=sys.stderr)

# Verify imports
try:
    from app.routes.users import router as users_router
    from app.routes.roles import router as roles_router
    from app.routes.email import router as email_router  # Add email router import
    print("Imports successful", file=sys.stderr)
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    raise

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Convert non-serializable objects in error context to string
    for error in errors:
        if 'ctx' in error and isinstance(error['ctx'], dict):
            for key, value in error['ctx'].items():
                try:
                    _ = value.__str__()
                except Exception:
                    error['ctx'][key] = str(value)
                else:
                    error['ctx'][key] = str(value)
    logger.error(f"Validation error: {exc.errors()}")
    print(f"Validation error: {exc.errors()}", file=sys.stderr)
    return JSONResponse(status_code=400, content={"detail": errors, "body": exc.body})

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    print(f"Database error: {str(exc)}", file=sys.stderr)
    return JSONResponse(status_code=500, content={"detail": "A database error occurred.", "error": str(exc)})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    print(f"Internal server error: {str(exc)}", file=sys.stderr)
    return JSONResponse(status_code=500, content={"detail": "An internal server error occurred.", "error": str(exc)})

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(roles.router, prefix="/api/roles", tags=["Roles"])
app.include_router(email_router, prefix="/api/email", tags=["Email"])  # Add email router
app.include_router(permissions.router, prefix="/api/permissions", tags=["Permissions"])
logger.debug("Routers included")

@app.on_event("startup")
async def startup_event():
    logger.debug("Initializing core permissions")
    db = SessionLocal()
    try:
        initialize_core_permissions(db)
        logger.debug("Core permissions initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing core permissions: {str(e)}")
    finally:
        db.close()

# Routes
@app.get("/")
def read_root():
    logger.debug("Root endpoint accessed")
    print("DEBUG: Root endpoint accessed", file=sys.stderr)
    return {"message": "Welcome to the Portfolio API"}

@app.get("/test-error")
async def test_error():
    logger.debug("Triggering test error")
    print("DEBUG: Triggering test error", file=sys.stderr)
    raise Exception("This is a test error")

@app.get("/debug")
def debug():
    logger.debug("Debug endpoint hit")
    print("DEBUG: Debug endpoint hit", file=sys.stderr)
    return {"status": "ok"}
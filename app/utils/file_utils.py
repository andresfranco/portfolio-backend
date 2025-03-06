import os
import shutil
import uuid
from fastapi import UploadFile
from pathlib import Path
import logging

logger = logging.getLogger("uvicorn.error")

# Define the base directory for uploads
UPLOAD_DIR = Path("uploads")
LANGUAGE_IMAGES_DIR = UPLOAD_DIR / "language_images"

# Ensure directories exist
def ensure_upload_dirs():
    """Create upload directories if they don't exist"""
    UPLOAD_DIR.mkdir(exist_ok=True)
    LANGUAGE_IMAGES_DIR.mkdir(exist_ok=True)
    logger.debug(f"Ensured upload directories exist: {UPLOAD_DIR}, {LANGUAGE_IMAGES_DIR}")

# Save an uploaded file
async def save_upload_file(upload_file: UploadFile, directory: Path = UPLOAD_DIR) -> str:
    """
    Save an uploaded file to the specified directory with a unique filename
    Returns the path to the saved file relative to the upload directory
    """
    ensure_upload_dirs()
    
    # Generate a unique filename to avoid collisions
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create the full path
    file_path = directory / unique_filename
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    logger.debug(f"Saved uploaded file to {file_path}")
    
    # Return the full path
    return str(file_path)

# Delete a file
def delete_file(file_path: str) -> bool:
    """
    Delete a file at the given path
    Returns True if successful, False otherwise
    """
    try:
        # Convert to absolute path if it's relative
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted file: {file_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False

# Get file URL
def get_file_url(file_path: str) -> str:
    """
    Convert a file path to a URL for client access
    """
    if not file_path:
        return ""
    
    # Replace backslashes with forward slashes for URL
    file_path = file_path.replace("\\", "/")
    
    # If it's a Path object or a string path, get just the filename part
    if isinstance(file_path, Path) or "/" in file_path:
        # Extract just the relative path from uploads directory
        if isinstance(file_path, str) and "uploads/" in file_path:
            file_path = file_path.split("uploads/", 1)[1]
        elif isinstance(file_path, Path):
            try:
                file_path = str(file_path.relative_to(UPLOAD_DIR.parent))
            except ValueError:
                # If it's not relative to the parent, try just the filename
                file_path = file_path.name
    
    # Remove any leading slash
    if file_path.startswith("/"):
        file_path = file_path[1:]
    
    return f"/uploads/{file_path}"

import os, sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Insert project root into sys.path so that modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import your models' Base for target_metadata
from app.core.database import Base  # This Base must include all models
# Ensure models are imported so that they get registered with Base.metadata
import app.models.user  
import app.models.role  
# ... import other models if needed ...

target_metadata = Base.metadata

# ...existing alembic configuration...

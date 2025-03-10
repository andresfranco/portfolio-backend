"""
Utility script to fix NULL code values in the experiences table.
This script directly updates the database without using migrations.
"""

import sys
import os
from sqlalchemy import create_engine, text
from app.core.database import SQLALCHEMY_DATABASE_URL

def fix_experience_codes():
    print("Connecting to database...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if the code column exists
        try:
            result = conn.execute(text("SELECT code FROM experiences LIMIT 1"))
            print("Code column exists in experiences table.")
        except Exception as e:
            print(f"Error checking code column: {e}")
            print("The code column might not exist yet. Run migrations first.")
            return
        
        # Update NULL code values
        try:
            result = conn.execute(text(
                """
                UPDATE experiences 
                SET code = 'EXP-' || id 
                WHERE code IS NULL
                """
            ))
            conn.commit()
            print(f"Updated {result.rowcount} experiences with NULL code values.")
        except Exception as e:
            print(f"Error updating code values: {e}")
            return
        
        # Verify all experiences have a code value
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM experiences WHERE code IS NULL"))
            null_count = result.scalar()
            if null_count == 0:
                print("All experiences now have a code value.")
            else:
                print(f"Warning: {null_count} experiences still have NULL code values.")
        except Exception as e:
            print(f"Error verifying code values: {e}")
            return

if __name__ == "__main__":
    fix_experience_codes() 
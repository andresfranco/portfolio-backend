"""Create category types table

Revision ID: create_category_types
Revises: 
Create Date: 2025-03-14 10:46:33.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_category_types'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create category_types table
    op.create_table(
        'category_types',
        sa.Column('code', sa.String(5), primary_key=True, index=True),
        sa.Column('name', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String()),
        sa.Column('updated_by', sa.String())
    )
    
    # Create index
    op.create_index(op.f('ix_category_types_code'), 'category_types', ['code'], unique=True)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_category_types_code'), table_name='category_types')
    
    # Drop tables
    op.drop_table('category_types')

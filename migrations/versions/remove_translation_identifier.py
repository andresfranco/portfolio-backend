"""Remove translation_identifier from sections

Revision ID: 7a8bc9def456
Revises: 62b987ae72f3
Create Date: 2025-03-10 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a8bc9def456'
down_revision = '62b987ae72f3'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the translation_identifier column from the sections table
    op.drop_column('sections', 'translation_identifier')


def downgrade():
    # Add the translation_identifier column back to the sections table
    op.add_column('sections', sa.Column('translation_identifier', sa.String(), nullable=True))
    op.create_index(op.f('ix_sections_translation_identifier'), 'sections', ['translation_identifier'], unique=False)

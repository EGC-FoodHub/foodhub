"""Merge heads

Revision ID: 0afb187a38df
Revises: fd895fb8a9b3, f35b3d8bb0ee
Create Date: 2025-12-12 17:02:14.327819

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006"
down_revision = ("002", "005")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

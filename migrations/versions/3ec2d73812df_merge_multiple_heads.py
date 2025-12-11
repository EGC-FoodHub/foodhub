"""Merge multiple heads

Revision ID: 3ec2d73812df
Revises: fd895fb8a9b3, f35b3d8bb0ee
Create Date: 2025-12-11 14:11:41.587348

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ec2d73812df'
down_revision = ('fd895fb8a9b3', 'f35b3d8bb0ee')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

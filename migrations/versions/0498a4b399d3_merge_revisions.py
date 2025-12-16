"""merge revisions

Revision ID: 0498a4b399d3
Revises: c1addf000001, ac9e4c075145
Create Date: 2025-12-16 00:19:15.118798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0498a4b399d3'
down_revision = ('c1addf000001', 'ac9e4c075145')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

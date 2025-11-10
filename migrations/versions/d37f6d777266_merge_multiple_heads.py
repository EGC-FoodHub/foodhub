"""Merge multiple heads

Revision ID: d37f6d777266
Revises: 775f59704dcc, b007fa5e6a49
Create Date: 2025-11-10 18:19:50.390907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd37f6d777266'
down_revision = ('775f59704dcc', 'b007fa5e6a49')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

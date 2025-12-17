"""Set server defaults for food_model counters

Revision ID: c1addf000001
Revises: b9b7f834559e
Create Date: 2025-12-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    # ensure no NULLs exist
    op.execute("UPDATE food_model SET download_count = 0 WHERE download_count IS NULL")
    op.execute("UPDATE food_model SET view_count = 0 WHERE view_count IS NULL")

    # set server default to 0
    with op.batch_alter_table("food_model") as batch_op:
        batch_op.alter_column("download_count", existing_type=sa.Integer(), nullable=False, server_default=sa.text("0"))
        batch_op.alter_column("view_count", existing_type=sa.Integer(), nullable=False, server_default=sa.text("0"))


def downgrade():
    with op.batch_alter_table("food_model") as batch_op:
        batch_op.alter_column("download_count", existing_type=sa.Integer(), nullable=False, server_default=None)
        batch_op.alter_column("view_count", existing_type=sa.Integer(), nullable=False, server_default=None)

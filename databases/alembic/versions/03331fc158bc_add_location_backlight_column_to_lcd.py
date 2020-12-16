"""Add location_backlight column to lcd

Revision ID: 03331fc158bc
Revises: 782b86a98efe
Create Date: 2020-12-15 20:02:22.020495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '03331fc158bc'
down_revision = '782b86a98efe'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column(sa.Column('location_backlight', sa.String))


def downgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.drop_column('location_backlight')

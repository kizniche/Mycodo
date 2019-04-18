"""add pin_reset for lcd

Revision ID: 7a9b3cea5c06
Revises: f9ddbe510462
Create Date: 2019-04-17 18:21:59.270010

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a9b3cea5c06'
down_revision = 'f9ddbe510462'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column(sa.Column('pin_reset', sa.Integer))


def downgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.drop_column('pin_reset')

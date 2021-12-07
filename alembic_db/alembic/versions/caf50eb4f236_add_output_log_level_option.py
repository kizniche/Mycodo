"""Add Output Log Level option

Revision ID: caf50eb4f236
Revises: e5bd30e798b8
Create Date: 2020-05-09 15:03:50.417803

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'caf50eb4f236'
down_revision = 'e5bd30e798b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))


def downgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('log_level_debug')

"""Add invert option

Revision ID: 82ee046fbf9b
Revises: 70c828e05255
Create Date: 2019-01-28 18:24:25.423767

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82ee046fbf9b'
down_revision = '70c828e05255'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.add_column(sa.Column('option_invert', sa.Boolean))


def downgrade():
    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.drop_column('option_invert')

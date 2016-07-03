"""Add reset period to edge detection

Revision ID: c8ae8ea703af
Revises: d549de374d71
Create Date: 2016-06-29 23:17:52.132705

"""

# revision identifiers, used by Alembic.
revision = 'c8ae8ea703af'
down_revision = 'd549de374d71'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('switch_reset_period', sa.INT))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('switch_reset_period')

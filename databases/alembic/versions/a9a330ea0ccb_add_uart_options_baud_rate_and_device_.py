"""Add UART options: baud rate and device location

Revision ID: a9a330ea0ccb
Revises: f1c6b2901d45
Create Date: 2017-04-24 15:42:56.338401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9a330ea0ccb'
down_revision = 'f1c6b2901d45'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('baud_rate', sa.INTEGER))
        batch_op.add_column(sa.Column('device_loc', sa.TEXT))
        batch_op.add_column(sa.Column('interface', sa.TEXT))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('baud_rate')
        batch_op.drop_column('device_loc')
        batch_op.drop_column('interface')

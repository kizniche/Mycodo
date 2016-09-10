"""Add sine wave variables to methods table

Revision ID: 054aacc97ae8
Revises: b62c62a93a7d
Create Date: 2016-09-09 23:20:38.351021

"""

# revision identifiers, used by Alembic.
revision = '054aacc97ae8'
down_revision = 'b62c62a93a7d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("method") as batch_op:
        batch_op.add_column(sa.Column('amplitude', sa.REAL))
        batch_op.add_column(sa.Column('frequency', sa.REAL))
        batch_op.add_column(sa.Column('shift_angle', sa.REAL))
        batch_op.add_column(sa.Column('shift_y', sa.REAL))


def downgrade():
    with op.batch_alter_table("method") as batch_op:
        batch_op.drop_column('amplitude')
        batch_op.drop_column('frequency')
        batch_op.drop_column('shift_angle')
        batch_op.drop_column('shift_y')

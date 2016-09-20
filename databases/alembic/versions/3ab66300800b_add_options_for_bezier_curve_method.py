"""Add options for Bezier curve method

Revision ID: 3ab66300800b
Revises: 2445c9b1bf3a
Create Date: 2016-09-20 16:17:19.099397

"""

# revision identifiers, used by Alembic.
revision = '3ab66300800b'
down_revision = '2445c9b1bf3a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("method") as batch_op:
        batch_op.add_column(sa.Column('x0', sa.REAL))
        batch_op.add_column(sa.Column('y0', sa.REAL))
        batch_op.add_column(sa.Column('x1', sa.REAL))
        batch_op.add_column(sa.Column('y1', sa.REAL))
        batch_op.add_column(sa.Column('x2', sa.REAL))
        batch_op.add_column(sa.Column('y2', sa.REAL))
        batch_op.add_column(sa.Column('x3', sa.REAL))
        batch_op.add_column(sa.Column('y3', sa.REAL))


def downgrade():
    with op.batch_alter_table("method") as batch_op:
        batch_op.drop_column('x0')
        batch_op.drop_column('y0')
        batch_op.drop_column('x1')
        batch_op.drop_column('y1')
        batch_op.drop_column('x2')
        batch_op.drop_column('y2')
        batch_op.drop_column('x3')
        batch_op.drop_column('y3')

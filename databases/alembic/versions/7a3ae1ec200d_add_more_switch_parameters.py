"""Add more switch parameters

Revision ID: 7a3ae1ec200d
Revises: c6efd02bdf96
Create Date: 2016-06-29 19:21:08.311035

"""

# revision identifiers, used by Alembic.
revision = '7a3ae1ec200d'
down_revision = 'c6efd02bdf96'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('switch_edge', sa.TEXT))
        batch_op.add_column(sa.Column('switch_bouncetime', sa.INT))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('switch_edge')
        batch_op.drop_column('switch_bouncetime')

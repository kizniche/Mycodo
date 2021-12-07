"""Add position to Input table

Revision ID: b8ff72b5c2c9
Revises: 37509b846483
Create Date: 2021-06-26 19:51:11.005360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8ff72b5c2c9'
down_revision = '37509b846483'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('position_y', sa.Integer))

    op.execute(
        '''
        UPDATE input
        SET position_y=0
        '''
    )


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('position_y')

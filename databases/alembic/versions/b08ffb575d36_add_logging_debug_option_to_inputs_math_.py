"""Add logging debug option to Inputs/Math/etc

Revision ID: b08ffb575d36
Revises: 7a9b3cea5c06
Create Date: 2019-04-30 13:53:35.296501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b08ffb575d36'
down_revision = '7a9b3cea5c06'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    op.execute(
        '''
        UPDATE input
        SET log_level_debug=0
        '''
    )

    with op.batch_alter_table("math") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    op.execute(
        '''
        UPDATE math
        SET log_level_debug=0
        '''
    )

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    op.execute(
        '''
        UPDATE pid
        SET log_level_debug=0
        '''
    )

    with op.batch_alter_table("trigger") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    op.execute(
        '''
        UPDATE trigger
        SET log_level_debug=0
        '''
    )

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    op.execute(
        '''
        UPDATE conditional
        SET log_level_debug=0
        '''
    )


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('log_level_debug')

    with op.batch_alter_table("math") as batch_op:
        batch_op.drop_column('log_level_debug')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('log_level_debug')

    with op.batch_alter_table("trigger") as batch_op:
        batch_op.drop_column('log_level_debug')

    with op.batch_alter_table("trigger") as batch_op:
        batch_op.drop_column('log_level_debug')

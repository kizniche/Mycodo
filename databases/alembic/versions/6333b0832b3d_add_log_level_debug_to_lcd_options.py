"""Add log_level_debug to LCD options

Revision ID: 6333b0832b3d
Revises: 2c3b61fdb239
Create Date: 2019-06-11 20:21:55.845740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6333b0832b3d'
down_revision = '2c3b61fdb239'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    op.execute(
        '''
        UPDATE lcd
        SET log_level_debug=0
        '''
    )


def downgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.drop_column('log_level_debug')

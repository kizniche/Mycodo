"""Add Dashboard element options

Revision ID: 1031452acfc9
Revises: 06f149fb3fd6
Create Date: 2018-02-20 14:51:05.403258

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1031452acfc9'
down_revision = '06f149fb3fd6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('decimal_places', sa.Integer))
        batch_op.add_column(sa.Column('enable_pid_info', sa.Boolean))


    op.execute(
        '''
        UPDATE graph
        SET decimal_places=1
        '''
    )


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('decimal_places')
        batch_op.drop_column('enable_pid_info')

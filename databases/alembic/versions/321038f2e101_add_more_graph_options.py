"""Add more Graph options

Revision ID: 321038f2e101
Revises: d0757b2ecd33
Create Date: 2017-11-20 16:47:48.886204

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '321038f2e101'
down_revision = 'd0757b2ecd33'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('enable_title', sa.Boolean))
        batch_op.add_column(sa.Column('enable_auto_refresh', sa.Boolean))

    op.execute(
        '''
        UPDATE graph
        SET enable_auto_refresh=1
        '''
    )

    op.execute(
        '''
        UPDATE graph
        SET enable_title=0
        '''
    )


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('enable_title')
        batch_op.drop_column('enable_auto_refresh')

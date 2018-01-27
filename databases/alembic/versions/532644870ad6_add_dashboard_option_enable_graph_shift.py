"""Add Dashboard option enable_graph_shift

Revision ID: 532644870ad6
Revises: b7acb4de5e00
Create Date: 2018-01-27 17:12:55.542872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '532644870ad6'
down_revision = 'b7acb4de5e00'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('enable_graph_shift', sa.Boolean))

    op.execute(
        '''
        UPDATE graph
        SET enable_graph_shift=0
        WHERE enable_graph_shift IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('enable_graph_shift')


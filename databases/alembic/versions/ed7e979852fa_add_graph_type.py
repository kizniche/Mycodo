"""Add graph type

Revision ID: ed7e979852fa
Revises: c7b4a120a7bb
Create Date: 2017-09-15 17:31:54.579033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed7e979852fa'
down_revision = 'c7b4a120a7bb'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('graph_type', sa.Text))
        batch_op.add_column(sa.Column('y_axis_min', sa.Float))
        batch_op.add_column(sa.Column('y_axis_max', sa.Float))
        batch_op.add_column(sa.Column('max_measure_age', sa.Float))
        batch_op.add_column(sa.Column('range_colors', sa.Text))

    op.execute(
        '''
        UPDATE graph
        SET graph_type='graph'
        WHERE graph_type IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('graph_type')
        batch_op.drop_column('y_axis_min')
        batch_op.drop_column('y_axis_max')
        batch_op.drop_column('max_measure_age')
        batch_op.drop_column('range_colors')

"""add Python Code widget options

Revision ID: d66e33093e8e
Revises: 4d3258ef5864
Create Date: 2020-07-30 10:04:55.625878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd66e33093e8e'
down_revision = '4d3258ef5864'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("widget") as batch_op:
        batch_op.add_column(sa.Column('code_execute_loop', sa.String))
        batch_op.add_column(sa.Column('code_execute_single', sa.String))

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('sample_rate_controller_widget', sa.Float))

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_widget=0.25
        '''
    )


def downgrade():
    with op.batch_alter_table("widget") as batch_op:
        batch_op.drop_column('code_execute_loop')
        batch_op.drop_column('code_execute_single')

    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('sample_rate_controller_widget')

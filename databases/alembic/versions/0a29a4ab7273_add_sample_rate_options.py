"""Add sample rate options

Revision ID: 0a29a4ab7273
Revises: c10d401e574c
Create Date: 2018-04-23 21:03:55.214844

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a29a4ab7273'
down_revision = 'c10d401e574c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('sample_rate_controller_conditional', sa.Float))
        batch_op.add_column(sa.Column('sample_rate_controller_input', sa.Float))
        batch_op.add_column(sa.Column('sample_rate_controller_math', sa.Float))
        batch_op.add_column(sa.Column('sample_rate_controller_output', sa.Float))
        batch_op.add_column(sa.Column('sample_rate_controller_pid', sa.Float))

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_conditional=0.25
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_input=0.1
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_math=0.25
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_output=0.05
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_pid=0.1
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('sample_rate_controller_conditional')
        batch_op.drop_column('sample_rate_controller_input')
        batch_op.drop_column('sample_rate_controller_math')
        batch_op.drop_column('sample_rate_controller_output')
        batch_op.drop_column('sample_rate_controller_pid')

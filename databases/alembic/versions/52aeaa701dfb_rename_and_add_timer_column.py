"""rename and add timer column

Revision ID: 52aeaa701dfb
Revises: 25b4c7b9969e
Create Date: 2016-10-02 16:49:42.128061

"""

# revision identifiers, used by Alembic.
revision = '52aeaa701dfb'
down_revision = '25b4c7b9969e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("timer") as batch_op:
        batch_op.add_column(sa.Column('time_end', sa.TEXT))
        batch_op.add_column(sa.Column('timer_type', sa.TEXT))
        batch_op.alter_column("time_on", new_column_name="time_start")

    op.execute(
        '''
        UPDATE timer
        SET timer_type='duration'
        WHERE time_start IS ''
        '''
    )

    op.execute(
        '''
        UPDATE timer
        SET timer_type='time'
        WHERE time_start IS NOT ''
        '''
    )


def downgrade():
    with op.batch_alter_table("timer") as batch_op:
        batch_op.drop_column('time_end')
        batch_op.drop_column('timer_type')
        batch_op.alter_column("time_start", new_column_name="time_on")

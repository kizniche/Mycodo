"""Add method_id as option for new PWM Timer

Revision ID: 214c6bb4603a
Revises: f4c0693f12a4
Create Date: 2017-10-31 20:17:36.094703

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '214c6bb4603a'
down_revision = 'f4c0693f12a4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("timer") as batch_op:
        batch_op.add_column(sa.Column('method_id', sa.Integer))
        batch_op.add_column(sa.Column('timer_type_main', sa.Text))

    op.execute(
        '''
        UPDATE timer
        SET timer_type_main='relay'
        WHERE timer_type_main IS NULL
        '''
    )

def downgrade():
    with op.batch_alter_table("timer") as batch_op:
        batch_op.drop_column('method_id')
        batch_op.drop_column('timer_type_main')

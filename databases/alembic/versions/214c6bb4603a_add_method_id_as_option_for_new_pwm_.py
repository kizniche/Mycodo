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
        batch_op.add_column(sa.Column('method_start_time', sa.Text))
        batch_op.add_column(sa.Column('method_end_time', sa.Text))
        batch_op.add_column(sa.Column('method_period', sa.Float))

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('method_start_time', sa.Text))
        batch_op.add_column(sa.Column('method_end_time', sa.Text))

    with op.batch_alter_table("method") as batch_op:
        batch_op.drop_column('start_time')
        batch_op.drop_column('end_time')


def downgrade():
    with op.batch_alter_table("timer") as batch_op:
        batch_op.drop_column('method_id')
        batch_op.drop_column('method_start_time')
        batch_op.drop_column('method_end_time')
        batch_op.drop_column('method_period')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('method_id')
        batch_op.drop_column('method_start_time')
        batch_op.drop_column('method_end_time')

    with op.batch_alter_table("method") as batch_op:
        batch_op.drop_column('start_time')
        batch_op.drop_column('end_time')

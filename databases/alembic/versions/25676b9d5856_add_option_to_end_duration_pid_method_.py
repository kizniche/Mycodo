"""Add option to end duration PID method with repeats after duration

Revision ID: 25676b9d5856
Revises: ed7e979852fa
Create Date: 2017-10-04 21:42:29.072048

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25676b9d5856'
down_revision = 'ed7e979852fa'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("method") as batch_op:
        batch_op.add_column(sa.Column('end_time', sa.TEXT))
    with op.batch_alter_table("method_data") as batch_op:
        batch_op.add_column(sa.Column('duration_end', sa.TEXT))


def downgrade():
    with op.batch_alter_table("method") as batch_op:
        batch_op.drop_column('end_time')
    with op.batch_alter_table("method_data") as batch_op:
        batch_op.drop_column('duration_end')

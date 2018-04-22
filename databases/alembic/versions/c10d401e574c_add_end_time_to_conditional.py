"""Add end_time to Conditional

Revision ID: c10d401e574c
Revises: 032b48f920b8
Create Date: 2018-04-22 15:33:40.746985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c10d401e574c'
down_revision = '032b48f920b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('timer_end_time', sa.Text))


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('timer_end_time')

"""Remove PID type option

Revision ID: a0c55d19384c
Revises: 08a36ebf1a82
Create Date: 2017-10-26 20:58:58.239070

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0c55d19384c'
down_revision = '08a36ebf1a82'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('pid_type')


def downgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('pid_type', sa.TEXT))

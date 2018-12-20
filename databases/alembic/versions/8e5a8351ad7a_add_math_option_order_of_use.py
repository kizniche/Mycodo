"""Add Math option order_of_use

Revision ID: 8e5a8351ad7a
Revises: 90wvmtnznxb8
Create Date: 2018-12-16 16:16:43.793554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e5a8351ad7a'
down_revision = '90wvmtnznxb8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("math") as batch_op:
        batch_op.add_column(sa.Column('order_of_use', sa.Text))


def downgrade():
    with op.batch_alter_table("math") as batch_op:
        batch_op.drop_column('order_of_use')

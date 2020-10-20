"""Add LCD CS Pin

Revision ID: 66e27f22b15a
Revises: 0e150fb8020b
Create Date: 2020-10-20 10:46:17.348908

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66e27f22b15a'
down_revision = '0e150fb8020b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column(sa.Column('pin_cs', sa.Integer))


def downgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.drop_column('pin_cs')

"""Add math_id option to conditionals

Revision ID: d36de7e4e477
Revises: 8b36095c6cf9
Create Date: 2017-12-09 19:07:50.321466

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd36de7e4e477'
down_revision = '8b36095c6cf9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('math_id', sa.INTEGER))


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('math_id')

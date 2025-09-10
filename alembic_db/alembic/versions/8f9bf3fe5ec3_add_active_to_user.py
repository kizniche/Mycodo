"""Add api_key to user table

Revision ID: 8f9bf3fe5ec4
Revises: 0bd51c536219
Create Date: 2019-10-25 16:01:39.300231

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8f9bf3fe5ec4'
down_revision = '0bd51c536219'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('active', sa.String))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column('active')

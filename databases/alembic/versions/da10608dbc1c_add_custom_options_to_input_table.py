"""Add custom_options to Input table

Revision ID: da10608dbc1c
Revises: 1421f1a02f25
Create Date: 2018-10-10 16:43:35.786970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da10608dbc1c'
down_revision = '1421f1a02f25'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('custom_options', sa.Text))


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('custom_options')

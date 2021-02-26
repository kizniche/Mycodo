"""add_cascaded_methods

Revision ID: 1cf1cd4d06bd
Revises: cc7261a89a87
Create Date: 2021-02-23 10:38:46.133612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cf1cd4d06bd'
down_revision = 'cc7261a89a87'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("method_data") as batch_op:
        batch_op.add_column(sa.Column('linked_method_id', sa.String))


def downgrade():
    with op.batch_alter_table("method_data") as batch_op:
        batch_op.drop_column('linked_method_id')


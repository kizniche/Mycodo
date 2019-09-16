"""Add Output option output_mode

Revision ID: 96ac315ec212
Revises: 2e416233221b
Create Date: 2019-09-15 22:24:57.278717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96ac315ec212'
down_revision = '2e416233221b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('output_mode', sa.Text))


def downgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('output_mode')

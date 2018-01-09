"""add camera option to dashboard

Revision ID: 4bb64e530d87
Revises: f0e4df767286
Create Date: 2018-01-09 16:44:17.405148

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bb64e530d87'
down_revision = 'f0e4df767286'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('camera_id', sa.Text))
        batch_op.add_column(sa.Column('camera_save_image', sa.Boolean))
        batch_op.add_column(sa.Column('camera_timestamp', sa.Boolean))


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('camera_id')
        batch_op.drop_column('camera_save_image')
        batch_op.drop_column('camera_timestamp')

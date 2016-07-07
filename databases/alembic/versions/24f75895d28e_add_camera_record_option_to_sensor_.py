"""Add camera record option to sensor conditional

Revision ID: 24f75895d28e
Revises: c8ae8ea703af
Create Date: 2016-07-07 12:34:51.674881

"""

# revision identifiers, used by Alembic.
revision = '24f75895d28e'
down_revision = 'c8ae8ea703af'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.add_column(sa.Column('camera_record', sa.TEXT))


def downgrade():
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.drop_column('camera_record')

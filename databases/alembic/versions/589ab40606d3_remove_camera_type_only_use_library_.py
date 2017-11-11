"""Remove camera type, only use library instead

Revision ID: 589ab40606d3
Revises: 214c6bb4603a
Create Date: 2017-11-11 13:27:12.117600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '589ab40606d3'
down_revision = '214c6bb4603a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('camera_type')


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('camera_type', sa.Text))

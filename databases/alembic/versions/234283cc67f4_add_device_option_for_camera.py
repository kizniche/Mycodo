"""Add device option for camera

Revision ID: 234283cc67f4
Revises: 8828a0074a44
Create Date: 2017-11-29 01:35:04.116656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '234283cc67f4'
down_revision = '8828a0074a44'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('device', sa.TEXT))


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('device')

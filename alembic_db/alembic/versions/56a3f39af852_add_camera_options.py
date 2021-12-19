"""add camera options

Revision ID: 56a3f39af852
Revises: ca91c47e7274
Create Date: 2021-12-19 15:58:01.319169

"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56a3f39af852'
down_revision = 'ca91c47e7274'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('output_format', sa.Text))


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('output_format')

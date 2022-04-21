"""add json_headers to camera table

Revision ID: 743de2cd05e3
Revises: b354722c9b8b
Create Date: 2022-04-21 19:11:56.122219

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '743de2cd05e3'
down_revision = 'b354722c9b8b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('json_headers', sa.Text))


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('json_headers')

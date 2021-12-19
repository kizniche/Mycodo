"""add camera options

Revision ID: ca91c47e7274
Revises: 0187ea22dc4b
Create Date: 2021-12-19 15:15:48.525102

"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca91c47e7274'
down_revision = '0187ea22dc4b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('show_preview', sa.Boolean))

    op.execute(
        '''
        UPDATE camera
        SET show_preview=0
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('show_preview')

"""Add custom_layout

Revision ID: 9bdb60d2a2cd
Revises: d6b624da47f4
Create Date: 2024-09-03 13:44:20.678365

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9bdb60d2a2cd'
down_revision = 'd6b624da47f4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('custom_layout', sa.Text))

    op.execute(
        '''
        UPDATE misc
        SET custom_layout=''
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('custom_layout')

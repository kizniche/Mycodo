"""Add table custom_controller

Revision ID: a6ec4e059470
Revises: 895ddcdef4ce
Create Date: 2019-10-03 16:17:37.783020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6ec4e059470'
down_revision = '895ddcdef4ce'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    op.create_table(
        'custom_controller',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('name', sa.Text),
        sa.Column('device', sa.Text),
        sa.Column('is_activated', sa.Boolean),
        sa.Column('log_level_debug', sa.Boolean),
        sa.Column('custom_options', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)


def downgrade():
    op.drop_table('custom_controller')

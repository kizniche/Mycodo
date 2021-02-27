"""add function_channels

Revision ID: 24dbd0b8c8d1
Revises: 1cf1cd4d06bd
Create Date: 2021-02-27 10:35:13.934674

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24dbd0b8c8d1'
down_revision = '1cf1cd4d06bd'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    op.create_table(
        'function_channel',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('function_id', sa.Text),
        sa.Column('channel', sa.Integer),
        sa.Column('name', sa.Text),
        sa.Column('custom_options', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)


def downgrade():
    op.drop_table('function_channel')

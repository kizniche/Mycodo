"""Add Input Channel Options

Revision ID: cc7261a89a87
Revises: 706a32b64ba2
Create Date: 2021-02-01 16:00:40.668774

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc7261a89a87'
down_revision = '706a32b64ba2'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    op.create_table(
        'input_channel',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('input_id', sa.Text),
        sa.Column('channel', sa.Integer),
        sa.Column('name', sa.Text),
        sa.Column('custom_options', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)


def downgrade():
    op.drop_table('input_channel')

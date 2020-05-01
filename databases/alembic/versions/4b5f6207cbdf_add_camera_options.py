"""Add Camera options

Revision ID: 4b5f6207cbdf
Revises: 267dc913a062
Create Date: 2020-04-30 19:45:55.844301

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b5f6207cbdf'
down_revision = '267dc913a062'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('url', sa.Text))


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('url')

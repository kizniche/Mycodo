"""Add api_key to user table

Revision ID: 8f9bf3fe5ec2
Revises: 0bd51c536217
Create Date: 2019-10-25 16:01:39.300231

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8f9bf3fe5ec2'
down_revision = '0bd51c536217'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('api_key', sa.String))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column('api_key')

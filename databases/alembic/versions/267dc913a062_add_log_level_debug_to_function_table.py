"""Add log_level_debug to Function table

Revision ID: 267dc913a062
Revises: dc9eddfc845d
Create Date: 2020-04-03 00:45:51.754745

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '267dc913a062'
down_revision = 'dc9eddfc845d'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("function") as batch_op:
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('message_include_code', sa.Boolean))


def downgrade():
    with op.batch_alter_table("function") as batch_op:
        batch_op.drop_column('log_level_debug')

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('message_include_code')

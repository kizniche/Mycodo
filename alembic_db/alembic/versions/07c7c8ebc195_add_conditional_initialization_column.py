"""add conditional initialization column

Revision ID: 07c7c8ebc195
Revises: 2c70a9e9e131
Create Date: 2022-08-06 12:51:56.767617

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07c7c8ebc195'
down_revision = '2c70a9e9e131'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('conditional_import', sa.Text))
        batch_op.add_column(sa.Column('conditional_initialize', sa.Text))

    op.execute(
        '''
        UPDATE conditional
        SET conditional_import=""
        '''
    )

    op.execute(
        '''
        UPDATE conditional
        SET conditional_initialize=""
        '''
    )


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('conditional_import')
        batch_op.drop_column('conditional_initialize')

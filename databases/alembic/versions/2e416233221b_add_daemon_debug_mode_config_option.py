"""Add daemon debug mode config option

Revision ID: 2e416233221b
Revises: ef49f6644e0c
Create Date: 2019-09-15 11:43:07.003473

"""

import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from databases.alembic_post import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e416233221b'
down_revision = 'ef49f6644e0c'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('daemon_debug_mode', sa.Boolean))

    op.execute(
        '''
        UPDATE misc
        SET daemon_debug_mode=0
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('daemon_debug_mode')

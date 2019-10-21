"""Add more camera options

Revision ID: 4b619edb9a8f
Revises: 440d382bfaa6
Create Date: 2019-10-21 13:12:43.893863

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b619edb9a8f'
down_revision = '440d382bfaa6'
branch_labels = None
depends_on = None

def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('hide_still', sa.Boolean))
        batch_op.add_column(sa.Column('hide_timelapse', sa.Boolean))
        batch_op.add_column(sa.Column('resolution_stream_width', sa.Integer))
        batch_op.add_column(sa.Column('resolution_stream_height', sa.Integer))

    op.execute(
        '''
        UPDATE camera
        SET hide_still=0
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET hide_timelapse=0
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET resolution_stream_width=1024
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET resolution_stream_height=768
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('hide_still')
        batch_op.drop_column('hide_timelapse')
        batch_op.drop_column('resolution_stream_width')
        batch_op.drop_column('resolution_stream_height')

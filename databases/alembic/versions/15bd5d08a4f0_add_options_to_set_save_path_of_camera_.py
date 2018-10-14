"""Add options to set save path of camera files

Revision ID: 15bd5d08a4f0
Revises: da10608dbc1c
Create Date: 2018-10-14 12:52:03.677929

"""
import os
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '15bd5d08a4f0'
down_revision = 'da10608dbc1c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('path_still', sa.Text))
        batch_op.add_column(sa.Column('path_timelapse', sa.Text))
        batch_op.add_column(sa.Column('path_video', sa.Text))

    op.execute(
        '''
        UPDATE camera
        SET path_still=''
        WHERE path_still IS NULL
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET path_timelapse=''
        WHERE path_timelapse IS NULL
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET path_video=''
        WHERE path_video IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('path_still')
        batch_op.drop_column('path_timelapse')
        batch_op.drop_column('path_video')
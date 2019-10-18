"""Add white balance options to picamera

Revision ID: daa60c17e66e
Revises: b6e332156961
Create Date: 2019-10-18 18:12:28.517150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'daa60c17e66e'
down_revision = 'b6e332156961'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('picamera_awb', sa.Text))
        batch_op.add_column(sa.Column('picamera_awb_gain_red', sa.Float))
        batch_op.add_column(sa.Column('picamera_awb_gain_blue', sa.Float))

    op.execute(
        '''
        UPDATE camera
        SET picamera_awb='auto'
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET picamera_awb_gain_red=0.5
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET picamera_awb_gain_blue=0.5
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('picamera_awb')
        batch_op.drop_column('picamera_awb_gain_red')
        batch_op.drop_column('picamera_awb_gain_blue')

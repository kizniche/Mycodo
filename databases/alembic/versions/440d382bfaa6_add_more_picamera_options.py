"""Add more picamera options

Revision ID: 440d382bfaa6
Revises: daa60c17e66e
Create Date: 2019-10-18 20:33:20.669877

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '440d382bfaa6'
down_revision = 'daa60c17e66e'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('picamera_shutter_speed', sa.Integer))
        batch_op.add_column(sa.Column('picamera_sharpness', sa.Integer))
        batch_op.add_column(sa.Column('picamera_iso', sa.Integer))
        batch_op.add_column(sa.Column('picamera_exposure_mode', sa.Text))
        batch_op.add_column(sa.Column('picamera_meter_mode', sa.Text))
        batch_op.add_column(sa.Column('picamera_image_effect', sa.Text))

    op.execute(
        '''
        UPDATE camera
        SET picamera_shutter_speed=0
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET picamera_sharpness=0
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET picamera_iso=0
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET picamera_exposure_mode='auto'
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET picamera_meter_mode='average'
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET picamera_image_effect='none'
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('picamera_shutter_speed')
        batch_op.drop_column('picamera_sharpness')
        batch_op.drop_column('picamera_iso')
        batch_op.drop_column('picamera_exposure_mode')
        batch_op.drop_column('picamera_meter_mode')
        batch_op.drop_column('picamera_image_effect')

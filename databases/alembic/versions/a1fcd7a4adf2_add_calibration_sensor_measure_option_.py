"""Add calibration_sensor_measure option for Atlas Scientific pH sensors

Revision ID: a1fcd7a4adf2
Revises: a9a330ea0ccb
Create Date: 2017-05-12 14:14:12.068662

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1fcd7a4adf2'
down_revision = 'a9a330ea0ccb'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('calibrate_sensor_measure', sa.TEXT))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('calibrate_sensor_measure')

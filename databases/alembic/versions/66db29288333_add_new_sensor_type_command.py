"""Add new sensor type command

Revision ID: 66db29288333
Revises: 25676b9d5856
Create Date: 2017-10-20 20:08:47.082519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66db29288333'
down_revision = '25676b9d5856'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('cmd_command', sa.TEXT))
        batch_op.add_column(sa.Column('cmd_measurement', sa.TEXT))
        batch_op.add_column(sa.Column('cmd_measurement_units', sa.TEXT))

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('sensor_id')

    op.execute(
        '''
        UPDATE pid
        SET measurement=''
        '''
    )

    op.execute(
        '''
        UPDATE pid
        SET is_activated=0
        '''
    )


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('cmd_command')
        batch_op.drop_column('cmd_measurement')
        batch_op.drop_column('cmd_measurement_units')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('sensor_id', sa.Integer, sa.ForeignKey('sensor.id')))

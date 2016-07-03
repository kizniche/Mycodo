"""Add ADC columns to sensor table

Revision ID: c6efd02bdf96
Revises: 0c69ae36f0d3
Create Date: 2016-06-26 17:46:14.542333

"""

# revision identifiers, used by Alembic.
revision = 'c6efd02bdf96'
down_revision = '0c69ae36f0d3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('adc_address', sa.TEXT))
        batch_op.add_column(sa.Column('adc_channel', sa.INT))
        batch_op.add_column(sa.Column('adc_resolution', sa.INT))
        batch_op.add_column(sa.Column('adc_measure', sa.TEXT))
        batch_op.add_column(sa.Column('adc_measure_units', sa.TEXT))
        batch_op.add_column(sa.Column('adc_volts_min', sa.REAL))
        batch_op.add_column(sa.Column('adc_volts_max', sa.REAL))
        batch_op.add_column(sa.Column('adc_units_min', sa.REAL))
        batch_op.add_column(sa.Column('adc_units_max', sa.REAL))
    op.execute(
        '''
        UPDATE sensor
        SET adc_address=''
        WHERE adc_address IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('adc_address')
        batch_op.drop_column('adc_channel')
        batch_op.drop_column('adc_resolution')
        batch_op.drop_column('adc_measure')
        batch_op.drop_column('adc_measure_units')
        batch_op.drop_column('adc_volts_min')
        batch_op.drop_column('adc_volts_max')
        batch_op.drop_column('adc_units_min')
        batch_op.drop_column('adc_units_max')

"""Refactor for single-file input modules

Revision ID: d10573676ecb
Revises: 7dbc5357d3a9
Create Date: 2018-09-08 16:26:51.833832

"""
from alembic import op
import sqlalchemy as sa

from mycodo.databases.models import Input
from mycodo.databases.utils import session_scope
from mycodo.config import SQL_DATABASE_MYCODO

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# revision identifiers, used by Alembic.
revision = 'd10573676ecb'
down_revision = '7dbc5357d3a9'
branch_labels = None
depends_on = None


def upgrade():
    # Add note and tag tables
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('date_time', sa.DateTime),
        sa.Column('name', sa.Text),
        sa.Column('tags', sa.Text),
        sa.Column('files', sa.Text),
        sa.Column('note', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)

    op.create_table(
        'note_tags',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('name', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)

    # Add note column to graphs table
    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.add_column(sa.Column('note_tag_ids', sa.Text))

    # New input options
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('i2c_location', sa.Text))
        batch_op.add_column(sa.Column('uart_location', sa.Text))
        batch_op.add_column(sa.Column('gpio_location', sa.Integer))

    # Rename input names
    with session_scope(MYCODO_DB_PATH) as new_session:
        for each_input in new_session.query(Input).all():
            if each_input.device == 'ATLAS_PT1000_I2C':
                each_input.interface = 'I2C'
                each_input.device = 'ATLAS_PT1000'
            elif each_input.device == 'ATLAS_PT1000_UART':
                each_input.interface = 'UART'
                each_input.device = 'ATLAS_PT1000'

            elif each_input.device == 'ATLAS_EC_I2C':
                each_input.interface = 'I2C'
                each_input.device = 'ATLAS_EC'
            elif each_input.device == 'ATLAS_EC_UART':
                each_input.interface = 'UART'
                each_input.device = 'ATLAS_EC'

            elif each_input.device == 'ATLAS_PH_I2C':
                each_input.interface = 'I2C'
                each_input.device = 'ATLAS_PH'
            elif each_input.device == 'ATLAS_PH_UART':
                each_input.interface = 'UART'
                each_input.device = 'ATLAS_PH'

            elif each_input.device == 'K30_I2C':
                each_input.interface = 'I2C'
                each_input.device = 'K30'
            elif each_input.device == 'K30_UART':
                each_input.interface = 'UART'
                each_input.device = 'K30'

            elif each_input.device == 'MH_Z16_I2C':
                each_input.interface = 'I2C'
                each_input.device = 'MH_Z16'
            elif each_input.device == 'MH_Z16_UART':
                each_input.interface = 'UART'
                each_input.device = 'MH_Z16'

            elif each_input.device == 'MH_Z19_I2C':
                each_input.interface = 'I2C'
                each_input.device = 'MH_Z19'
            elif each_input.device == 'MH_Z19_UART':
                each_input.interface = 'UART'
                each_input.device = 'MH_Z19'

            if (each_input.location == 'RPi' or
                    each_input.device == 'RPiFreeSpace'):
                each_input.interface = 'RPi'
            elif each_input.location == 'Mycodo_daemon':
                each_input.interface = 'Mycodo'

            # Move values to new respective device locations
            if each_input.device_loc:
                each_input.uart_location = each_input.device_loc

            if each_input.device in [
                    'MCP3008', 'MAX31855', 'MAX31856', 'MAX31865']:
                each_input.interface = 'UART'

            if each_input.location and each_input.device in [
                    'ATLAS_EC', 'TSL2591', 'ATLAS_PH', 'BH1750', 'SHT2x',
                    'MH_Z16', 'CHIRP', 'BMP280', 'TMP006', 'AM2315', 'BME280',
                    'ATLAS_PT1000', 'BMP180', 'TSL2561', 'HTU21D', 'HDC1000',
                    'CCS811', 'MCP342x', 'ADS1x15']:
                each_input.i2c_location = each_input.location
                each_input.interface = 'I2C'

            if each_input.location and each_input.device in [
                    'DHT11', 'DHT22', 'SIGNAL_PWM', 'SIGNAL_RPM', 'SHT1x_7x',
                    'GPIO_STATE']:
                each_input.gpio_location = int(each_input.location)

        new_session.commit()


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('i2c_location')
        batch_op.drop_column('uart_location')
        batch_op.drop_column('gpio_location')

    op.drop_table('notes')
    op.drop_table('note_tags')

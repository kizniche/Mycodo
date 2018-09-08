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
    # Update unique names for inputs
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

            if each_input.location == 'RPi' or each_input.device == 'RPiFreeSpace':
                each_input.interface = 'RPi'
            elif each_input.location == 'Mycodo_daemon':
                each_input.interface = 'Mycodo'

        new_session.commit()


def downgrade():
    pass

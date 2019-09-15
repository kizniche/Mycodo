"""Add daemon debug mode config option

Revision ID: 2e416233221b
Revises: ef49f6644e0c
Create Date: 2019-09-15 11:43:07.003473

"""


import sys
import textwrap

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic import op
import sqlalchemy as sa
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Output
from mycodo.databases.models import Dashboard
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Input
from mycodo.databases.utils import session_scope
from mycodo.config import OUTPUT_INFO
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.inputs.python_code import execute_at_creation
from mycodo.mycodo_flask.utils.utils_misc import pre_statement_run
from mycodo.utils.system_pi import assure_path_exists

# revision identifiers, used by Alembic.
revision = '2e416233221b'
down_revision = 'ef49f6644e0c'
branch_labels = None
depends_on = None

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('daemon_debug_mode', sa.Boolean))

    op.execute(
        '''
        UPDATE misc
        SET daemon_debug_mode=False
        '''
    )

    # Upgrade output system to use device_measurements

    output_unique_id = {}

    # Go through each output to get output unique_id
    with session_scope(MYCODO_DB_PATH) as output_sess:
        for each_output in output_sess.query(Output).all():
            output_unique_id[each_output.unique_id] = []

            # Create measurements in device_measurements table
            for measurement, measure_data in OUTPUT_INFO[each_output.output_type]['measure'].items():
                for unit, unit_data in measure_data.items():
                    for channel, channel_data in unit_data.items():
                        new_measurement = DeviceMeasurements()
                        new_measurement.device_id = each_output.unique_id
                        new_measurement.name = ''
                        new_measurement.is_enabled = True
                        new_measurement.measurement = measurement
                        new_measurement.unit = unit
                        new_measurement.channel = channel
                        output_sess.add(new_measurement)
                        output_sess.commit()

                        output_unique_id[each_output.unique_id].append(new_measurement.unique_id)

        # Update all outputs in Dashboard elements to new unique_ids
        for each_dash in output_sess.query(Dashboard).all():
            each_dash.output_ids = each_dash.output_ids.replace(',output', '')
            output_sess.commit()

            for each_output_id, list_device_ids in output_unique_id.items():
                id_string = ''
                for index, each_device_id in enumerate(list_device_ids):
                    id_string += '{},{}'.format(each_output_id, each_device_id)
                    if index + 1 < len(list_device_ids):
                        id_string += ';'

                if each_output_id in each_dash.output_ids:
                    each_dash.output_ids = each_dash.output_ids.replace(each_output_id, id_string)
                    output_sess.commit()


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('daemon_debug_mode')

# -*- coding: utf-8 -*-
#
# Script to be executed following an alembic update of the SQLite database
#
# Alembic is used to update the database schema. This script is used to
# execute code after all database schema updates have been performed, and
# typically involves database entry modifications.
#
# Note: Newest revision at the top
#
# The following code is also needed in the upgrade() function of the alembic
# upgrade script to indicate which section of this script to run. This should
# already be included in the alembic script template.
#
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
# from databases.alembic_post_utils import write_revision_post_alembic
# def upgrade():
#     write_revision_post_alembic(revision)
#
import sys
import traceback

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from databases.alembic_post_utils import read_revision_file
from mycodo.config import ALEMBIC_UPGRADE_POST
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.utils import session_scope


MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


if __name__ == "__main__":
    error = []
    print("Found revision IDs to execute code: {con}".format(
        con=read_revision_file()))

    for each_revision in read_revision_file():
        print("Revision ID {rev}".format(
            file=ALEMBIC_UPGRADE_POST, rev=each_revision))

        if not each_revision:
            print("Error: Revision ID empty")

        # elif each_revision == 'REPLACE WITH ALEMBIC REVISION ID':
        #     print("Executing post-alembic code for revision {}".format(
        #         each_revision))
        #     try:
        #         pass  # Code goes here
        #     except Exception:
        #         msg = "ERROR: post-alembic revision {}: {}".format(
        #             each_revision, traceback.format_exc())
        #         error.append(msg)
        #         print(msg)

        elif each_revision == '61a0d0568d24':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Role

                with session_scope(MYCODO_DB_PATH) as session:
                    for role in session.query(Role).all():
                        if role.name in ['Kiosk', 'Guest']:
                            role.reset_password = False
                        else:
                            role.reset_password = True
                        session.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == 'f5b77ef5f17c':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import SMTP

                with session_scope(MYCODO_DB_PATH) as session:
                    for smtp in session.query(SMTP).all():
                        error = []
                        if smtp.ssl:
                            smtp.protocol = 'ssl'
                            if smtp.port == 465:
                                smtp.port = None
                        elif not smtp.ssl:
                            smtp.protocol = 'tls'
                            if smtp.port == 587:
                                smtp.port = None
                        else:
                            smtp.protocol = 'unencrypted'
                        if not error:
                            session.commit()
                        else:
                            for each_error in error:
                                print("Error: {}".format(each_error))
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '0a8a5eb1be4b':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Input

                with session_scope(MYCODO_DB_PATH) as session:
                    for each_input in session.query(Input).all():
                        error = []
                        if each_input.device == 'DS18B20' and 'library,ow_shell' in each_input.custom_options:
                            each_input.device = 'DS18B20_OWS'
                        each_input.custom_options = ''
                        if not error:
                            session.commit()
                        else:
                            for each_error in error:
                                print("Error: {}".format(each_error))
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '55aca47c2362':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Widget
                from mycodo.databases.models import Dashboard

                with session_scope(MYCODO_DB_PATH) as session:
                    new_dash = Dashboard()
                    new_dash.name = 'Default Dashboard'
                    session.add(new_dash)

                    for each_widget in session.query(Widget).all():
                        each_widget.dashboard_id = new_dash.unique_id
                        session.commit()

                    if not error:
                        session.commit()
                    else:
                        for each_error in error:
                            print("Error: {}".format(each_error))
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '895ddcdef4ce':
            # Add PID setpoint_tracking_type and setpoint_tracking_id
            # If method_id set, set setpoint_tracking_type to 'method;
            # and copy method_id to new setpoint_tracking_id.
            # PID.method_id deleted after executing this code.
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import PID

                with session_scope(MYCODO_DB_PATH) as session:
                    for each_pid in session.query(PID).all():
                        error = []
                        if each_pid.setpoint_tracking_id:
                            each_pid.setpoint_tracking_type = 'method'
                        if not error:
                            session.commit()
                        else:
                            for each_error in error:
                                print("Error: {}".format(each_error))
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '0ce53d526f13':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Actions
                from mycodo.databases.models import Conditional
                from mycodo.utils.conditional import save_conditional_code

                conditions = conditional_sess.query(ConditionalConditions).all()
                actions = conditional_sess.query(Actions).all()

                with session_scope(MYCODO_DB_PATH) as cond_sess:
                    for each_cond in cond_sess.query(Conditional).all():
                        error = []
                        each_cond.conditional_statement = each_cond.conditional_statement.replace(
                            'self.measure(', 'self.condition(')
                        each_cond.conditional_statement = each_cond.conditional_statement.replace(
                            'self.measure_dict(', 'self.condition_dict(')
                        if not error:
                            cond_sess.commit()
                        else:
                            for each_error in error:
                                print("Error: {}".format(each_error))

                        save_conditional_code(
                            [],
                            each_cond.conditional_statement,
                            each_cond.unique_is,
                            conditions,
                            actions)
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '545744b31813':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Output

                with session_scope(MYCODO_DB_PATH) as output_sess:
                    for each_output in output_sess.query(Output).all():
                        if each_output.measurement == 'time':
                            each_output.measurement = 'duration_time'
                            output_sess.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '802cc65f734e':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:  # Check if already installed
                import Pyro5.api
            except Exception:  # Not installed. Try to install
                try:
                    from mycodo.config import INSTALL_DIRECTORY
                    import subprocess
                    command = '{path}/env/bin/pip install -r {path}/install/requirements.txt'.format(
                        path=INSTALL_DIRECTORY)
                    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                    cmd_out, cmd_err = cmd.communicate()
                    cmd_status = cmd.wait()
                    import Pyro5.api
                except Exception:
                    msg = "ERROR: post-alembic revision {}: {}".format(
                        each_revision, traceback.format_exc())
                    error.append(msg)
                    print(msg)

        elif each_revision == '2e416233221b':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Dashboard
                from mycodo.databases.models import DeviceMeasurements
                from mycodo.databases.models import Output
                from mycodo.config import OUTPUT_INFO

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

                                    output_unique_id[each_output.unique_id].append(
                                        new_measurement.unique_id)

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
                                each_dash.output_ids = each_dash.output_ids.replace(
                                    each_output_id, id_string)
                                output_sess.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == 'ef49f6644e0c':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Actions
                from mycodo.databases.models import Conditional
                from mycodo.databases.models import Input
                from mycodo.inputs.python_code import execute_at_creation
                from mycodo.utils.conditional import save_conditional_code

                conditions = conditional_sess.query(ConditionalConditions).all()
                actions = conditional_sess.query(Actions).all()

                with session_scope(MYCODO_DB_PATH) as conditional_sess:
                    for each_conditional in conditional_sess.query(Conditional).all():
                        save_conditional_code(
                            [],
                            each_conditional.conditional_statement,
                            each_conditional.unique_is,
                            conditions,
                            actions)

                with session_scope(MYCODO_DB_PATH) as conditional_sess:
                    with session_scope(MYCODO_DB_PATH) as input_sess:
                        for each_input in input_sess.query(Input).all():
                            if each_input.device == 'PythonCode' and each_input.cmd_command:
                                try:
                                    execute_at_creation(each_input.unique_id,
                                                        each_input.cmd_command,
                                                        None)
                                except Exception as msg:
                                    print("Exception: {}".format(msg))
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '65271370a3a9':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Actions
                from mycodo.databases.models import Conditional
                from mycodo.databases.models import Input
                from mycodo.inputs.python_code import execute_at_creation
                from mycodo.utils.conditional import save_conditional_code

                conditions = conditional_sess.query(ConditionalConditions).all()
                actions = conditional_sess.query(Actions).all()

                # Conditionals
                with session_scope(MYCODO_DB_PATH) as conditional_sess:
                    for each_conditional in conditional_sess.query(Conditional).all():
                        if each_conditional.conditional_statement:
                            # Replace strings
                            try:
                                strings_replace = [
                                    ('measure(', 'self.measure('),
                                    ('measure_dict(', 'self.measure_dict('),
                                    ('run_action(', 'self.run_action('),
                                    ('run_all_actions(', 'self.run_all_actions('),
                                    ('=message', '=self.message'),
                                    ('= message', '= self.message'),
                                    ('message +=', 'self.message +='),
                                    ('message+=', 'self.message+=')
                                ]
                                for each_set in strings_replace:
                                    if each_set[0] in each_conditional.conditional_statement:
                                        each_conditional.conditional_statement = each_conditional.conditional_statement.replace(
                                            each_set[0], each_set[1])
                            except Exception as msg:
                                print("Exception: {}".format(msg))

                        conditional_sess.commit()

                        save_conditional_code(
                            [],
                            each_conditional.conditional_statement,
                            each_conditional.unique_is,
                            conditions,
                            actions)

                # Inputs
                with session_scope(MYCODO_DB_PATH) as input_sess:
                    for each_input in input_sess.query(Input).all():
                        if each_input.device == 'PythonCode' and each_input.cmd_command:
                            # Replace strings
                            try:
                                strings_replace = [
                                    ('store_measurement(', 'self.store_measurement(')
                                ]
                                for each_set in strings_replace:
                                    if each_set[0] in each_input.cmd_command:
                                        each_input.cmd_command = each_input.cmd_command.replace(
                                            each_set[0], each_set[1])
                            except Exception as msg:
                                print("Exception: {}".format(msg))

                    input_sess.commit()

                    for each_input in input_sess.query(Input).all():
                        if each_input.device == 'PythonCode' and each_input.cmd_command:
                            try:
                                execute_at_creation(each_input.unique_id,
                                                    each_input.cmd_command,
                                                    None)
                            except Exception as msg:
                                print("Exception: {}".format(msg))
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '70c828e05255':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Conditional
                from mycodo.databases.models import ConditionalConditions

                with session_scope(MYCODO_DB_PATH) as conditional_sess:
                    for each_conditional in conditional_sess.query(Conditional).all():
                        if each_conditional.conditional_statement:

                            # Get conditions for this conditional
                            with session_scope(MYCODO_DB_PATH) as condition_sess:
                                for each_condition in condition_sess.query(ConditionalConditions).all():
                                    # Replace {ID} with measure("{ID}")
                                    id_str = '{{{id}}}'.format(id=each_condition.unique_id.split('-')[0])
                                    new_str = 'measure("{{{id}}}")'.format(id=each_condition.unique_id.split('-')[0])
                                    if id_str in each_conditional.conditional_statement:
                                        each_conditional.conditional_statement = each_conditional.conditional_statement.replace(
                                            id_str, new_str)

                                    # Replace print(1) with run_all_actions()
                                    new_str = 'run_all_actions()'
                                    if id_str in each_conditional.conditional_statement:
                                        each_conditional.conditional_statement = each_conditional.conditional_statement.replace(
                                            'print(1)', new_str)
                                        each_conditional.conditional_statement = each_conditional.conditional_statement.replace(
                                            'print("1")', new_str)
                                        each_conditional.conditional_statement = each_conditional.conditional_statement.replace(
                                            "print('1')", new_str)

                    conditional_sess.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == 'b4d958997cf0':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Input

                with session_scope(MYCODO_DB_PATH) as new_session:
                    for each_input in new_session.query(Input).all():
                        if each_input.device in ['DS18B20', 'DS18S20']:
                            if 'library' not in each_input.custom_options:
                                if each_input.custom_options in [None, '']:
                                    each_input.custom_options = 'library,w1thermsensor'
                                else:
                                    each_input.custom_options += ';library,w1thermsensor'

                    new_session.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        else:
            print("Code for revision {} not found".format(each_revision))

    if error:
        print("Completed with errors. Review the entire log for details.")
    else:
        try:
            print("Completed without errors. Deleting {}".format(
                ALEMBIC_UPGRADE_POST))
            os.remove(ALEMBIC_UPGRADE_POST)
        except Exception:
            msg = "ERROR: Could not delete {}: {}".format(
                ALEMBIC_UPGRADE_POST, traceback.format_exc())

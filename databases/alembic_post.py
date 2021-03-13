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

        # elif each_revision == 'REPLACE_WITH_ALEMBIC_REVISION_ID':
        #     print("Executing post-alembic code for revision {}".format(
        #         each_revision))
        #     try:
        #         pass  # Code goes here
        #     except Exception:
        #         msg = "ERROR: post-alembic revision {}: {}".format(
        #             each_revision, traceback.format_exc())
        #         error.append(msg)
        #         print(msg)

        elif each_revision == '110d2d00e91d':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from sqlalchemy import and_
                from mycodo.databases.models import Conversion

                with session_scope(MYCODO_DB_PATH) as session:
                    conv = session.query(Conversion).filter(
                        and_(Conversion.convert_unit_from == "kPa",
                             Conversion.convert_unit_to == "jPa")).first()
                    if conv:
                        session.delete(conv)
                        session.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == 'cc7261a89a87':
            # This version adds Input Channel Options
            # We need to create Input channels and copy the measurement name to the new
            # custom channel option for the MQTT and TTN Inputs.
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                import json
                from sqlalchemy import and_
                from mycodo.databases.models import DeviceMeasurements
                from mycodo.databases.models import Input
                from mycodo.databases.models import InputChannel

                with session_scope(MYCODO_DB_PATH) as session:
                    for each_input in session.query(Input).all():
                        if each_input.device in ["MQTT_PAHO", "TTN_DATA_STORAGE"]:
                            for each_measure in session.query(DeviceMeasurements).filter(
                                    DeviceMeasurements.device_id == each_input.unique_id).all():
                                # does Input Channel exist?
                                channel_exist = session.query(InputChannel).filter(and_(
                                    InputChannel.input_id == each_input.unique_id,
                                    InputChannel.channel == each_measure.channel)).first()
                                if not channel_exist:
                                    new_channel = InputChannel()
                                    new_channel.input_id = each_input.unique_id
                                    new_channel.channel = each_measure.channel
                                    if each_input.device == "MQTT_PAHO":
                                        custom_options = {"subscribe_topic": each_measure.name}
                                    elif each_input.device == "TTN_DATA_STORAGE":
                                        custom_options = {"variable_name": each_measure.name}
                                    new_channel.custom_options = json.dumps(custom_options)
                                    session.add(new_channel)
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '313a6fb99082':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import Actions

                with session_scope(MYCODO_DB_PATH) as session:
                    for each_action in session.query(Actions).all():
                        try:
                            if each_action.action_type == 'command' and not each_action.do_output_state:
                                # "pi" was the default prior to this update.
                                # The new default is "mycodo"
                                each_action.do_output_state = 'pi'
                                session.commit()
                        except Exception:
                            msg = "ERROR: Update Action {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '0e150fb8020b':
            print("Executing post-alembic code for revision {}".format(each_revision))
            import json
            from mycodo.databases.models import Actions
            from mycodo.databases.models import Camera
            from mycodo.databases.models import ConditionalConditions
            from mycodo.databases.models import DeviceMeasurements
            from mycodo.databases.models import Input
            from mycodo.databases.models import Math
            from mycodo.databases.models import Output
            from mycodo.databases.models import OutputChannel
            from mycodo.databases.models import PID
            from mycodo.databases.models import Trigger
            from mycodo.databases.models import Widget
            from mycodo.utils.inputs import parse_input_information

            try:
                with session_scope(MYCODO_DB_PATH) as session:

                    # Update Input custom_options
                    dict_inputs = parse_input_information()
                    for each_input in session.query(Input).all():
                        custom_options = {}
                        if 'custom_options' not in dict_inputs[each_input.device]:
                            continue

                        try:
                            for each_option_default in dict_inputs[each_input.device]['custom_options']:
                                try:
                                    option_value = each_option_default['default_value']

                                    if each_input.custom_options:
                                        for each_option in each_input.custom_options.split(';'):
                                            option = each_option.split(',')[0]

                                            if option == each_option_default['id']:
                                                option_value = each_option.split(',', 1)[1]

                                    if each_option_default['type'] == 'integer':
                                        custom_options[each_option_default['id']] = int(option_value)

                                    elif each_option_default['type'] == 'float':
                                        custom_options[each_option_default['id']] = float(option_value)

                                    elif each_option_default['type'] == 'bool':
                                        custom_options[each_option_default['id']] = bool(option_value)

                                    elif each_option_default['type'] in ['multiline_text',
                                                                         'text',
                                                                         'select_measurement',
                                                                         'select_device']:
                                        custom_options[each_option_default['id']] = str(option_value)

                                    elif each_option_default['type'] == 'select':
                                        option_value = str(option_value)
                                        if 'cast_value' in each_option_default and each_option_default['cast_value']:
                                            if each_option_default['cast_value'] == 'integer':
                                                option_value = int(option_value)
                                            elif each_option_default['cast_value'] == 'float':
                                                option_value = float(option_value)
                                        custom_options[each_option_default['id']] = option_value

                                    else:
                                        print("Unknown custom_option type '{}'".format(each_option_default['type']))
                                except Exception:
                                    print("Error parsing custom_options")

                        except Exception:
                            msg = "ERROR: Update Input {}: {}".format(each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                        each_input.custom_options = json.dumps(custom_options)
                        session.commit()

                    # Update outputs
                    for each_output in session.query(Output).all():
                        try:
                            custom_options = {
                                'pin': each_output.pin,
                                'amps': each_output.amps,
                                'protocol': each_output.protocol,
                                'pulse_length': each_output.pulse_length,
                                'linux_command_user': each_output.linux_command_user,
                                'on_command': each_output.on_command,
                                'off_command': each_output.off_command,
                                'pwm_command': each_output.pwm_command,
                                'force_command': each_output.force_command,
                                'trigger_functions_at_start': each_output.trigger_functions_at_start,
                                'startup_value': each_output.startup_value,
                                'shutdown_value': each_output.shutdown_value,
                                'pwm_hertz': each_output.pwm_hertz,
                                'pwm_library': each_output.pwm_library,
                                'pwm_invert_signal': each_output.pwm_invert_signal,
                                'flow_mode': each_output.output_mode,
                                'flow_rate': each_output.flow_rate,
                                'state_startup': each_output.state_startup,
                                'state_shutdown': each_output.state_shutdown
                            }

                            try:
                                custom_options['state_startup'] = int(each_output.state_startup)
                            except:
                                pass

                            try:
                                custom_options['state_shutdown'] = int(each_output.state_shutdown)
                            except:
                                pass

                            try:
                                custom_options['on_state'] = int(each_output.on_state)
                            except:
                                pass

                            # Add any custom options already present
                            if each_output.custom_options and "," in each_output.custom_options:
                                for each_set in each_output.custom_options.split(";"):
                                    if len(each_set.split(",")) > 1:
                                        key = each_set.split(",")[0]
                                        value = each_set.split(",")[1]
                                        if key in ['port', 'keepalive']:
                                            value = int(value)
                                        custom_options[key] = value

                            if each_output.output_type in ["python",
                                                           "command",
                                                           "wireless_rpi_rf",
                                                           "MQTT_PAHO"]:
                                try:
                                    custom_options['state_startup'] = int(each_output.state_startup)
                                    custom_options['state_shutdown'] = int(each_output.state_shutdown)
                                except:
                                    pass

                            new_channel = OutputChannel()
                            new_channel.output_id = each_output.unique_id
                            new_channel.channel = 0
                            new_channel.custom_options = json.dumps(custom_options)
                            session.add(new_channel)
                            each_output.custom_options = ''
                            session.commit()
                        except Exception:
                            msg = "ERROR: Update Output {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update Math outputs
                    for each_math in session.query(Math).all():
                        try:
                            if (each_math.math_type in ['average',
                                                        'difference',
                                                        'redundancy',
                                                        'statistics',
                                                        'sum',
                                                        'verification'] and
                                    each_math.inputs):
                                selections = each_math.inputs.split(";")
                                new_list = []
                                for each_selection in selections:
                                    if "," in each_selection:
                                        output_id = each_selection.split(",")[0]
                                        output = session.query(Output).filter(Output.unique_id == output_id).first()
                                        if output:
                                            output_channel = session.query(OutputChannel).filter(
                                                OutputChannel.output_id == output_id).first()
                                            new_list.append("{},{}".format(output_id, output_channel.unique_id))
                                        else:
                                            new_list.append(each_selection)
                                each_math.inputs = ";".join(new_list)

                            elif (each_math.math_type in ['average_single',
                                                          'sum_single'] and
                                    each_math.inputs):
                                output_id = each_math.inputs.split(",")[0]
                                output = session.query(Output).filter(Output.unique_id == output_id).first()
                                if output:
                                    output_channel = session.query(OutputChannel).filter(
                                        OutputChannel.output_id == output_id).first()
                                    each_math.inputs = "{},{}".format(output_id, output_channel.unique_id)

                            session.commit()
                        except Exception:
                            msg = "ERROR: Update Math {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update PID outputs
                    for each_pid in session.query(PID).all():
                        try:
                            if each_pid.raise_output_id:
                                output_id = each_pid.raise_output_id
                                output_channel = session.query(OutputChannel).filter(
                                    OutputChannel.output_id == output_id).first()
                                each_pid.raise_output_id = "{},{}".format(output_id, output_channel.unique_id)
                            if each_pid.lower_output_id:
                                output_id = each_pid.lower_output_id
                                output_channel = session.query(OutputChannel).filter(
                                    OutputChannel.output_id == output_id).first()
                                each_pid.lower_output_id = "{},{}".format(output_id, output_channel.unique_id)
                            session.commit()
                        except Exception:
                            msg = "ERROR: Update PID {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update Trigger outputs
                    for each_trigger in session.query(Trigger).all():
                        try:
                            if (each_trigger.trigger_type in ['trigger_output',
                                                              'trigger_output_pwm'] and
                                    each_trigger.unique_id_1):
                                output_channel = session.query(OutputChannel).filter(
                                    OutputChannel.output_id == each_trigger.unique_id_1).first()
                                each_trigger.unique_id_2 = output_channel.unique_id
                            elif (each_trigger.trigger_type == 'trigger_run_pwm_method' and
                                    each_trigger.unique_id_2):
                                output_channel = session.query(OutputChannel).filter(
                                    OutputChannel.output_id == each_trigger.unique_id_2).first()
                                each_trigger.unique_id_3 = output_channel.unique_id
                            session.commit()
                        except Exception:
                            msg = "ERROR: Update Trigger {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update Function Action outputs
                    for each_action in session.query(Actions).all():
                        try:
                            if each_action.action_type in ['output',
                                                           'output_pwm',
                                                           'output_ramp_pwm',
                                                           'output_volume']:
                                output_id = each_action.do_unique_id
                                output = session.query(Output).filter(
                                    Output.unique_id == output_id).first()
                                if not output:
                                    continue
                                output_channel = session.query(OutputChannel).filter(
                                    OutputChannel.output_id == output_id).first()
                                each_action.do_unique_id = "{},{}".format(output_id, output_channel.unique_id)
                                session.commit()
                        except Exception:
                            msg = "ERROR: Update Action {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update Conditional Condition outputs
                    for each_cond in session.query(ConditionalConditions).all():
                        try:
                            if each_cond.condition_type in ['output_state',
                                                            'output_duration_on']:
                                output_id = each_cond.output_id
                                output = session.query(Output).filter(
                                    Output.unique_id == output_id).first()
                                if not output:
                                    continue
                                output_channel = session.query(OutputChannel).filter(
                                    OutputChannel.output_id == output_id).first()
                                each_cond.output_id = "{},{}".format(output_id, output_channel.unique_id)
                                session.commit()
                        except Exception:
                            msg = "ERROR: Update Condition {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update Widget outputs
                    for each_widget in session.query(Widget).all():
                        try:
                            custom_options = json.loads(each_widget.custom_options)
                            if each_widget.graph_type in ["widget_output",
                                                          "widget_output_pwm_slider",
                                                          "widget_measurement",
                                                          "widget_indicator"]:
                                if each_widget.graph_type in ["widget_output",
                                                              "widget_output_pwm_slider"]:
                                    option_name = "output"
                                elif each_widget.graph_type in ["widget_measurement",
                                                                "widget_indicator"]:
                                    option_name = "measurement"

                                if custom_options[option_name] and "," in custom_options[option_name]:
                                    output_id = custom_options[option_name].split(",")[0]
                                    output = session.query(Output).filter(
                                        Output.unique_id == output_id).first()
                                    if not output:
                                        continue
                                    output_channel = session.query(OutputChannel).filter(
                                        OutputChannel.output_id == output_id).first()
                                    measurement = session.query(DeviceMeasurements).filter(
                                        DeviceMeasurements.device_id == output_id).first()
                                    custom_options[option_name] = "{},{},{}".format(
                                        output_id, measurement.unique_id, output_channel.unique_id)
                                    each_widget.custom_options = json.dumps(custom_options)
                                    session.commit()
                        except Exception:
                            msg = "ERROR: Update Widget {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update Camera outputs
                    for each_camera in session.query(Camera).all():
                        try:
                            output_id = each_camera.output_id
                            output = session.query(Output).filter(
                                Output.unique_id == output_id).first()
                            if not output:
                                continue
                            output_channel = session.query(OutputChannel).filter(
                                OutputChannel.output_id == output_id).first()
                            each_camera.output_id = "{},{}".format(output_id, output_channel.unique_id)
                            session.commit()
                        except Exception:
                            msg = "ERROR: Update Camera {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

                    # Update Input outputs
                    for each_input in session.query(Input).all():
                        try:
                            output_id = each_input.pre_output_id
                            output = session.query(Output).filter(
                                Output.unique_id == output_id).first()
                            if not output:
                                continue
                            output_channel = session.query(OutputChannel).filter(
                                OutputChannel.output_id == output_id).first()
                            each_input.pre_output_id = "{},{}".format(output_id, output_channel.unique_id)
                            session.commit()
                        except Exception:
                            msg = "ERROR: Update Input {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == 'd66e33093e8e':
            # convert database entries to JSON string for custom_options entry
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            import json
            from mycodo.databases.models import Widget
            try:
                with session_scope(MYCODO_DB_PATH) as session:
                    for each_widget in session.query(Widget).all():
                        custom_options = {
                            'refresh_seconds': each_widget.refresh_duration,
                            'x_axis_minutes': each_widget.x_axis_duration,
                            'decimal_places': each_widget.decimal_places,
                            'enable_status': each_widget.enable_status,
                            'enable_value': each_widget.enable_value,
                            'enable_name': each_widget.enable_name,
                            'enable_unit': each_widget.enable_unit,
                            'enable_measurement': each_widget.enable_measurement,
                            'enable_channel': each_widget.enable_channel,
                            'enable_timestamp': each_widget.enable_timestamp,
                            'enable_navbar': each_widget.enable_navbar,
                            'enable_rangeselect': each_widget.enable_rangeselect,
                            'enable_export': each_widget.enable_export,
                            'enable_title': each_widget.enable_title,
                            'enable_auto_refresh': each_widget.enable_auto_refresh,
                            'enable_xaxis_reset': each_widget.enable_xaxis_reset,
                            'enable_manual_y_axis': each_widget.enable_manual_y_axis,
                            'enable_start_on_tick': each_widget.enable_start_on_tick,
                            'enable_end_on_tick': each_widget.enable_end_on_tick,
                            'enable_align_ticks': each_widget.enable_align_ticks,
                            'use_custom_colors': each_widget.use_custom_colors,
                            'max_measure_age': each_widget.max_measure_age,
                            'stops': each_widget.stops,
                            'min': each_widget.y_axis_min,
                            'max': each_widget.y_axis_max,
                            'option_invert': each_widget.option_invert,
                            'font_em_name': each_widget.font_em_name,
                            'font_em_value': each_widget.font_em_value,
                            'font_em_timestamp': each_widget.font_em_timestamp,
                            'enable_output_controls': each_widget.enable_output_controls,
                            'show_pid_info': each_widget.show_pid_info,
                            'show_set_setpoint': each_widget.show_set_setpoint,
                            'camera_id': each_widget.camera_id,
                            'camera_image_type': each_widget.camera_image_type,
                            'max_age': each_widget.camera_max_age
                        }

                        try:
                            custom_options['custom_yaxes'] = each_widget.math_ids.split(";")
                            custom_options['custom_colors'] = each_widget.math_ids.split(",")
                            custom_options['range_colors'] = each_widget.math_ids.split(";")
                            custom_options['disable_data_grouping'] = each_widget.math_ids.split(",")
                        except:
                            pass

                        if each_widget.graph_type == 'graph':
                            each_widget.graph_type = 'widget_graph_synchronous'
                            try:
                                custom_options['measurements_math'] = each_widget.math_ids.split(";")
                                custom_options['measurements_note_tag'] = each_widget.note_tag_ids.split(";")
                                custom_options['measurements_input'] = each_widget.input_ids_measurements.split(";")
                                custom_options['measurements_output'] = each_widget.output_ids.split(";")
                                custom_options['measurements_pid'] = each_widget.pid_ids.split(";")
                            except:
                                pass
                        elif each_widget.graph_type == 'spacer':
                            each_widget.graph_type = 'widget_spacer'
                        elif each_widget.graph_type == 'gauge_angular':
                            each_widget.graph_type = 'widget_gauge_angular'
                            custom_options['measurement'] = each_widget.input_ids_measurements
                        elif each_widget.graph_type == 'gauge_solid':
                            each_widget.graph_type = 'widget_gauge_solid'
                            custom_options['measurement'] = each_widget.input_ids_measurements
                        elif each_widget.graph_type == 'indicator':
                            each_widget.graph_type = 'widget_indicator'
                            custom_options['measurement'] = each_widget.input_ids_measurements
                        elif each_widget.graph_type == 'measurement':
                            each_widget.graph_type = 'widget_measurement'
                            custom_options['measurement'] = each_widget.input_ids_measurements
                        elif each_widget.graph_type == 'output':
                            each_widget.graph_type = 'widget_output'
                            custom_options['output'] = each_widget.output_ids
                        elif each_widget.graph_type == 'output_pwm_slider':
                            each_widget.graph_type = 'widget_output_pwm_slider'
                            custom_options['output'] = each_widget.output_ids
                        elif each_widget.graph_type == 'pid_control':
                            each_widget.graph_type = 'widget_pid'
                            custom_options['pid'] = each_widget.pid_ids
                        elif each_widget.graph_type == 'camera':
                            each_widget.graph_type = 'widget_camera'

                        each_widget.custom_options = json.dumps(custom_options)
                        session.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '4d3258ef5864':
            # The post-script for 4ea0a59dee2b didn't work to change minute to s
            # This one works
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import DeviceMeasurements
                from mycodo.databases.models import Output

                with session_scope(MYCODO_DB_PATH) as session:
                    for each_output in session.query(Output).all():
                        if each_output.output_type == 'atlas_ezo_pmp':
                            measurements = session.query(DeviceMeasurements).filter(
                                DeviceMeasurements.device_id == each_output.unique_id).all()
                            for meas in measurements:
                                if meas.unit == 'minute':
                                    meas.unit = 's'
                                    session.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '4ea0a59dee2b':
            # Only LCDs with I2C interface were supported until this revision.
            # "interface" column added in this revision.
            # Sets all current interfaces to I2C.
            # Atlas Scientific pump output duration measurements are set to minute.
            # Change unit minute to the SI unit second, like other outputs.
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import DeviceMeasurements
                from mycodo.databases.models import LCD
                from mycodo.databases.models import Output

                with session_scope(MYCODO_DB_PATH) as session:
                    for meas in session.query(DeviceMeasurements).all():
                        if meas.measurement == 'acceleration_g_force':
                            meas.measurement = 'acceleration'
                        elif meas.measurement == 'acceleration_x_g_force':
                            meas.measurement = 'acceleration_x'
                        elif meas.measurement == 'acceleration_y_g_force':
                            meas.measurement = 'acceleration_y'
                        elif meas.measurement == 'acceleration_z_g_force':
                            meas.measurement = 'acceleration_z'
                        session.commit()

                    outputs = session.query(Output).filter(
                        Output.output_type == 'atlas_ezo_pmp').all()
                    for each_output in outputs:
                        measurements = session.query(DeviceMeasurements).filter(
                            DeviceMeasurements.device_id == each_output.unique_id).all()
                        for meas in measurements:
                            if meas.unit == 'minute':
                                meas.unit = 's'
                                session.commit()

                    for lcd in session.query(LCD).all():
                        lcd.interface = 'I2C'
                        session.commit()

            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == 'af5891792291':
            # Set the output_type for PID controller outputs
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.utils.outputs import parse_output_information
                from mycodo.databases.models import DeviceMeasurements
                from mycodo.databases.models import Output
                from mycodo.databases.models import PID

                dict_outputs = parse_output_information()

                with session_scope(MYCODO_DB_PATH) as session:
                    for each_pid in session.query(PID).all():
                        try:
                            new_measurement = DeviceMeasurements()
                            new_measurement.name = "Output (Volume)"
                            new_measurement.device_id = each_pid.unique_id
                            new_measurement.measurement = 'volume'
                            new_measurement.unit = 'ml'
                            new_measurement.channel = 8
                            session.add(new_measurement)

                            if each_pid.raise_output_id:
                                output_raise = session.query(Output).filter(
                                    Output.unique_id == each_pid.raise_output_id).first()
                                if output_raise:  # Use first output type listed (default)
                                    each_pid.raise_output_type = dict_outputs[output_raise.output_type]['output_types'][0]
                            if each_pid.lower_output_id:
                                output_lower = session.query(Output).filter(
                                    Output.unique_id == each_pid.lower_output_id).first()
                                if output_lower:  # Use first output type listed (default)
                                    each_pid.lower_output_type = dict_outputs[output_lower.output_type]['output_types'][0]
                            session.commit()
                        except:
                            msg = "ERROR-1: post-alembic revision {}: {}".format(
                                each_revision, traceback.format_exc())
                            error.append(msg)
                            print(msg)

            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

        elif each_revision == '561621f634cb':
            print("Executing post-alembic code for revision {}".format(
                each_revision))
            try:
                from mycodo.databases.models import DeviceMeasurements
                from mycodo.databases.models import Output
                from mycodo.utils.outputs import parse_output_information

                dict_outputs = parse_output_information()

                with session_scope(MYCODO_DB_PATH) as session:
                    for each_output in session.query(Output).all():

                        if not session.query(DeviceMeasurements).filter(
                                DeviceMeasurements.device_id == each_output.unique_id).first():
                            # No output device measurements exist. Need to create them.
                            if ('measurements_dict' in dict_outputs[each_output.output_type] and
                                    dict_outputs[each_output.output_type]['measurements_dict'] != []):
                                for each_channel in dict_outputs[each_output.output_type]['measurements_dict']:
                                    measure_info = dict_outputs[each_output.output_type]['measurements_dict'][each_channel]
                                    new_measurement = DeviceMeasurements()
                                    if 'name' in measure_info:
                                        new_measurement.name = measure_info['name']
                                    new_measurement.device_id = each_output.unique_id
                                    new_measurement.measurement = measure_info['measurement']
                                    new_measurement.unit = measure_info['unit']
                                    new_measurement.channel = each_channel
                                    session.add(new_measurement)

                        session.commit()
            except Exception:
                msg = "ERROR: post-alembic revision {}: {}".format(
                    each_revision, traceback.format_exc())
                error.append(msg)
                print(msg)

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
        print("Completed with errors. Review the entire log for details. "
              "Errors recorded:")
        for each_error in error:
            print("ERROR: {}".format(each_error))
    else:
        print("Completed without errors. Deleting {}".format(
            ALEMBIC_UPGRADE_POST))
        try:
            os.remove(ALEMBIC_UPGRADE_POST)
        except:
            pass

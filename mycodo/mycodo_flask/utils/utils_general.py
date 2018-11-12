# -*- coding: utf-8 -*-
import glob
import importlib
import logging
from collections import OrderedDict
from datetime import datetime

import flask_login
import os
import sqlalchemy
from flask import flash
from flask import redirect
from flask import request
from flask import url_for
from flask_babel import gettext

from mycodo.config import CALIBRATION_INFO
from mycodo.config import MATH_INFO
from mycodo.config import METHOD_INFO
from mycodo.config import OUTPUT_INFO
from mycodo.config import PATH_CAMERAS
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.config_devices_units import UNITS
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import Input
from mycodo.databases.models import InputMeasurements
from mycodo.databases.models import LCD
from mycodo.databases.models import Math
from mycodo.databases.models import MathMeasurements
from mycodo.databases.models import Measurement
from mycodo.databases.models import PID
from mycodo.databases.models import PIDMeasurements
from mycodo.databases.models import Role
from mycodo.databases.models import Trigger
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import add_custom_conversions
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import cmd_output

logger = logging.getLogger(__name__)


#
# Activate/deactivate controller
#

def controller_activate_deactivate(controller_action,
                                   controller_type,
                                   controller_id):
    """
    Activate or deactivate controller

    :param controller_action: Activate or deactivate
    :type controller_action: str
    :param controller_type: The controller type (Conditional, LCD, Math, PID, Input)
    :type controller_type: str
    :param controller_id: Controller with ID to activate or deactivate
    :type controller_id: str
    """
    if not user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))

    activated = bool(controller_action == 'activate')

    translated_names = {
        "Conditional": gettext("Conditional"),
        "Input": gettext("Input"),
        "LCD": gettext("LCD"),
        "Math": gettext("Math"),
        "PID": gettext("PID"),
        "Trigger": gettext("Trigger")
    }

    mod_controller = None
    if controller_type == 'Conditional':
        mod_controller = Conditional.query.filter(
            Conditional.unique_id == controller_id).first()
    elif controller_type == 'Input':
        mod_controller = Input.query.filter(
            Input.unique_id == controller_id).first()
    elif controller_type == 'LCD':
        mod_controller = LCD.query.filter(
            LCD.unique_id == controller_id).first()
    elif controller_type == 'Math':
        mod_controller = Math.query.filter(
            Math.unique_id == controller_id).first()
    elif controller_type == 'PID':
        mod_controller = PID.query.filter(
            PID.unique_id == controller_id).first()
    elif controller_type == 'Trigger':
        mod_controller = Trigger.query.filter(
            Trigger.unique_id == controller_id).first()

    if mod_controller is None:
        flash("{type} Controller {id} doesn't exist".format(
            type=controller_type, id=controller_id), "error")
        return redirect(url_for('routes_general.home'))

    try:
        mod_controller.is_activated = activated
        db.session.commit()

        if activated:
            flash(gettext("%(cont)s controller activated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
        else:
            flash(gettext("%(cont)s controller deactivated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
    except Exception as except_msg:
        flash(gettext("Error: %(err)s",
                      err='SQL: {msg}'.format(msg=except_msg)),
              "error")

    try:
        control = DaemonControl()
        if controller_action == 'activate':
            return_values = control.controller_activate(controller_type,
                                                        controller_id)
        else:
            return_values = control.controller_deactivate(controller_type,
                                                          controller_id)
        if return_values[0]:
            flash("{err}".format(err=return_values[1]), "error")
        else:
            flash("{err}".format(err=return_values[1]), "success")
    except Exception as except_msg:
        flash(gettext("Error: %(err)s",
                      err='Daemon: {msg}'.format(msg=except_msg)),
              "error")


#
# Choices
#

def choices_measurements_units(measurements, units):
    dict_measurements = add_custom_measurements(measurements)

    # Sort dictionary by keys
    sorted_keys = sorted(list(dict_measurements), key=lambda s: s.casefold())
    sorted_dict_measurements = OrderedDict()
    for each_key in sorted_keys:
        sorted_dict_measurements[each_key] = dict_measurements[each_key]

    dict_units = add_custom_units(units)

    choices = OrderedDict()
    for each_meas, each_info in sorted_dict_measurements.items():
        for each_unit in each_info['units']:
            value = '{meas},{unit}'.format(
                meas=each_meas, unit=each_unit)
            display = '{meas}: {unit_name}'.format(
                meas=each_info['name'],
                unit_name=dict_units[each_unit]['name'])
            if dict_units[each_unit]['unit']:
                display += ' ({unit})'.format(
                    unit=dict_units[each_unit]['unit'])
            choices.update({value: display})

    return choices


def choices_conversion(conversions, measurements, units, input_measurements):
    dict_units = add_custom_units(units)
    dict_measurements = add_custom_measurements(measurements)
    dict_conversions = add_custom_conversions(conversions)

    # Sort dictionary by keys
    sorted_keys = sorted(list(dict_measurements), key=lambda s: s.casefold())
    sorted_dict_measurements = OrderedDict()
    for each_key in sorted_keys:
        sorted_dict_measurements[each_key] = dict_measurements[each_key]

    choices = {}
    for each_measurement in input_measurements:
        if each_measurement.unique_id not in choices:
            choices[each_measurement.unique_id] = OrderedDict()

        for each_conversion in dict_conversions:
            conversion_from_unit = each_conversion.split('_')[0]
            conversion_to_unit = each_conversion.split('_')[2]

            if each_measurement.unit == conversion_from_unit:
                value = '{unit},{meas}'.format(unit=conversion_to_unit, meas=each_measurement.measurement)
                display = '{meas}: {name} ({unit})'.format(
                    meas=dict_measurements[each_measurement.measurement]['name'],
                    name=dict_units[conversion_to_unit]['name'],
                    unit=dict_units[conversion_to_unit]['unit'])
                choices[each_measurement.unique_id].update({value: display})

    return choices


def choices_measurements(measurements):
    """ populate form multi-select choices from Measurement entries """
    choices = OrderedDict()
    for each_meas in measurements:
        value = '{meas}'.format(
            meas=each_meas.name_safe)
        display = '{name} ({units})'.format(
            name=each_meas.name,
            units=each_meas.units)
        choices.update({value: display})
    for each_meas, each_info in MEASUREMENTS.items():
        value = '{meas}'.format(
            meas=each_meas)
        display = '{name} ({units})'.format(
            name=each_info['name'],
            units=",".join(each_info['units']))
        choices.update({value: display})

    # Sort dictionary by keys
    sorted_keys = sorted(list(choices), key=lambda s: s.casefold())
    sorted_dict_choices = OrderedDict()
    for each_key in sorted_keys:
        sorted_dict_choices[each_key] = choices[each_key]

    return sorted_dict_choices


def choices_units(units):
    """ populate form multi-select choices from Units entries """
    choices = OrderedDict()
    for each_unit in units:
        value = '{unit}'.format(
            unit=each_unit.name_safe)
        display = '{name} ({unit})'.format(
            name=each_unit.name,
            unit=each_unit.unit)
        choices.update({value: display})
    for each_unit, each_info in UNITS.items():
        if each_info['unit']:
            value = '{unit}'.format(
                unit=each_unit)
            display = '{name} ({unit})'.format(
                name=each_info['name'],
                unit=each_info['unit'])
            choices.update({value: display})

    # Sort dictionary by keys
    sorted_keys = sorted(list(choices), key=lambda s: s.casefold())
    sorted_dict_choices = OrderedDict()
    for each_key in sorted_keys:
        sorted_dict_choices[each_key] = choices[each_key]

    return sorted_dict_choices


def choices_inputs(inputs, dict_units, dict_measurements):
    """ populate form multi-select choices from Input entries """
    choices = OrderedDict()
    for each_input in inputs:
        choices = form_input_choices(
            choices, each_input, dict_units, dict_measurements)
    return choices


def choices_maths(maths, dict_units, dict_measurements):
    """ populate form multi-select choices from Math entries """
    choices = OrderedDict()
    for each_math in maths:
        choices = form_math_choices(
            choices, each_math, dict_units, dict_measurements)
    return choices


def choices_pids(pid, dict_units, dict_measurements):
    """ populate form multi-select choices from PID entries """
    choices = OrderedDict()
    for each_pid in pid:
        choices = form_pid_choices(
            choices, each_pid, dict_units, dict_measurements)
    return choices


def choices_outputs(output):
    """ populate form multi-select choices from Output entries """
    choices = OrderedDict()
    for each_output in output:
        choices = form_output_choices(choices, each_output)
    return choices


def choices_tags(tags):
    """ populate form multi-select choices from Tag entries """
    choices = OrderedDict()
    for each_tag in tags:
        choices = form_tag_choices(choices, each_tag)
    return choices


def choices_lcd(inputs, maths, pids, outputs, dict_units, dict_measurements):
    choices = OrderedDict()

    # Display IP address
    value = '0000,IP'
    display = 'IP Address of Raspberry Pi'
    choices.update({value: display})

    # Inputs
    for each_input in inputs:
        value = '{id},input_time'.format(
            id=each_input.unique_id)
        display = '[Input {id:02d}] {name} (Timestamp)'.format(
            id=each_input.id,
            name=each_input.name)
        choices.update({value: display})
        choices = form_input_choices(
            choices, each_input, dict_units, dict_measurements)

    # Maths
    for each_math in maths:
        value = '{id},math_time'.format(
            id=each_math.unique_id)
        display = '[Math {id:02d}] {name} (Timestamp)'.format(
            id=each_math.id,
            name=each_math.name)
        choices.update({value: display})
        choices = form_math_choices(
            choices, each_math, dict_units, dict_measurements)

    # PIDs
    for each_pid in pids:
        value = '{id},pid_time'.format(
            id=each_pid.unique_id)
        display = '[PID {id:02d}] {name} (Timestamp)'.format(
            id=each_pid.id,
            name=each_pid.name)
        choices.update({value: display})
        choices = form_pid_choices(
            choices, each_pid, dict_units, dict_measurements)

    # Outputs
    for each_output in outputs:
        value = '{id},pid_time'.format(
            id=each_output.unique_id)
        display = '[Output {id:02d}] {name} (Timestamp)'.format(
            id=each_output.id,
            name=each_output.name)
        choices.update({value: display})
        choices = form_output_choices(choices, each_output)

    return choices


def form_input_choices(choices, each_input, dict_units, dict_measurements):
    input_measurements = InputMeasurements.query.filter(
        InputMeasurements.device_id == each_input.unique_id).all()

    try:
        for each_measure in input_measurements:
            value = '{input_id},{meas_id}'.format(
                input_id=each_input.unique_id,
                meas_id=each_measure.unique_id)

            if each_measure.converted_unit not in ['', None]:
                measure_display, unit_display = check_display_names(
                    each_measure.converted_measurement,
                    each_measure.converted_unit,
                    dict_units,
                    dict_measurements)
            else:
                measure_display, unit_display = check_display_names(
                    each_measure.measurement,
                    each_measure.unit,
                    dict_units,
                    dict_measurements)

            channel_number = ' CH{chan}'.format(chan=each_measure.channel + 1)

            if each_measure.name:
                channel_name = ' ({name})'.format(name=each_measure.name)
            else:
                channel_name = ''

            channel_info = "{}{}".format(channel_number, channel_name)

            if unit_display:
                display = '[Input {id:02d}] {name}{chan} ({meas}, {unit})'.format(
                    id=each_input.id,
                    name=each_input.name,
                    chan=channel_info,
                    meas=measure_display,
                    unit=unit_display)
            else:
                display = '[Input {id:02d}] {name}{chan} ({meas})'.format(
                    id=each_input.id,
                    name=each_input.name,
                    chan=channel_info,
                    meas=measure_display)
            choices.update({value: display})
    except Exception as msg:
        logger.exception("Generating input choices: {}".format(msg))

    return choices


def form_math_choices(choices, each_math, dict_units, dict_measurements):
    math_measurements = MathMeasurements.query.filter(
        MathMeasurements.device_id == each_math.unique_id).all()

    for each_measure in math_measurements:
        if each_measure.measurement and each_measure.unit:
            value = '{input_id},{meas_id}'.format(
                input_id=each_math.unique_id,
                meas_id=each_measure.unique_id)

            measure_display, unit_display = check_display_names(
                each_measure.measurement,
                each_measure.unit,
                dict_units,
                dict_measurements)
            display = '[Math {id:02d}] {name} ({meas}, {unit})'.format(
                id=each_math.id,
                name=each_measure.name,
                meas=measure_display,
                unit=unit_display)
            choices.update({value: display})

    return choices


def form_pid_choices(choices, each_pid, dict_units, dict_measurements):
    pid_measurements = PIDMeasurements.query.filter(
        PIDMeasurements.device_id == each_pid.unique_id).all()

    for each_measure in pid_measurements:
        if each_measure.measurement and each_measure.unit:
            value = '{input_id},{meas_id}'.format(
                input_id=each_pid.unique_id,
                meas_id=each_measure.unique_id)

            measure_display, unit_display = check_display_names(
                each_measure.measurement,
                each_measure.unit,
                dict_units,
                dict_measurements)
            display = '[PID {id:02d}] {name} ({meas}, {unit})'.format(
                id=each_pid.id,
                name=each_measure.name,
                meas=measure_display,
                unit=unit_display)
            choices.update({value: display})

    return choices


def form_tag_choices(choices, each_tag):
    value = '{id},tag'.format(id=each_tag.unique_id)
    display = '[Tag {id:02d}] {name}'.format(
        id=each_tag.id, name=each_tag.name)
    choices.update({value: display})
    return choices


def form_output_choices(choices, each_output):
    value = '{id},output'.format(id=each_output.unique_id)
    display = '[Output {id:02d}] {name} CH{chan}, {meas} ({unit})'.format(
        id=each_output.id,
        name=each_output.name,
        chan=each_output.channel,
        meas=MEASUREMENTS[each_output.measurement]['name'],
        unit=UNITS[each_output.unit]['unit'])
    choices.update({value: display})
    return choices


def check_display_names(measure, unit, dict_units, dict_measurements):
    if measure in dict_measurements:
        measure = dict_measurements[measure]['name']
    if unit in dict_units:
        unit = dict_units[unit]['unit']
    return measure, unit


def choices_id_name(table):
    """ Return a dictionary of all available ids and names of a table """
    choices = OrderedDict()
    for each_entry in table:
        value = each_entry.unique_id
        display = '[{id:02d}] {name}'.format(id=each_entry.id,
                                             name=each_entry.name)
        choices.update({value: display})
    return choices


def user_has_permission(permission):
    """ Determine if the currently-logged-in user has permission to perform a spceific action """
    user = User.query.filter(User.name == flask_login.current_user.name).first()
    role = Role.query.filter(Role.id == user.role_id).first()
    if ((permission == 'edit_settings' and role.edit_settings) or
        (permission == 'edit_controllers' and role.edit_controllers) or
        (permission == 'edit_users' and role.edit_users) or
        (permission == 'view_settings' and role.view_settings) or
        (permission == 'view_camera' and role.view_camera) or
        (permission == 'view_stats' and role.view_stats) or
        (permission == 'view_logs' and role.view_logs)):
        return True
    flash("You don't have permission to do that", "error")
    return False


def delete_entry_with_id(table, entry_id):
    """ Delete SQL database entry with specific id """
    try:
        entries = table.query.filter(
            table.unique_id == entry_id).first()
        db.session.delete(entries)
        db.session.commit()
        flash(gettext("%(msg)s",
                      msg='{action} {table} with ID: {id}'.format(
                          action=gettext("Delete"),
                          table=table.__tablename__,
                          id=entry_id)),
              "success")
        return 1
    except sqlalchemy.orm.exc.NoResultFound:
        flash(gettext("%(err)s",
                      err=gettext("Entry with ID %(id)s not found",
                                  id=entry_id)),
              "error")
        flash(gettext("%(msg)s",
                      msg='{action} {id}: {err}'.format(
                          action=gettext("Delete"),
                          id=entry_id,
                          err=gettext("Entry with ID %(id)s not found",
                                      id=entry_id))),
              "success")
        return 0


def flash_form_errors(form):
    """ Flashes form errors for easier display """
    for field, errors in form.errors.items():
        for error in errors:
            flash(gettext("Error in the %(field)s field - %(err)s",
                          field=getattr(form, field).label.text,
                          err=error),
                  "error")


def flash_success_errors(error, action, redirect_url):
    if error:
        for each_error in error:
            flash(gettext("%(msg)s",
                          msg='{action}: {err}'.format(
                              action=action,
                              err=each_error)),
                  "error")
        return redirect(redirect_url)
    else:
        flash(gettext("%(msg)s",
                      msg=action),
              "success")


def add_display_order(display_order, device_id):
    """ Add integer ID to list of string IDs """
    if display_order:
        display_order.append(device_id)
        return ','.join(display_order)
    return device_id


def reorder(display_order, device_id, direction):
    if direction == 'up':
        status, reord_list = reorder_list(
            display_order,
            device_id,
            'up')
    elif direction == 'down':
        status, reord_list = reorder_list(
            display_order,
            device_id,
            'down')
    else:
        status = "Fail"
        reord_list = "unrecognized command"
    return status, reord_list


def reorder_list(modified_list, item, direction):
    """ Reorder entry in a comma-separated list either up or down """
    from_position = modified_list.index(item)
    if direction == "up":
        if from_position == 0:
            return 'error', gettext('Cannot move above the first item in the list')
        to_position = from_position - 1
    elif direction == 'down':
        if from_position == len(modified_list) - 1:
            return 'error', gettext('Cannot move below the last item in the list')
        to_position = from_position + 1
    else:
        return 'error', []
    modified_list.insert(to_position, modified_list.pop(from_position))
    return 'success', modified_list


def test_sql():
    try:
        num_entries = 1000000
        factor_info = 25000
        PID.query.delete()
        db.session.commit()
        logger.error("Starting SQL uuid generation test: "
                     "{n} entries...".format(n=num_entries))
        before_count = PID.query.count()
        run_times = []
        a = datetime.now()
        for x in range(1, num_entries + 1):
            db.session.add(PID())
            if x % factor_info == 0:
                db.session.commit()
                after_count = PID.query.count()
                b = datetime.now()
                run_times.append(float((b - a).total_seconds()))
                logger.error("Run Time: {time:.2f} sec, "
                             "New entries: {new}, "
                             "Total entries: {tot}".format(
                                time=run_times[-1],
                                new=after_count - before_count,
                                tot=PID.query.count()))
                before_count = PID.query.count()
                a = datetime.now()
        avg_run_time = sum(run_times) / float(len(run_times))
        logger.error("Finished. Total: {tot} entries. "
                     "Averages: {avg:.2f} sec, "
                     "{epm:.2f} entries/min".format(
                        tot=PID.query.count(),
                        avg=avg_run_time,
                        epm=(factor_info / avg_run_time) * 60.0))
    except Exception as msg:
        logger.error("Error creating entries: {err}".format(err=msg))


def get_camera_image_info():
    """ Retrieve information about the latest camera images """
    latest_img_still_ts = {}
    latest_img_still = {}
    latest_img_tl_ts = {}
    latest_img_tl = {}

    camera = Camera.query.all()

    for each_camera in camera:
        camera_path = os.path.join(PATH_CAMERAS, '{uid}'.format(
            uid=each_camera.unique_id))
        try:
            latest_still_img_full_path = max(glob.iglob(
                '{path}/still/Still-{cam_id}-*.jpg'.format(
                    path=camera_path,
                    cam_id=each_camera.id)),
                key=os.path.getmtime)
        except ValueError:
            latest_still_img_full_path = None
        if latest_still_img_full_path:
            ts = os.path.getmtime(latest_still_img_full_path)
            latest_img_still_ts[each_camera.unique_id] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_img_still[each_camera.unique_id] = os.path.basename(latest_still_img_full_path)
        else:
            latest_img_still[each_camera.unique_id] = None

        try:
            latest_time_lapse_img_full_path = max(glob.iglob(
                '{path}/timelapse/Timelapse-{cam_id}-*.jpg'.format(
                    path=camera_path,
                    cam_id=each_camera.id)),
                key=os.path.getmtime)
        except ValueError:
            latest_time_lapse_img_full_path = None
        if latest_time_lapse_img_full_path:
            ts = os.path.getmtime(latest_time_lapse_img_full_path)
            latest_img_tl_ts[each_camera.unique_id] = datetime.fromtimestamp(
                ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_img_tl[each_camera.unique_id] = os.path.basename(
                latest_time_lapse_img_full_path)
        else:
            latest_img_tl[each_camera.unique_id] = None

    return (latest_img_still_ts, latest_img_still,
            latest_img_tl_ts, latest_img_tl)


def return_dependencies(device_type):
    unmet_deps = []
    met_deps = False

    dict_inputs = parse_input_information()

    list_dependencies = [
        dict_inputs,
        MATH_INFO,
        METHOD_INFO,
        OUTPUT_INFO,
        CALIBRATION_INFO
    ]
    for each_section in list_dependencies:
        if device_type in each_section:
            for each_device, each_dict in each_section[device_type].items():
                if each_device == 'dependencies_module':
                    for (install_type, package, install_id) in each_dict:
                        entry = (package, '{0} {1}'.format(install_type, install_id), install_type, install_id)
                        if install_type in ['pip-pypi', 'pip-git']:
                            try:
                                module = importlib.util.find_spec(package)
                                if module is None:
                                    if entry not in unmet_deps:
                                        unmet_deps.append(entry)
                                else:
                                    met_deps = True
                            except ImportError:
                                if entry not in unmet_deps:
                                    unmet_deps.append(entry)
                        elif install_type == 'apt':
                            cmd = 'dpkg -l {}'.format(package)
                            _, _, stat = cmd_output(cmd)
                            if stat and entry not in unmet_deps:
                                unmet_deps.append(entry)
                            else:
                                met_deps = True
                        elif install_type == 'internal':
                            if package.startswith('file-exists'):
                                filepath = package.split(' ')[1]
                                if not os.path.isfile(filepath):
                                    if entry not in unmet_deps:
                                        unmet_deps.append(entry)
                                    else:
                                        met_deps = True
                            if package.startswith('pip-exists'):
                                py_module = package.split(' ')[1]
                                try:
                                    module = importlib.util.find_spec(py_module)
                                    if module is None:
                                        if entry not in unmet_deps:
                                            unmet_deps.append(entry)
                                    else:
                                        met_deps = True
                                except ImportError:
                                    if entry not in unmet_deps:
                                        unmet_deps.append(entry)

                    if not each_dict:
                        met_deps = True

    return unmet_deps, met_deps


def use_unit_generate(input_dev, input_measurements, output, math, math_measurements):
    """Generate dictionary of units to convert to"""
    # TODO: next major version: rename table columns and combine functionality
    use_unit = {}

    # Input and Math controllers have measurement tables with the same schema
    list_devices_with_measurements = [
        input_dev, math
    ]

    for devices in list_devices_with_measurements:
        for each_device in devices:
            use_unit[each_device.unique_id] = {}

            for each_meas in input_measurements:
                if each_meas.device_id == each_device.unique_id:
                    if each_meas.measurement not in use_unit[each_device.unique_id]:
                        use_unit[each_device.unique_id][each_meas.measurement] = {}
                    if each_meas.unit not in use_unit[each_device.unique_id][each_meas.measurement]:
                        use_unit[each_device.unique_id][each_meas.measurement][each_meas.unit] = OrderedDict()
                    use_unit[each_device.unique_id][each_meas.measurement][each_meas.unit][each_meas.channel] = None

    for each_output in output:
        use_unit[each_output.unique_id] = {}
        if each_output.output_type == 'wired':
            use_unit[each_output.unique_id]['duration_time'] = 'second'

    return use_unit


def get_ip_address():
    return request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown address')


def generate_form_input_list(dict_inputs):
    # Sort dictionary entries by input_manufacturer, then input_name
    # Results in list of sorted dictionary keys
    list_tuples_sorted = sorted(dict_inputs.items(), key=lambda x: (x[1]['input_manufacturer'], x[1]['input_name']))
    list_inputs_sorted = []
    for each_input in list_tuples_sorted:
        list_inputs_sorted.append(each_input[0])
    return list_inputs_sorted

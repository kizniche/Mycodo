# -*- coding: utf-8 -*-
import json
import logging
import subprocess

import sqlalchemy
from flask import current_app, flash, url_for
from flask_babel import gettext

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases import clone_model, set_uuid
from mycodo.databases.models import (PID, Conversion, CustomController,
                                     Dashboard, DeviceMeasurements, Input,
                                     Output, Widget)
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import (
    custom_options_return_json, delete_entry_with_id, flash_success_errors,
    return_dependencies, use_unit_generate)
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger(__name__)

#
# Dashboards
#

def dashboard_add():
    """Add a dashboard."""
    error = []

    last_dashboard = Dashboard.query.order_by(
        Dashboard.id.desc()).first()

    new_dash = Dashboard()
    new_dash.name = f"{TRANSLATIONS['dashboard']['title']} {last_dashboard.id + 1}"

    if not error:
        new_dash.save()

        flash(gettext(
            "Dashboard with ID %(id)s successfully added", id=new_dash.id),
            "success")

    return new_dash.unique_id


def dashboard_mod(form):
    """Modify a dashboard."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['dashboard']['title'])
    error = []

    dash_mod = Dashboard.query.filter(
        Dashboard.unique_id == form.dashboard_id.data).first()

    name_exists = Dashboard.query.filter(
        Dashboard.name == form.name.data).first()
    if dash_mod.name != form.name.data and name_exists:
        flash('Dashboard name already is use', 'error')

    dash_mod.name = form.name.data

    if not error:
        db.session.commit()

    flash_success_errors(
        error, action, url_for('routes_dashboard.page_dashboard_default'))


def dashboard_lock(dashboard_id, lock):
    """Lock a dashboard."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['lock']['title'],
        controller=TRANSLATIONS['dashboard']['title'])
    error = []

    try:
        dash_mod = Dashboard.query.filter(
            Dashboard.unique_id == dashboard_id).first()

        dash_mod.locked = lock

        if not error:
            db.session.commit()

    except Exception as msg:
        error.append(msg)
        logger.exception("Duplicating dashboard")

    flash_success_errors(
        error, action, url_for('routes_dashboard.page_dashboard_default'))


def dashboard_copy(form):
    """Duplicate a dashboard and its widgets."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['duplicate']['title'],
        controller=TRANSLATIONS['dashboard']['title'])
    error = []

    try:
        # Get current dashboard and its widgets
        dashboard = Dashboard.query.filter(
            Dashboard.unique_id == form.dashboard_id.data).first()
        widgets = Widget.query.filter(
            Widget.dashboard_id == dashboard.unique_id).all()

        # Duplicate dashboard with new unique_id and name
        new_dashboard = clone_model(
            dashboard, unique_id=set_uuid(), name="New Dashboard")

        # Duplicate all widgets and assign them to the new dashboard
        for each_widget in widgets:
            clone_model(each_widget, unique_id=set_uuid(), dashboard_id=new_dashboard.unique_id)
    except Exception as msg:
        error.append(msg)
        logger.exception("Duplicating dashboard")

    flash_success_errors(
        error, action, url_for('routes_dashboard.page_dashboard_default'))


def dashboard_del(form):
    """Delete a dashboard."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['dashboard']['title'])
    error = []
    create_new_dash = False

    dashboards = Dashboard.query.all()
    if len(dashboards) == 1:
        create_new_dash = True

    widgets = Widget.query.filter(
        Widget.dashboard_id == form.dashboard_id.data).all()
    for each_widget in widgets:
        delete_entry_with_id(Widget, each_widget.unique_id)

    delete_entry_with_id(Dashboard, form.dashboard_id.data)

    if create_new_dash:
        new_dash = Dashboard()
        new_dash.name = 'New Dashboard'
        new_dash.save()

    flash_success_errors(
        error, action, url_for('routes_dashboard.page_dashboard_default'))


#
# Widgets
#

def widget_add(form_base, request_form):
    """Add a widget to the dashboard."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['widget']['title'])
    error = []

    reload_flask = False

    dict_widgets = parse_widget_information()

    if form_base.widget_type.data:
        widget_name = form_base.widget_type.data
    else:
        widget_name = ''
        error.append("Missing widget name")

    if current_app.config['TESTING']:
        dep_unmet = False
    else:
        dep_unmet, _, _ = return_dependencies(widget_name)
        if dep_unmet:
            list_unmet_deps = []
            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[3])
            error.append("The {dev} device you're trying to add has unmet dependencies: {dep}".format(
                dev=widget_name, dep=', '.join(list_unmet_deps)))

    new_widget = Widget()
    new_widget.dashboard_id = form_base.dashboard_id.data
    new_widget.graph_type = widget_name
    new_widget.name = form_base.name.data
    new_widget.font_em_name = form_base.font_em_name.data
    new_widget.enable_drag_handle = form_base.enable_drag_handle.data
    new_widget.refresh_duration = form_base.refresh_duration.data

    # Find where the next widget should be placed on the grid
    # Finds the lowest position to create as the new Widget's starting position
    position_y_start = 0
    for each_widget in Widget.query.filter(
            Widget.dashboard_id == form_base.dashboard_id.data).all():
        highest_position = each_widget.position_y + each_widget.height
        if highest_position > position_y_start:
            position_y_start = highest_position
    new_widget.position_y = position_y_start

    # widget add options
    if widget_name in dict_widgets:
        def dict_has_value(key):
            if (key in dict_widgets[widget_name] and
                    (dict_widgets[widget_name][key] or dict_widgets[widget_name][key] == 0)):
                return True

        if dict_has_value('widget_width'):
            new_widget.width = dict_widgets[widget_name]['widget_width']
        if dict_has_value('widget_height'):
            new_widget.height = dict_widgets[widget_name]['widget_height']

    # Generate string to save from custom options
    error, custom_options = custom_options_return_json(
        error, dict_widgets, request_form, device=widget_name, use_defaults=True)
    new_widget.custom_options = custom_options

    #
    # Execute at Creation
    #

    if ('execute_at_creation' in dict_widgets[widget_name] and
            not current_app.config['TESTING']):
        error, new_widget = dict_widgets[widget_name]['execute_at_creation'](
            error, new_widget, dict_widgets[widget_name])

    try:
        if not error:
            new_widget.save()

            # If the first of this widget added, reload the frontend
            # Otherwise, if add_url_rule is called in register_widget_endpoints(), it will result in an error:
            # AssertionError: The setup method 'add_url_rule' can no longer be called on the application.
            # It has already handled its first request, any changes will not be applied consistently.
            # Make sure all imports, decorators, functions, etc. needed to set up the application are done before running it.
            if Widget.query.filter(Widget.graph_type == widget_name).count() == 1:
                reload_flask = True

            if not current_app.config['TESTING']:
                # Refresh widget settings
                control = DaemonControl()
                control.widget_add_refresh(new_widget.unique_id)

            flash(gettext(
                "{dev} with ID %(id)s successfully added".format(
                    dev=dict_widgets[form_base.widget_type.data]['widget_name']),
                id=new_widget.id),
                "success")
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)

    for each_error in error:
        flash(each_error, "error")

    return dep_unmet, reload_flask


def widget_mod(form_base, request_form):
    """Modify the settings of an item on the dashboard."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['widget']['title'])
    error = []

    dict_widgets = parse_widget_information()

    mod_widget = Widget.query.filter(
        Widget.unique_id == form_base.widget_id.data).first()
    mod_widget.name = form_base.name.data
    mod_widget.font_em_name = form_base.font_em_name.data
    mod_widget.enable_drag_handle = form_base.enable_drag_handle.data
    mod_widget.refresh_duration = form_base.refresh_duration.data

    try:
        custom_options_json_presave = json.loads(mod_widget.custom_options)
    except:
        logger.error("Malformed JSON")
        custom_options_json_presave = {}

    # Generate string to save from custom options
    error, custom_options_json_postsave = custom_options_return_json(
        error, dict_widgets, request_form, mod_dev=mod_widget, device=mod_widget.graph_type)

    if 'execute_at_modification' in dict_widgets[mod_widget.graph_type]:
        (allow_saving,
         page_refresh,
         mod_widget,
         custom_options) = dict_widgets[mod_widget.graph_type]['execute_at_modification'](
            mod_widget, request_form, custom_options_json_presave, json.loads(custom_options_json_postsave))
        custom_options = json.dumps(custom_options)  # Convert from dict to JSON string
        if not allow_saving:
            error.append("execute_at_modification() would not allow widget options to be saved")
    else:
        custom_options = custom_options_json_postsave

    mod_widget.custom_options = custom_options

    if not error:
        try:
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

        control = DaemonControl()
        control.widget_add_refresh(mod_widget.unique_id)

    flash_success_errors(error, action, url_for(
        'routes_dashboard.page_dashboard',
        dashboard_id=form_base.dashboard_id.data))


def widget_del(form_base):
    """Delete a widget from a dashboard."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['widget']['title'])
    error = []

    dict_widgets = parse_widget_information()
    widget = Widget.query.filter(
        Widget.unique_id == form_base.widget_id.data).first()

    try:
        if 'execute_at_deletion' in dict_widgets[widget.graph_type]:
            dict_widgets[widget.graph_type]['execute_at_deletion'](form_base.widget_id.data)
    except Exception as except_msg:
        error.append(except_msg)

    try:
        delete_entry_with_id(Widget, form_base.widget_id.data)

        control = DaemonControl()
        control.widget_remove(form_base.widget_id.data)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_dashboard.page_dashboard',
                               dashboard_id=form_base.dashboard_id.data))


def graph_y_axes_async(dict_measurements, ids_measures):
    """Determine which y-axes to use for each Graph."""
    if not ids_measures:
        return

    y_axes = []

    function = CustomController.query.all()
    device_measurements = DeviceMeasurements.query.all()
    input_dev = Input.query.all()
    output = Output.query.all()
    pid = PID.query.all()

    devices_list = [input_dev, output, pid]

    # Iterate through device tables
    for each_device in devices_list:

        # Iterate through each set of ID and measurement of the dashboard element
        for each_id_measure in ids_measures:

            if ',' in each_id_measure:
                measure_id = each_id_measure.split(',')[1]
                measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == measure_id).first()

                if not measurement:
                    pass
                elif measurement.conversion_id:
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == measurement.conversion_id).first()
                    if not conversion:
                        pass
                    elif not y_axes:
                        y_axes = [conversion.convert_unit_to]
                    elif y_axes and conversion.convert_unit_to not in y_axes:
                        y_axes.append(conversion.convert_unit_to)
                elif (measurement.rescaled_measurement and
                        measurement.rescaled_unit):
                    if not y_axes:
                        y_axes = [measurement.rescaled_unit]
                    elif y_axes and measurement.rescaled_unit not in y_axes:
                        y_axes.append(measurement.rescaled_unit)
                else:
                    if not y_axes:
                        y_axes = [measurement.unit]
                    elif y_axes and measurement.unit not in y_axes:
                        y_axes.append(measurement.unit)

            if len(each_id_measure.split(',')) > 1 and each_id_measure.split(',')[1].startswith('channel_'):
                unit = each_id_measure.split(',')[1].split('_')[4]

                if not y_axes:
                    y_axes = [unit]
                elif y_axes and unit not in y_axes:
                    y_axes.append(unit)

            else:
                if len(each_id_measure.split(',')) == 2:
                    unique_id = each_id_measure.split(',')[0]
                    measurement = each_id_measure.split(',')[1]

                    # Iterate through each device entry
                    for each_device_entry in each_device:

                        # If the ID saved to the dashboard element matches the table entry ID
                        if each_device_entry.unique_id == unique_id:
                            y_axes = check_func(each_device,
                                                unique_id,
                                                y_axes,
                                                measurement,
                                                dict_measurements,
                                                device_measurements,
                                                input_dev,
                                                output,
                                                function)

                elif len(each_id_measure.split(',')) == 3:
                    unique_id = each_id_measure.split(',')[0]
                    measurement = each_id_measure.split(',')[1]
                    unit = each_id_measure.split(',')[2]

                    # Iterate through each device entry
                    for each_device_entry in each_device:

                        # If the ID saved to the dashboard element matches the table entry ID
                        if each_device_entry.unique_id == unique_id:
                            y_axes = check_func(each_device,
                                                unique_id,
                                                y_axes,
                                                measurement,
                                                dict_measurements,
                                                device_measurements,
                                                input_dev,
                                                output,
                                                function,
                                                unit=unit)

    return y_axes


def check_func(all_devices,
               unique_id,
               y_axes,
               measurement,
               dict_measurements,
               device_measurements,
               input_dev,
               output,
               function,
               unit=None):
    """
    Generate a list of y-axes
    :param all_devices: Input, Output, and PID SQL entries of a table
    :param unique_id: The ID of the measurement
    :param y_axes: empty list to populate
    :param measurement:
    :param dict_measurements:
    :param device_measurements:
    :param input_dev:
    :param output:
    :param function
    :param unit:
    :return: None
    """
    # Iterate through each device entry
    for each_device in all_devices:

        # If the ID saved to the dashboard element matches the table entry ID
        if each_device.unique_id == unique_id:

            use_unit = use_unit_generate(
                device_measurements, input_dev, output, function)

            # Add duration
            if measurement == 'duration_time':
                if 'second' not in y_axes:
                    y_axes.append('second')

            # Add duty cycle
            elif measurement == 'duty_cycle':
                if 'percent' not in y_axes:
                    y_axes.append('percent')

            # Use custom-converted units
            elif (unique_id in use_unit and
                    measurement in use_unit[unique_id] and
                    use_unit[unique_id][measurement]):
                measure_short = use_unit[unique_id][measurement]
                if measure_short not in y_axes:
                    y_axes.append(measure_short)

            # Find the y-axis the setpoint or bands apply to
            elif measurement in ['setpoint', 'setpoint_band_min', 'setpoint_band_max']:
                for each_input in input_dev:
                    if each_input.unique_id == each_device.measurement.split(',')[0]:
                        pid_measurement = each_device.measurement.split(',')[1]

                        # If PID uses input with custom conversion, use custom unit
                        if (each_input.unique_id in use_unit and
                                pid_measurement in use_unit[each_input.unique_id] and
                                use_unit[each_input.unique_id][pid_measurement]):
                            measure_short = use_unit[each_input.unique_id][pid_measurement]
                            if measure_short not in y_axes:
                                y_axes.append(measure_short)
                        # Else use default unit for input measurement
                        else:
                            if pid_measurement in dict_measurements:
                                measure_short = dict_measurements[pid_measurement]['meas']
                                if measure_short not in y_axes:
                                    y_axes.append(measure_short)

            # Append all other measurements if they don't already exist
            elif measurement in dict_measurements and not unit:
                measure_short = dict_measurements[measurement]['meas']
                if measure_short not in y_axes:
                    y_axes.append(measure_short)

            # use custom y-axis
            elif measurement not in dict_measurements or unit not in dict_measurements[measurement]['units']:
                meas_name = '{meas}_{un}'.format(meas=measurement, un=unit)
                if meas_name not in y_axes and unit:
                    y_axes.append(meas_name)

    return y_axes

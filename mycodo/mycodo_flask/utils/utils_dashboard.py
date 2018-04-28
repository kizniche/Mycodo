# -*- coding: utf-8 -*-
import logging

import re
import sqlalchemy
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import MEASUREMENT_UNITS
from mycodo.databases.models import Dashboard
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import use_unit_generate
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# Dashboard
#

def dashboard_add(form_base, form_object, display_order):
    """
    Add an item to the dashboard

    Either Graph, Gauge, or Camera
    """
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Dashboard"))
    error = []
    dashboard_type = ''

    new_graph = Dashboard()
    new_graph.name = form_base.name.data

    # Graph
    if (form_base.dashboard_type.data == 'graph' and
            (form_base.name.data and
             form_base.width.data and
             form_base.height.data and
             form_object.xaxis_duration.data and
             form_base.refresh_duration.data)):

        dashboard_type = 'Graph'
        error = graph_error_check(form_object, error)
        new_graph.graph_type = form_base.dashboard_type.data
        if form_object.math_ids.data:
            math_ids_joined = ";".join(form_object.math_ids.data)
            new_graph.math_ids = math_ids_joined
        if form_object.pid_ids.data:
            pid_ids_joined = ";".join(form_object.pid_ids.data)
            new_graph.pid_ids = pid_ids_joined
        if form_object.output_ids.data:
            output_ids_joined = ";".join(form_object.output_ids.data)
            new_graph.output_ids = output_ids_joined
        if form_object.input_ids.data:
            input_ids_joined = ";".join(form_object.input_ids.data)
            new_graph.input_ids_measurements = input_ids_joined
        new_graph.width = form_base.width.data
        new_graph.height = form_base.height.data
        new_graph.x_axis_duration = form_object.xaxis_duration.data
        new_graph.refresh_duration = form_base.refresh_duration.data
        new_graph.enable_auto_refresh = form_object.enable_auto_refresh.data
        new_graph.enable_xaxis_reset = form_object.enable_xaxis_reset.data
        new_graph.enable_title = form_object.enable_title.data
        new_graph.enable_navbar = form_object.enable_navbar.data
        new_graph.enable_rangeselect = form_object.enable_range.data
        new_graph.enable_export = form_object.enable_export.data
        new_graph.enable_graph_shift = form_object.enable_graph_shift.data
        new_graph.enable_manual_y_axis = form_object.enable_manual_y_axis.data

    # Gauge
    elif form_base.dashboard_type.data == 'gauge':

        dashboard_type = 'Gauge'
        error = gauge_error_check(form_object, error)
        new_graph.graph_type = form_object.gauge_type.data
        if form_object.gauge_type.data == 'gauge_solid':
            new_graph.range_colors = '20,#33CCFF;40,#55BF3B;60,#DDDF0D;80,#DF5353'
        elif form_object.gauge_type.data == 'gauge_angular':
            new_graph.range_colors = '0,25,#33CCFF;25,50,#55BF3B;50,75,#DDDF0D;75,100,#DF5353'
        new_graph.width = form_base.width.data
        new_graph.height = form_base.height.data
        new_graph.max_measure_age = form_object.max_measure_age.data
        new_graph.refresh_duration = form_base.refresh_duration.data
        new_graph.y_axis_min = form_object.y_axis_min.data
        new_graph.y_axis_max = form_object.y_axis_max.data
        new_graph.input_ids_measurements = form_object.input_ids.data
        new_graph.enable_timestamp = form_object.enable_timestamp.data

    # Measurement
    elif form_base.dashboard_type.data == 'measurement':

        dashboard_type = 'Measurement'
        error = measurement_error_check(form_object, error)
        new_graph.graph_type = 'measurement'
        new_graph.width = form_base.width.data
        new_graph.height = form_base.height.data
        new_graph.max_measure_age = form_object.max_measure_age.data
        new_graph.refresh_duration = form_base.refresh_duration.data
        new_graph.font_em_value = form_object.font_em_value.data
        new_graph.font_em_timestamp = form_object.font_em_timestamp.data
        new_graph.decimal_places = form_object.decimal_places.data
        new_graph.input_ids_measurements = form_object.measurement_id.data

    # Output
    elif form_base.dashboard_type.data == 'output':

        dashboard_type = 'Output'
        error = output_error_check(form_object, error)
        new_graph.graph_type = 'output'
        new_graph.width = form_base.width.data
        new_graph.height = form_base.height.data
        new_graph.max_measure_age = form_object.max_measure_age.data
        new_graph.refresh_duration = form_base.refresh_duration.data
        new_graph.font_em_value = form_object.font_em_value.data
        new_graph.font_em_timestamp = form_object.font_em_timestamp.data
        new_graph.enable_output_controls = form_object.enable_output_controls.data
        new_graph.decimal_places = form_object.decimal_places.data
        new_graph.output_ids = form_object.output_id.data

    # PID Control
    elif form_base.dashboard_type.data == 'pid_control':

        dashboard_type = 'PID Control'
        error = pid_error_check(form_object, error)
        new_graph.graph_type = 'pid_control'
        new_graph.width = form_base.width.data
        new_graph.height = form_base.height.data
        new_graph.max_measure_age = form_object.max_measure_age.data
        new_graph.refresh_duration = form_base.refresh_duration.data
        new_graph.font_em_value = form_object.font_em_value.data
        new_graph.font_em_timestamp = form_object.font_em_timestamp.data
        new_graph.decimal_places = form_object.decimal_places.data
        new_graph.show_pid_info = form_object.show_pid_info.data
        new_graph.show_set_setpoint = form_object.show_set_setpoint.data
        new_graph.pid_ids = form_object.pid_id.data

    # Camera
    elif (form_base.dashboard_type.data == 'camera' and
          form_object.camera_id.data):

        dashboard_type = 'Camera'
        new_graph.graph_type = form_base.dashboard_type.data
        new_graph.width = form_base.width.data
        new_graph.height = form_base.height.data
        new_graph.refresh_duration = form_base.refresh_duration.data
        new_graph.camera_max_age = form_object.camera_max_age.data
        new_graph.camera_id = form_object.camera_id.data
        new_graph.camera_image_type = form_object.camera_image_type.data
    else:
        flash_form_errors(form_base)
        return

    try:
        if not error:
            new_graph.save()
            flash(gettext(
                "{dev} with ID %(id)s successfully added".format(dev=dashboard_type),
                id=new_graph.id),
                "success")
            DisplayOrder.query.first().dashboard = add_display_order(
                display_order, new_graph.unique_id)
            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_dashboard'))


def dashboard_mod(form_base, form_object, request_form):
    """Modify the settings of an item on the dashboard"""
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Dashboard"))
    error = []

    mod_graph = Dashboard.query.filter(
        Dashboard.unique_id == form_base.dashboard_id.data).first()
    mod_graph.name = form_base.name.data

    # Graph Mod
    if form_base.dashboard_type.data == 'graph':

        error = graph_error_check(form_object, error)

        # Generate color option string from form inputs
        sorted_colors_string, error = custom_colors_graph_str(request_form, error)
        mod_graph.custom_colors = sorted_colors_string
        mod_graph.use_custom_colors = form_object.use_custom_colors.data

        # Generate y-axis option string from form inputs
        yaxes_string = custom_yaxes_str_from_form(request_form)
        mod_graph.custom_yaxes = yaxes_string
        mod_graph.enable_manual_y_axis = form_object.enable_manual_y_axis.data
        mod_graph.enable_align_ticks = form_object.enable_align_ticks.data
        mod_graph.enable_start_on_tick = form_object.enable_start_on_tick.data
        mod_graph.enable_end_on_tick = form_object.enable_end_on_tick.data

        if form_object.math_ids.data:
            math_ids_joined = ";".join(form_object.math_ids.data)
            mod_graph.math_ids = math_ids_joined
        else:
            mod_graph.math_ids = ''

        if form_object.pid_ids.data:
            pid_ids_joined = ";".join(form_object.pid_ids.data)
            mod_graph.pid_ids = pid_ids_joined
        else:
            mod_graph.pid_ids = ''

        if form_object.output_ids.data:
            output_ids_joined = ";".join(form_object.output_ids.data)
            mod_graph.output_ids = output_ids_joined
        else:
            mod_graph.output_ids = ''

        if form_object.input_ids.data:
            input_ids_joined = ";".join(form_object.input_ids.data)
            mod_graph.input_ids_measurements = input_ids_joined
        else:
            mod_graph.input_ids_measurements = ''

        mod_graph.width = form_base.width.data
        mod_graph.height = form_base.height.data
        mod_graph.x_axis_duration = form_object.xaxis_duration.data
        mod_graph.refresh_duration = form_base.refresh_duration.data
        mod_graph.enable_auto_refresh = form_object.enable_auto_refresh.data
        mod_graph.enable_xaxis_reset = form_object.enable_xaxis_reset.data
        mod_graph.enable_title = form_object.enable_title.data
        mod_graph.enable_navbar = form_object.enable_navbar.data
        mod_graph.enable_export = form_object.enable_export.data
        mod_graph.enable_rangeselect = form_object.enable_range.data
        mod_graph.enable_graph_shift = form_object.enable_graph_shift.data

    # If a gauge type is changed, the color format must change
    elif (form_base.dashboard_type.data == 'gauge' and
            mod_graph.graph_type != form_object.gauge_type.data):

        mod_graph.graph_type = form_object.gauge_type.data
        if form_object.gauge_type.data == 'gauge_solid':
            mod_graph.range_colors = '0.2,#33CCFF;0.4,#55BF3B;0.6,#DDDF0D;0.8,#DF5353'
        elif form_object.gauge_type.data == 'gauge_angular':
            mod_graph.range_colors = '0,25,#33CCFF;25,50,#55BF3B;50,75,#DDDF0D;75,100,#DF5353'

    # Gauge Mod
    elif form_base.dashboard_type.data == 'gauge':

        error = gauge_error_check(form_object, error)

        # Generate color option string from form inputs
        sorted_colors_string, error = custom_colors_gauge_str(
            request_form, form_object.gauge_type.data, error)

        mod_graph.range_colors = sorted_colors_string
        mod_graph.width = form_base.width.data
        mod_graph.height = form_base.height.data
        mod_graph.refresh_duration = form_base.refresh_duration.data
        mod_graph.y_axis_min = form_object.y_axis_min.data
        mod_graph.y_axis_max = form_object.y_axis_max.data
        mod_graph.max_measure_age = form_object.max_measure_age.data
        mod_graph.enable_timestamp = form_object.enable_timestamp.data
        if form_object.input_ids.data:
            mod_graph.input_ids_measurements = form_object.input_ids.data
        else:
            error.append("A valid Measurement must be selected")

    # Measurement Mod
    elif form_base.dashboard_type.data == 'measurement':

        error = measurement_error_check(form_object, error)
        mod_graph.width = form_base.width.data
        mod_graph.height = form_base.height.data
        mod_graph.refresh_duration = form_base.refresh_duration.data
        mod_graph.max_measure_age = form_object.max_measure_age.data
        mod_graph.font_em_value = form_object.font_em_value.data
        mod_graph.font_em_timestamp = form_object.font_em_timestamp.data
        mod_graph.decimal_places = form_object.decimal_places.data
        if form_object.measurement_id.data:
            mod_graph.input_ids_measurements = form_object.measurement_id.data

    # Output Mod
    elif form_base.dashboard_type.data == 'output':

        error = output_error_check(form_object, error)
        mod_graph.width = form_base.width.data
        mod_graph.height = form_base.height.data
        mod_graph.refresh_duration = form_base.refresh_duration.data
        mod_graph.max_measure_age = form_object.max_measure_age.data
        mod_graph.font_em_value = form_object.font_em_value.data
        mod_graph.font_em_timestamp = form_object.font_em_timestamp.data
        mod_graph.decimal_places = form_object.decimal_places.data
        mod_graph.enable_output_controls = form_object.enable_output_controls.data
        if form_object.output_id.data:
            mod_graph.output_ids = form_object.output_id.data

    # PID Control Mod
    elif form_base.dashboard_type.data == 'pid_control':

        error = pid_error_check(form_object, error)
        mod_graph.width = form_base.width.data
        mod_graph.height = form_base.height.data
        mod_graph.refresh_duration = form_base.refresh_duration.data
        mod_graph.max_measure_age = form_object.max_measure_age.data
        mod_graph.font_em_value = form_object.font_em_value.data
        mod_graph.font_em_timestamp = form_object.font_em_timestamp.data
        mod_graph.decimal_places = form_object.decimal_places.data
        mod_graph.show_pid_info = form_object.show_pid_info.data
        mod_graph.show_set_setpoint = form_object.show_set_setpoint.data
        if form_object.pid_id.data:
            mod_graph.pid_ids = form_object.pid_id.data

    # Camera Mod
    elif form_base.dashboard_type.data == 'camera':
        mod_graph.width = form_base.width.data
        mod_graph.height = form_base.height.data
        mod_graph.refresh_duration = form_base.refresh_duration.data
        mod_graph.camera_max_age = form_object.camera_max_age.data
        mod_graph.camera_id = form_object.camera_id.data
        mod_graph.camera_image_type = form_object.camera_image_type.data

    else:
        flash_form_errors(form_base)

    if not error:
        try:
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_dashboard'))


def dashboard_del(form_base):
    """Delete an item on the dashboard"""
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Dashboard"))
    error = []

    try:
        delete_entry_with_id(Dashboard,
                             form_base.dashboard_id.data)
        display_order = csv_to_list_of_str(DisplayOrder.query.first().dashboard)
        display_order.remove(form_base.dashboard_id.data)
        DisplayOrder.query.first().dashboard = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_dashboard'))


def dashboard_reorder(dashboard_id, display_order, direction):
    """reorder something on the dashboard"""
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Dashboard"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     dashboard_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().dashboard = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_dashboard'))


def graph_error_check(form, error):
    """Determine if there are any errors in the graph form"""
    # Error checks go here
    return error


def gauge_error_check(form, error):
    """Determine if there are any errors in the gauge form"""
    if not form.input_ids.data:
        error.append("A valid Measurement must be selected")
    return error


def measurement_error_check(form, error):
    """Determine if there are any errors in the gauge form"""
    if form.measurement_id.data == '':
        error.append("A valid Measurement must be selected")
    return error


def output_error_check(form, error):
    """Determine if there are any errors in the gauge form"""
    if form.output_id.data == '':
        error.append("A valid Output must be selected")
    return error


def pid_error_check(form, error):
    """Determine if there are any errors in the gauge form"""
    if form.pid_id.data == '':
        error.append("A valid PID Controller must be selected")
    return error


def graph_y_axes(dict_measurements):
    """ Determine which y-axes to use for each Graph """
    y_axes = {}

    graph = Dashboard.query.all()
    input_dev = Input.query.all()
    math = Math.query.all()
    output = Output.query.all()
    pid = PID.query.all()

    devices_list = [input_dev, math, output, pid]

    # Iterate through each Dashboard object
    for each_graph in graph:

        # Iterate through device tables
        for each_device in devices_list:

            if each_device == input_dev:
                ids_and_measures = each_graph.input_ids_measurements.split(';')
            elif each_device == math:
                ids_and_measures = each_graph.math_ids.split(';')
            elif each_device == output:
                ids_and_measures = each_graph.output_ids.split(';')
            elif each_device == pid:
                ids_and_measures = each_graph.pid_ids.split(';')
            else:
                ids_and_measures = []

            # Iterate through each set of ID and measurement of the
            # dashboard element
            for each_id_measure in ids_and_measures:
                if len(each_id_measure.split(',')) == 2:
                    if each_graph.unique_id not in y_axes:
                        y_axes[each_graph.unique_id] = []

                    unique_id = each_id_measure.split(',')[0]
                    measurement = each_id_measure.split(',')[1]

                    y_axes[each_graph.unique_id] = check_func(
                        each_device,
                        unique_id,
                        y_axes[each_graph.unique_id],
                        measurement,
                        dict_measurements,
                        input_dev)

    return y_axes


def graph_y_axes_async(dict_measurements, ids_measures):
    """ Determine which y-axes to use for each Graph """
    if ids_measures == None:
        return

    y_axes = []

    input_dev = Input.query.all()
    math = Math.query.all()
    output = Output.query.all()
    pid = PID.query.all()

    devices_list = [input_dev, math, output, pid]

    # Iterate through device tables
    for each_device in devices_list:

        # Iterate through each set of ID and measurement of the dashboard element
        for each_id_measure in ids_measures:
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
                                            input_dev)

    return y_axes

def check_func(all_devices, unique_id, y_axes, measurement, dict_measurements, input_dev):
    """
    Generate a list of y-axes for Live and Asynchronous Graphs
    :param all Input, Math, Output, and PID SQL entries of a table
    :param unique_id: The ID of the measurement
    :param y_axes: empty list to populate
    :param measurement:
    :param dict_measurements:
    :param input_dev:
    :return: None
    """
    # Iterate through each device entry
    for each_device in all_devices:

        # If the ID saved to the dashboard element matches the table entry ID
        if each_device.unique_id == unique_id:

            use_unit = use_unit_generate(input_dev)

            # Add duration_sec
            if measurement == 'duration_sec':
                if 'duration_sec' not in y_axes:
                    y_axes.append('duration_sec')

            # Use Linux Command measurement
            elif (all_devices == input_dev and
                    each_device.cmd_measurement and
                    each_device.cmd_measurement != '' and
                    each_device.cmd_measurement == measurement and
                    each_device.cmd_measurement not in y_axes):
                y_axes.append(each_device.cmd_measurement)

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
            elif measurement in dict_measurements:
                measure_short = dict_measurements[measurement]['meas']
                if measure_short not in y_axes:
                    y_axes.append(measure_short)

    return y_axes


def custom_colors_gauge_str(form, gauge_type, error):
    """
    Get variable number of gauge color inputs, turn into CSV string
    :param form:
    :param gauge_type:
    :param error:
    :return:
    """
    sorted_colors_string = ''
    colors_hex = {}
    if gauge_type == 'gauge_angular':
        # Combine all color form inputs to dictionary
        for key in form.keys():
            if ('color_hex_number' in key or
                    'color_low_number' in key or
                    'color_high_number' in key):
                if int(key[17:]) not in colors_hex:
                    colors_hex[int(key[17:])] = {}
            if 'color_hex_number' in key:
                for value in form.getlist(key):
                    if not is_rgb_color(value):
                        error.append('Invalid hex color value')
                    colors_hex[int(key[17:])]['hex'] = value
            elif 'color_low_number' in key:
                for value in form.getlist(key):
                    colors_hex[int(key[17:])]['low'] = value
            elif 'color_high_number' in key:
                for value in form.getlist(key):
                    colors_hex[int(key[17:])]['high'] = value

    elif gauge_type == 'gauge_solid':
        # Combine all color form inputs to dictionary
        for key in form.keys():
            if ('color_hex_number' in key or
                    'color_stop_number' in key):
                if int(key[17:]) not in colors_hex:
                    colors_hex[int(key[17:])] = {}
            if 'color_hex_number' in key:
                for value in form.getlist(key):
                    if not is_rgb_color(value):
                        error.append("Invalid hex color value")
                    colors_hex[int(key[17:])]['hex'] = value
            elif 'color_stop_number' in key:
                for value in form.getlist(key):
                    colors_hex[int(key[17:])]['stop'] = value

    # Build string of colors and associated gauge values
    for i, _ in enumerate(colors_hex):
        try:
            if gauge_type == 'gauge_angular':
                sorted_colors_string += "{},{},{}".format(
                    colors_hex[i]['low'],
                    colors_hex[i]['high'],
                    colors_hex[i]['hex'])
            elif gauge_type == 'gauge_solid':
                try:
                    sorted_colors_string += "{},{}".format(
                        colors_hex[i]['stop'],
                        colors_hex[i]['hex'])
                except Exception as err_msg:
                    error.append(err_msg)
                    sorted_colors_string += "0,{}".format(
                        colors_hex[i]['hex'])
            if i < len(colors_hex) - 1:
                sorted_colors_string += ";"
        except Exception as err_msg:
            error.append(err_msg)
    return sorted_colors_string, error


def custom_colors_graph_str(form, error):
    """
    Get variable number of graph color inputs, turn into CSV string
    :param request_form:
    :return:
    """
    colors = {}
    short_list = []
    for key in form.keys():
        if 'color_number' in key:
            for value in form.getlist(key):
                if not is_rgb_color(value):
                    error.append("Invalid hex color value")
                colors[key[12:]] = value
    sorted_list = [(k, colors[k]) for k in sorted(colors)]
    for each_color in sorted_list:
        short_list.append(each_color[1])
    return ','.join(short_list), error


def custom_yaxes_str_from_form(form):
    """
    Parse several yaxis min/max inputs and turn them into CSV string to
    save in the database
    :param request_form: UI form submitted by mycodo
    :return: string of CSV data sets separated by ';'
    """
    # Parse custom y-axis options from the UI form
    yaxes = {}
    for key in form.keys():
        if 'custom_yaxis_name_' in key:
            for value in form.getlist(key):
                unique_number = key[18:]
                if unique_number not in yaxes:
                    yaxes[unique_number] = {}
                yaxes[unique_number]['name'] = value
        if 'custom_yaxis_min_' in key:
            for value in form.getlist(key):
                unique_number = key[17:]
                if unique_number not in yaxes:
                    yaxes[unique_number] = {}
                yaxes[unique_number]['minimum'] = value
        if 'custom_yaxis_max_' in key:
            for value in form.getlist(key):
                unique_number = key[17:]
                if unique_number not in yaxes:
                    yaxes[unique_number] = {}
                yaxes[unique_number]['maximum'] = value
    # Create a list of CSV sets in the format 'y-axis, minimum, maximum'
    yaxes_list = []
    for each_yaxis, yaxis_type in yaxes.items():
        yaxes_list.append('{},{},{}'.format(yaxis_type['name'], yaxis_type['minimum'], yaxis_type['maximum']))
    # Join the list of CSV sets with ';'
    return ';'.join(yaxes_list)


def is_rgb_color(color_hex):
    """
    Check if string is a hex color value for the web UI
    :param color_hex: string to check if it represents a hex color value
    :return: bool
    """
    return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))

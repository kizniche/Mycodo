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
from mycodo.utils.system_pi import csv_to_list_of_int
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

    new_graph = Dashboard()
    new_graph.name = form_base.name.data

    # Graph
    if (form_base.dashboard_type.data == 'graph' and
            (form_base.name.data and
             form_object.width.data and
             form_object.height.data and
             form_object.xaxis_duration.data and
             form_object.refresh_duration.data)):

        error = graph_error_check(form_object, error)

        new_graph.graph_type = form_base.dashboard_type.data

        if form_object.math_ids.data:
            math_ids_joined = ";".join(form_object.math_ids.data)
            new_graph.math_ids = math_ids_joined
        if form_object.pid_ids.data:
            pid_ids_joined = ";".join(form_object.pid_ids.data)
            new_graph.pid_ids = pid_ids_joined
        if form_object.relay_ids.data:
            relay_ids_joined = ";".join(form_object.relay_ids.data)
            new_graph.relay_ids = relay_ids_joined
        if form_object.sensor_ids.data:
            sensor_ids_joined = ";".join(form_object.sensor_ids.data)
            new_graph.sensor_ids_measurements = sensor_ids_joined
        new_graph.width = form_object.width.data
        new_graph.height = form_object.height.data
        new_graph.x_axis_duration = form_object.xaxis_duration.data
        new_graph.refresh_duration = form_object.refresh_duration.data
        new_graph.enable_auto_refresh = form_object.enable_auto_refresh.data
        new_graph.enable_xaxis_reset = form_object.enable_xaxis_reset.data
        new_graph.enable_title = form_object.enable_title.data
        new_graph.enable_navbar = form_object.enable_navbar.data
        new_graph.enable_rangeselect = form_object.enable_range.data
        new_graph.enable_export = form_object.enable_export.data
        new_graph.enable_graph_shift = form_object.enable_graph_shift.data
        new_graph.enable_manual_y_axis = form_object.enable_manual_y_axis.data
        new_graph.y_axis_min = form_object.y_axis_min.data
        new_graph.y_axis_max = form_object.y_axis_max.data

        try:
            if not error:
                new_graph.save()
                flash(gettext(
                    "Graph with ID %(id)s successfully added",
                    id=new_graph.id),
                    "success")

                DisplayOrder.query.first().graph = add_display_order(
                    display_order, new_graph.id)
                db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

    # Gauge
    elif (form_base.dashboard_type.data == 'gauge' and
          form_object.sensor_ids.data):

        error = gauge_error_check(form_object, error)

        new_graph.graph_type = form_object.gauge_type.data

        if form_object.gauge_type.data == 'gauge_solid':
            new_graph.range_colors = '0.2,#33CCFF;0.4,#55BF3B;0.6,#DDDF0D;0.8,#DF5353'
        elif form_object.gauge_type.data == 'gauge_angular':
            new_graph.range_colors = '0,25,#33CCFF;25,50,#55BF3B;50,75,#DDDF0D;75,100,#DF5353'
        new_graph.width = form_object.width.data
        new_graph.height = form_object.height.data
        new_graph.max_measure_age = form_object.max_measure_age.data
        new_graph.refresh_duration = form_object.refresh_duration.data
        new_graph.y_axis_min = form_object.y_axis_min.data
        new_graph.y_axis_max = form_object.y_axis_max.data
        new_graph.sensor_ids_measurements = form_object.sensor_ids.data[0]
        new_graph.enable_timestamp = form_object.enable_timestamp.data
        try:
            if not error:
                new_graph.save()
                flash(gettext(
                    "Gauge with ID %(id)s successfully added",
                    id=new_graph.id),
                    "success")

                DisplayOrder.query.first().graph = add_display_order(
                    display_order, new_graph.id)
                db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

    # Camera
    elif (form_base.dashboard_type.data == 'camera' and
          form_object.camera_id.data):

        new_graph.graph_type = form_base.dashboard_type.data
        new_graph.width = form_object.width.data
        new_graph.height = form_object.height.data
        new_graph.refresh_duration = form_object.refresh_duration.data
        new_graph.camera_max_age = form_object.camera_max_age.data
        new_graph.camera_id = form_object.camera_id.data
        new_graph.camera_image_type = form_object.camera_image_type.data
        try:
            if not error:
                new_graph.save()
                flash(gettext(
                    "Camera with ID %(id)s successfully added",
                    id=new_graph.id),
                    "success")

                DisplayOrder.query.first().graph = add_display_order(
                    display_order, new_graph.id)
                db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

    else:
        flash_form_errors(form_base)
        return

    flash_success_errors(error, action, url_for('routes_page.page_dashboard'))


def dashboard_mod(form_base, form_object, request_form):
    """Modify the settings of an item on the dashboard"""
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Dashboard"))
    error = []

    def is_rgb_color(color_hex):
        return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))

    mod_graph = Dashboard.query.filter(
        Dashboard.id == form_base.dashboard_id.data).first()
    mod_graph.name = form_base.name.data

    # Graph Mod
    if form_base.dashboard_type.data == 'graph':

        error = graph_error_check(form_object, error)

        # Get variable number of color inputs, turn into CSV string
        colors = {}
        short_list = []
        f = request_form
        for key in f.keys():
            if 'color_number' in key:
                for value in f.getlist(key):
                    if not is_rgb_color(value):
                        error.append("Invalid hex color value")
                    colors[key[12:]] = value
        sorted_list = [(k, colors[k]) for k in sorted(colors)]
        for each_color in sorted_list:
            short_list.append(each_color[1])
        sorted_colors_string = ",".join(short_list)

        mod_graph.custom_colors = sorted_colors_string
        mod_graph.use_custom_colors = form_object.use_custom_colors.data

        # Get variable number of yaxis min/max inputs, turn into CSV string
        f = request_form
        yaxes = {}
        for key in f.keys():
            if 'custom_yaxis_name_' in key:
                for value in f.getlist(key):
                    if key[18:] not in yaxes:
                        yaxes[key[18:]] = {}
                    yaxes[key[18:]]['name'] = value
            if 'custom_yaxis_min_' in key:
                for value in f.getlist(key):
                    if key[17:] not in yaxes:
                        yaxes[key[17:]] = {}
                    yaxes[key[17:]]['minimum'] = value
            if 'custom_yaxis_max_' in key:
                for value in f.getlist(key):
                    if key[17:] not in yaxes:
                        yaxes[key[17:]] = {}
                    yaxes[key[17:]]['maximum'] = value
        yaxes_sorted = {}
        for each_yaxis, yaxis_type in yaxes.items():
            yaxes_sorted[yaxis_type['name']] = {}
            yaxes_sorted[yaxis_type['name']]['minimum'] = yaxis_type['minimum']
            yaxes_sorted[yaxis_type['name']]['maximum'] = yaxis_type['maximum']
        yaxes_list = []
        for each_yaxis, yaxis_type in yaxes_sorted.items():
            yaxes_list.append('{},{},{}'.format(each_yaxis, yaxis_type['minimum'], yaxis_type['maximum']))
        yaxes_string = ';'.join(yaxes_list)

        mod_graph.custom_yaxes = yaxes_string
        mod_graph.enable_manual_y_axis = form_object.enable_manual_y_axis.data

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

        if form_object.relay_ids.data:
            relay_ids_joined = ";".join(form_object.relay_ids.data)
            mod_graph.relay_ids = relay_ids_joined
        else:
            mod_graph.relay_ids = ''

        if form_object.sensor_ids.data:
            sensor_ids_joined = ";".join(form_object.sensor_ids.data)
            mod_graph.sensor_ids_measurements = sensor_ids_joined
        else:
            mod_graph.sensor_ids_measurements = ''

        mod_graph.width = form_object.width.data
        mod_graph.height = form_object.height.data
        mod_graph.x_axis_duration = form_object.xaxis_duration.data
        mod_graph.refresh_duration = form_object.refresh_duration.data
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

        colors_hex = {}
        f = request_form
        sorted_colors_string = ""

        if form_object.gauge_type.data == 'gauge_angular':
            # Combine all color form inputs to dictionary
            for key in f.keys():
                if ('color_hex_number' in key or
                        'color_low_number' in key or
                        'color_high_number' in key):
                    if int(key[17:]) not in colors_hex:
                        colors_hex[int(key[17:])] = {}
                if 'color_hex_number' in key:
                    for value in f.getlist(key):
                        if not is_rgb_color(value):
                            error.append("Invalid hex color value")
                        colors_hex[int(key[17:])]['hex'] = value
                elif 'color_low_number' in key:
                    for value in f.getlist(key):
                        colors_hex[int(key[17:])]['low'] = value
                elif 'color_high_number' in key:
                    for value in f.getlist(key):
                        colors_hex[int(key[17:])]['high'] = value

        elif form_object.gauge_type.data == 'gauge_solid':
            # Combine all color form inputs to dictionary
            for key in f.keys():
                if ('color_hex_number' in key or
                        'color_stop_number' in key):
                    if int(key[17:]) not in colors_hex:
                        colors_hex[int(key[17:])] = {}
                if 'color_hex_number' in key:
                    for value in f.getlist(key):
                        if not is_rgb_color(value):
                            error.append("Invalid hex color value")
                        colors_hex[int(key[17:])]['hex'] = value
                elif 'color_stop_number' in key:
                    for value in f.getlist(key):
                        colors_hex[int(key[17:])]['stop'] = value

        # Build string of colors and associated gauge values
        for i, _ in enumerate(colors_hex):
            try:
                if form_object.gauge_type.data == 'gauge_angular':
                    sorted_colors_string += "{},{},{}".format(
                        colors_hex[i]['low'],
                        colors_hex[i]['high'],
                        colors_hex[i]['hex'])
                elif form_object.gauge_type.data == 'gauge_solid':
                    try:
                        if 0 > colors_hex[i]['stop'] > 1:
                            error.append("Color stops must be between 0 and 1")
                        sorted_colors_string += "{},{}".format(
                            colors_hex[i]['stop'],
                            colors_hex[i]['hex'])
                    except Exception:
                        sorted_colors_string += "0,{}".format(
                            colors_hex[i]['hex'])
                if i < len(colors_hex) - 1:
                    sorted_colors_string += ";"
            except Exception as err_msg:
                error.append(err_msg)

        mod_graph.range_colors = sorted_colors_string
        mod_graph.width = form_object.width.data
        mod_graph.height = form_object.height.data
        mod_graph.refresh_duration = form_object.refresh_duration.data
        mod_graph.y_axis_min = form_object.y_axis_min.data
        mod_graph.y_axis_max = form_object.y_axis_max.data
        mod_graph.max_measure_age = form_object.max_measure_age.data
        mod_graph.enable_timestamp = form_object.enable_timestamp.data
        if form_object.sensor_ids.data[0]:
            sensor_ids_joined = ";".join(form_object.sensor_ids.data)
            mod_graph.sensor_ids_measurements = sensor_ids_joined
        else:
            error.append("A valid Measurement must be selected")

    # Camera Mod
    elif form_base.dashboard_type.data == 'camera':
        mod_graph.width = form_object.width.data
        mod_graph.height = form_object.height.data
        mod_graph.refresh_duration = form_object.refresh_duration.data
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
        display_order = csv_to_list_of_int(DisplayOrder.query.first().graph)
        display_order.remove(int(form_base.dashboard_id.data))
        DisplayOrder.query.first().graph = list_to_csv(display_order)
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
            DisplayOrder.query.first().graph = ','.join(map(str, reord_list))
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
    if not form.sensor_ids.data[0]:
        error.append("A valid Measurement must be selected")
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
                ids_and_measures = each_graph.sensor_ids_measurements.split(';')
            elif each_device == math:
                ids_and_measures = each_graph.math_ids.split(';')
            elif each_device == output:
                ids_and_measures = each_graph.relay_ids.split(';')
            elif each_device == pid:
                ids_and_measures = each_graph.pid_ids.split(';')
            else:
                ids_and_measures = []

            # Iterate through each set of ID and measurement of the
            # dashboard element
            for each_id_measure in ids_and_measures:
                if len(each_id_measure.split(',')) == 2:
                    if each_graph.id not in y_axes:
                        y_axes[each_graph.id] = []

                    unique_id = each_id_measure.split(',')[0]
                    measurement = each_id_measure.split(',')[1]

                    y_axes[each_graph.id] = check_func(each_device,
                                                       unique_id,
                                                       y_axes[each_graph.id],
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
    :param all_devices: A list of Input, Math, Output, and PID SQL objects
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

            # Add duration_sec
            # TODO: rename 'pid_output' to 'duration_sec'
            if measurement == 'pid_output':
                if 'duration_sec' not in y_axes:
                    y_axes.append('duration_sec')

            # Find the y-axis the setpoint or bands apply to
            elif measurement in ['setpoint', 'setpoint_band_min', 'setpoint_band_max']:
                for each_input in input_dev:
                    if each_input.unique_id == each_device.measurement.split(',')[0]:
                        pid_measurement = each_device.measurement.split(',')[1]
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

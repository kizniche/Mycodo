# -*- coding: utf-8 -*-
import json
import logging
import os
import re

import sqlalchemy
from flask import current_app
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import PATH_HTML_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Conversion
from mycodo.databases.models import Dashboard
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Widget
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_json
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.mycodo_flask.utils.utils_general import use_unit_generate
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import set_user_grp
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger(__name__)


#
# Dashboards
#

def dashboard_add():
    """Add a dashboard"""
    error = []

    last_dashboard = Dashboard.query.order_by(
        Dashboard.id.desc()).first()

    new_dash = Dashboard()
    new_dash.name = '{} {}'.format(TRANSLATIONS['dashboard']['title'], last_dashboard.id + 1)

    if not error:
        new_dash.save()

        flash(gettext(
            "Dashboard with ID %(id)s successfully added", id=new_dash.id),
            "success")

    return new_dash.unique_id


def dashboard_mod(form):
    """Modify a dashboard"""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['dashboard']['title'])
    error = []

    name_exists = Dashboard.query.filter(
        Dashboard.name == form.name.data).first()
    if name_exists:
        flash('Dashboard name already is use', 'error')
        return

    dash_mod = Dashboard.query.filter(
        Dashboard.unique_id == form.dashboard_id.data).first()
    dash_mod.name = form.name.data

    db.session.commit()

    flash_success_errors(
        error, action, url_for('routes_page.page_dashboard_default'))


def dashboard_del(form):
    """Delete a dashboard"""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['dashboard']['title'])
    error = []

    dashboards = Dashboard.query.all()
    if len(dashboards) == 1:
        flash('Cannot delete the only remaining dashboard.', 'error')
        return

    widgets = Widget.query.filter(
        Widget.dashboard_id == form.dashboard_id.data).all()
    for each_widget in widgets:
        delete_entry_with_id(Widget, each_widget.unique_id)

    delete_entry_with_id(Dashboard, form.dashboard_id.data)

    flash_success_errors(
        error, action, url_for('routes_page.page_dashboard_default'))


#
# Widgets
#

def widget_add(form_base, request_form):
    """Add a widget to the dashboard"""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['widget']['title'])
    error = []

    dict_widgets = parse_widget_information()

    if form_base.widget_type.data:
        widget_name = form_base.widget_type.data
    else:
        widget_name = ''
        error.append("Missing widget name")

    if current_app.config['TESTING']:
        dep_unmet = False
    else:
        dep_unmet, _ = return_dependencies(widget_name)
        if dep_unmet:
            list_unmet_deps = []
            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[0])
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
        error, dict_widgets, request_form, device=widget_name)
    new_widget.custom_options = custom_options

    #
    # Execute at Creation
    #

    if 'execute_at_creation' in dict_widgets[widget_name] and not current_app.config['TESTING']:
        dict_widgets[widget_name]['execute_at_creation'](
            new_widget, dict_widgets[widget_name])

    try:
        if not error:
            new_widget.save()

            #
            # Save HTML files
            #
            assure_path_exists(PATH_HTML_USER)

            filename_head = "widget_template_{}_head.html".format(widget_name)
            path_head = os.path.join(PATH_HTML_USER, filename_head)
            with open(path_head, 'w') as fw:
                if 'widget_dashboard_head' in dict_widgets[widget_name]:
                    html_head = dict_widgets[widget_name]['widget_dashboard_head']
                else:
                    html_head = ""
                fw.write(html_head)
                fw.close()
            set_user_grp(path_head, 'mycodo', 'mycodo')

            filename_title_bar = "widget_template_{}_title_bar.html".format(widget_name)
            path_title_bar = os.path.join(PATH_HTML_USER, filename_title_bar)
            with open(path_title_bar, 'w') as fw:
                if 'widget_dashboard_title_bar' in dict_widgets[widget_name]:
                    html_title_bar = dict_widgets[widget_name]['widget_dashboard_title_bar']
                else:
                    html_title_bar = ""
                fw.write(html_title_bar)
                fw.close()
            set_user_grp(path_title_bar, 'mycodo', 'mycodo')

            filename_body = "widget_template_{}_body.html".format(widget_name)
            path_body = os.path.join(PATH_HTML_USER, filename_body)
            with open(path_body, 'w') as fw:
                if 'widget_dashboard_body' in dict_widgets[widget_name]:
                    html_body = dict_widgets[widget_name]['widget_dashboard_body']
                else:
                    html_body = ""
                fw.write(html_body)
                fw.close()
            set_user_grp(path_body, 'mycodo', 'mycodo')

            filename_configure_options = "widget_template_{}_configure_options.html".format(widget_name)
            path_configure_options = os.path.join(PATH_HTML_USER, filename_configure_options)
            with open(path_configure_options, 'w') as fw:
                if 'widget_dashboard_configure_options' in dict_widgets[widget_name]:
                    html_configure_options = dict_widgets[widget_name]['widget_dashboard_configure_options']
                else:
                    html_configure_options = ""
                fw.write(html_configure_options)
                fw.close()
            set_user_grp(path_configure_options, 'mycodo', 'mycodo')

            filename_js = "widget_template_{}_js.html".format(widget_name)
            path_js = os.path.join(PATH_HTML_USER, filename_js)
            with open(path_js, 'w') as fw:
                if 'widget_dashboard_js' in dict_widgets[widget_name]:
                    html_js = dict_widgets[widget_name]['widget_dashboard_js']
                else:
                    html_js = ""
                fw.write(html_js)
                fw.close()
            set_user_grp(path_js, 'mycodo', 'mycodo')

            filename_js_ready = "widget_template_{}_js_ready.html".format(widget_name)
            path_js_ready = os.path.join(PATH_HTML_USER, filename_js_ready)
            with open(path_js_ready, 'w') as fw:
                if 'widget_dashboard_js_ready' in dict_widgets[widget_name]:
                    html_js_ready = dict_widgets[widget_name]['widget_dashboard_js_ready']
                else:
                    html_js_ready = ""
                fw.write(html_js_ready)
                fw.close()
            set_user_grp(path_js_ready, 'mycodo', 'mycodo')

            filename_js_ready_end = "widget_template_{}_js_ready_end.html".format(widget_name)
            path_js_ready_end = os.path.join(PATH_HTML_USER, filename_js_ready_end)
            with open(path_js_ready_end, 'w') as fw:
                if 'widget_dashboard_js_ready_end' in dict_widgets[widget_name]:
                    html_js_ready_end = dict_widgets[widget_name]['widget_dashboard_js_ready_end']
                else:
                    html_js_ready_end = ""
                fw.write(html_js_ready_end)
                fw.close()
            set_user_grp(path_js_ready_end, 'mycodo', 'mycodo')

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

    return dep_unmet


# def widget_add(form_base, form_object):
#     """Add a widget to the dashboard"""
#     action = '{action} {controller}'.format(
#         action=TRANSLATIONS['add']['title'],
#         controller=TRANSLATIONS['widget']['title'])
#     error = []
#
#     new_widget = Widget()
#     new_widget.dashboard_id = form_base.dashboard_id.data
#     new_widget.name = form_base.name.data
#     new_widget.font_em_name = form_base.font_em_name.data
#     new_widget.enable_drag_handle = form_base.enable_drag_handle.data
#
#     # Find where the next widget should be placed on the grid
#     # Finds the lowest position to create as the new Widget's starting position
#     position_y_start = 0
#     for each_widget in Widget.query.filter(
#             Widget.dashboard_id == form_base.dashboard_id.data).all():
#         highest_position = each_widget.position_y + each_widget.height
#         if highest_position > position_y_start:
#             position_y_start = highest_position
#     new_widget.position_y = position_y_start
#
#     # Spacer
#     if form_base.widget_type.data == 'spacer':
#
#         widget_type = 'Spacer'
#
#         new_widget.graph_type = form_base.widget_type.data
#
#         new_widget.width = 20
#         new_widget.height = 1
#
#     # Graph
#     elif (form_base.widget_type.data == 'graph' and
#             (form_base.name.data and
#              form_object.xaxis_duration.data and
#              form_base.refresh_duration.data)):
#
#         widget_type = 'Graph'
#
#         error = graph_error_check(form_object, error)
#
#         new_widget.graph_type = form_base.widget_type.data
#         if form_object.math_ids.data:
#             new_widget.math_ids = ";".join(form_object.math_ids.data)
#         if form_object.pid_ids.data:
#             new_widget.pid_ids = ";".join(form_object.pid_ids.data)
#         if form_object.output_ids.data:
#             new_widget.output_ids = ";".join(form_object.output_ids.data)
#         if form_object.input_ids.data:
#             new_widget.input_ids_measurements = ";".join(form_object.input_ids.data)
#         if form_object.note_tag_ids.data:
#             new_widget.note_tag_ids = ";".join(form_object.note_tag_ids.data)
#
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.enable_header_buttons = form_object.enable_header_buttons.data
#         new_widget.x_axis_duration = form_object.xaxis_duration.data
#         new_widget.enable_auto_refresh = form_object.enable_auto_refresh.data
#         new_widget.enable_xaxis_reset = form_object.enable_xaxis_reset.data
#         new_widget.enable_title = form_object.enable_title.data
#         new_widget.enable_navbar = form_object.enable_navbar.data
#         new_widget.enable_rangeselect = form_object.enable_rangeselect.data
#         new_widget.enable_export = form_object.enable_export.data
#         new_widget.enable_manual_y_axis = form_object.enable_manual_y_axis.data
#
#         new_widget.width = 20
#         new_widget.height = 9
#
#     # Gauge
#     elif form_base.widget_type.data == 'gauge':
#
#         widget_type = 'Gauge'
#
#         error = gauge_error_check(form_object, error)
#
#         new_widget.graph_type = form_object.gauge_type.data
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.max_measure_age = form_object.max_measure_age.data
#         new_widget.y_axis_min = form_object.y_axis_min.data
#         new_widget.y_axis_max = form_object.y_axis_max.data
#         new_widget.input_ids_measurements = form_object.input_ids.data
#         new_widget.enable_timestamp = form_object.enable_timestamp.data
#         new_widget.stops = form_object.stops.data
#         new_widget.width = 4
#
#         if form_object.gauge_type.data == 'gauge_solid':
#             new_widget.height = 4
#         elif form_object.gauge_type.data == 'gauge_angular':
#             new_widget.height = 5
#
#         if form_object.stops.data < 2:
#             error.append("Must be at least 2 stops")
#         else:
#             new_widget.range_colors = gauge_reformat_stops(form_object.gauge_type.data, 4, new_widget.stops, current_colors=None)
#
#     # Indicator
#     elif form_base.widget_type.data == 'indicator':
#
#         widget_type = 'Indicator'
#
#         error = measurement_error_check(form_object, error)
#
#         new_widget.graph_type = 'indicator'
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.max_measure_age = form_object.max_measure_age.data
#         new_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         new_widget.input_ids_measurements = form_object.measurement_id.data
#         new_widget.enable_timestamp = form_object.enable_timestamp.data
#
#         new_widget.width = 3
#         new_widget.height = 4
#
#     # Measurement
#     elif form_base.widget_type.data == 'measurement':
#
#         widget_type = 'Measurement'
#
#         error = measurement_error_check(form_object, error)
#
#         new_widget.graph_type = 'measurement'
#         new_widget.max_measure_age = form_object.max_measure_age.data
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.font_em_value = form_object.font_em_value.data
#         new_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         new_widget.decimal_places = form_object.decimal_places.data
#         new_widget.input_ids_measurements = form_object.measurement_id.data
#         new_widget.enable_name = form_object.enable_name.data
#         new_widget.enable_unit = form_object.enable_unit.data
#         new_widget.enable_measurement = form_object.enable_measurement.data
#         new_widget.enable_channel = form_object.enable_channel.data
#         new_widget.enable_timestamp = form_object.enable_timestamp.data
#
#         new_widget.width = 4
#         new_widget.height = 5
#
#     # Output
#     elif form_base.widget_type.data == 'output':
#
#         widget_type = 'Output'
#
#         error = output_error_check(form_object, error)
#
#         new_widget.graph_type = 'output'
#         new_widget.max_measure_age = form_object.max_measure_age.data
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.font_em_value = form_object.font_em_value.data
#         new_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         new_widget.enable_output_controls = form_object.enable_output_controls.data
#         new_widget.decimal_places = form_object.decimal_places.data
#         new_widget.output_ids = form_object.output_id.data
#         new_widget.enable_status = form_object.enable_status.data
#         new_widget.enable_value = form_object.enable_value.data
#         new_widget.enable_unit = form_object.enable_unit.data
#         new_widget.enable_timestamp = form_object.enable_timestamp.data
#
#         new_widget.width = 5
#         new_widget.height = 4
#
#     # Output Range Slider
#     elif form_base.widget_type.data == 'output_pwm_slider':
#
#         widget_type = 'Output Range Slider'
#
#         error = output_error_check(form_object, error)
#
#         new_widget.graph_type = 'output_pwm_slider'
#         new_widget.max_measure_age = form_object.max_measure_age.data
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.font_em_value = form_object.font_em_value.data
#         new_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         new_widget.enable_output_controls = form_object.enable_output_controls.data
#         new_widget.decimal_places = form_object.decimal_places.data
#         new_widget.output_ids = form_object.output_id.data
#         new_widget.enable_status = form_object.enable_status.data
#         new_widget.enable_value = form_object.enable_value.data
#         new_widget.enable_unit = form_object.enable_unit.data
#         new_widget.enable_timestamp = form_object.enable_timestamp.data
#
#         new_widget.width = 5
#         new_widget.height = 4
#
#     # PID Control
#     elif form_base.widget_type.data == 'pid_control':
#
#         widget_type = 'PID Control'
#
#         error = pid_error_check(form_object, error)
#
#         new_widget.graph_type = 'pid_control'
#         new_widget.max_measure_age = form_object.max_measure_age.data
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.font_em_value = form_object.font_em_value.data
#         new_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         new_widget.decimal_places = form_object.decimal_places.data
#         new_widget.show_pid_info = form_object.show_pid_info.data
#         new_widget.enable_status = form_object.enable_status.data
#         new_widget.enable_timestamp = form_object.enable_timestamp.data
#         new_widget.show_set_setpoint = form_object.show_set_setpoint.data
#         new_widget.pid_ids = form_object.pid_id.data
#
#         new_widget.width = 6
#         new_widget.height = 5
#
#     # Camera
#     elif form_base.widget_type.data == 'camera':
#
#         widget_type = 'Camera'
#
#         camera = Camera.query.filter(
#             Camera.unique_id == form_object.camera_id.data).first()
#         if not camera:
#             error.append("Invalid Camera ID.")
#         elif (form_object.camera_image_type.data == 'stream' and
#                 camera.library not in ['opencv', 'picamera']):
#             error.append("Only cameras that use the 'picamera' or "
#                          "'opencv' library may be used for streaming")
#
#         new_widget.graph_type = form_base.widget_type.data
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.camera_max_age = form_object.camera_max_age.data
#         new_widget.camera_id = form_object.camera_id.data
#         new_widget.camera_image_type = form_object.camera_image_type.data
#
#         new_widget.width = 7
#         new_widget.height = 8
#
#     # Python code
#     elif form_base.widget_type.data == 'python_code':
#
#         widget_type = 'Python Code'
#
#         new_widget.graph_type = form_base.widget_type.data
#         new_widget.refresh_duration = form_base.refresh_duration.data
#         new_widget.font_em_value = form_object.font_em_value.data
#         new_widget.code_execute_loop = form_object.code_execute_loop.data
#         new_widget.code_execute_single = form_object.code_execute_single.data
#         new_widget.width = 4
#         new_widget.height = 4
#         new_widget.save()
#
#         pre_statement_loop = """import os
# import sys
# sys.path.append(os.path.abspath('/var/mycodo-root'))
# from mycodo.mycodo_client import DaemonControl
# control = DaemonControl()
# class PythonRun:
#     def __init__(self, logger, unique_id):
#         self.logger = logger
#         self.unique_id = unique_id
#     def python_code_loop(self):
# """
#
#         pre_statement_single = """
#     def python_code_refresh(self):
# """
#
#         indented_code_loop = textwrap.indent(form_object.code_execute_loop.data, ' ' * 8)
#         indented_code_single = textwrap.indent(form_object.code_execute_single.data, ' ' * 8)
#         input_python_code_run = pre_statement_loop + indented_code_loop + pre_statement_single + indented_code_single
#
#         file_run = '{}/python_code_{}.py'.format(PATH_PYTHON_CODE_USER, new_widget.unique_id)
#         create_python_file(input_python_code_run, file_run)
#         successes, errors = test_python_code(input_python_code_run, file_run)
#
#         for each_error in errors:
#             flash(each_error, "error")
#
#         for each_success in successes:
#             flash(each_success, "success")
#
#     else:
#         flash_form_errors(form_base)
#         return
#
#     try:
#         if not error:
#             new_widget.save()
#
#             if form_base.widget_type.data == 'python_code':
#                 control = DaemonControl()
#                 control.widget_add_refresh(new_widget.unique_id)
#
#             flash(gettext(
#                 "{dev} with ID %(id)s successfully added".format(dev=widget_type),
#                 id=new_widget.id),
#                 "success")
#     except sqlalchemy.exc.OperationalError as except_msg:
#         error.append(except_msg)
#     except sqlalchemy.exc.IntegrityError as except_msg:
#         error.append(except_msg)
#
#     flash_success_errors(error, action, url_for(
#         'routes_page.page_dashboard', dashboard_id=form_base.dashboard_id.data))


def widget_mod(form_base, request_form):
    """Modify the settings of an item on the dashboard"""
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

    custom_options_json_presave = json.loads(mod_widget.custom_options)

    # Generate string to save from custom options
    error, custom_options_json_postsave = custom_options_return_json(
        error, dict_widgets, request_form, device=mod_widget.graph_type)

    if 'execute_at_modification' in dict_widgets[mod_widget.graph_type]:
        (allow_saving,
         mod_input,
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
        'routes_page.page_dashboard',
        dashboard_id=form_base.dashboard_id.data))


# def widget_mod(form_base, form_object, request_form):
#     """Modify the settings of an item on the dashboard"""
#     action = '{action} {controller}'.format(
#         action=TRANSLATIONS['modify']['title'],
#         controller=TRANSLATIONS['widget']['title'])
#     error = []
#
#     mod_widget = Widget.query.filter(
#         Widget.unique_id == form_base.widget_id.data).first()
#     mod_widget.name = form_base.name.data
#     mod_widget.font_em_name = form_base.font_em_name.data
#     mod_widget.enable_drag_handle = form_base.enable_drag_handle.data
#
#     # Graph Mod
#     if form_base.widget_type.data == 'graph':
#
#         error = graph_error_check(form_object, error)
#
#         # Generate color option string from form inputs
#         sorted_colors_string, error = custom_colors_graph_str(request_form, error)
#         mod_widget.custom_colors = sorted_colors_string
#         disable_data_grouping_string, error = data_grouping_graph_str(request_form, error)
#         mod_widget.disable_data_grouping = disable_data_grouping_string
#         mod_widget.use_custom_colors = form_object.use_custom_colors.data
#
#         # Generate y-axis option string from form inputs
#         yaxes_string = custom_yaxes_str_from_form(request_form)
#         mod_widget.custom_yaxes = yaxes_string
#         mod_widget.enable_manual_y_axis = form_object.enable_manual_y_axis.data
#         mod_widget.enable_align_ticks = form_object.enable_align_ticks.data
#         mod_widget.enable_start_on_tick = form_object.enable_start_on_tick.data
#         mod_widget.enable_end_on_tick = form_object.enable_end_on_tick.data
#
#         if form_object.math_ids.data:
#             mod_widget.math_ids = ";".join(form_object.math_ids.data)
#         else:
#             mod_widget.math_ids = ''
#
#         if form_object.pid_ids.data:
#             mod_widget.pid_ids = ";".join(form_object.pid_ids.data)
#         else:
#             mod_widget.pid_ids = ''
#
#         if form_object.output_ids.data:
#             mod_widget.output_ids = ";".join(form_object.output_ids.data)
#         else:
#             mod_widget.output_ids = ''
#
#         if form_object.input_ids.data:
#             mod_widget.input_ids_measurements = ";".join(form_object.input_ids.data)
#         else:
#             mod_widget.input_ids_measurements = ''
#
#         if form_object.note_tag_ids.data:
#             mod_widget.note_tag_ids = ";".join(form_object.note_tag_ids.data)
#         else:
#             mod_widget.note_tag_ids = ''
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.enable_header_buttons = form_object.enable_header_buttons.data
#         mod_widget.x_axis_duration = form_object.xaxis_duration.data
#         mod_widget.enable_auto_refresh = form_object.enable_auto_refresh.data
#         mod_widget.enable_xaxis_reset = form_object.enable_xaxis_reset.data
#         mod_widget.enable_title = form_object.enable_title.data
#         mod_widget.enable_navbar = form_object.enable_navbar.data
#         mod_widget.enable_export = form_object.enable_export.data
#         mod_widget.enable_rangeselect = form_object.enable_rangeselect.data
#
#     # If a gauge type is changed, the color format must change
#     elif (form_base.widget_type.data == 'gauge' and
#             mod_widget.graph_type != form_object.gauge_type.data):
#
#         mod_widget.graph_type = form_object.gauge_type.data
#         mod_widget.range_colors = gauge_reformat_stops(
#             form_object.gauge_type.data,
#             4,
#             form_object.stops.data,
#             current_colors=None)
#         mod_widget.stops = form_object.stops.data
#
#     # Gauge Mod
#     elif form_base.widget_type.data == 'gauge':
#
#         error = gauge_error_check(form_object, error)
#
#         # Generate color option string from form inputs
#         sorted_colors_string, error = custom_colors_gauge_str(
#             request_form, form_object.gauge_type.data, error)
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.range_colors = sorted_colors_string
#         mod_widget.y_axis_min = form_object.y_axis_min.data
#         mod_widget.y_axis_max = form_object.y_axis_max.data
#         mod_widget.max_measure_age = form_object.max_measure_age.data
#         mod_widget.enable_timestamp = form_object.enable_timestamp.data
#         mod_widget.range_colors = gauge_reformat_stops(
#             form_object.gauge_type.data,
#             mod_widget.stops,
#             form_object.stops.data,
#             current_colors=mod_widget.range_colors)
#         mod_widget.stops = form_object.stops.data
#
#         if form_object.input_ids.data:
#             mod_widget.input_ids_measurements = form_object.input_ids.data
#         else:
#             error.append("A valid Measurement must be selected")
#
#     # Indicator Mod
#     elif form_base.widget_type.data == 'indicator':
#
#         error = indicator_error_check(form_object, error)
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.max_measure_age = form_object.max_measure_age.data
#         mod_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         mod_widget.option_invert = form_object.option_invert.data
#         mod_widget.enable_timestamp = form_object.enable_timestamp.data
#         if form_object.measurement_id.data:
#             mod_widget.input_ids_measurements = form_object.measurement_id.data
#
#     # Measurement Mod
#     elif form_base.widget_type.data == 'measurement':
#
#         error = measurement_error_check(form_object, error)
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.max_measure_age = form_object.max_measure_age.data
#         mod_widget.font_em_value = form_object.font_em_value.data
#         mod_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         mod_widget.decimal_places = form_object.decimal_places.data
#         mod_widget.enable_name = form_object.enable_name.data
#         mod_widget.enable_unit = form_object.enable_unit.data
#         mod_widget.enable_measurement = form_object.enable_measurement.data
#         mod_widget.enable_channel = form_object.enable_channel.data
#         mod_widget.enable_timestamp = form_object.enable_timestamp.data
#         if form_object.measurement_id.data:
#             mod_widget.input_ids_measurements = form_object.measurement_id.data
#
#     # Output Mod
#     elif form_base.widget_type.data in ['output', 'output_pwm_slider']:
#
#         error = output_error_check(form_object, error)
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.max_measure_age = form_object.max_measure_age.data
#         mod_widget.font_em_value = form_object.font_em_value.data
#         mod_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         mod_widget.decimal_places = form_object.decimal_places.data
#         mod_widget.enable_output_controls = form_object.enable_output_controls.data
#         mod_widget.enable_status = form_object.enable_status.data
#         mod_widget.enable_value = form_object.enable_value.data
#         mod_widget.enable_unit = form_object.enable_unit.data
#         mod_widget.enable_timestamp = form_object.enable_timestamp.data
#         if form_object.output_id.data:
#             mod_widget.output_ids = form_object.output_id.data
#
#     # PID Control Mod
#     elif form_base.widget_type.data == 'pid_control':
#
#         error = pid_error_check(form_object, error)
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.max_measure_age = form_object.max_measure_age.data
#         mod_widget.font_em_value = form_object.font_em_value.data
#         mod_widget.font_em_timestamp = form_object.font_em_timestamp.data
#         mod_widget.decimal_places = form_object.decimal_places.data
#         mod_widget.enable_status = form_object.enable_status.data
#         mod_widget.enable_timestamp = form_object.enable_timestamp.data
#         mod_widget.show_pid_info = form_object.show_pid_info.data
#         mod_widget.show_set_setpoint = form_object.show_set_setpoint.data
#         if form_object.pid_id.data:
#             mod_widget.pid_ids = form_object.pid_id.data
#
#     # Camera Mod
#     elif form_base.widget_type.data == 'camera':
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.camera_max_age = form_object.camera_max_age.data
#         mod_widget.camera_id = form_object.camera_id.data
#         mod_widget.camera_image_type = form_object.camera_image_type.data
#
#     # Python code Mod
#     elif form_base.widget_type.data == 'python_code':
#
#         pre_statement_loop = """import os
# import sys
# sys.path.append(os.path.abspath('/var/mycodo-root'))
# from mycodo.mycodo_client import DaemonControl
# control = DaemonControl()
#
# class PythonRun:
#     def __init__(self, logger, unique_id):
#         self.logger = logger
#         self.unique_id = unique_id
#
#     def python_code_loop(self):
# """
#
#         pre_statement_single = """
#
#     def python_code_refresh(self):
# """
#
#         indented_code_loop = textwrap.indent(form_object.code_execute_loop.data, ' ' * 8)
#         indented_code_single = textwrap.indent(form_object.code_execute_single.data, ' ' * 8)
#         input_python_code_run = pre_statement_loop + indented_code_loop + pre_statement_single + indented_code_single
#
#         file_run = '{}/python_code_{}.py'.format(PATH_PYTHON_CODE_USER, mod_widget.unique_id)
#         create_python_file(input_python_code_run, file_run)
#         successes, errors = test_python_code(input_python_code_run, file_run)
#
#         for each_error in errors:
#             flash(each_error, "error")
#
#         for each_success in successes:
#             flash(each_success, "success")
#
#         mod_widget.refresh_duration = form_base.refresh_duration.data
#         mod_widget.font_em_value = form_object.font_em_value.data
#         mod_widget.code_execute_loop = form_object.code_execute_loop.data
#         mod_widget.code_execute_single = form_object.code_execute_single.data
#
#     else:
#         flash_form_errors(form_base)
#
#     if not error:
#         try:
#             db.session.commit()
#         except sqlalchemy.exc.OperationalError as except_msg:
#             error.append(except_msg)
#         except sqlalchemy.exc.IntegrityError as except_msg:
#             error.append(except_msg)
#
#         if form_base.widget_type.data == 'python_code':
#             control = DaemonControl()
#             control.widget_add_refresh(mod_widget.unique_id)
#
#     flash_success_errors(error, action, url_for(
#         'routes_page.page_dashboard',
#         dashboard_id=form_base.dashboard_id.data))


def widget_del(form_base):
    """Delete a widget from a dashboard"""
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
        error, action, url_for('routes_page.page_dashboard',
                               dashboard_id=form_base.dashboard_id.data))


def graph_error_check(form, error):
    """Determine if there are any errors in the graph form"""
    # Error checks go here
    return error


def gauge_error_check(form, error):
    """Determine if there are any errors in the gauge form"""
    if not form.input_ids.data:
        error.append("A valid Measurement must be selected")
    return error


def indicator_error_check(form, error):
    """Determine if there are any errors in the indicator form"""
    if form.measurement_id.data == '':
        error.append("A valid Measurement must be selected")
    return error


def measurement_error_check(form, error):
    """Determine if there are any errors in the measurement form"""
    if form.measurement_id.data == '':
        error.append("A valid Measurement must be selected")
    return error


def output_error_check(form, error):
    """Determine if there are any errors in the output form"""
    if form.output_id.data == '':
        error.append("A valid Output must be selected")
    return error


def pid_error_check(form, error):
    """Determine if there are any errors in the PID form"""
    if form.pid_id.data == '':
        error.append("A valid PID Controller must be selected")
    return error


def graph_y_axes_async(dict_measurements, ids_measures):
    """ Determine which y-axes to use for each Graph """
    if not ids_measures:
        return

    y_axes = []

    device_measurements = DeviceMeasurements.query.all()
    input_dev = Input.query.all()
    math = Math.query.all()
    output = Output.query.all()
    pid = PID.query.all()

    devices_list = [input_dev, math, output, pid]

    # Iterate through device tables
    for each_device in devices_list:

        # Iterate through each set of ID and measurement of the dashboard element
        for each_id_measure in ids_measures:

            if each_device != output and ',' in each_id_measure:
                measure_id = each_id_measure.split(',')[1]

                for each_measure in device_measurements:
                    if each_measure.unique_id == measure_id:

                        if each_measure.conversion_id:
                            conversion = Conversion.query.filter(
                                Conversion.unique_id == each_measure.conversion_id).first()
                            if not y_axes:
                                y_axes = [conversion.convert_unit_to]
                            elif y_axes and conversion.convert_unit_to not in y_axes:
                                y_axes.append(conversion.convert_unit_to)
                        elif (each_measure.rescaled_measurement and
                                each_measure.rescaled_unit):
                            if not y_axes:
                                y_axes = [each_measure.rescaled_unit]
                            elif y_axes and each_measure.rescaled_unit not in y_axes:
                                y_axes.append(each_measure.rescaled_unit)
                        else:
                            if not y_axes:
                                y_axes = [each_measure.unit]
                            elif y_axes and each_measure.unit not in y_axes:
                                y_axes.append(each_measure.unit)

            elif each_device == output and ',' in each_id_measure:
                output_id = each_id_measure.split(',')[0]

                for each_output in output:
                    if each_output.unique_id == output_id:
                        if not y_axes:
                            y_axes = [each_output.unit]
                        elif y_axes and each_output.unit not in y_axes:
                            y_axes.append(each_output.unit)

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
                                                math)

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
                                                math,
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
               math,
               unit=None):
    """
    Generate a list of y-axes for Live and Asynchronous Graphs
    :param all_devices: Input, Math, Output, and PID SQL entries of a table
    :param unique_id: The ID of the measurement
    :param y_axes: empty list to populate
    :param measurement:
    :param dict_measurements:
    :param device_measurements:
    :param input_dev:
    :param output:
    :param math:
    :param unit:
    :return: None
    """
    # Iterate through each device entry
    for each_device in all_devices:

        # If the ID saved to the dashboard element matches the table entry ID
        if each_device.unique_id == unique_id:

            use_unit = use_unit_generate(
                device_measurements, input_dev, output, math)

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


# def custom_colors_gauge_str(form, gauge_type, error):
#     """
#     Get variable number of gauge color inputs, turn into CSV string
#     :param form:
#     :param gauge_type:
#     :param error:
#     :return:
#     """
#     sorted_colors_string = ''
#     colors_hex = {}
#     if gauge_type == 'gauge_angular':
#         # Combine all color form inputs to dictionary
#         for key in form.keys():
#             if ('color_hex_number' in key or
#                     'color_low_number' in key or
#                     'color_high_number' in key):
#                 if int(key[17:]) not in colors_hex:
#                     colors_hex[int(key[17:])] = {}
#             if 'color_hex_number' in key:
#                 for value in form.getlist(key):
#                     if not is_rgb_color(value):
#                         error.append('Invalid hex color value')
#                     colors_hex[int(key[17:])]['hex'] = value
#             elif 'color_low_number' in key:
#                 for value in form.getlist(key):
#                     colors_hex[int(key[17:])]['low'] = value
#             elif 'color_high_number' in key:
#                 for value in form.getlist(key):
#                     colors_hex[int(key[17:])]['high'] = value
#
#     elif gauge_type == 'gauge_solid':
#         # Combine all color form inputs to dictionary
#         for key in form.keys():
#             if ('color_hex_number' in key or
#                     'color_stop_number' in key):
#                 if int(key[17:]) not in colors_hex:
#                     colors_hex[int(key[17:])] = {}
#             if 'color_hex_number' in key:
#                 for value in form.getlist(key):
#                     if not is_rgb_color(value):
#                         error.append("Invalid hex color value")
#                     colors_hex[int(key[17:])]['hex'] = value
#             elif 'color_stop_number' in key:
#                 for value in form.getlist(key):
#                     colors_hex[int(key[17:])]['stop'] = value
#
#     # Build string of colors and associated gauge values
#     for i, _ in enumerate(colors_hex):
#         try:
#             if gauge_type == 'gauge_angular':
#                 sorted_colors_string += "{},{},{}".format(
#                     colors_hex[i]['low'],
#                     colors_hex[i]['high'],
#                     colors_hex[i]['hex'])
#             elif gauge_type == 'gauge_solid':
#                 try:
#                     sorted_colors_string += "{},{}".format(
#                         colors_hex[i]['stop'],
#                         colors_hex[i]['hex'])
#                 except Exception as err_msg:
#                     error.append(err_msg)
#                     sorted_colors_string += "0,{}".format(
#                         colors_hex[i]['hex'])
#             if i < len(colors_hex) - 1:
#                 sorted_colors_string += ";"
#         except Exception as err_msg:
#             error.append(err_msg)
#     return sorted_colors_string, error


def custom_colors_graph_str(form, error):
    """
    Get variable number of graph color inputs, turn into CSV string
    :param form:
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


def data_grouping_graph_str(form, error):
    """
    Get checkbox options for data grouping, turn into CSV string
    :param form:
    :return:
    """
    list_data_grouping = []
    for key in form.keys():
        if 'disable_data_grouping' in key:
            list_data_grouping.append(key[22:])
    return ','.join(list_data_grouping), error


def custom_yaxes_str_from_form(form):
    """
    Parse several yaxis min/max inputs and turn them into CSV string to
    save in the database
    :param form: UI form submitted by mycodo
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
    for _, yaxis_type in yaxes.items():
        yaxes_list.append('{},{},{}'.format(yaxis_type['name'], yaxis_type['minimum'], yaxis_type['maximum']))
    # Join the list of CSV sets with ';'
    return ';'.join(yaxes_list)


# def gauge_reformat_stops(gauge_type, current_stops, new_stops, current_colors=None):
#     """Generate stops and colors for new and modified gauges"""
#     if current_colors:
#         colors = current_colors
#     else:  # Default colors (adding new gauge)
#         if gauge_type == 'gauge_solid':
#             colors = '20,#33CCFF;40,#55BF3B;60,#DDDF0D;80,#DF5353'
#         elif gauge_type == 'gauge_angular':
#             colors = '0,20,#33CCFF;20,40,#55BF3B;40,60,#DDDF0D;60,80,#DF5353'
#
#     if new_stops > current_stops:
#         stop = 80
#         for _ in range(new_stops - current_stops):
#             stop += 20
#             if gauge_type == 'gauge_solid':
#                 colors += ';{},#DF5353'.format(stop)
#             elif gauge_type == 'gauge_angular':
#                 colors += ';{low},{high},#DF5353'.format(low=stop - 20, high=stop)
#     elif new_stops < current_stops:
#         colors_list = colors.split(';')
#         colors = ';'.join(colors_list[: len(colors_list) - (current_stops - new_stops)])
#     new_colors = colors
#
#     return new_colors


def is_rgb_color(color_hex):
    """
    Check if string is a hex color value for the web UI
    :param color_hex: string to check if it represents a hex color value
    :return: bool
    """
    return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))

# coding=utf-8
#
#  widget_graph_synchronous.py - Synchronous Graph dashboard widget
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com
#
import datetime
import json
import logging
import re

import flask_login
from flask import flash
from flask import jsonify
from flask_babel import lazy_gettext
from flask_login import current_user
from pytz import timezone

from mycodo.config import THEMES_DARK
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Measurement
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.mycodo_flask.utils.utils_general import use_unit_generate
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.influx import read_influxdb_list
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.system_pi import str_is_float

logger = logging.getLogger(__name__)


def past_data(unique_id, measure_type, measurement_id, past_seconds):
    """Return data from past_seconds until present from influxdb."""
    if not current_user.is_authenticated:
        return "You are not logged in and cannot access this endpoint"
    if not str_is_float(past_seconds):
        return '', 204

    if measure_type == 'tag':
        notes_list = []

        tag = NoteTags.query.filter(NoteTags.unique_id == unique_id).first()
        notes = Notes.query.filter(
            Notes.date_time >= (datetime.datetime.utcnow() - datetime.timedelta(seconds=int(past_seconds)))).all()

        for each_note in notes:
            if tag.unique_id in each_note.tags.split(','):
                notes_list.append(
                    [each_note.date_time.replace(tzinfo=timezone('UTC')).timestamp(), each_note.name, each_note.note])

        if notes_list:
            return jsonify(notes_list)
        else:
            return '', 204

    elif measure_type in ['input', 'function', 'output', 'pid']:
        if measure_type in ['input', 'function', 'output', 'pid']:
            measure = DeviceMeasurements.query.filter(
                DeviceMeasurements.unique_id == measurement_id).first()
        else:
            measure = None

        if not measure:
            return "Could not find measurement"

        if measure:
            conversion = Conversion.query.filter(
                Conversion.unique_id == measure.conversion_id).first()
        else:
            conversion = None

        channel, unit, measurement = return_measurement_info(
            measure, conversion)

        if hasattr(measure, 'measurement_type') and measure.measurement_type == 'setpoint':
            setpoint_pid = PID.query.filter(PID.unique_id == measure.device_id).first()
            if setpoint_pid and ',' in setpoint_pid.measurement:
                pid_measurement = setpoint_pid.measurement.split(',')[1]
                setpoint_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == pid_measurement).first()
                if setpoint_measurement:
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == setpoint_measurement.conversion_id).first()
                    _, unit, measurement = return_measurement_info(setpoint_measurement, conversion)

        try:
            list_data = read_influxdb_list(
                unique_id, unit,
                channel=channel,
                measure=measurement,
                duration_sec=past_seconds)

            if not list_data:
                return '', 204

            return jsonify(list_data)
        except Exception as err:
            logger.debug(f"URL for 'past_data' raised and error: {err}")
            return '', 204


def execute_at_creation(error, new_widget, dict_widget):
    # Create initial default values
    custom_options_json = json.loads(new_widget.custom_options)
    custom_options_json['disable_data_grouping'] = ""
    custom_options_json['series_type'] = ""
    custom_options_json['custom_yaxes'] = ""
    custom_options_json['custom_colors'] = ""
    new_widget.custom_options = json.dumps(custom_options_json)
    return error, new_widget


def execute_at_modification(
        mod_widget,
        request_form,
        custom_options_json_presave,
        custom_options_json_postsave):
    allow_saving = True
    page_refresh = False
    error = []

    for key in request_form.keys():
        if key == 'use_custom_colors':
            custom_options_json_postsave['use_custom_colors'] = request_form.get(key)
        elif key == 'enable_manual_y_axis':
            custom_options_json_postsave['enable_manual_y_axis'] = request_form.get(key)
        elif key == 'enable_align_ticks':
            custom_options_json_postsave['enable_align_ticks'] = request_form.get(key)
        elif key == 'enable_start_on_tick':
            custom_options_json_postsave['enable_start_on_tick'] = request_form.get(key)
        elif key == 'enable_end_on_tick':
            custom_options_json_postsave['enable_end_on_tick'] = request_form.get(key)
        elif key == 'enable_graph_legend':
            custom_options_json_postsave['enable_graph_legend'] = request_form.get(key)

    custom_options_json_postsave['custom_yaxes'] = custom_yaxes_str_from_form(request_form)

    sorted_colors, error = custom_colors_graph(request_form, error)
    custom_options_json_postsave['custom_colors'] = sorted_colors

    disable_data_grouping, error = data_grouping_graph(request_form, error)
    custom_options_json_postsave['disable_data_grouping'] = disable_data_grouping

    series_type, error = series_type_graph(request_form, error)
    custom_options_json_postsave['series_type'] = series_type

    for each_error in error:
        flash(each_error, "error")

    return allow_saving, page_refresh, mod_widget, custom_options_json_postsave


def generate_page_variables(widget_unique_id, widget_options):
    dict_measurements = add_custom_measurements(Measurement.query.all())

    # Generate dictionary of custom colors for each graph
    colors_graph = dict_custom_colors(widget_options)

    # Generate a dictionary of lists of y-axes for each graph/gauge
    y_axes = graph_y_axes(dict_measurements, widget_options)

    # Generate a dictionary of each graph's y-axis minimum and maximum
    custom_yaxes = dict_custom_yaxes_min_max(y_axes, widget_options)

    dict_return = {
        'colors_graph': colors_graph,
        'y_axes': y_axes,
        'custom_yaxes': custom_yaxes
    }

    return dict_return


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_graph_synchronous',
    'widget_name': 'Graph (Synchronous) [Highstock]',
    'widget_library': 'Highstock',
    'no_class': True,

    'message': 'Displays a synchronous graph (all data is downloaded for the selected period on the x-axis).',

    'dependencies_module': [
        ('bash-commands',
        [
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/data-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/exporting-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/export-data-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/offline-exporting-9.1.2.js'
        ],
        [
            'rm -rf Highcharts-Stock-9.1.2.zip',
            'wget https://code.highcharts.com/zips/Highcharts-Stock-9.1.2.zip 2>&1',
            'unzip Highcharts-Stock-9.1.2.zip -d Highcharts-Stock-9.1.2',
            'cp -rf Highcharts-Stock-9.1.2/code/highstock.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/highstock.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/highcharts-more.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/highcharts-more.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/data.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/data-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/data.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/data.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/exporting.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/exporting-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/exporting.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/exporting.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/export-data.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/export-data-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/export-data.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/export-data.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/offline-exporting.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/offline-exporting-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/offline-exporting.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/offline-exporting.js.map',
            'rm -rf Highcharts-Stock-9.1.2.zip',
            'rm -rf Highcharts-Stock-9.1.2'
        ])
    ],

    'dependencies_message': 'Highcharts is free to use for open source, personal use. However, '
                            'if you are using this software as a part of a commercial product, '
                            'you or the manufacturer may be required to obtain a commercial '
                            'license to use it. Contact Highcharts for the most accurate '
                            'information, at https://shop.highsoft.com',

    'execute_at_creation': execute_at_creation,
    'execute_at_modification': execute_at_modification,
    'generate_page_variables': generate_page_variables,

    'endpoints': [
        # Route URL, route endpoint name, view function, methods
        ("/past/<unique_id>/<measure_type>/<measurement_id>/<past_seconds>", "past", past_data, ["GET"]),
    ],

    'widget_width': 24,
    'widget_height': 15,

    'custom_options': [
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 90.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': '{} ({})'.format(lazy_gettext("Refresh"), lazy_gettext("Seconds")),
            'phrase': 'The period of time between refreshing the widget'
        },
        {
            'id': 'x_axis_minutes',
            'type': 'integer',
            'default_value': 1440,
            'name': 'X-Axis Duration (minutes)',
            'phrase': 'The x-axis duration'
        },
        {
            'id': 'enable_auto_refresh',
            'type': 'bool',
            'default_value': True,
            'name': 'Enable Auto Refresh',
            'phrase': 'Enable the graph to automatically refresh with new data every Refresh period.'
        },
        {
            'id': 'enable_xaxis_reset',
            'type': 'bool',
            'default_value': True,
            'name': 'Enable X-Axis Reset',
            'phrase': 'Enable the X-Axis to reset every Refresh period.'
        },
        {
            'id': 'enable_header_buttons',
            'type': 'bool',
            'default_value': True,
            'name': 'Enable Header Buttons',
            'phrase': 'Enable buttons to control the graph on the widget header.'
        },
        {
            'id': 'enable_title',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Title',
            'phrase': 'Enable the graph title.'
        },
        {
            'id': 'enable_navbar',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Navbar',
            'phrase': 'Enable the graph navigation bar.'
        },
        {
            'id': 'enable_export',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Export',
            'phrase': 'Enable the graph export button.'
        },
        {
            'id': 'enable_range_selector',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Range Selector',
            'phrase': 'Enagle the graph range selector.'
        },
        {
            'id': 'enable_graph_legend',
            'type': 'bool',
            'default_value': True,
            'name': 'Enable Graph Legend',
            'phrase': 'Enable the Graph Legend that is displayed below the graph.'
        },
        {
            'id': 'graph_font_size_em_axes',
            'type': 'float',
            'default_value': 1.0,
            'name': 'Graph Axis Value Font Size (em)',
            'phrase': 'The size of the fonts of the x/y axis values of the graph'
        },
        {
            'id': 'graph_font_size_em_axes_title',
            'type': 'float',
            'default_value': 1.0,
            'name': 'Graph Axis Title Font Size (em)',
            'phrase': 'The size of the fonts of the x/y axis titles of the graph'
        },
        {
            'id': 'graph_font_size_em_legend',
            'type': 'float',
            'default_value': 1.0,
            'name': 'Graph Legend Font Size (em)',
            'phrase': 'The size of the fonts on the legend of the graph'
        },
        {
            'id': 'graph_font_size_em_title',
            'type': 'float',
            'default_value': 1.0,
            'name': 'Graph Title Font Size (em)',
            'phrase': 'The size of the fonts on the title of the graph'
        },
        {'type': 'new_line'},
        {
            'id': 'measurements_input',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Input'
            ],
            'name': lazy_gettext('Inputs'),
            'phrase': lazy_gettext('Select measurements to display')
        },
        {
            'id': 'measurements_function',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Function'
            ],
            'name': lazy_gettext('Function'),
            'phrase': lazy_gettext('Select measurements to display')
        },
        {
            'id': 'measurements_output',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Output'
            ],
            'name': lazy_gettext('Outputs'),
            'phrase': lazy_gettext('Select measurements to display')
        },
        {
            'id': 'measurements_pid',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'PID'
            ],
            'name': lazy_gettext('PIDs'),
            'phrase': lazy_gettext('Select measurements to display')
        },
        {
            'id': 'measurements_note_tag',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Tag'
            ],
            'name': lazy_gettext('Note Tags'),
            'phrase': lazy_gettext('Select measurements to display')
        },
        {
            'type': 'message',
            'default_value': 'Hold down the <kbd>Ctrl</kbd> or <kbd>&#8984;</kbd> key to select more than one',
        }
    ],

    'widget_dashboard_head': """{% if "highstock" not in dashboard_dict %}
  <script type="text/javascript" src="/static/js/user_js/highstock-9.1.2.js"></script>
  {% set _dummy = dashboard_dict.update({"highstock": 1}) %}
{% endif %}
<script type="text/javascript" src="/static/js/user_js/highcharts-more-9.1.2.js"></script>
<script type="text/javascript" src="/static/js/user_js/data-9.1.2.js"></script>
<script type="text/javascript" src="/static/js/user_js/exporting-9.1.2.js"></script>
<script type="text/javascript" src="/static/js/user_js/export-data-9.1.2.js"></script>
<script type="text/javascript" src="/static/js/user_js/offline-exporting-9.1.2.js"></script>

{% if current_user.theme in dark_themes %}
  <script type="text/javascript" src="/static/js/dark-unica-custom.js"></script>
{% endif %}
""",

    'widget_dashboard_title_bar': """
        <div class="widget-graph-title" id="widget-graph-title-{{each_widget.unique_id}}">
            <span style="font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>
        </div>
        {% if widget_options['enable_header_buttons'] -%}
        <div class="widget-graph-controls" id="widget-graph-controls-{{each_widget.unique_id}}">
            <div class="widget-graph-responsive-controls" id="widget-graph-responsive-controls-{{each_widget.unique_id}}">
                <a class="btn btn-sm btn-success" id="updateData{{each_widget.unique_id}}" title="{{_('Update')}}">
                    <i class="fa fa-download"></i>
                </a>
                <a class="btn btn-sm btn-success" id="resetZoom{{each_widget.unique_id}}" title="{{_('Reset')}}">
                    <i class="fa fa-undo-alt"></i>
                </a>
                <a class="btn btn-sm btn-success" id="showhidebutton{{each_widget.unique_id}}" title="{{_('Hide')}}">
                    <i class="fa fa-eye-slash"></i>
                </a>
            </div>
            <a href="javascript:void(0);" class="btn btn-sm menu" onclick="return graphMenuFunction('{{each_widget.unique_id}}');" title="{{_('Options')}}">
                <i class="fa fa-bars"></i>
            </a>
        </div>
        {% endif %}
    """,

    'widget_dashboard_body': """<div class="not-draggable" id="container-synchronous-graph-{{each_widget.unique_id}}" style="position: absolute; left: 0; top: 0; bottom: 0; right: 0; overflow: hidden;"></div>""",

    'widget_dashboard_configure_options': """
        <div class="row small-gutters" style="padding: 0.5em">
          <div class="col-12" style="font-weight: bold">
            Series Options
          </div>
          <div class="col-auto">
            <label class="control-label">Enable Custom Colors</label>
            <div class="input-group-text">
              <input id="use_custom_colors" name="use_custom_colors" type="checkbox" value="y"{% if widget_options['use_custom_colors'] %} checked{% endif %}>
            </div>
          </div>
        </div>
          {% for n in range(widget_variables['colors_graph']|length) %}
        <div class="row small-gutters" style="padding: 0.5em">
          <div class="col-12">
            {{widget_variables['colors_graph'][n]['type']}}
            {%- if 'channel' in widget_variables['colors_graph'][n] and widget_variables['colors_graph'][n]['channel'] is not none -%}
              {{', CH' + widget_variables['colors_graph'][n]['channel']|string}}
            {%- endif -%}
            {%- if widget_variables['colors_graph'][n]['name'] -%}
              {{', ' + widget_variables['colors_graph'][n]['name']}}
            {%- endif -%}
            {%- if widget_variables['colors_graph'][n]['measure_name'] -%}
              {{', ' + widget_variables['colors_graph'][n]['measure_name']}}
            {%- endif -%}
            {%- if widget_variables['colors_graph'][n]['unit'] in dict_units -%}
              {{' (' + dict_units[widget_variables['colors_graph'][n]['unit']]['name'] + ')'}}
            {%- endif -%}
          </div>
          <div class="col-auto">
            {% set index = '{0:0>2}'.format(n) %}
            <label class="control-label" for="color_number{{index}}">Color</label>
            <div>
              <input id="color_number{{index}}" name="color_number{{index}}" placeholder="#000000" type="color" value="{{widget_variables['colors_graph'][n]['color']}}">
            </div>
          </div>
            {% if widget_variables['colors_graph'][n]['type'] != 'Tag' %}
          <div class="col-auto">
            <label class="control-label">Disable Data Grouping</label>
            <div class="input-group-text">
              <input id="disable_data_grouping-{{widget_variables['colors_graph'][n]['measure_id']}}" name="disable_data_grouping-{{widget_variables['colors_graph'][n]['measure_id']}}" type="checkbox" value="y"{% if widget_variables['colors_graph'][n]['disable_data_grouping'] %} checked{% endif %}>
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label">Series Type</label>
            <div class="input-group-text">
              <select id="series_type-{{widget_variables['colors_graph'][n]['measure_id']}}" name="series_type-{{widget_variables['colors_graph'][n]['measure_id']}}">
                <option value="line" {% if widget_variables['colors_graph'][n]['series_type'] == "line" %} selected{% endif %}>Line</option>
                <option value="step-left" {% if widget_variables['colors_graph'][n]['series_type'] == "step-left" %} selected{% endif %}>Line (Step, Left)</option>
                <option value="step-center" {% if widget_variables['colors_graph'][n]['series_type'] == "step-center" %} selected{% endif %}>Line (Step, Center)</option>
                <option value="step-right" {% if widget_variables['colors_graph'][n]['series_type'] == "step-right" %} selected{% endif %}>Line (Step, Right)</option>
                <option value="column" {% if widget_variables['colors_graph'][n]['series_type'] == "column" %} selected{% endif %}>Column</option>
              </select>
            </div>
          </div>
            {% endif %}
        </div>
          {% endfor %}

        <div class="row small-gutters" style="padding: 0.5em">
          <div class="col-12" style="font-weight: bold">
            Y-Axis Options
          </div>
          <div class="col-auto">
            <label class="control-label">Enable Manual Y-Axis Min/Max</label>
            <div class="input-group-text">
              <input id="enable_manual_y_axis" name="enable_manual_y_axis" type="checkbox" value="y"{% if widget_options['enable_manual_y_axis'] %} checked{% endif %}>
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label">Enable Y-Axis Align Ticks</label>
            <div class="input-group-text">
              <input id="enable_align_ticks" name="enable_align_ticks" type="checkbox" value="y"{% if widget_options['enable_align_ticks'] %} checked{% endif %}>
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label">Enable Y-Axis Start On Tick</label>
            <div class="input-group-text">
              <input id="enable_start_on_tick" name="enable_start_on_tick" type="checkbox" value="y"{% if widget_options['enable_start_on_tick'] %} checked{% endif %}>
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label">Enable Y-Axis End On Tick</label>
            <div class="input-group-text">
              <input id="enable_end_on_tick" name="enable_end_on_tick" type="checkbox" value="y"{% if widget_options['enable_end_on_tick'] %} checked{% endif %}>
            </div>
          </div>
        </div>

      {% for each_yaxis in widget_variables['y_axes'] if each_yaxis in dict_units %}
        {% set index = '{0:0>2}'.format(loop.index) %}
        <div class="row small-gutters" style="padding-left: 0.5em">
          <div class="col-auto">
            {{dict_units[each_yaxis]['name']}}{% if dict_units[each_yaxis]['unit'] != '' %} ({{dict_units[each_yaxis]['unit']}}){% endif %}
          </div>
        </div>

        <div class="row small-gutters" style="padding-left: 0.5em">
          <input type="hidden" name="custom_yaxis_name_{{index}}" value="{{each_yaxis}}">
          <div class="col-auto">
            <label class="form-check-label" for="custom_yaxis_min_{{index}}">Y-Axis Minimum</label>
            <div>
              <input id="yaxis_min_{{index}}" class="form-control" name="custom_yaxis_min_{{index}}" type="number" value="{% if widget_variables['custom_yaxes'][each_yaxis] %}{{widget_variables['custom_yaxes'][each_yaxis]['minimum']}}{% endif %}">
            </div>
          </div>
          <div class="col-auto">
            <label class="form-check-label" for="custom_yaxis_max_{{index}}">Y-Axis Maximum</label>
            <div>
              <input id="yaxis_max_{{index}}" class="form-control" name="custom_yaxis_max_{{index}}" type="number" value="{% if widget_variables['custom_yaxes'][each_yaxis] %}{{widget_variables['custom_yaxes'][each_yaxis]['maximum']}}{% endif %}">
            </div>
          </div>
        </div>
      {% endfor %}
""",

    'widget_dashboard_js': """
  Highcharts.setOptions({
    global: {
      useUTC: false
    },
    lang: {
      thousandsSep: ','
    }
  });

  // Change opacity of all chart colors
  Highcharts.getOptions().colors = Highcharts.map(Highcharts.getOptions().colors, function (color) {
    return Highcharts.Color(color).setOpacity(0.6).get('rgba');
  });

  let note_timestamps = {};
  let last_output_time_mil = {};  // Store the time (epoch) of the last data point received

  function graphMenuFunction(widget_id) {
    var x = document.getElementById("widget-graph-responsive-controls-" + widget_id);
    var y = document.getElementById("widget-graph-title-" + widget_id);
    if (x.className === "widget-graph-responsive-controls") {
      x.className += " responsive";
    } else {
      x.className = "widget-graph-responsive-controls";
    }
    if (y.className === "widget-graph-title") {
      y.className += " responsive";
    } else {
      y.className = "widget-graph-title";
    }
  }

  // Redraw a particular chart
  function redrawGraph(widget_id, refresh_seconds, xaxis_duration_min, xaxis_reset) {
    widget[widget_id].redraw();

    if (xaxis_reset) {
      const epoch_min = new Date().setMinutes(new Date().getMinutes() - (1 * (xaxis_duration_min)));
      const epoch_max = new Date().getTime();

      // Ensure Reset Zoom button resets to the proper start and end times
      widget[widget_id].xAxis[0].update({min: epoch_min}, false);
      widget[widget_id].xAxis[0].update({max: epoch_max}, false);

      // Update the new data time frame and redraw the chart
      widget[widget_id].xAxis[0].setExtremes(epoch_min, epoch_max, true);
      widget[widget_id].xAxis[0].isDirty = true;
    }
  }

  // Retrieve initial graph data set from the past (duration set by user)
  function getPastDataSynchronousGraph(widget_id,
                       series,
                       unique_id,
                       measure_type,
                       measurement_id,
                       past_seconds) {
    const epoch_mil = new Date().getTime();
    const url = '/past/' + unique_id + '/' + measure_type + '/' + measurement_id + '/' + past_seconds;
    const update_id = widget_id + "-" + series + "-" + unique_id + "-" + measure_type + '-' + measurement_id;

    $.getJSON(url,
      function(data, responseText, jqXHR) {
        if (jqXHR.status !== 204) {
          let past_data = [];
          const note_key = widget_id + "_" + series;

          // Add the received data to the graph
          for (let i = 0; i < data.length; i++) {
            const new_time = new Date(data[i][0] * 1000).getTime();

            if (measure_type === 'tag') {
              if (!(note_key in note_timestamps)) note_timestamps[note_key] = [];
              if (!note_timestamps[note_key].includes(new_time)) {
                past_data.push({
                  x: new_time,
                  title: data[i][1],
                  text: data[i][2].replace(/(?:\\r\\n|\\r|\\n)/g, '<br/>').replace(/  /g, '\\u2591\\u2591')
                });
                note_timestamps[note_key].push(new_time);
              }
            }
            else {
              past_data.push([new_time, data[i][1]]);
            }

            // Store the epoch time of the last data point received
            if (i === data.length - 1) {
              if (measure_type === 'tag') last_output_time_mil[update_id] = new_time + 3000;
              else last_output_time_mil[update_id] = new_time;
            }
          }

          // Set x-axis extremes, set graph data
          widget[widget_id].series[series].isDirty = true;  // Data may not be in order by timestamp
          const epoch_min = new Date().setMinutes(new Date().getMinutes() - (past_seconds / 60))
          widget[widget_id].xAxis[0].setExtremes(epoch_min, epoch_mil);
          widget[widget_id].series[series].setData(past_data, true, false);
        }
      }
    );
  }

  // Retrieve chart data for the period since the last data acquisition (refresh period set by user)
  function retrieveLiveDataSynchronousGraph(widget_id,
                            series,
                            unique_id,
                            measure_type,
                            measurement_id,
                            xaxis_duration_min,
                            xaxis_reset,
                            refresh_seconds) {
    // Determine the timestamp of the last known measurement on the graph and
    // calculate the number of seconds from then until now, then build the URL
    // to query the measurements from that time period.
    let url = '';
    const epoch_mil = new Date().getTime();
    let update_id = widget_id + "-" + series + "-" + unique_id + "-" + measure_type + '-' + measurement_id;
    if (update_id in last_output_time_mil) {
      const past_seconds = Math.floor((epoch_mil - last_output_time_mil[update_id]) / 1000);  // seconds (integer)
      url = '/past/' + unique_id + '/' + measure_type + '/' + measurement_id + '/' + past_seconds;
    } else {
      url = '/past/' + unique_id + '/' + measure_type + '/' + measurement_id + '/' + refresh_seconds;
    }

    $.getJSON(url,
      function(data, responseText, jqXHR) {
        if (jqXHR.status !== 204) {
          let time_point;
          const note_key = widget_id + "_" + series;
          // The timestamp of the beginning of the graph (oldest timestamp allowed on the graph)
          const oldest_timestamp_allowed = epoch_mil - (xaxis_duration_min * 60 * 1000);

          // Loop through data and add points to chart
          for (let i = 0; i < data.length; i++) {
            const time_point_raw = new Date(data[i][0] * 1000);
            time_point = time_point_raw.getTime();

            if (measure_type === 'tag') {
              if (!(note_key in note_timestamps)) note_timestamps[note_key] = [];
              if (!note_timestamps[note_key].includes(time_point)) {
                widget[widget_id].series[series].addPoint({
                    x: time_point,
                    title: data[i][1],
                    text: data[i][2].replace(/(?:\\r\\n|\\r|\\n)/g, '<br/>').replace(/  /g, '\\u2591\\u2591')
                }, false, false);
                note_timestamps[note_key].push(time_point);
              }
            }
            else {
              widget[widget_id].series[series].addPoint([time_point, data[i][1]], false, false);
            }
          }

          // Store last point timestamp
          if (measure_type === 'tag') last_output_time_mil[update_id] = time_point + 3000;
          else last_output_time_mil[update_id] = time_point;

          // Finally, redraw the graph
          redrawGraph(widget_id, refresh_seconds, xaxis_duration_min, xaxis_reset);

          // Remove any points before beginning of chart
          for (let i = 0; i < widget[widget_id].series[series].options.data.length; i++) {
            // Get stored point timestamp
            if (measure_type === 'tag') point_ts = widget[widget_id].series[series].options.data[i].x;
            else point_ts = widget[widget_id].series[series].options.data[i][0];

            // If stored point timestamp outside graph view, delete the point
            if (point_ts < oldest_timestamp_allowed) {
              widget[widget_id].series[series].removePoint(i, false);

              // Remove timestamp from note array
              if (measure_type === 'tag') {
                const index = note_timestamps[note_key].indexOf(point_ts);
                if (index > -1) note_timestamps[note_key].splice(index, 1);
              }
            } else break;
          }
        }
      }
    );
  }

  // Repeat function for retrieveLiveData()
  function getLiveDataSynchronousGraph(widget_id,
                       series,
                       unique_id,
                       measure_type,
                       measurement_id,
                       xaxis_duration_min,
                       xaxis_reset,
                       refresh_seconds) {
    setInterval(function () {
      retrieveLiveDataSynchronousGraph(widget_id,
                       series,
                       unique_id,
                       measure_type,
                       measurement_id,
                       xaxis_duration_min,
                       xaxis_reset,
                       refresh_seconds);
    }, refresh_seconds * 1000);
  }
""",

    'widget_dashboard_js_ready': """<!-- No JS ready content -->""",

    'widget_dashboard_js_ready_end': """
{% set graph_output_ids = widget_options['measurements_output'] %}
{% set graph_input_ids = widget_options['measurements_input'] %}
{% set graph_function_ids = widget_options['measurements_function'] %}
{% set graph_pid_ids = widget_options['measurements_pid'] %}
{% set graph_note_tag_ids = widget_options['measurements_note_tag'] %}

  widget['{{each_widget.unique_id}}'] = new Highcharts.StockChart({
    chart : {
      renderTo: 'container-synchronous-graph-{{each_widget.unique_id}}',
      zoomType: 'x',
      alignTicks: {% if widget_options['enable_align_ticks'] %}true{% else %}false{% endif %},
      resetZoomButton: {
        theme: { style: { display: 'none'} }
      },

      events: {
        load: function () {
          {% set count_series = [] -%}

          {%- for output_and_measurement_ids in graph_output_ids -%}
            {%- set output_id = output_and_measurement_ids.split(',')[0] -%}
            {%- set measurement_id = output_and_measurement_ids.split(',')[1] -%}
            {%- set all_output = table_output.query.filter(table_output.unique_id == output_id).all() -%}
            {%- if all_output -%}
              {% for each_output in all_output %}
          getPastDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_output.unique_id}}', 'output', '{{measurement_id}}', {{widget_options['x_axis_minutes']*60}});
                {% if widget_options['enable_auto_refresh'] -%}
          getLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_output.unique_id}}', 'output', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
                {%- endif -%}
                {%- do count_series.append(1) -%}
              {%- endfor -%}
            {%- endif -%}
          {%- endfor -%}

          {%- for input_and_measurement_ids in graph_input_ids -%}
            {%- set input_id = input_and_measurement_ids.split(',')[0] -%}
            {%- set measurement_id = input_and_measurement_ids.split(',')[1] -%}
            {%- set all_input = table_input.query.filter(table_input.unique_id == input_id).all() -%}
            {%- if all_input -%}
              {% for each_input in all_input %}
          getPastDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_input.unique_id}}', 'input', '{{measurement_id}}', {{widget_options['x_axis_minutes']*60}});
                {% if widget_options['enable_auto_refresh'] -%}
          getLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_input.unique_id}}', 'input', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
                {%- endif -%}
                {%- do count_series.append(1) -%}
              {%- endfor -%}
            {%- endif -%}
          {%- endfor -%}

          {%- for function_and_measurement_ids in graph_function_ids -%}
            {%- set function_id = function_and_measurement_ids.split(',')[0] -%}
            {%- set measurement_id = function_and_measurement_ids.split(',')[1] -%}
            {%- set all_function = table_function.query.filter(table_function.unique_id == function_id).all() -%}
            {%- if all_function -%}
              {% for each_function in all_function %}
          getPastDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_function.unique_id}}', 'function', '{{measurement_id}}', {{widget_options['x_axis_minutes']*60}});
                {% if widget_options['enable_auto_refresh'] %}
          getLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_function.unique_id}}', 'function', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
                {% endif %}
                {%- do count_series.append(1) %}
              {%- endfor -%}
            {%- endif -%}
          {%- endfor -%}

          {%- for each_pid in pid -%}
            {%- for pid_and_measurement_id in graph_pid_ids if each_pid.unique_id == pid_and_measurement_id.split(',')[0] %}
              {%- set measurement_id = pid_and_measurement_id.split(',')[1] -%}
          getPastDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_pid.unique_id}}', 'pid', '{{measurement_id}}', {{widget_options['x_axis_minutes']*60}});
          {% if widget_options['enable_auto_refresh'] %}
          getLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_pid.unique_id}}', 'pid', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
          {% endif %}
              {%- do count_series.append(1) %}
            {%- endfor -%}
          {%- endfor -%}

          {%- for each_tag in tags -%}
            {%- for tag_and_measurement_id in graph_note_tag_ids if each_tag.unique_id == tag_and_measurement_id.split(',')[0] %}
              {%- set measurement_id = tag_and_measurement_id.split(',')[1] -%}
          getPastDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_tag.unique_id}}', 'tag', '{{measurement_id}}', {{widget_options['x_axis_minutes']*60}});
          {% if widget_options['enable_auto_refresh'] %}
          getLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_tag.unique_id}}', 'tag', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
          {% endif %}
              {%- do count_series.append(1) %}
            {%- endfor -%}
          {%- endfor -%}
        }
      }
    },
  {% if widget_options['use_custom_colors'] and widget_options['custom_colors'] -%}
    {% set color_list = widget_options['custom_colors'] %}
      colors: [
    {%- for each_color in color_list -%}
      "{{each_color}}",
     {%- endfor -%}],
  {%- endif -%}

    title: {
      text: "{% if widget_options['enable_title'] %}{{each_widget.name}}{% endif %}",
      style: {
        fontSize:'{{widget_options['graph_font_size_em_title']}}em'
      }
    },

    legend: {
      enabled: {% if widget_options['enable_graph_legend'] %}true{% else %}false{% endif %},
      itemStyle: {
        fontSize:'{{widget_options['graph_font_size_em_legend']}}em'
      }
    },

    xAxis: {
      type: 'datetime',
      ordinal: false,
      labels: {
        style: {
          fontSize:'{{widget_options['graph_font_size_em_axes']}}em'
        }
      }
    },

    yAxis: [
  {% for each_axis_meas in widget_variables['y_axes'] if each_axis_meas in dict_units %}
      {
    {% if widget_options['enable_manual_y_axis'] and
          widget_variables['custom_yaxes'][each_axis_meas]['minimum'] != widget_variables['custom_yaxes'][each_axis_meas]['maximum'] %}
        min: {{widget_variables['custom_yaxes'][each_axis_meas]['minimum']}},
        max: {{widget_variables['custom_yaxes'][each_axis_meas]['maximum']}},
        startOnTick: {% if widget_options['enable_start_on_tick'] %}true{% else %}false{% endif %},
        endOnTick: {% if widget_options['enable_end_on_tick'] %}true{% else %}false{% endif %},
    {% endif %}
        title: {
          text: "{{dict_units[each_axis_meas]['name']}}
    {%- if dict_units[each_axis_meas]['unit'] != '' -%}
      {{' (' + dict_units[each_axis_meas]['unit'] + ')'}}
    {%- endif -%}",
          style: {
            fontSize:'{{widget_options['graph_font_size_em_axes_title']}}em'
          }
        },
        labels: {
          format: '{value}',
          style: {
            fontSize:'{{widget_options['graph_font_size_em_axes']}}em'
          }
        },
        opposite: false,
        id: '{{each_axis_meas}}'
      },
  {% endfor %}
    ],

    exporting: {
      enabled: {% if widget_options['enable_export'] %}true{% else %}false{% endif %},
      fallbackToExportServer: false,
    },

    navigator: {
      enabled: {% if widget_options['enable_navbar'] %}true{% else %}false{% endif %}
    },

    scrollbar: {
      enabled: false
    },

    rangeSelector: {
      enabled: {% if widget_options['enable_range_selector'] %}true{% else %}false{% endif %},
      buttons: [{
        count: 1,
        type: 'minute',
        text: '1m'
      }, {
        count: 5,
        type: 'minute',
        text: '5m'
      }, {
        count: 15,
        type: 'minute',
        text: '15m'
      }, {
        count: 30,
        type: 'minute',
        text: '30m'
      }, {
        type: 'hour',
        count: 1,
        text: '1h'
      }, {
        type: 'hour',
        count: 6,
        text: '6h'
      }, {
        type: 'day',
        count: 1,
        text: '1d'
      }, {
        type: 'week',
        count: 1,
        text: '1w'
      }, {
        type: 'month',
        count: 1,
        text: '1m'
      }, {
        type: 'month',
        count: 3,
        text: '3m'
      }, {
        type: 'all',
        text: 'Full'
      }],
      selected: 15
    },

    credits: {
      enabled: false,
      href: "https://github.com/kizniche/Mycodo",
      text: "Mycodo"
    },

    tooltip: {
      shared: true,
      useHTML: true,
      formatter: function(){
        const d = new Date(this.x);
        if (this.point) {
          return '<b>'+ Highcharts.dateFormat('%B %e, %Y %H:%M:%S.', this.x) + d.getMilliseconds()
               + '</b><br/>' + this.series.name
               + '<br/>' + this.point.title
               + '<br/>' + this.point.text;
        }
        else {
          let s = '<b>' + Highcharts.dateFormat('%B %e, %Y %H:%M:%S.', this.x) + d.getMilliseconds() + '</b>';
          $.each(this.points, function(i, point) {
              s += '<br/><span style="color:' + point.color + '">&#9679;</span> ' + point.series.name + ': ' + Highcharts.numberFormat(point.y, this.series.tooltipOptions.valueDecimals) + ' ' + this.series.tooltipOptions.valueSuffix;
          });
          return s;
        }
      }
    },

    plotOptions: {
      column: {
        maxPointWidth: 3  /* limit the maximum column width. */
      },
      series:{
        states: {
          hover: {
            enabled: false
          }
        }
      }
    },

{#    // Generate  thermal image from pixel data#}
{#    // point click event opens image in a new window#}
{#    plotOptions: {#}
{#      series: {#}
{#        cursor: 'pointer',#}
{#        point: {#}
{#          events: {#}
{#            click: function () {#}
{#              URL = '/generate_thermal_image/f36ce034-3129-456d-b877-ff0d5587e375/' + this.x;#}
{#              window.open(URL, "_blank");#}
{#            }#}
{#          }#}
{#        }#}
{#      }#}
{#    },#}

{#    plotOptions: {#}
{#      series: {#}
{#        cursor: 'pointer',#}
{#        point: {#}
{#          events: {#}
{#            click: function(e){#}
{#              hs.htmlExpand(null, {#}
{#                pageOrigin: {#}
{#                  x: e.pageX || e.clientX,#}
{#                  y: e.pageY || e.clientY#}
{#                },#}
{#                headingText: this.series.name,#}
{#                maincontentText: '<img src="/generate_thermal_image/f36ce034-3129-456d-b877-ff0d5587e375/' + this.x + '">',#}
{#                width: 215,#}
{#                height: 255,#}
{#              });#}
{#            }#}
{#          }#}
{#        },#}
{#        marker: {#}
{#          lineWidth: 1#}
{#        }#}
{#      }#}
{#    },#}

    series: [
  {%- for output_and_measurement_ids in graph_output_ids -%}
    {%- set output_id = output_and_measurement_ids.split(',')[0] -%}
    {%- set this_output = table_output.query.filter(table_output.unique_id == output_id).first() -%}
    {%- if this_output -%}
      {%- set measurement_id = output_and_measurement_ids.split(',')[1] -%}
      {%- set ns = namespace() -%}

      {%- set ns.disable_data_grouping = false -%}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['disable_data_grouping'] %}
        {%- set ns.disable_data_grouping = true -%}
      {% endfor %}
      
      {%- set ns.series_type = "column" %}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['series_type'] %}
        {% set ns.series_type = each_series['series_type'] -%}
      {% endfor %}

      {%- if measurement_id in device_measurements_dict -%}
      {
        name: "{{this_output.name}}

        {%- if device_measurements_dict[measurement_id].name -%}
          {{' (' + device_measurements_dict[measurement_id].name}})
        {%- endif -%}

        {{' (CH' + (device_measurements_dict[measurement_id].channel)|string}}

        {%- if 'channels_dict' in dict_outputs[this_output.output_type] -%}
          {%- for channel_num in dict_outputs[this_output.output_type]['channels_dict'] -%}
            {%- if device_measurements_dict[measurement_id].channel in dict_outputs[this_output.output_type]['channels_dict'][channel_num]['measurements'] and
                   output_id in custom_options_values_output_channels and
                   channel_num in custom_options_values_output_channels[output_id] and
                   'name' in custom_options_values_output_channels[output_id][channel_num] -%}
              {{', ' + custom_options_values_output_channels[output_id][channel_num]['name']}}
            {%- endif -%}
          {%- endfor -%}
        {%- endif -%}

        {%- if dict_measure_measurements[measurement_id] in dict_measurements and
               dict_measurements[dict_measure_measurements[measurement_id]]['name'] -%}
          {{', ' + dict_measurements[dict_measure_measurements[measurement_id]]['name']}}
        {%- endif -%}

        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] -%}
          {{', ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

          )",
        {% if ns.series_type in ['line', 'column'] -%}
        type: '{{ns.series_type}}',
        {%- elif ns.series_type == 'step-left' -%}
        step: 'left',
        {%- elif ns.series_type == 'step-center' -%}
        step: 'center',
        {%- elif ns.series_type == 'step-right' -%}
        step: 'right',
        {%- endif %}
        dataGrouping: {
          enabled: {% if ns.disable_data_grouping %}false{% else %}true{% endif %},
          groupPixelWidth: 5
        },
        tooltip: {
          valueSuffix: '
        {%- if device_measurements_dict[measurement_id].conversion_id -%}
          {{' ' + dict_units[table_conversion.query.filter(table_conversion.unique_id == device_measurements_dict[measurement_id].conversion_id).first().convert_unit_to]['unit']}}
        {%- elif device_measurements_dict[measurement_id].rescaled_unit -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].rescaled_unit]['unit']}}
        {%- else -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
        {%- endif -%}
          ',
          valueDecimals: 3
        },
        yAxis: '
        {%- if measurement_id in dict_measure_units -%}
          {{dict_measure_units[measurement_id]}}
        {%- endif -%}
            ',
        data: []
      },

      {%- endif -%}
    {%- endif -%}
  {%- endfor -%}

  {%- for input_and_measurement_ids in graph_input_ids -%}
    {%- set input_id = input_and_measurement_ids.split(',')[0] -%}
    {%- set this_input = table_input.query.filter(table_input.unique_id == input_id).first() -%}
    {%- if this_input -%}
      {%- set measurement_id = input_and_measurement_ids.split(',')[1] -%}
      {%- set ns = namespace() -%}

      {%- set ns.disable_data_grouping = false -%}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['disable_data_grouping'] %}
        {%- set ns.disable_data_grouping = true -%}
      {% endfor %}
      
      {%- set ns.series_type = "line" %}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['series_type'] %}
        {% set ns.series_type = each_series['series_type'] -%}
      {% endfor %}

      {%- if measurement_id in device_measurements_dict -%}
      {
        name: "{{this_input.name}}

        {%- if device_measurements_dict[measurement_id].name -%}
          {{' (' + device_measurements_dict[measurement_id].name}})
        {%- endif -%}

        {{' (CH' + (device_measurements_dict[measurement_id].channel)|string}}

        {%- if dict_measure_measurements[measurement_id] in dict_measurements and
               dict_measurements[dict_measure_measurements[measurement_id]]['name'] -%}
          {{', ' + dict_measurements[dict_measure_measurements[measurement_id]]['name']}}
        {%- endif -%}

        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] -%}
          {{', ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

          )",
        {% if ns.series_type in ['line', 'column'] -%}
        type: '{{ns.series_type}}',
        {%- elif ns.series_type == 'step-left' -%}
        step: 'left',
        {%- elif ns.series_type == 'step-center' -%}
        step: 'center',
        {%- elif ns.series_type == 'step-right' -%}
        step: 'right',
        {%- endif %}
        dataGrouping: {
          enabled: {% if ns.disable_data_grouping %}false{% else %}true{% endif %},
          groupPixelWidth: 2
        },
        tooltip: {
          valueSuffix: '
        {%- if device_measurements_dict[measurement_id].conversion_id -%}
          {{' ' + dict_units[table_conversion.query.filter(table_conversion.unique_id == device_measurements_dict[measurement_id].conversion_id).first().convert_unit_to]['unit']}}
        {%- elif device_measurements_dict[measurement_id].rescaled_unit -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].rescaled_unit]['unit']}}
        {%- else -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
        {%- endif -%}
          ',
          valueDecimals: 3
        },
        yAxis: '
        {%- if measurement_id in dict_measure_units -%}
          {{dict_measure_units[measurement_id]}}
        {%- endif -%}
            ',
        data: []
      },

      {%- endif -%}
    {%- endif -%}
  {%- endfor -%}

  {% for each_function in function -%}
    {%- for function_and_measurement_ids in graph_function_ids if each_function.unique_id == function_and_measurement_ids.split(',')[0] -%}
      {%- set measurement_id = function_and_measurement_ids.split(',')[1] -%}
      {%- set ns = namespace() -%}

      {%- set ns.disable_data_grouping = false -%}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['disable_data_grouping'] %}
        {%- set ns.disable_data_grouping = true -%}
      {% endfor %}
      
      {%- set ns.series_type = "line" %}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['series_type'] %}
        {% set ns.series_type = each_series['series_type'] -%}
      {% endfor %}

      {%- if measurement_id in device_measurements_dict -%}
      {
      name: "{{each_function.name}}

        {%- if device_measurements_dict[measurement_id].name -%}
          {{' (' + device_measurements_dict[measurement_id].name}})
        {%- endif -%}

          {{' (CH' + (device_measurements_dict[measurement_id].channel)|string}}

        {%- if dict_measure_measurements[measurement_id] in dict_measurements and
               dict_measurements[dict_measure_measurements[measurement_id]]['name'] -%}
          {{', ' + dict_measurements[dict_measure_measurements[measurement_id]]['name']}}
        {%- endif -%}

        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] -%}
          {{', ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

        )",
      {% if ns.series_type in ['line', 'column'] -%}
      type: '{{ns.series_type}}',
      {%- elif ns.series_type == 'step-left' -%}
      step: 'left',
      {%- elif ns.series_type == 'step-center' -%}
      step: 'center',
      {%- elif ns.series_type == 'step-right' -%}
      step: 'right',
      {%- endif %}
      dataGrouping: {
        enabled: {% if ns.disable_data_grouping %}false{% else %}true{% endif %},
        groupPixelWidth: 2
      },
      tooltip: {
        valueSuffix: '
        {%- if device_measurements_dict[measurement_id].conversion_id -%}
          {{' ' + dict_units[table_conversion.query.filter(table_conversion.unique_id == device_measurements_dict[measurement_id].conversion_id).first().convert_unit_to]['unit']}}
        {%- elif device_measurements_dict[measurement_id].rescaled_unit -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].rescaled_unit]['unit']}}
        {%- else -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
        {%- endif -%}
        ',
        valueDecimals: 3
      },
      yAxis: '
        {%- if measurement_id in dict_measure_units -%}
          {{dict_measure_units[measurement_id]}}
        {%- endif -%}
          ',
      data: []
    },

      {%- endif -%}
    {%- endfor -%}
  {% endfor %}

  {%- for each_pid in pid -%}
    {%- for pid_and_measurement_ids in graph_pid_ids if each_pid.unique_id == pid_and_measurement_ids.split(',')[0] -%}
      {%- set measurement_id = pid_and_measurement_ids.split(',')[1] -%}
      {%- set ns = namespace() -%}

      {%- set ns.disable_data_grouping = false -%}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['disable_data_grouping'] %}
        {%- set ns.disable_data_grouping = true -%}
      {% endfor %}
      
      {%- set ns.series_type = "line" %}
      {% for each_series in widget_variables['colors_graph'] if each_series['measure_id'] == measurement_id and each_series['series_type'] %}
        {% set ns.series_type = each_series['series_type'] -%}
      {% endfor %}

      {%- if measurement_id in device_measurements_dict -%}
    {
      name: "{{each_pid.name}}

        {%- if device_measurements_dict[measurement_id].name -%}
          {{' (' + device_measurements_dict[measurement_id].name}})
        {%- endif -%}

          {{' (CH' + (device_measurements_dict[measurement_id].channel)|string}}

        {%- if dict_measure_measurements[measurement_id] in dict_measurements and
               dict_measurements[dict_measure_measurements[measurement_id]]['name'] -%}
          {{', ' + dict_measurements[dict_measure_measurements[measurement_id]]['name']}}
        {%- endif -%}

        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] -%}
          {{', ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

        )",
      {% if ns.series_type in ['line', 'column'] -%}
      type: '{{ns.series_type}}',
      {%- elif ns.series_type == 'step-left' -%}
      step: 'left',
      {%- elif ns.series_type == 'step-center' -%}
      step: 'center',
      {%- elif ns.series_type == 'step-right' -%}
      step: 'right',
      {%- endif %}
      dataGrouping: {
        enabled: {% if ns.disable_data_grouping %}false{% else %}true{% endif %},
        groupPixelWidth: 2
      },
      tooltip: {
        valueSuffix: '
        {%- if measurement_id in dict_measure_units and dict_measure_units[measurement_id] in dict_units -%}
          {{' ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}
        ',
        valueDecimals: 3
      },
      yAxis: '
        {%- if measurement_id in dict_measure_units -%}
          {{dict_measure_units[measurement_id]}}
        {%- endif -%}
          ',
      data: []
    },

      {%- endif -%}
    {%- endfor -%}
  {% endfor %}

  {%- for each_tag in tags -%}
    {%- for each_graph_note_tag_id in graph_note_tag_ids if each_tag.unique_id == each_graph_note_tag_id.split(',')[0] -%}
      {
        name: 'Note Tag: {{each_tag.name}}',
        type: 'flags',
        data: [],
        stackDistance: 40,
        shape: 'squarepin'
      },
    {% endfor %}
  {% endfor %}

    ]
  });

  $('#updateData{{each_widget.unique_id}}').click(function() {
    {% set count_series = [] -%}

    {% for each_output in output -%}
      {% for output_and_measurement_ids in graph_output_ids if each_output.unique_id == output_and_measurement_ids.split(',')[0] %}
        {%- set measurement_id = output_and_measurement_ids.split(',')[1] -%}
    retrieveLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_output.unique_id}}', 'output', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
        {%- do count_series.append(1) %}
      {% endfor %}
    {%- endfor -%}

    {% for each_input in input -%}
      {% for input_and_measurement_ids in graph_input_ids if each_input.unique_id == input_and_measurement_ids.split(',')[0] %}
        {%- set measurement_id = input_and_measurement_ids.split(',')[1] -%}
    retrieveLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_input.unique_id}}', 'input', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
        {%- do count_series.append(1) %}
      {% endfor %}
    {%- endfor -%}

    {% for each_function in function -%}
      {% for function_and_measurement_id in graph_function_ids if each_function.unique_id == function_and_measurement_id.split(',')[0] %}
        {%- set measurement_id = function_and_measurement_id.split(',')[1] -%}
    retrieveLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_function.unique_id}}', 'function', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
        {%- do count_series.append(1) %}
      {% endfor %}
    {%- endfor -%}

    {% for each_pid in pid -%}
      {% for pid_and_measurement_id in graph_pid_ids if each_pid.unique_id == pid_and_measurement_id.split(',')[0] %}
        {%- set measurement_id = pid_and_measurement_id.split(',')[1] -%}
    retrieveLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_pid.unique_id}}', 'pid', '{{measurement_id}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
        {%- do count_series.append(1) %}
      {% endfor %}
    {%- endfor -%}

    {%- for each_tag in tag -%}
      {% for each_id_and_measure in graph_note_tag_ids if each_pid.unique_id == each_id_and_measure.split(',')[0] %}
    retrieveLiveDataSynchronousGraph('{{each_widget.unique_id}}', {{count_series|count}}, '{{each_id_and_measure.split(',')[1]}}', '{{each_id_and_measure.split(',')[0]}}', {{widget_options['x_axis_minutes']}}, {{widget_options['enable_xaxis_reset']|int}}, {{widget_options['refresh_seconds']}});
        {%- do count_series.append(1) %}
      {% endfor %}
    {%- endfor -%}
  });

  $('#resetZoom{{each_widget.unique_id}}').click(function() {
    const chart = $('#container-synchronous-graph-{{each_widget.unique_id}}').highcharts();
    chart.zoomOut();
  });

  $('#showhidebutton{{each_widget.unique_id}}').click(function() {
    const chart = $('#container-synchronous-graph-{{each_widget.unique_id}}').highcharts();
    const series = chart.series[0];
    if (series.visible) {
      $(chart.series).each(function(){
        this.setVisible(false, false);
      });
      chart.redraw();
    } else {
      $(chart.series).each(function(){
        this.setVisible(true, false);
      });
      chart.redraw();
    }
  });
""",
}


def data_grouping_graph(form, error):
    """
    Get checkbox options for data grouping
    :param form: form object submitted by user on web page
    :param error: list of accumulated errors to add to
    :return:
    """
    list_data_grouping = []
    for key in form.keys():
        if 'disable_data_grouping' in key:
            list_data_grouping.append(key[22:])
    return list_data_grouping, error


def series_type_graph(form, error):
    """
    Get select options for series type
    :param form: form object submitted by user on web page
    :param error: list of accumulated errors to add to
    :return:
    """
    series_types = {}
    for key in form.keys():
        if 'series_type' in key:
            for value in form.getlist(key):
                if value not in ["column", "line", "step-left", "step-center", "step-right"]:
                    error.append("Invalid series type")
                series_types[key[12:]] = value
    return series_types, error


def custom_yaxes_str_from_form(form):
    """
    Parse several yaxis min/max inputs
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
        yaxes_list.append('{},{},{}'.format(
            yaxis_type['name'], yaxis_type['minimum'], yaxis_type['maximum']))
    # Join the list of CSV sets with ';'
    return yaxes_list


def is_rgb_color(color_hex):
    """
    Check if string is a hex color value for the web UI
    :param color_hex: string to check if it represents a hex color value
    :return: bool
    """
    return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))


def custom_colors_graph(form, error):
    """
    Get variable number of graph color inputs, turn into CSV string
    :param form: form object submitted by user on web page
    :param error: list of accumulated errors to add to
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
    return short_list, error


def dict_custom_colors(widget_options):
    """
    Generate a dictionary of custom colors from CSV strings saved in the
    database. If custom colors aren't already saved, fill in with a default
    palette.

    :return: dictionary of graph_ids and lists of custom colors
    """
    color_count = []
    if flask_login.current_user.theme in THEMES_DARK:
        default_palette = [
            '#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066',
            '#eeaaee', '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'
        ]
    else:
        default_palette = [
            '#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9', '#f15c80',
            '#e4d354', '#2b908f', '#f45b5b', '#91e8e1'
        ]

    try:
        # Get current saved colors
        if widget_options['custom_colors']:  # Split into list
            colors = widget_options['custom_colors']
        else:  # Create empty list
            colors = []
        # Fill end of list with empty strings
        while len(colors) < len(default_palette):
            colors.append('')

        # Populate empty strings with default colors
        for x, _ in enumerate(default_palette):
            if colors[x] == '':
                colors[x] = default_palette[x]

        index_sum = 0
        total = []

        if widget_options['measurements_output']:
            index = 0
            for each_set in widget_options['measurements_output']:
                if not each_set:
                    continue

                output_unique_id = each_set.split(',')[0]
                output_measure_id = each_set.split(',')[1]

                device_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == output_measure_id).first()
                if device_measurement:
                    measurement_name = device_measurement.name
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == device_measurement.conversion_id).first()
                else:
                    measurement_name = None
                    conversion = None
                channel, unit, measurement = return_measurement_info(
                    device_measurement, conversion)

                output = Output.query.filter_by(unique_id=output_unique_id).first()

                if (index < len(widget_options['measurements_output']) and
                        len(colors) > index_sum + index):
                    color = colors[index_sum + index]
                else:
                    color = '#FF00AA'

                # Data grouping
                disable_data_grouping = False
                if 'disable_data_grouping' in widget_options and output_measure_id in widget_options['disable_data_grouping']:
                    disable_data_grouping = True

                # Series type
                series_type = 'column'
                if 'series_type' in widget_options and output_measure_id in widget_options['series_type']:
                    series_type = widget_options['series_type'][output_measure_id]

                if None not in [output, device_measurement]:
                    total.append({
                        'unique_id': output_unique_id,
                        'measure_id': output_measure_id,
                        'type': 'Output',
                        'name': output.name,
                        'channel': channel,
                        'unit': unit,
                        'measure': measurement,
                        'measure_name': measurement_name,
                        'color': color,
                        'disable_data_grouping': disable_data_grouping,
                        'series_type': series_type
                    })
                    index += 1
            index_sum += index

        if widget_options['measurements_input']:
            index = 0
            for each_set in widget_options['measurements_input']:
                if not each_set:
                    continue

                input_unique_id = each_set.split(',')[0]
                input_measure_id = each_set.split(',')[1]

                device_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == input_measure_id).first()
                if device_measurement:
                    measurement_name = device_measurement.name
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == device_measurement.conversion_id).first()
                else:
                    measurement_name = None
                    conversion = None
                channel, unit, measurement = return_measurement_info(
                    device_measurement, conversion)

                input_dev = Input.query.filter_by(unique_id=input_unique_id).first()

                # Custom colors
                if (index < len(widget_options['measurements_input']) and
                        len(colors) > index_sum + index):
                    color = colors[index_sum + index]
                else:
                    color = '#FF00AA'

                # Data grouping
                disable_data_grouping = False
                if 'disable_data_grouping' in widget_options and input_measure_id in widget_options['disable_data_grouping']:
                    disable_data_grouping = True

                # Series type
                series_type = 'line'
                if 'series_type' in widget_options and input_measure_id in widget_options['series_type']:
                    series_type = widget_options['series_type'][input_measure_id]

                if None not in [input_dev, device_measurement]:
                    total.append({
                        'unique_id': input_unique_id,
                        'measure_id': input_measure_id,
                        'type': 'Input',
                        'name': input_dev.name,
                        'channel': channel,
                        'unit': unit,
                        'measure': measurement,
                        'measure_name': measurement_name,
                        'color': color,
                        'disable_data_grouping': disable_data_grouping,
                        'series_type': series_type
                    })
                    index += 1
            index_sum += index

        if widget_options['measurements_function']:
            index = 0
            for each_set in widget_options['measurements_function']:
                if not each_set:
                    continue

                function_unique_id = each_set.split(',')[0]
                function_measure_id = each_set.split(',')[1]

                device_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == function_measure_id).first()
                if device_measurement:
                    measurement_name = device_measurement.name
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == device_measurement.conversion_id).first()
                else:
                    measurement_name = None
                    conversion = None
                channel, unit, measurement = return_measurement_info(
                    device_measurement, conversion)

                function = CustomController.query.filter_by(unique_id=function_unique_id).first()

                # Custom colors
                if (index < len(widget_options['measurements_function']) and
                        len(colors) > index_sum + index):
                    color = colors[index_sum + index]
                else:
                    color = '#FF00AA'

                # Data grouping
                disable_data_grouping = False
                if 'disable_data_grouping' in widget_options and function_measure_id in widget_options['disable_data_grouping']:
                    disable_data_grouping = True

                # Series type
                series_type = 'line'
                if 'series_type' in widget_options and function_measure_id in widget_options['series_type']:
                    series_type = widget_options['series_type'][function_measure_id]

                if function is not None:
                    total.append({
                        'unique_id': function_unique_id,
                        'measure_id': function_measure_id,
                        'type': 'Function',
                        'name': function.name,
                        'channel': channel,
                        'unit': unit,
                        'measure': measurement,
                        'measure_name': measurement_name,
                        'color': color,
                        'disable_data_grouping': disable_data_grouping,
                        'series_type': series_type
                    })
                    index += 1
            index_sum += index

        if widget_options['measurements_pid']:
            index = 0
            for each_set in widget_options['measurements_pid']:
                if not each_set:
                    continue

                pid_unique_id = each_set.split(',')[0]
                pid_measure_id = each_set.split(',')[1]

                device_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == pid_measure_id).first()
                if device_measurement:
                    measurement_name = device_measurement.name
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == device_measurement.conversion_id).first()
                else:
                    measurement_name = None
                    conversion = None
                channel, unit, measurement = return_measurement_info(
                    device_measurement, conversion)

                pid = PID.query.filter_by(unique_id=pid_unique_id).first()

                # Custom colors
                if (index < len(widget_options['measurements_pid']) and
                        len(colors) > index_sum + index):
                    color = colors[index_sum + index]
                else:
                    color = '#FF00AA'

                # Data grouping
                disable_data_grouping = False
                if 'disable_data_grouping' in widget_options and pid_measure_id in widget_options['disable_data_grouping']:
                    disable_data_grouping = True

                # Series type
                series_type = 'line'
                if 'series_type' in widget_options and pid_measure_id in widget_options['series_type']:
                    series_type = widget_options['series_type'][pid_measure_id]

                if None not in [pid, device_measurement]:
                    total.append({
                        'unique_id': pid_unique_id,
                        'measure_id': pid_measure_id,
                        'type': 'PID',
                        'name': pid.name,
                        'channel': channel,
                        'unit': unit,
                        'measure': measurement,
                        'measure_name': measurement_name,
                        'color': color,
                        'disable_data_grouping': disable_data_grouping,
                        'series_type': series_type
                    })
                    index += 1
            index_sum += index

        if widget_options['measurements_note_tag']:
            index = 0
            for each_set in widget_options['measurements_note_tag']:
                if not each_set:
                    continue

                tag_unique_id = each_set.split(',')[0]

                device_measurement = NoteTags.query.filter_by(unique_id=tag_unique_id).first()

                if (index < len(widget_options['measurements_note_tag']) and
                        len(colors) > index_sum + index):
                    color = colors[index_sum + index]
                else:
                    color = '#FF00AA'
                if device_measurement is not None:
                    total.append({
                        'unique_id': tag_unique_id,
                        'measure_id': None,
                        'type': 'Tag',
                        'name': device_measurement.name,
                        'channel': None,
                        'unit': None,
                        'measure': None,
                        'measure_name': None,
                        'color': color,
                        'disable_data_grouping': None,
                        'series_type': None
                    })
                    index += 1
            index_sum += index

        color_count += total
    except IndexError:
        logger.exception("Index")
    except Exception:
        logger.exception("Exception")

    return color_count


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
    Generate a list of y-axes for Synchronous and Asynchronous Graphs
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


def graph_y_axes(dict_measurements, widget_options):
    """Determine which y-axes to use for each Graph."""
    y_axes = []

    function = CustomController.query.all()
    device_measurements = DeviceMeasurements.query.all()
    input_dev = Input.query.all()
    output = Output.query.all()
    pid = PID.query.all()

    devices_list = [input_dev, function, output, pid]

    # Iterate through device tables
    for each_device in devices_list:

        if each_device == output and widget_options['measurements_output']:
            dev_and_measure_ids = widget_options['measurements_output']
        elif each_device == input_dev and widget_options['measurements_input']:
            dev_and_measure_ids = widget_options['measurements_input']
        elif each_device == function and widget_options['measurements_function']:
            dev_and_measure_ids = widget_options['measurements_function']
        elif each_device == pid and widget_options['measurements_pid']:
            dev_and_measure_ids = widget_options['measurements_pid']
        else:
            dev_and_measure_ids = []

        # Iterate through each set of ID and measurement of the
        # dashboard element
        for each_id_measure in dev_and_measure_ids:

            if ',' in each_id_measure:

                measure_id = each_id_measure.split(',')[1]

                for each_measurement in device_measurements:
                    if each_measurement.unique_id == measure_id:

                        unit = None
                        if each_measurement.measurement_type == 'setpoint':
                            setpoint_pid = PID.query.filter(PID.unique_id == each_measurement.device_id).first()
                            if setpoint_pid and ',' in setpoint_pid.measurement:
                                pid_measurement = setpoint_pid.measurement.split(',')[1]
                                setpoint_measurement = DeviceMeasurements.query.filter(
                                    DeviceMeasurements.unique_id == pid_measurement).first()
                                if setpoint_measurement:
                                    conversion = Conversion.query.filter(
                                        Conversion.unique_id == setpoint_measurement.conversion_id).first()
                                    _, unit, measurement = return_measurement_info(setpoint_measurement, conversion)
                        else:
                            conversion = Conversion.query.filter(
                                Conversion.unique_id == each_measurement.conversion_id).first()
                            _, unit, _ = return_measurement_info(each_measurement, conversion)

                        if unit:
                            if not y_axes:
                                y_axes = [unit]
                            elif y_axes and unit not in y_axes:
                                y_axes.append(unit)

            elif len(each_id_measure.split(',')) == 4:

                unit = each_id_measure.split(',')[2]

                if not y_axes:
                    y_axes = [unit]
                elif y_axes and unit not in y_axes:
                    y_axes.append(unit)

            elif len(each_id_measure.split(',')) == 2:

                unique_id = each_id_measure.split(',')[0]
                measurement = each_id_measure.split(',')[1]

                y_axes = check_func(
                    each_device,
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

                y_axes = check_func(
                    each_device,
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


def dict_custom_yaxes_min_max(yaxes, widget_options):
    """Generate a dictionary of the y-axis minimum and maximum for each graph."""
    dict_yaxes = {}

    for each_yaxis in yaxes:
        dict_yaxes[each_yaxis] = {}
        dict_yaxes[each_yaxis]['minimum'] = 0
        dict_yaxes[each_yaxis]['maximum'] = 0

        for each_custom_yaxis in widget_options['custom_yaxes']:
            if each_custom_yaxis.split(',')[0] == each_yaxis:
                dict_yaxes[each_yaxis]['minimum'] = each_custom_yaxis.split(',')[1]
                dict_yaxes[each_yaxis]['maximum'] = each_custom_yaxis.split(',')[2]

    return dict_yaxes

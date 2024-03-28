# coding=utf-8
#
#  widget_gauge_angular.py - Angular Gauge dashboard widget
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
import json
import logging
import re

from flask import flash
from flask_babel import lazy_gettext

from mycodo.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)


def execute_at_creation(error, new_widget, dict_widget):
    color_list = ["#33CCFF", "#55BF3B", "#DDDF0D", "#DF5353"]
    custom_options_json = json.loads(new_widget.custom_options)
    custom_options_json['range_colors'] = []

    if custom_options_json['stops'] < 2:
        custom_options_json['stops'] = 2

    stop = custom_options_json['min']
    maximum = custom_options_json['max']
    difference = int(maximum - stop)
    stop_size = int(difference / custom_options_json['stops'])
    custom_options_json['range_colors'].append(
        '{low},{high},{color}'.format(low=stop, high=stop + stop_size, color=color_list[0]))
    for i in range(custom_options_json['stops'] - 1):
        stop += stop_size
        if i + 1 < len(color_list):
            color = color_list[i + 1]
        else:
            color = "#DF5353"
        custom_options_json['range_colors'].append(
            '{low},{high},{color}'.format(low=stop, high=stop + stop_size, color=color))

    new_widget.custom_options = json.dumps(custom_options_json)
    return error, new_widget


def execute_at_modification(
        mod_widget,
        request_form,
        custom_options_json_presave,
        custom_options_json_postsave):
    allow_saving = True
    page_refresh = True
    error = []

    sorted_colors, error = custom_colors_gauge(request_form, error)
    sorted_colors = gauge_reformat_stops(
        custom_options_json_presave['stops'],
        custom_options_json_postsave['stops'],
        current_colors=sorted_colors)

    custom_options_json_postsave['range_colors'] = sorted_colors
    return allow_saving, page_refresh, mod_widget, custom_options_json_postsave


def generate_page_variables(widget_unique_id, widget_options):
    # Retrieve custom colors for gauges
    colors_gauge_angular = []
    try:
        if 'range_colors' in widget_options and widget_options['range_colors']:  # Split into list
            color_areas = widget_options['range_colors']
        else:
            color_areas = []  # Create empty list
        for each_range in color_areas:
            colors_gauge_angular.append({
                'low': each_range.split(',')[0],
                'high': each_range.split(',')[1],
                'hex': each_range.split(',')[2]})
    except IndexError:
        logger.exception(1)
        flash("Colors Index Error", "error")

    return {"colors_gauge_angular": colors_gauge_angular}


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_gauge_angular',
    'widget_name': 'Gauge (Angular) [Highcharts]',
    'widget_library': 'Highcharts',
    'no_class': True,

    'message': 'Displays an angular gauge. Be sure to set the Maximum option to the last Stop High value for the gauge to display properly.',

    'dependencies_module': [
        ('bash-commands',
        [
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more-9.1.2.js'
        ],
        [
            'rm -rf Highcharts-Stock-9.1.2.zip',
            'wget https://code.highcharts.com/zips/Highcharts-Stock-9.1.2.zip 2>&1',
            'unzip Highcharts-Stock-9.1.2.zip -d Highcharts-Stock-9.1.2',
            'cp -rf Highcharts-Stock-9.1.2/code/highstock.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/highstock.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/highcharts-more.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/highcharts-more.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more.js.map',
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

    'widget_width': 4,
    'widget_height': 8,

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'PID'
            ],
            'name': lazy_gettext('Measurement'),
            'phrase': lazy_gettext('Select a measurement to display')
        },
        {
            'id': 'max_measure_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Max Age'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The maximum age of the measurement to use')
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 30.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': '{} ({})'.format(lazy_gettext("Refresh"), lazy_gettext("Seconds")),
            'phrase': 'The period of time between refreshing the widget'
        },
        {
            'id': 'decimal_places',
            'type': 'integer',
            'default_value': 1,
            'name': 'Decimal Places',
            'phrase': 'The number of digits to display after the decimal'
        },
        {
            'id': 'min',
            'type': 'float',
            'default_value': 0,
            'name': 'Minimum',
            'phrase': 'The gauge minimum'
        },
        {
            'id': 'max',
            'type': 'float',
            'default_value': 100,
            'name': 'Maximum',
            'phrase': 'The gauge maximum'
        },
        {
            'id': 'stops',
            'type': 'integer',
            'default_value': 4,
            'name': 'Stops',
            'phrase': 'The number of color stops'
        }
    ],

    'widget_dashboard_head': """{% if "highstock" not in dashboard_dict %}
  <script src="/static/js/user_js/highstock-9.1.2.js"></script>
  {% set _dummy = dashboard_dict.update({"highstock": 1}) %}
{% endif %}
<script src="/static/js/user_js/highcharts-more-9.1.2.js"></script>

{% if current_user.theme in dark_themes %}
  <script type="text/javascript" src="/static/js/dark-unica-custom.js"></script>
{% endif %}
""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    'widget_dashboard_body': """<div class="not-draggable" id="container-gauge-{{each_widget.unique_id}}" style="position: absolute; left: 0; top: 0; bottom: 0; right: 0; overflow: hidden;"></div>""",

    'widget_dashboard_configure_options': """
            {% for n in range(widget_variables['colors_gauge_angular']|length) %}
              {% set index = '{0:0>2}'.format(n) %}
        <div class="form-row">
          <div class="col-auto">
            <label class="control-label" for="color_low_number{{index}}">[{{n}}] Low</label>
            <div>
              <input class="form-control" id="color_low_number{{index}}" name="color_low_number{{index}}" type="text" value="{{widget_variables['colors_gauge_angular'][n]['low']}}">
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label" for="color_high_number{{index}}">[{{n}}] High</label>
            <div>
              <input class="form-control" id="color_high_number{{index}}" name="color_high_number{{index}}" type="text" value="{{widget_variables['colors_gauge_angular'][n]['high']}}">
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label" for="color_hex_number{{index}}">[{{n}}] Color</label>
            <div>
              <input id="color_hex_number{{index}}" name="color_hex_number{{index}}" placeholder="#000000" type="color" value="{{widget_variables['colors_gauge_angular'][n]['hex']}}">
            </div>
          </div>
        </div>
            {% endfor %}
""",

    'widget_dashboard_js': """
  function getLastDataGaugeAngular(widget_id,
                       unique_id,
                       measure_type,
                       measurement_id,
                       max_measure_age_sec) {
    const url = '/last/' + unique_id + '/' + measure_type + '/' + measurement_id + '/' + max_measure_age_sec.toString();
    $.ajax(url, {
      success: function(data, responseText, jqXHR) {
        if (jqXHR.status === 204) {
          widget[widget_id].series[0].points[0].update(null);
        }
        else {
          const formattedTime = epoch_to_timestamp(data[0] * 1000);
          const measurement = data[1];
          widget[widget_id].series[0].points[0].update(measurement);
          //document.getElementById('timestamp-' + widget_id).innerHTML = formattedTime;
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        widget[widget_id].series[0].points[0].update(null);
      }
    });
  }

  // Repeat function for getLastDataGaugeAngular()
  function repeatLastDataGaugeAngular(widget_id,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec) {
    setInterval(function () {
      getLastDataGaugeAngular(widget_id,
                  dev_id,
                  measure_type,
                  measurement_id,
                  max_measure_age_sec)
    }, period_sec * 1000);
  }
""",

    'widget_dashboard_js_ready': """<!-- No JS ready content -->""",

    'widget_dashboard_js_ready_end': """
{%- set device_id = widget_options['measurement'].split(",")[0] -%}
{%- set measurement_id = widget_options['measurement'].split(",")[1] -%}

{% set measure = { 'measurement_id': None } %}
  widget['{{each_widget.unique_id}}'] = new Highcharts.chart({
    chart: {
      renderTo: 'container-gauge-{{each_widget.unique_id}}',
      type: 'gauge',
      plotBackgroundColor: null,
      plotBackgroundImage: null,
      plotBorderWidth: 0,
      plotShadow: false,
      events: {
        load: function () {
          {% for each_input in input  if each_input.unique_id == device_id %}
          getLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'input', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'input', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}
          
          {% for each_function in function if each_function.unique_id == device_id %}
          getLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'function', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'function', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}

          {%- for each_pid in pid if each_pid.unique_id == device_id %}
          getLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'pid', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'pid', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}
        }
      },
      spacingTop: 0,
      spacingLeft: 0,
      spacingRight: 0,
      spacingBottom: 0
    },

    title: null,

    exporting: {
      enabled: false
    },

    pane: {
        startAngle: -150,
        endAngle: 150,
        background: [{
            backgroundColor: '#c1c1c1',
            borderWidth: 0,
            outerRadius: '105%',
            innerRadius: '103%'
        }]
    },

    // the value axis
    yAxis: {
        min: {{widget_options['min']}},
        max: {{widget_options['max']}},
        title: {
      {%- if measurement_id in dict_measure_units and
             dict_measure_units[measurement_id] in dict_units and
             dict_units[dict_measure_units[measurement_id]]['unit'] -%}
          text: '{{dict_units[dict_measure_units[measurement_id]]['unit']}}',
      {% else %}
          text: '',
      {%- endif -%}
          y: 20
        },

        minColor: "#3e3f46",
        maxColor: "#3e3f46",

        minorTickInterval: 'auto',
        minorTickWidth: 1,
        minorTickLength: 10,
        minorTickPosition: 'inside',
        minorTickColor: '#666',

        tickPixelInterval: 30,
        tickWidth: 2,
        tickPosition: 'inside',
        tickLength: 10,
        tickColor: '#666',
        labels: {
            step: 2,
            rotation: 'auto'
        },
        plotBands: [
          {% for n in range(widget_variables['colors_gauge_angular']|length) %}
            {% set index = '{0:0>2}'.format(n) %}
        {
            from: {{widget_variables['colors_gauge_angular'][n]['low']}},
            to: {{widget_variables['colors_gauge_angular'][n]['high']}},
            color: '{{widget_variables['colors_gauge_angular'][n]['hex']}}'
        },
          {% endfor %}
        ]
    },

    series: [{
        name: '
        {%- for each_input in input if each_input.unique_id == device_id -%}
          {%- if measurement_id in device_measurements_dict -%}
          {{each_input.name}} (
            {%- if not device_measurements_dict[measurement_id].single_channel -%}
              {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
            {%- endif -%}
            {%- if device_measurements_dict[measurement_id].measurement -%}
          {{', ' + dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
            {%- endif -%}
          {%- endif -%}
        {%- endfor -%}
        
        {%- for each_function in function if each_function.unique_id == device_id -%}
          {{each_function.measure|safe}}
        {%- endfor -%}

        {%- for each_pid in pid if each_pid.unique_id == device_id -%}
          {{each_pid.measure|safe}}
        {%- endfor -%})',
        data: [null],
        dataLabels: {
          style: {"fontSize": "14px"},
          format: '{point.y:,.{{widget_options['decimal_places']}}f}'
        },
        yAxis: 0,
          dial: {
            backgroundColor: '{% if current_user.theme in dark_themes %}#e3e4f4{% else %}#3e3f46{% endif %}',
            baseWidth: 5
        },
        tooltip: {

        {%- for each_input in input if each_input.unique_id == device_id %}
             pointFormatter: function () {
              return this.series.name + ':<b> ' + Highcharts.numberFormat(this.y, 2) + ' {{dict_units[device_measurements_dict[measurement_id].unit]['unit']}}</b><br>';
            },
        {%- endfor -%}

            valueSuffix: '
        {%- for each_input in input if each_input.unique_id == device_id -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
        {%- endfor -%}
        
        {%- for each_function in function if each_function.unique_id == device_id -%}
          {{' ' + each_function.measure_units|safe}}
        {%- endfor -%}

        {%- for each_pid in pid if each_pid.unique_id == device_id -%}
          {{' ' + each_pid.measure_units|safe}}
        {%- endfor -%}'
        }
    }],

    credits: {
      enabled: false,
      href: "https://github.com/kizniche/Mycodo",
      text: "Mycodo"
    }
  });
"""
}

def is_rgb_color(color_hex):
    """
    Check if string is a hex color value for the web UI
    :param color_hex: string to check if it represents a hex color value
    :return: bool
    """
    return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))


def custom_colors_gauge(form, error):
    sorted_colors = []
    colors_hex = {}
    # Combine all color form inputs to dictionary
    for key in form.keys():
        if ('color_hex_number' in key or
                'color_low_number' in key or
                'color_high_number' in key):
            if 'color_hex_number' in key and int(key[16:]) not in colors_hex:
                colors_hex[int(key[16:])] = {}
            if 'color_low_number' in key and int(key[16:]) not in colors_hex:
                colors_hex[int(key[16:])] = {}
            if 'color_high_number' in key and int(key[17:]) not in colors_hex:
                colors_hex[int(key[17:])] = {}
        if 'color_hex_number' in key:
            for value in form.getlist(key):
                if not is_rgb_color(value):
                    error.append('Invalid hex color value')
                colors_hex[int(key[16:])]['hex'] = value
        elif 'color_low_number' in key:
            for value in form.getlist(key):
                if not is_rgb_color(value):
                    error.append("Invalid hex color value")
                colors_hex[int(key[16:])]['low'] = value
        elif 'color_high_number' in key:
            for value in form.getlist(key):
                if not is_rgb_color(value):
                    error.append("Invalid hex color value")
                colors_hex[int(key[17:])]['high'] = value

    # Build string of colors and associated gauge values
    for i, _ in enumerate(colors_hex):
        try:
            sorted_colors.append("{},{},{}".format(
                colors_hex[i]['low'],
                colors_hex[i]['high'],
                colors_hex[i]['hex']))
        except Exception as err_msg:
            logger.exception(1)
            error.append(err_msg)
    return sorted_colors, error


def gauge_reformat_stops(current_stops, new_stops, current_colors=None):
    """Generate stops and colors for new and modified gauges."""
    if current_colors:
        colors = current_colors
    else:  # Default colors (adding new gauge)
        colors = ['0,20,#33CCFF', '20,40,#55BF3B', '40,60,#DDDF0D', '60,80,#DF5353']

    if new_stops > current_stops:
        try:
            stop = float(colors[-1].split(",")[1])
        except:
            stop = 80
        for _ in range(new_stops - current_stops):
            stop += 20
            colors.append('{low},{high},#DF5353'.format(low=stop - 20, high=stop))
    elif new_stops < current_stops:
        colors = colors[:len(colors) - (current_stops - new_stops)]

    return colors

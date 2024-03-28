# coding=utf-8
#
#  widget_gauge_solid.py - Solid Gauge dashboard widget
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

    difference = int(custom_options_json['max'] - custom_options_json['min'])
    stop_size = int(difference / custom_options_json['stops'])
    stop = custom_options_json['min'] + stop_size
    custom_options_json['range_colors'].append('{stop},{color}'.format(stop=stop, color=color_list[0]))
    for i in range(custom_options_json['stops'] - 1):
        stop += stop_size
        if i + 1 < len(color_list):
            color = color_list[i + 1]
        else:
            color = "#DF5353"
        custom_options_json['range_colors'].append('{stop},{color}'.format(stop=stop, color=color))

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
    colors_gauge_solid = []
    colors_gauge_solid_form = []
    try:
        if 'range_colors' in widget_options and widget_options['range_colors']:
            color_areas = widget_options['range_colors']
        else:  # Create empty list
            color_areas = []

        try:
            gauge_low = widget_options['min']
            gauge_high = widget_options['max']
            gauge_difference = gauge_high - gauge_low
            for each_range in color_areas:
                percent_of_range = float((float(each_range.split(',')[0]) - gauge_low) / gauge_difference)
                colors_gauge_solid.append({
                    'stop': '{:.2f}'.format(percent_of_range),
                    'hex': each_range.split(',')[1]})
                colors_gauge_solid_form.append({
                    'stop': each_range.split(',')[0],
                    'hex': each_range.split(',')[1]})
        except:
            # Prevent mathematical errors from preventing proper page render
            for each_range in color_areas:
                colors_gauge_solid.append({
                    'stop': '0',
                    'hex': each_range.split(',')[1]})
                colors_gauge_solid_form.append({
                    'stop': '0',
                    'hex': each_range.split(',')[1]})
    except IndexError:
        logger.exception(1)
        flash("Colors Index Error", "error")

    dict_return = {
        "colors_gauge_solid": colors_gauge_solid,
        "colors_gauge_solid_form": colors_gauge_solid_form,
    }
    return dict_return


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_gauge_solid',
    'widget_name': 'Gauge (Solid) [Highcharts]',
    'widget_library': 'Highcharts',
    'no_class': True,

    'message': 'Displays a solid gauge. Be sure to set the Maximum option to the last Stop value for the gauge to display properly.',

    'dependencies_module': [
        ('bash-commands',
        [
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more-9.1.2.js',
            '/opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/solid-gauge-9.1.2.js'
        ],
        [
            'rm -rf Highcharts-Stock-9.1.2.zip',
            'wget https://code.highcharts.com/zips/Highcharts-Stock-9.1.2.zip 2>&1',
            'unzip Highcharts-Stock-9.1.2.zip -d Highcharts-Stock-9.1.2',
            'cp -rf Highcharts-Stock-9.1.2/code/highstock.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/highstock.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highstock.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/highcharts-more.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/highcharts-more.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/highcharts-more.js.map',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/solid-gauge.js /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/solid-gauge-9.1.2.js',
            'cp -rf Highcharts-Stock-9.1.2/code/modules/solid-gauge.js.map /opt/Mycodo/mycodo/mycodo_flask/static/js/user_js/solid-gauge.js.map',
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
<script src="/static/js/user_js/solid-gauge-9.1.2.js"></script>

{% if current_user.theme in dark_themes %}
  <script type="text/javascript" src="/static/js/dark-unica-custom.js"></script>
{% endif %}
""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    'widget_dashboard_body': """<div class="not-draggable" id="container-gauge-{{each_widget.unique_id}}" style="position: absolute; left: 0; top: 0; bottom: 0; right: 0; overflow: hidden;"></div>""",

    'widget_dashboard_configure_options': """
            {% for n in range(widget_variables['colors_gauge_solid_form']|length) %}
              {% set index = '{0:0>2}'.format(n) %}
        <div class="form-row">
          <div class="col-auto">
            <label class="control-label" for="color_stop_number{{index}}">[{{n}}] Stop</label>
            <div>
              <input class="form-control" id="color_stop_number{{index}}" name="color_stop_number{{index}}" type="text" value="{{widget_variables['colors_gauge_solid_form'][n]['stop']}}">
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label" for="color_hex_number{{index}}">[{{n}}] Color</label>
            <div>
              <input id="color_hex_number{{index}}" name="color_hex_number{{index}}" placeholder="#000000" type="color" value="{{widget_variables['colors_gauge_solid_form'][n]['hex']}}">
            </div>
          </div>
        </div>
            {% endfor %}
""",

    'widget_dashboard_js': """
  function getLastDataGaugeSolid(widget_id,
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

  // Repeat function for getLastDataGaugeSolid()
  function repeatLastDataGaugeSolid(widget_id,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec) {
    setInterval(function () {
      getLastDataGaugeSolid(widget_id,
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

  widget['{{each_widget.unique_id}}'] = new Highcharts.chart({
    chart: {
      renderTo: 'container-gauge-{{each_widget.unique_id}}',
      type: 'solidgauge',
      events: {
        load: function () {
          {% for each_input in input if each_input.unique_id == device_id %}
          getLastDataGaugeSolid('{{each_widget.unique_id}}', '{{device_id}}', 'input', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeSolid('{{each_widget.unique_id}}', '{{device_id}}', 'input', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}
          
          {% for each_function in function if each_function.unique_id == device_id %}
          getLastDataGaugeSolid('{{each_widget.unique_id}}', '{{device_id}}', 'function', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeSolid('{{each_widget.unique_id}}', '{{device_id}}', 'function', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}

          {%- for each_pid in pid  if each_pid.unique_id == device_id %}
          getLastDataGaugeSolid('{{each_widget.unique_id}}', '{{device_id}}', 'pid', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeSolid('{{each_widget.unique_id}}', '{{device_id}}', 'pid', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}
        }
      },
      spacingTop: 0,
      spacingLeft: 0,
      spacingRight: 0,
      spacingBottom: 0
    },

    title: null,

    pane: {
      center: ['50%', '85%'],
      size: '140%',
      startAngle: -90,
      endAngle: 90,
      background: {
        backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
        innerRadius: '60%',
        outerRadius: '100%',
        shape: 'arc'
      }
    },

    exporting: {
      enabled: false
    },
    rangeSelector: {
        enabled: false
    },

    // the value axis
    yAxis: {
      min: {{widget_options['min']}},
      max: {{widget_options['max']}},
      stops: [
          {% for n in range(widget_variables['colors_gauge_solid']|length) %}
              {% set index = '{0:0>2}'.format(n) %}
        [{{widget_variables['colors_gauge_solid'][n]['stop']}}, '{{widget_variables['colors_gauge_solid'][n]['hex']}}'],
          {% endfor %}
      ],
      lineWidth: 0,
      minorTickInterval: null,
      tickAmount: 2,
      title: {
      {%- if dict_measure_units[measurement_id] in dict_units and
             dict_units[dict_measure_units[measurement_id]]['unit'] -%}
          text: '{{dict_units[dict_measure_units[measurement_id]]['unit']}}',
      {% else %}
          text: '',
      {%- endif -%}
        y: -80
      },
      labels: {
        y: 16
      }
    },

    plotOptions: {
      solidgauge: {
        dataLabels: {
          y: 5,
          borderWidth: 0,
          useHTML: true
        }
      }
    },

    series: [{
      name: '
        {%- for each_input in input if each_input.unique_id == device_id and measurement_id in device_measurements_dict -%}
          {{each_input.name}} (
            {%- if not device_measurements_dict[measurement_id].single_channel -%}
              {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
            {%- endif -%}
            {%- if device_measurements_dict[measurement_id].measurement -%}
          {{', ' + dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
            {%- endif -%}
        {%- endfor -%}
        
        {%- for each_function in function if each_function.unique_id == device_id and measurement_id in device_measurements_dict -%}
          {{each_function.name}} (
            {%- if not device_measurements_dict[measurement_id].single_channel -%}
              {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
            {%- endif -%}
            {%- if device_measurements_dict[measurement_id].measurement -%}
          {{', ' + dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
            {%- endif -%}
        {%- endfor -%}

        {%- for each_pid in pid if each_pid.unique_id == device_id and measurement_id in device_measurements_dict -%}
          {{each_pid.name}} (
            {%- if not device_measurements_dict[measurement_id].single_channel -%}
              {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
            {%- endif -%}
            {%- if device_measurements_dict[measurement_id].measurement -%}
          {{', ' + dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
            {%- endif -%}
        {%- endfor -%})',
      data: [null],
      dataLabels: {
        format: '<div style="text-align:center"><span style="font-size:25px;color:' +
          ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{point.y:,.{{widget_options['decimal_places']}}f}</span><br/>' +
           '<span style="font-size:12px;color:silver">{{measure_unit}}</span></div>'
      },
      tooltip: {

        {%- for each_input in input if each_input.unique_id == device_id %}
        pointFormatter: function () {
            return this.series.name + ':<b> ' + Highcharts.numberFormat(this.y, 2) + ' {{dict_units[device_measurements_dict[measurement_id].unit]['unit']}}</b><br>';
        },
        {%- endfor -%}
        
        {%- for each_function in function if each_function.unique_id == device_id %}
        pointFormatter: function () {
            return this.series.name + '</span>:<b> ' + Highcharts.numberFormat(this.y, 2) + ' {{dict_units[device_measurements_dict[measurement_id].unit]['unit']}}</b><br>';
        },
        {%- endfor -%}

        valueSuffix: '
        {%- for each_input in input if each_input.unique_id == device_id -%}
            {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
        {%- endfor -%}

        {%- for each_function in function if each_function.unique_id == device_id -%}
            {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
        {%- endfor -%}

        {%- for each_pid in pid if each_pid.unique_id == device_id -%}
            {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
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
    """Get variable number of gauge color inputs, turn into CSV string."""
    sorted_colors = []
    colors_hex = {}
    # Combine all color form inputs to dictionary
    for key in form.keys():
        if 'color_hex_number' in key or 'color_stop_number' in key:
            if 'color_hex_number' in key and int(key[16:]) not in colors_hex:
                colors_hex[int(key[16:])] = {}
            if 'color_stop_number' in key and int(key[17:]) not in colors_hex:
                colors_hex[int(key[17:])] = {}
        if 'color_hex_number' in key:
            for value in form.getlist(key):
                if not is_rgb_color(value):
                    error.append("Invalid hex color value")
                colors_hex[int(key[16:])]['hex'] = value
        elif 'color_stop_number' in key:
            for value in form.getlist(key):
                if not is_rgb_color(value):
                    error.append("Invalid hex color value")
                colors_hex[int(key[17:])]['stop'] = value

    # Build string of colors and associated gauge values
    for i, _ in enumerate(colors_hex):
        try:
            try:
                sorted_colors.append("{},{}".format(colors_hex[i]['stop'], colors_hex[i]['hex']))
            except Exception as err_msg:
                error.append(err_msg)
                sorted_colors.append("0,{}".format(colors_hex[i]['hex']))
        except Exception as err_msg:
            error.append(err_msg)
    return sorted_colors, error


def gauge_reformat_stops(current_stops, new_stops, current_colors=None):
    """Generate stops and colors for new and modified gauges."""
    if current_colors:
        colors = current_colors
    else:  # Default colors (adding new gauge)
        colors = ['20,#33CCFF', '40,#55BF3B', '60,#DDDF0D', '80,#DF5353']

    if new_stops > current_stops:
        try:
            stop = float(colors[-1].split(",")[0])
        except:
            stop = 80
        for _ in range(new_stops - current_stops):
            stop += 20
            colors.append('{},#DF5353'.format(stop))
    elif new_stops < current_stops:
        colors = colors[: len(colors) - (current_stops - new_stops)]

    return colors

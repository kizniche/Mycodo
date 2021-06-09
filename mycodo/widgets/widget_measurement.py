# coding=utf-8
#
#  widget_measurement.py - Measurement dashboard widget
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
import logging

from flask_babel import lazy_gettext

from mycodo.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_measurement',
    'widget_name': 'Measurement',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays a measurement value and timestamp.',

    'widget_width': 4,
    'widget_height': 5,

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function',
                'Output_Channels_Measurements',
                'PID'
            ],
            'name': lazy_gettext('Measurement'),
            'phrase': lazy_gettext('Select a measurement to display')
        },
        {
            'id': 'measurement_max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('{} {}'.format(lazy_gettext('Measurement'), lazy_gettext('Max Age'))),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement')
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 30.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Widget Refresh (seconds)',
            'phrase': 'The period of time between refreshing the widget'
        },
        {
            'id': 'font_em_value',
            'type': 'float',
            'default_value': 1.5,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Value Font Size (em)',
            'phrase': 'The font size of the measurement'
        },
        {
            'id': 'font_em_timestamp',
            'type': 'float',
            'default_value': 1.5,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Timestamp Font Size (em)',
            'phrase': 'The font size of the timestamp'
        },
        {
            'id': 'decimal_places',
            'type': 'integer',
            'default_value': 2,
            'name': 'Decimal Places',
            'phrase': 'The number of measurement decimal places'
        },
        {
            'id': 'enable_unit',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Show Unit'),
            'phrase': lazy_gettext('Show the unit')
        },
        {
            'id': 'enable_name',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Show Name'),
            'phrase': lazy_gettext('Show the name')
        },
        {
            'id': 'enable_channel',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Show Channel'),
            'phrase': lazy_gettext('Show the channel')
        },
        {
            'id': 'enable_measurement',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Show Measurement'),
            'phrase': lazy_gettext('Show the measurement')
        },
        {
            'id': 'enable_timestamp',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Show Timestamp'),
            'phrase': lazy_gettext('Show the timestamp')
        }
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    'widget_dashboard_body': """
  {%- set device_id = widget_options['measurement'].split(",")[0] -%}
  {%- set measurement_id = widget_options['measurement'].split(",")[1] -%}
  
  <div style="text-align: center">
  
  {%- for each_input in input if each_input.unique_id == device_id and measurement_id in device_measurements_dict -%}
  
    <span style="font-size: {{widget_options['font_em_value']}}em" id="value-{{chart_number}}"></span>
    <span style="font-size: {{widget_options['font_em_value']}}em">
        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] and
               widget_options['enable_unit'] -%}
          {{' ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}
    </span>
    
        {%- if widget_options['enable_name'] or widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
    <br/><span style="font-size: {{widget_options['font_em_timestamp']}}em">
        {%- endif -%}
    
        {%- if widget_options['enable_name'] -%}
          {{each_input.name + ' '}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{'('}}
        {%- endif -%}
        {%- if not device_measurements_dict[measurement_id].single_channel and widget_options['enable_channel'] -%}
          {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] and widget_options['enable_measurement'] -%}
          {{', '}}
        {%- endif -%}
        {%- if widget_options['enable_measurement'] and device_measurements_dict[measurement_id].measurement -%}
          {{dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{')'}}
        {%- endif -%}
  {%- endfor -%}

  {%- for each_math in math if each_math.unique_id == device_id and measurement_id in device_measurements_dict -%}

  <span style="font-size: {{widget_options['font_em_value']}}em" id="value-{{chart_number}}"></span>
        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] and
               widget_options['enable_unit'] -%}
          {{' ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

        {%- if widget_options['enable_name'] or widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
  <br/><span style="font-size: {{widget_options['font_em_timestamp']}}em">
        {%- endif -%}

        {%- if widget_options['enable_name'] -%}
          {{each_math.name + ' '}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{'('}}
        {%- endif -%}
        {%- if not device_measurements_dict[measurement_id].single_channel and widget_options['enable_channel'] -%}
          {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] and widget_options['enable_measurement'] -%}
          {{', '}}
        {%- endif -%}
        {%- if widget_options['enable_measurement'] and device_measurements_dict[measurement_id].measurement -%}
          {{dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{')'}}
        {%- endif -%}
  {%- endfor -%}
  
  {%- for each_function in function if each_function.unique_id == device_id and measurement_id in device_measurements_dict -%}

  <span style="font-size: {{widget_options['font_em_value']}}em" id="value-{{chart_number}}"></span>
        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] and
               widget_options['enable_unit'] -%}
          {{' ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

        {%- if widget_options['enable_name'] or widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
  <br/><span style="font-size: {{widget_options['font_em_timestamp']}}em">
        {%- endif -%}

        {%- if widget_options['enable_name'] -%}
          {{each_function.name + ' '}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{'('}}
        {%- endif -%}
        {%- if not device_measurements_dict[measurement_id].single_channel and widget_options['enable_channel'] -%}
          {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] and widget_options['enable_measurement'] -%}
          {{', '}}
        {%- endif -%}
        {%- if widget_options['enable_measurement'] and device_measurements_dict[measurement_id].measurement -%}
          {{dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{')'}}
        {%- endif -%}
  {%- endfor -%}

  {%- for each_output in output  if each_output.unique_id == device_id and measurement_id in device_measurements_dict -%}

  <span style="font-size: {{widget_options['font_em_value']}}em" id="value-{{chart_number}}"></span>
        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] and
               widget_options['enable_unit'] -%}
          {{' ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

        {%- if widget_options['enable_name'] or widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
  <br/><span style="font-size: {{widget_options['font_em_timestamp']}}em">
        {%- endif -%}

        {%- if widget_options['enable_name'] -%}
          {{each_output.name + ' '}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{'('}}
        {%- endif -%}
        {%- if not device_measurements_dict[measurement_id].single_channel and widget_options['enable_channel'] -%}
          {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] and widget_options['enable_measurement'] -%}
          {{', '}}
        {%- endif -%}
        {%- if widget_options['enable_measurement'] and device_measurements_dict[measurement_id].measurement -%}
          {{dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{')'}}
        {%- endif -%}
  {%- endfor -%}

  {%- for each_pid in pid  if each_pid.unique_id == device_id and measurement_id in device_measurements_dict -%}

  <span style="font-size: {{widget_options['font_em_value']}}em" id="value-{{chart_number}}"></span>
        {%- if dict_measure_units[measurement_id] in dict_units and
               dict_units[dict_measure_units[measurement_id]]['unit'] and
               widget_options['enable_unit'] -%}
          {{' ' + dict_units[dict_measure_units[measurement_id]]['unit']}}
        {%- endif -%}

        {%- if widget_options['enable_name'] or widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
  <br/><span style="font-size: {{widget_options['font_em_timestamp']}}em">
        {%- endif -%}

        {%- if widget_options['enable_name'] -%}
          {{each_pid.name + ' '}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{'('}}
        {%- endif -%}
        {%- if not device_measurements_dict[measurement_id].single_channel and widget_options['enable_channel'] -%}
          {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] and widget_options['enable_measurement'] -%}
          {{', '}}
        {%- endif -%}
        {%- if widget_options['enable_measurement'] and device_measurements_dict[measurement_id].measurement -%}
          {{dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
        {%- endif -%}
        {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
          {{')'}}
        {%- endif -%}
  {%- endfor -%}

  {%- if widget_options['enable_name'] or widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
    </span>
  {%- endif -%}

  {%- if widget_options['enable_timestamp'] -%}
  <br/><span style="font-size: {{widget_options['font_em_timestamp']}}em" id="timestamp-{{chart_number}}"></span>
  {%- endif -%}
  </div>
""",

    'widget_dashboard_js': """<!-- No JS content -->""",

    'widget_dashboard_js_ready': """
  // Retrieve the latest/last measurement for Measurement widget
  function getLastDataMeasurement(chart_number,
                       unique_id,
                       measure_type,
                       measurement_id,
                       max_measure_age_sec,
                       decimal_places) {
    if (decimal_places === null) {
      decimal_places = 1;
    }

    const url = '/last/' + unique_id + '/' + measure_type + '/' + measurement_id + '/' + max_measure_age_sec.toString();
    $.ajax(url, {
      success: function(data, responseText, jqXHR) {
        if (jqXHR.status === 204) {
          document.getElementById('value-' + chart_number).innerHTML = 'NO DATA';
          document.getElementById('timestamp-' + chart_number).innerHTML = 'MAX AGE EXCEEDED';
        }
        else {
          const formattedTime = epoch_to_timestamp(data[0]);
          const measurement = data[1];
          document.getElementById('value-' + chart_number).innerHTML = measurement.toFixed(decimal_places);
          const range_exists = document.getElementById("range_" + chart_number);
          if (range_exists != null) {  // Update range slider value
            document.getElementById("range_" + chart_number).value = measurement.toFixed(0);
            document.getElementById("range_val_" + chart_number).innerHTML = measurement.toFixed(0);
          }
          document.getElementById('timestamp-' + chart_number).innerHTML = formattedTime;
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        document.getElementById('value-' + chart_number).innerHTML = 'NO DATA';
        document.getElementById('timestamp-' + chart_number).innerHTML = '{{_('Error')}}';
      }
    });
  
  }

  // Repeat function for getLastData()
  function repeatLastDataMeasurement(chart_number,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec,
                          decimal_places) {
    setInterval(function () {
      getLastDataMeasurement(chart_number,
                  dev_id,
                  measure_type,
                  measurement_id,
                  max_measure_age_sec,
                  decimal_places)
    }, period_sec * 1000);
  }
""",

    'widget_dashboard_js_ready_end': """
  {%- set device_id = widget_options['measurement'].split(",")[0] -%}
  {%- set measurement_id = widget_options['measurement'].split(",")[1] -%}
  
  {% for each_input in input if each_input.unique_id == device_id %}
  getLastDataMeasurement({{chart_number}}, '{{each_input.unique_id}}', 'input', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  repeatLastDataMeasurement({{chart_number}}, '{{each_input.unique_id}}', 'input', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  {%- endfor -%}

  {% for each_math in math if each_math.unique_id == device_id %}
  getLastDataMeasurement({{chart_number}}, '{{each_math.unique_id}}', 'math', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  repeatLastDataMeasurement({{chart_number}}, '{{each_math.unique_id}}', 'math', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  {%- endfor -%}
  
  {% for each_function in function if each_function.unique_id == device_id %}
  getLastDataMeasurement({{chart_number}}, '{{each_function.unique_id}}', 'function', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  repeatLastDataMeasurement({{chart_number}}, '{{each_function.unique_id}}', 'function', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  {%- endfor -%}

  {% for each_output in output if each_output.unique_id == device_id %}
  getLastDataMeasurement({{chart_number}}, '{{each_output.unique_id}}', 'output', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  repeatLastDataMeasurement({{chart_number}}, '{{each_output.unique_id}}', 'output', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  {%- endfor -%}

  {% for each_pid in pid if each_pid.unique_id == device_id %}
  getLastDataMeasurement({{chart_number}}, '{{each_pid.unique_id}}', 'pid', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  repeatLastDataMeasurement({{chart_number}}, '{{each_pid.unique_id}}', 'pid', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}});
  {%- endfor -%}
"""
}

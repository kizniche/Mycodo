# coding=utf-8
#
#  widget_indicator.py - Indicator dashboard widget
#
#  Copyright (C) 2017  Kyle T. Gabriel
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
import importlib.util
import logging
import os
import textwrap
import threading
import time

from flask import flash
from flask_babel import lazy_gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.widgets.base_widget import AbstractWidget
from mycodo.databases.models import Widget
from mycodo.utils.code_verification import create_python_file
from mycodo.utils.code_verification import test_python_code
from mycodo.utils.system_pi import parse_custom_option_values_json
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger(__name__)


def constraints_pass_positive_value(mod_widget, value):
    """
    Check if the user widget is acceptable
    :param mod_widget: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_widget


WIDGET_INFORMATION = {
    'widget_name_unique': 'WIDGET_INDICATOR',
    'widget_name': 'Indicator',
    'widget_library': '',
    'no_class': True,

    'message': 'This widget will display a measurement value and timestamp.',

    'widget_width': 3,
    'widget_height': 4,

    'custom_options': [
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 30.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Widget Refresh (seconds)',
            'phrase': 'The period of time between refreshing the widget'
        },
        {
            'id': 'font_em_measurement',
            'type': 'float',
            'default_value': 1.5,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Body Font Size (em)',
            'phrase': 'The font size of the measurement'
        },
        {
            'id': 'show_timestamp',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Show Timestamp'),
            'phrase': lazy_gettext('Show the timestamp on the widget')
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
            'id': 'measurement',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Output',
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
            'name': lazy_gettext('Measurement Max Age'),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement')
        },
        {
            'id': 'decimal_places',
            'type': 'integer',
            'default_value': 2,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Decimal Places',
            'phrase': 'The number of measurement decimal places'
        },
        {
            'id': 'option_invert',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Colors'),
            'phrase': lazy_gettext('Invert the indicator colors')
        }
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    'widget_dashboard_body': """<img style="max-width: 60%; max-height: 60%" id="value-{{chart_number}}" src="" alt="">
  {% if widget_options['show_timestamp'] %}<br/><span style="font-size: {{widget_options['font_em_timestamp']}}em" id="timestamp-{{chart_number}}"></span>{% endif %}""",

    'widget_dashboard_js': """<!-- No JS content -->""",

    'widget_dashboard_js_ready': """
  // Retrieve the latest/last measurement for indicator widget
  function getLastDataIndicator(chart_number,
                       unique_id,
                       measure_type,
                       measurement_id,
                       max_measure_age_sec,
                       decimal_places,
                       invert) {
    if (decimal_places === null) {
      decimal_places = 1;
    }

    // Get output state for indicator and output widgets
    if (measure_type === "output") {
      const url = '/outputstate_unique_id/' + unique_id;
      $.ajax(url, {
        success: function (data, responseText, jqXHR) {
          if (jqXHR.status !== 204) {
            if (data !== null) {
              document.getElementById('timestamp-' + chart_number).innerHTML = '';
              if (data !== 'off') {
                document.getElementById('value-' + chart_number).title = "{{_('On')}}";
              } else {
                document.getElementById('value-' + chart_number).title = "{{_('Off')}}";
              }
              if ((data !== 'off' && !invert) || (data === 'off' && invert)) {
                document.getElementById('value-' + chart_number).src = '/static/img/button-green.png';
              }
              else {
                document.getElementById('value-' + chart_number).src = '/static/img/button-red.png';
              }
            }
          } else {
            document.getElementById('value-' + chart_number).src = '/static/img/button-yellow.png';
            document.getElementById('timestamp-' + chart_number).innerHTML = '{{_('Error')}}';
          }
        },
        error: function (jqXHR, textStatus, errorThrown) {
          document.getElementById('value-' + chart_number).src = '';
          document.getElementById('value-' + chart_number).innerHTML = 'NO DATA';
          document.getElementById('timestamp-' + chart_number).innerHTML = '{{_('Error')}}';
        }
      });
    }

    // Get last measurement
    else {
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
            if ((measurement && !invert) || (!measurement && invert)) {
              document.getElementById('value-' + chart_number).src = '/static/img/button-green.png';
            } else {
              document.getElementById('value-' + chart_number).src = '/static/img/button-red.png';
            }
            document.getElementById('value-' + chart_number).title = "{{_('Value')}}: " + measurement;
            document.getElementById('timestamp-' + chart_number).innerHTML = formattedTime;
          }
        },
        error: function(jqXHR, textStatus, errorThrown) {
          document.getElementById('value-' + chart_number).innerHTML = 'NO DATA';
          document.getElementById('timestamp-' + chart_number).innerHTML = '{{_('Error')}}';
        }
      });
    }
  }

  // Repeat function for getLastDataIndicator()
  function repeatLastDataIndicator(chart_number,
                                   dev_id,
                                   measure_type,
                                   measurement_id,
                                   period_sec,
                                   max_measure_age_sec,
                                   decimal_places,
                                   invert) {
    setInterval(function () {
      getLastDataIndicator(chart_number,
                           dev_id,
                           measure_type,
                           measurement_id,
                           max_measure_age_sec,
                           decimal_places,
                           invert)
    }, period_sec * 1000);
  }
""",

    'widget_dashboard_js_ready_end': """
  {%- set device_id = widget_options['measurement'].split(",")[0] -%}
  {%- set measurement_id = widget_options['measurement'].split(",")[1] -%}
  
  {% for each_input in input if each_input.unique_id == device_id %}
  getLastDataIndicator({{chart_number}}, '{{each_input.unique_id}}', 'input', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}}, {{widget_options['option_invert']|int}});
  repeatLastDataIndicator({{chart_number}}, '{{each_input.unique_id}}', 'input', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{each_widget.decimal_places}}, {{widget_options['option_invert']|int}});
  {%- endfor -%}

  {% for each_math in math if each_math.unique_id == device_id %}
  getLastDataIndicator({{chart_number}}, '{{each_math.unique_id}}', 'math', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}}, {{widget_options['option_invert']|int}});
  repeatLastDataIndicator({{chart_number}}, '{{each_math.unique_id}}', 'math', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{each_widget.decimal_places}}, {{widget_options['option_invert']|int}});
  {%- endfor -%}

  {% for each_output in output if each_output.unique_id == device_id %}
  getLastDataIndicator({{chart_number}}, '{{each_output.unique_id}}', 'output', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}}, {{widget_options['option_invert']|int}});
  repeatLastDataIndicator({{chart_number}}, '{{each_output.unique_id}}', 'output', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{each_widget.decimal_places}}, {{widget_options['option_invert']|int}});
  {%- endfor -%}

  {% for each_pid in pid if each_pid.unique_id == device_id %}
  getLastDataIndicator({{chart_number}}, '{{each_pid.unique_id}}', 'pid', '{{measurement_id}}', {{widget_options['measurement_max_age']}}, {{widget_options['decimal_places']}}, {{widget_options['option_invert']|int}});
  repeatLastDataIndicator({{chart_number}}, '{{each_pid.unique_id}}', 'pid', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_max_age']}}, {{each_widget.decimal_places}}, {{widget_options['option_invert']|int}});
  {%- endfor -%}
"""
}

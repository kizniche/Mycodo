# coding=utf-8
#
#  widget_function_status.py - Function Status dashboard widget
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
    'widget_name_unique': 'widget_function_status',
    'widget_name': 'Function Status',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays the status of a Function (if supported).',

    'widget_width': 7,
    'widget_height': 10,

    'custom_options': [
        {
            'id': 'function_id',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Function',
                'Conditional',
                'PID'
            ],
            'name': lazy_gettext('Function'),
            'phrase': lazy_gettext('Select a Function to display the status of')
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
            'id': 'font_em_value',
            'type': 'float',
            'default_value': 1.2,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Value Font Size (em)',
            'phrase': 'The font size of the measurement'
        },
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    'widget_dashboard_body': """Activated: <span style="font-size: {{widget_options['font_em_value']}}em" id="status_activated-{{each_widget.unique_id}}"></span><br>Always: <span style="font-size: {{widget_options['font_em_value']}}em" id="status_always-{{each_widget.unique_id}}"></span>""",

    'widget_dashboard_js': """
    function function_status_activated(function_id, widget_id) {
      const url = '/function_status_activated/' + function_id;
      $.getJSON(url,
        function(data, responseText, jqXHR) {
          if (jqXHR.status !== 204) {
            let string_display = "";
            if ('error' in data) {
              for (var i = 0, size = data['error'].length; i < size; i++){
                string_display += "<p>Error: " + data['error'][i] + "</p>";
              }
            }
            if ('string_status' in data) {
              string_display += data['string_status'].replace(/(?:\\r\\n|\\r|\\n)/g, "<br>");
            }
            document.getElementById("status_activated-" + widget_id).innerHTML = string_display;
          }
          else {
            document.getElementById("status_activated-" + widget_id).innerHTML = "Error";
          }
        }
      );
    }
    // Repeat function for function_status()
    function repeat_function_status_activated(function_id, widget_id, period_sec) {
      setInterval(function () {
        function_status_activated(function_id, widget_id)
      }, period_sec * 1000);
    }
    
    function function_status_always(function_id, widget_id) {
      const url_2 = '/function_status_always/' + function_id;
      $.getJSON(url_2,
        function(data, responseText, jqXHR) {
          if (jqXHR.status !== 204) {
            let string_display = "";
            if ('error' in data) {
              for (var i = 0, size = data['error'].length; i < size; i++){
                string_display += "<p>Error: " + data['error'][i] + "</p>";
              }
            }
            if ('string_status' in data) {
              string_display += data['string_status'].replace(/(?:\\r\\n|\\r|\\n)/g, "<br>");
            }
            document.getElementById("status_always-" + widget_id).innerHTML = string_display;
          }
          else {
            document.getElementById("status_always-" + widget_id).innerHTML = "Error";
          }
        }
      );
    }
    // Repeat function for function_status_always()
    function repeat_function_status_always(function_id, widget_id, period_sec) {
      setInterval(function () {
        function_status_always(function_id, widget_id)
      }, period_sec * 1000);
    }""",

    'widget_dashboard_js_ready': """<!-- No JS ready content -->""",

    'widget_dashboard_js_ready_end': """
  function_status_activated('{{widget_options['function_id']}}', '{{each_widget.unique_id}}');
  repeat_function_status_activated('{{widget_options['function_id']}}', '{{each_widget.unique_id}}', {{widget_options['refresh_seconds']}});
  function_status_always('{{widget_options['function_id']}}', '{{each_widget.unique_id}}');
  repeat_function_status_always('{{widget_options['function_id']}}', '{{each_widget.unique_id}}', {{widget_options['refresh_seconds']}});
"""
}

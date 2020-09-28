# coding=utf-8
#
#  widget_output_pwm_slider.py - PWM Slider Output dashboard widget
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
    'widget_name_unique': 'widget_output_pwm_slider',
    'widget_name': 'Output (PWM Slider)',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays and allows control of a PWM output using a slider.',

    'widget_width': 5,
    'widget_height': 4,

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_measurement_channel',
            'default_value': '',
            'options_select': [
                'Output_PWM_Channels_Measurements',
            ],
            'name': lazy_gettext('Output'),
            'phrase': lazy_gettext('Select the output to display and control')
        },
        {
            'id': 'max_measure_age',
            'type': 'integer',
            'default_value': 3600,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Max Age (seconds)',
            'phrase': 'The maximum age of the camera image'
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
            'id': 'enable_timestamp',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Enable Timestamp'),
            'phrase': lazy_gettext('Show the timestamp on the widget')
        },
        {
            'id': 'font_em_timestamp',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Timestamp Font Size (em)'),
            'phrase': lazy_gettext('The font size of the timestamp')
        },
        {
            'id': 'decimal_places',
            'type': 'integer',
            'default_value': 1,
            'name': lazy_gettext('Decimal Places'),
            'phrase': lazy_gettext('The number of decimal places to display')
        },
        {
            'id': 'enable_status',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Enable Status'),
            'phrase': lazy_gettext('Show the current output status')
        },
        {
            'id': 'enable_value',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Enable Value'),
            'phrase': lazy_gettext('Show the current value')
        },
        {
            'id': 'enable_unit',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Enable Unit'),
            'phrase': lazy_gettext('Show the value unit')
        },
        {
            'id': 'enable_output_controls',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Enable Output Controls'),
            'phrase': lazy_gettext('Show output controls on the widget')
        }
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """
    {%- if widget_options['enable_status'] -%}
      (<span id="text-output-state-{{chart_number}}"></span>{{') '}}
    {%- else -%}
      <span style="display: none" id="text-output-state-{{chart_number}}"></span>
    {%- endif -%}

    <span style="padding-right: 0.5em"> {{each_widget.name}}</span>
""",

    'widget_dashboard_body': """
{%- set device_id = widget_options['output'].split(",")[0] -%}
{%- set measurement_id = widget_options['output'].split(",")[1] -%}
{%- set channel_id = widget_options['output'].split(",")[2] -%}

{% set is_pwm = [] -%}
{% set is_ezo_pump = [] -%}
{% for each_output in output if each_output.unique_id == device_id %}
  {% if each_output.output_type in output_types['pwm'] %}
    {%- do is_pwm.append(1) %}
  {% elif each_output.output_type in ['atlas_ezo_pmp'] %}
    {%- do is_ezo_pump.append(1) %}
  {% endif %}
{% endfor %}

<div class="pause-background" id="container-output-{{chart_number}}" style="height: 100%; text-align: center">
  {%- if widget_options['enable_timestamp'] -%}
  <span style="font-size: {{widget_options['font_em_timestamp']}}em" id="timestamp-{{chart_number}}"></span>
  {%- else -%}
  <span style="display: none" id="timestamp-{{chart_number}}"></span>
  {%- endif -%}

  {%- if widget_options['enable_value'] and widget_options['enable_timestamp'] -%}
    {{' - '}}
  {%- endif -%}

  {%- if widget_options['enable_value'] -%}
  <span style="font-size: {{widget_options['font_em_value']}}em" id="value-{{chart_number}}"></span> %
  {%- else -%}
  <span style="display: none" id="value-{{chart_number}}"></span>
  {%- endif -%}

  {%- if widget_options['enable_timestamp'] or widget_options['enable_value'] -%}
  <br/>
  {%- endif -%}

<span id="range_val_{{chart_number}}" style="font-size: {{widget_options['font_em_value']}}em"></span> <input id="range_{{chart_number}}" type="range" min="0" max="100" step="1" value="0" style="width:80%;" oninput="showVal({{chart_number}}, this.value)" onchange="PWMSlidersendVal({{chart_number}}, '{{device_id}}', '{{channel_id}}', this.value)">

  {% if widget_options['enable_output_controls'] %}

  <div class="row small-gutters" style="padding: 0.3em 1.5em 0 1.5em">
    <div class="col-auto">
      <input class="btn btn-sm btn-primary turn_off_pwm_slider" id="turn_off" name="{{chart_number}}/{{device_id}}/{{channel_id}}/off/sec/0" type="button" value="{{dict_translation['off']['title']}}">
    </div>
    <div class="col-auto">
      <input class="form-control-sm" id="pwm_slider_duty_cycle_on_amt_{{chart_number}}_{{device_id}}_{{channel_id}}" name="duty_cycle_on_amt_{{chart_number}}_{{device_id}}_{{channel_id}}" title="Select the PWM duty cycle (0.0 - 100.0)" type="number" step="any" value="" placeholder="% Duty Cycle">
    </div>
    <div class="col-auto">
      <input class="btn btn-sm btn-primary duty_cycle_on_amt_pwm_slider" id="turn_on" name="{{chart_number}}/{{device_id}}/{{channel_id}}/on/pwm/" type="button" value="{{_('PWM On')}}">
    </div>
  </div>

  {% endif %}

</div>
""",

    'widget_dashboard_js': """
// Turn Output on or off
function modOutputPWM(btn_val) {
  $.ajax({
      type: 'GET',
      url: '/output_mod/' + btn_val,
    {% if not misc.hide_alert_success %}
      success: function(data) {
        if (data.startsWith("SUCCESS")) {
          toastr['success']("Output: " + data);
        }
        else {
          toastr['error']("Output: " + data);
        }
      },
    {% endif %}
    {% if not misc.hide_alert_warning %}
      error: function(data) {
          toastr['error']("Output " + btn_val.split("/")[0] + ": " + data);
      }
    {% endif %}
  });
}

// Output PWM Slider Widget
function showVal(chart, duty_cycle){
  document.getElementById("range_val_" + chart).innerHTML = duty_cycle;
}

function PWMSlidersendVal(chart, output_id, channel_id, duty_cycle){
  document.getElementById("range_val_" + chart).innerHTML = duty_cycle;
  const cmd_send = output_id + '/' + channel_id + '/on/pwm/' + duty_cycle;
  modOutputPWM(cmd_send);
}

$(document).ready(function() {
  $('.turn_off_pwm_slider').click(function() {
    const btn_val = this.name;
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output Off');
    {% endif %}
    modOutputPWM(send_cmd);
  });
  $('.duty_cycle_on_amt_pwm_slider').click(function() {const output_id = btn_val.split('/')[1];
    const channel_id = btn_val.split('/')[2];
    const btn_val = this.name;
    const chart = btn_val.split('/')[0];
    
    const dc = $('#pwm_slider_duty_cycle_on_amt_' + chart + '_' + output_id + '_' + channel_id).val();
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output On with a duty cycle of ' + dc + '%');
    {% endif %}
    modOutputPWM(send_cmd + dc);
  });
});
""",

    'widget_dashboard_js_ready': """
 // Retrieve the latest/last measurement for gauges/outputs
  function getLastDataPWMSlider(chart_number,
                       unique_id,
                       measure_type,
                       measurement_id,
                       max_measure_age_sec,
                       decimal_places,
                       extra) {
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
  function repeatLastDataPWMSlider(chart_number,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec,
                          decimal_places,
                          extra) {
    setInterval(function () {
      getLastDataPWMSlider(chart_number,
                  dev_id,
                  measure_type,
                  measurement_id,
                  max_measure_age_sec,
                  decimal_places,
                  extra)
    }, period_sec * 1000);
  }
  
   function getGPIOStatePWMSlider(chart_number, unique_id, channel_id) {
    const url = '/outputstate_unique_id/' + unique_id + '/' + channel_id;
    $.getJSON(url,
      function(state, responseText, jqXHR) {
        if (jqXHR.status !== 204) {
          if (state !== null) {
            document.getElementById("container-output-" + chart_number).className = "active-background";
            if (state !== 'off') {
              if (state === 'on') {
                document.getElementById("text-output-state-" + chart_number).innerHTML = '{{_('Active')}}';
              } else {
                document.getElementById("text-output-state-" + chart_number).innerHTML = '{{_('Active')}}, ' + state.toFixed(1) + '%';
              }
            }
            else {
              document.getElementById("container-output-" + chart_number).className = "inactive-background";
              document.getElementById("text-output-state-" + chart_number).innerHTML = '{{_('Inactive')}}';
            }
          }
        }
        else {
          document.getElementById("container-output-" + chart_number).className = "pause-background";
          document.getElementById("text-output-state-" + chart_number).innerHTML = '{{_('No Connection')}}';
        }
      }
    );
  }

  function repeatGPIOStatePWMSlider(chart_number, unique_id, channel_id, refresh_seconds) {
    setInterval(function () {
      getGPIOStatePWMSlider(chart_number, unique_id, channel_id);
    }, refresh_seconds * 1000);  // Refresh duration in milliseconds
  }
""",

    'widget_dashboard_js_ready_end': """
{%- set device_id = widget_options['output'].split(",")[0] -%}
{%- set measurement_id = widget_options['output'].split(",")[1] -%}
{%- set channel_id = widget_options['output'].split(",")[2] -%}

{% for each_output in output if each_output.unique_id == device_id %}
  getLastDataPWMSlider({{chart_number}}, '{{device_id}}', 'output', '{{measurement_id}}', {{widget_options['max_measure_age']}}, {{widget_options['decimal_places']}});
  repeatLastDataPWMSlider({{chart_number}}, '{{device_id}}', 'output', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}}, {{widget_options['decimal_places']}});
{% endfor %}
  getGPIOStatePWMSlider({{chart_number}}, '{{device_id}}', '{{channel_id}}', {{widget_options['decimal_places']}});
  repeatGPIOStatePWMSlider({{chart_number}}, '{{device_id}}', '{{channel_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['decimal_places']}});
"""
}

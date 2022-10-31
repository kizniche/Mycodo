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

from mycodo.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_output_pwm_slider',
    'widget_name': 'Output (PWM Slider)',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays and allows control of a PWM output using a slider.',

    'widget_width': 5,
    'widget_height': 7,

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
            'id': 'invert_status',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Status'),
            'phrase': lazy_gettext('Invert the output status. Enable if the Invert Signal output option is set.')
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
      <span id="text-output-state-{{each_widget.unique_id}}"></span>
    {%- else -%}
      <span style="display: none" id="text-output-state-{{each_widget.unique_id}}"></span>
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

<div class="pause-background" id="container-output-{{each_widget.unique_id}}" style="height: 100%; text-align: center">
  {%- if widget_options['enable_timestamp'] -%}
  <span style="font-size: {{widget_options['font_em_timestamp']}}em" id="timestamp-{{each_widget.unique_id}}"></span>
  {%- else -%}
  <span style="display: none" id="timestamp-{{each_widget.unique_id}}"></span>
  {%- endif -%}

  {%- if widget_options['enable_value'] and widget_options['enable_timestamp'] -%}
    {{' - '}}
  {%- endif -%}

  {%- if widget_options['enable_value'] -%}
  <span style="font-size: {{widget_options['font_em_value']}}em" id="value-{{each_widget.unique_id}}"></span> %
  {%- else -%}
  <span style="display: none" id="value-{{each_widget.unique_id}}"></span>
  {%- endif -%}

  {%- if widget_options['enable_timestamp'] or widget_options['enable_value'] -%}
  <br/>
  {%- endif -%}

<span id="range_val_{{each_widget.unique_id}}" style="font-size: {{widget_options['font_em_value']}}em"></span> <input id="range_{{each_widget.unique_id}}" type="range" min="0" max="100" step="1" value="0" style="width:80%;" oninput="showVal('{{each_widget.unique_id}}', this.value)" onchange="PWMSlidersendVal('{{each_widget.unique_id}}', '{{device_id}}', '{{channel_id}}', this.value)">

  {% if widget_options['enable_output_controls'] %}

  <div class="row small-gutters" style="padding: 0.3em 1.5em 0 1.5em">
    <div class="col-auto">
      <input class="btn btn-sm btn-primary turn_off_pwm_slider" id="turn_off" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/off/sec/0" type="button" value="{{dict_translation['off']['title']}}">
    </div>
    <div class="col-auto">
      <input class="form-control-sm" id="pwm_slider_duty_cycle_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" name="duty_cycle_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" title="Select the PWM duty cycle (0.0 - 100.0)" type="number" step="any" value="" placeholder="% Duty Cycle">
    </div>
    <div class="col-auto">
      <input class="btn btn-sm btn-primary duty_cycle_on_amt_pwm_slider" id="turn_on" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/on/pwm/" type="button" value="{{_('PWM On')}}">
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

  // Retrieve the latest/last measurement for gauges/outputs
  function getLastDataPWMSlider(widget_id,
                       unique_id,
                       measure_type,
                       measurement_id,
                       max_measure_age_sec,
                       invert_status,
                       decimal_places) {
    if (decimal_places === null) {
      decimal_places = 1;
    }
    const url = '/last/' + unique_id + '/' + measure_type + '/' + measurement_id + '/' + max_measure_age_sec.toString();
    $.ajax(url, {
      success: function(data, responseText, jqXHR) {
        if (jqXHR.status === 204) {
          document.getElementById('value-' + widget_id).innerHTML = 'NO DATA';
          document.getElementById('timestamp-' + widget_id).innerHTML = 'MAX AGE EXCEEDED';
        }
        else {
          const formattedTime = epoch_to_timestamp(data[0] * 1000);
          let measurement = data[1];
          
          if (invert_status) {
            measurement = 100 - measurement;
          }          
          document.getElementById('value-' + widget_id).innerHTML = measurement.toFixed(decimal_places);
   
          const range_exists = document.getElementById("range_" + widget_id);
          if (range_exists != null) {  // Update range slider value
            document.getElementById("range_" + widget_id).value = measurement.toFixed(0);
            document.getElementById("range_val_" + widget_id).innerHTML = measurement.toFixed(0);
          }
          document.getElementById('timestamp-' + widget_id).innerHTML = formattedTime;
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        document.getElementById('value-' + widget_id).innerHTML = 'NO DATA';
        document.getElementById('timestamp-' + widget_id).innerHTML = '{{_('Error')}}';
      }
    });
  }

  // Repeat function for getLastData()
  function repeatLastDataPWMSlider(widget_id,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec,
                          invert_status,
                          decimal_places) {
    setInterval(function () {
      getLastDataPWMSlider(widget_id,
                  dev_id,
                  measure_type,
                  measurement_id,
                  max_measure_age_sec,
                  invert_status,
                  decimal_places)
    }, period_sec * 1000);
  }
  
  function getGPIOStatePWMSlider(widget_id, unique_id, channel_id, invert_status, decimal_places) {
    if (decimal_places === null) {
      decimal_places = 1;
    }
    const url = '/outputstate_unique_id/' + unique_id + '/' + channel_id;
    $.getJSON(url,
      function(state, responseText, jqXHR) {
        if (jqXHR.status !== 204) {
          if (state !== null) {
            document.getElementById("container-output-" + widget_id).className = "active-background";
            
            if (invert_status) {
              if (state === 100) {
                document.getElementById("container-output-" + widget_id).className = "inactive-background";
                document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Inactive')}})';
              } else {
                if (state === 'off') state = 100;
                else state = 100 - state;
                document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Active')}}, ' + state.toFixed(decimal_places) + '%)';
              }
            }
            else {
              if (state !== 'off') {
                if (state === 'on') {
                  document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Active')}})';
                } else {
                  document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Active')}}, ' + state.toFixed(decimal_places) + '%)';
                }
              }
              else {
                document.getElementById("container-output-" + widget_id).className = "inactive-background";
                document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Inactive')}})';
              }
            }

          }
        }
        else {
          document.getElementById("container-output-" + widget_id).className = "pause-background";
          document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('No Connection')}})';
        }
      }
    );
  }

  function repeatGPIOStatePWMSlider(widget_id, unique_id, channel_id, refresh_seconds, invert_status, decimal_places) {
    setInterval(function () {
      getGPIOStatePWMSlider(widget_id, unique_id, channel_id, invert_status, decimal_places);
    }, refresh_seconds * 1000);  // Refresh duration in milliseconds
  }
""",

    'widget_dashboard_js_ready': """
  $('.turn_off_pwm_slider').click(function() {
    const btn_val = this.name;
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output Off');
    {% endif %}
    modOutputPWM(send_cmd);
  });
  $('.duty_cycle_on_amt_pwm_slider').click(function() {
    const btn_val = this.name;
    const chart = btn_val.split('/')[0];
    const output_id = btn_val.split('/')[1];
    const channel_id = btn_val.split('/')[2];
    const dc = $('#pwm_slider_duty_cycle_on_amt_' + chart + '_' + output_id + '_' + channel_id).val();
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output On with a duty cycle of ' + dc + '%');
    {% endif %}
    modOutputPWM(send_cmd + dc);
  });
""",

    'widget_dashboard_js_ready_end': """
{%- set device_id = widget_options['output'].split(",")[0] -%}
{%- set measurement_id = widget_options['output'].split(",")[1] -%}
{%- set channel_id = widget_options['output'].split(",")[2] -%}

{% for each_output in output if each_output.unique_id == device_id %}
  getLastDataPWMSlider('{{each_widget.unique_id}}', '{{device_id}}', 'output', '{{measurement_id}}', {{widget_options['max_measure_age']}}, {% if widget_options['invert_status'] %}true{% else %}false{% endif %}, {{widget_options['decimal_places']}});
  repeatLastDataPWMSlider('{{each_widget.unique_id}}', '{{device_id}}', 'output', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}}, {% if widget_options['invert_status'] %}true{% else %}false{% endif %}, {{widget_options['decimal_places']}});
{% endfor %}
  getGPIOStatePWMSlider('{{each_widget.unique_id}}', '{{device_id}}', '{{channel_id}}', {% if widget_options['invert_status'] %}true{% else %}false{% endif %}, {{widget_options['decimal_places']}});
  repeatGPIOStatePWMSlider('{{each_widget.unique_id}}', '{{device_id}}', '{{channel_id}}', {{widget_options['refresh_seconds']}}, {% if widget_options['invert_status'] %}true{% else %}false{% endif %}, {{widget_options['decimal_places']}});
"""
}

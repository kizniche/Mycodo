# coding=utf-8
#
#  widget_output.py - Output channel select dashboard widget
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
    'widget_name_unique': 'widget_output',
    'widget_name': 'Output Control (Channel)',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays and allows control of an output channel. All output options and measurements for the selected channel will be displayed. E.g. pumps will have seconds on and volume as measurements, and can be turned on for a duration (Seconds) or amount (Volume). If NO DATA or TOO OLD is displayed, the Max Age is not sufficiently long enough to find a current measurement.',

    'widget_width': 5,
    'widget_height': 7,

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'options_select': [
                'Output_Channels',
            ],
            'name': lazy_gettext('Output'),
            'phrase': 'Select the output channel to display and control'
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
      <span id="text-output-state-{{each_widget.unique_id}}"></span>{{' '}}
    {%- else -%}
      <span style="display: none" id="text-output-state-{{each_widget.unique_id}}"></span>
    {%- endif -%}

    <span style="padding-right: 0.5em"> {{each_widget.name}}</span>
""",

    'widget_dashboard_body': """
{%- set device_id = "" -%}
{%- set channel_id = "" -%}
{%- set out = none -%}
{%- set out_chan = none -%}
{%- set measurements = [] -%}
{%- set channel_output = [] -%}

{%- if widget_options['output'] and "," in widget_options['output'] -%}
    {%- set device_id = widget_options['output'].split(",")[0] -%}
    {%- set channel_id = widget_options['output'].split(",")[1] -%}
{%- endif -%}

{%- if device_id and channel_id -%}
    {% set out = table_output.query.filter(table_output.unique_id == device_id).first() %}
    {% set out_chan = table_output_channel.query.filter(table_output_channel.unique_id == channel_id).first() %}
{%- endif -%}

{%- if out and out_chan and 
       out.output_type and out_chan.channel is not none and
       out.output_type in dict_outputs and
       "channels_dict" in dict_outputs[out.output_type] and
       out_chan.channel in dict_outputs[out.output_type]["channels_dict"] -%}
    {%- set channel_output = dict_outputs[out.output_type]["channels_dict"][out_chan.channel] -%}
    {%- if "measurements" in channel_output and channel_output["measurements"] -%}
        {% set measurements = table_device_measurements.query.filter(
                                and_(table_device_measurements.device_id == device_id,
                                     table_device_measurements.channel.in_(channel_output["measurements"]))).all() %}
    {%- endif -%}
{%- endif -%}

<div class="pause-background" id="container-output-{{each_widget.unique_id}}" style="height: 100%; text-align: center">

  <div class="container" style="padding: 0.3em 0">
    
    {% for each_measure in measurements if widget_options['enable_value'] or widget_options['enable_unit'] %}
        <span style="{% if not widget_options['enable_value'] %}display: none {% endif %}font-size: {{widget_options['font_em_value']}}em" id="value-{{each_measure.unique_id}}"></span>

        {% if widget_options['enable_unit'] and
              dict_measure_units[each_measure.unique_id] in dict_units and
              dict_units[dict_measure_units[each_measure.unique_id]]['unit'] -%}
            {{' ' + dict_units[dict_measure_units[each_measure.unique_id]]['unit']}}
            {% if 'name' in dict_outputs[out.output_type]["measurements_dict"][each_measure.channel] and
                  dict_outputs[out.output_type]["measurements_dict"][each_measure.channel]['name'] %}
                {{dict_outputs[out.output_type]["measurements_dict"][each_measure.channel]['name']}}
            {% endif %}
        {% endif %},

        <span style="{% if not widget_options['enable_timestamp'] %}display: none {% endif %}font-size: {{widget_options['font_em_timestamp']}}em" id="timestamp-{{each_measure.unique_id}}"></span>
        {%- if not loop.last %}<br/>{% endif %}
    {% endfor %}

  </div>

  {% if widget_options['enable_output_controls'] %}

  <div class="container" style="padding: 0.3em 1.5em 0 1.5em">

    {% if "types" in channel_output and "on_off" in channel_output["types"] -%}

    <div class="row small-gutters">
      <div class="col-auto">
        <input class="btn btn-sm btn-primary turn_on" id="turn_on" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/on/sec/0" type="button" value="{{dict_translation['on']['title']}}">
      </div>
      <div class="col-auto">
        <input class="btn btn-sm btn-primary turn_off" id="turn_off" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/off/sec/0" type="button" value="{{dict_translation['off']['title']}}">
      </div>
    </div>

    {%- endif %}
    
    {% if "types" in channel_output and "on_off" in channel_output["types"] -%}

    <div class="row small-gutters">
      <div class="col-auto">
        <input class="form-control-sm" id="sec_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" name="sec_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" title="Turn this output on for this duration (Seconds)" type="number" step="any" value="">
      </div>
      <div class="col-auto">
        <input class="btn btn-sm btn-primary sec_on_amt" id="turn_on" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/on/sec/" type="button" value="{{_('Seconds On')}}">
      </div>
    </div>

    {% endif %}

    {% if "types" in channel_output and "pwm" in channel_output["types"] -%}

    <div class="row small-gutters">
      <div class="col-auto">
        <input class="form-control-sm" id="duty_cycle_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" name="duty_cycle_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" title="Select the PWM duty cycle (0.0 - 100.0 %)" type="number" step="any" value="" placeholder="% Duty Cycle">
      </div>
      <div class="col-auto">
        <input class="btn btn-sm btn-primary duty_cycle_on_amt" id="turn_on" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/on/pwm/" type="button" value="{{_('Set PWM')}}">
      </div>
    </div>

    {% endif %}

    {% if "types" in channel_output and "volume" in channel_output["types"] -%}

    <div class="row small-gutters">
      <div class="col-auto">
        <input class="form-control-sm" id="vol_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" name="sec_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" title="Instruct the output to dispense this volume (ml, l, etc.)" type="number" step="any" value="">
      </div>
      <div class="col-auto">
        <input class="btn btn-sm btn-primary vol_on_amt" id="turn_on" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/on/vol/" type="button" value="{{_('Send Volume')}}">
      </div>
    </div>

    {% endif %}

    {% if "types" in channel_output and "value" in channel_output["types"] -%}

    <div class="row small-gutters">
      <div class="col-auto">
        <input class="form-control-sm" id="value_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" name="sec_on_amt_{{each_widget.unique_id}}_{{device_id}}_{{channel_id}}" title="Send this value to the output" type="number" step="any" value="">
      </div>
      <div class="col-auto">
        <input class="btn btn-sm btn-primary value_on_amt" id="turn_on" name="{{each_widget.unique_id}}/{{device_id}}/{{channel_id}}/on/value/" type="button" value="{{_('Send Value')}}">
      </div>
    </div>

    {% endif %}

  </div>

  {% endif %}

</div>
""",

    'widget_dashboard_js': """
  // Turn Output on or off
  function modOutputOutput(btn_val) {
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

  // Retrieve the latest/last measurement for gauges/outputs
  function getLastDataOutput(widget_id,
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
          document.getElementById('value-' + measurement_id).innerHTML = 'NO DATA';
          document.getElementById('timestamp-' + measurement_id).innerHTML = 'TOO OLD';
        }
        else {
          const formattedTime = epoch_to_timestamp(data[0] * 1000);
          const measurement = data[1];
            document.getElementById('value-' + measurement_id).innerHTML = measurement.toFixed(decimal_places);

            const range_exists = document.getElementById("range_" + widget_id);
            if (range_exists != null) {  // Update range slider value
              document.getElementById("range_" + widget_id).value = measurement.toFixed(0);
              document.getElementById("range_val_" + widget_id).innerHTML = measurement.toFixed(0);
            }
          document.getElementById('timestamp-' + measurement_id).innerHTML = formattedTime;
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        document.getElementById('value-' + measurement_id).innerHTML = 'NO DATA';
        document.getElementById('timestamp-' + measurement_id).innerHTML = '{{_('Error')}}';
      }
    });
  }

  // Repeat function for getLastData()
  function repeatLastDataOutput(widget_id,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec,
                          decimal_places,
                          extra) {
    setInterval(function () {
      getLastDataOutput(widget_id,
                  dev_id,
                  measure_type,
                  measurement_id,
                  max_measure_age_sec,
                  decimal_places,
                  extra)
    }, period_sec * 1000);
  }

  function getGPIOStateOutput(widget_id, unique_id, channel_id) {
    const url = '/outputstate_unique_id/' + unique_id + '/' + channel_id;
    $.getJSON(url,
      function(state, responseText, jqXHR) {
        if (jqXHR.status !== 204) {
          if (state !== null) {
            document.getElementById("container-output-" + widget_id).className = "active-background";
            if (state !== 'off') {
              if (state === 'on') {
                document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Active')}})';
              } else {
                document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Active')}}, ' + state.toFixed(1) + '%)';
              }
            }
            else {
              document.getElementById("container-output-" + widget_id).className = "inactive-background";
              document.getElementById("text-output-state-" + widget_id).innerHTML = '({{_('Inactive')}})';
            }
          }
        }
        else {
          document.getElementById("container-output-" + widget_id).className = "pause-background";
          document.getElementById("text-output-state-" + widget_id).innerHTML = '{{_('No Connection')}}';
        }
      }
    );
  }

  function repeatGPIOStateOutput(widget_id, unique_id, channel_id, refresh_duration) {
    setInterval(function () {
      getGPIOStateOutput(widget_id, unique_id, channel_id);
    }, refresh_duration * 1000);  // Refresh duration in milliseconds
  }
""",

    'widget_dashboard_js_ready': """
  $('.turn_on').click(function() {
    const btn_val = this.name;
    const send_cmd = btn_val.substring(btn_val.indexOf('/')+1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output On');
    {% endif %}
    modOutputOutput(send_cmd);
  });
  $('.turn_off').click(function() {
    const btn_val = this.name;
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output Off');
    {% endif %}
    modOutputOutput(send_cmd);
  });
  $('.sec_on_amt').click(function() {
    const btn_val = this.name;
    const chart = btn_val.split('/')[0];
    const output_id = btn_val.split('/')[1];
    const channel_id = btn_val.split('/')[2];
    const on_sec = $('#sec_on_amt_' + chart + '_' + output_id + '_' + channel_id).val();
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output On for ' + on_sec);
    {% endif %}
    modOutputOutput(send_cmd + on_sec);
  });   
  $('.vol_on_amt').click(function() {
    const btn_val = this.name;
    const chart = btn_val.split('/')[0];
    const output_id = btn_val.split('/')[1];
    const channel_id = btn_val.split('/')[2];
    const on_vol = $('#vol_on_amt_' + chart + '_' + output_id + '_' + channel_id).val();
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to output with volume ' + on_vol);
    {% endif %}
    modOutputOutput(send_cmd + on_vol);
  });
  $('.value_on_amt').click(function() {
    const btn_val = this.name;
    const chart = btn_val.split('/')[0];
    const output_id = btn_val.split('/')[1];
    const channel_id = btn_val.split('/')[2];
    const on_value = $('#value_on_amt_' + chart + '_' + output_id + '_' + channel_id).val();
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to output with value ' + on_value);
    {% endif %}
    modOutputOutput(send_cmd + on_value);
  });
  $('.duty_cycle_on_amt').click(function() {
    const btn_val = this.name;
    const chart = btn_val.split('/')[0];
    const output_id = btn_val.split('/')[1];
    const channel_id = btn_val.split('/')[2];
    const on_dc = $('#duty_cycle_on_amt_' + chart + '_' + output_id + '_' + channel_id).val();
    const send_cmd = btn_val.substring(btn_val.indexOf('/') + 1);
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to turn output On with a duty cycle of ' + on_dc + '%');
    {% endif %}
    modOutputOutput(send_cmd + on_dc);
  });
""",

    'widget_dashboard_js_ready_end': """
{%- set device_id = "" -%}
{%- set channel_id = "" -%}
{%- set out = none -%}
{%- set out_chan = none -%}
{%- set measurements = [] -%}
{%- set channel_output = [] -%}

{%- if widget_options['output'] and "," in widget_options['output'] -%}
    {%- set device_id = widget_options['output'].split(",")[0] -%}
    {%- set channel_id = widget_options['output'].split(",")[1] -%}
{%- endif -%}

{%- if device_id and channel_id -%}
    {% set out = table_output.query.filter(table_output.unique_id == device_id).first() %}
    {% set out_chan = table_output_channel.query.filter(table_output_channel.unique_id == channel_id).first() %}
{%- endif -%}

{%- if out and out_chan and 
       out.output_type and out_chan.channel is not none and
       out.output_type in dict_outputs and
       "channels_dict" in dict_outputs[out.output_type] and
       out_chan.channel in dict_outputs[out.output_type]["channels_dict"] -%}
    {%- set channel_output = dict_outputs[out.output_type]["channels_dict"][out_chan.channel] -%}
    {%- if "measurements" in channel_output and channel_output["measurements"] -%}
        {% set measurements = table_device_measurements.query.filter(
                                and_(table_device_measurements.device_id == device_id,
                                     table_device_measurements.channel.in_(channel_output["measurements"]))).all() %}
    {%- endif -%}
{%- endif -%}

{% for each_measure in measurements %}
  getLastDataOutput('{{each_widget.unique_id}}', '{{device_id}}', 'output', '{{each_measure.unique_id}}', {{widget_options['max_measure_age']}}, {{widget_options['decimal_places']}});
  repeatLastDataOutput('{{each_widget.unique_id}}', '{{device_id}}', 'output', '{{each_measure.unique_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}}, {{widget_options['decimal_places']}});
{% endfor %}
{% if device_id and channel_id %}
  getGPIOStateOutput('{{each_widget.unique_id}}', '{{device_id}}', '{{channel_id}}', {{widget_options['decimal_places']}});
  repeatGPIOStateOutput('{{each_widget.unique_id}}', '{{device_id}}', '{{channel_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['decimal_places']}});
{% endif %}
"""
}

# coding=utf-8
#
#  widget_pid.py - PID Controller dashboard widget
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
    'widget_name_unique': 'widget_pid',
    'widget_name': 'PID Controller',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays and allows control of a PID Controller.',

    'widget_width': 6,
    'widget_height': 6,

    'custom_options': [
        {
            'id': 'pid',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'PID',
            ],
            'name': lazy_gettext('PID Controller'),
            'phrase': lazy_gettext('Select the PID Controller to display and control')
        },
        {
            'id': 'max_measure_age',
            'type': 'integer',
            'default_value': 3600,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Max Age (seconds)',
            'phrase': 'The maximum age (seconds) of the measurement'
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
            'id': 'show_pid_info',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Show PID Info'),
            'phrase': lazy_gettext('Show the current PID output values')
        },
        {
            'id': 'show_set_setpoint',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Show Set Setpoint'),
            'phrase': lazy_gettext('Enable the setpoint to be set')
        }
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """
    {%- if widget_options['enable_status'] -%}
      <span id="text-pid-state-{{each_widget.unique_id}}"></span>{{' '}}
    {%- else -%}
      <span style="display: none" id="text-pid-state-{{each_widget.unique_id}}"></span>
    {%- endif -%}

    <span style="padding-right: 0.5em"> {{each_widget.name}}</span>
""",

    'widget_dashboard_body': """
{% set this_pid = table_pid.query.filter(table_pid.unique_id == widget_options['pid']).first() %}
<div class="pause-background" id="container-pid-{{each_widget.unique_id}}" style="height: 100%">

  <div class="row no-gutters" style="padding-top: 0.4em">
    <div class="col-6 text-center no-gutters">
      <div style="font-size: {{widget_options['font_em_value']}}em">
        Set: <span id="setpoint-{{each_widget.unique_id}}"></span>
      </div>
      {%- if widget_options['enable_timestamp'] -%}
      <span style="font-size: {{widget_options['font_em_timestamp']}}em" id="setpoint-timestamp-{{each_widget.unique_id}}"></span>
      {%- else -%}
      <span style="display: none" id="setpoint-timestamp-{{each_widget.unique_id}}"></span>
      {%- endif -%}
    </div>
    <div class="col-6 text-center no-gutters">
      <div style="font-size: {{widget_options['font_em_value']}}em">
        Now: <span id="actual-{{each_widget.unique_id}}"></span>
      </div>
      {%- if widget_options['enable_timestamp'] -%}
      <span style="font-size: {{widget_options['font_em_timestamp']}}em" id="actual-timestamp-{{each_widget.unique_id}}"></span>
      {%- else -%}
      <span style="display: none" id="actual-timestamp-{{each_widget.unique_id}}"></span>
      {%- endif -%}
    </div>
  </div>

  {% if widget_options['show_pid_info'] %}
  <div class="row">
    <div class="col-sm-12 text-center">
    P <span id="pid_p_value-{{each_widget.unique_id}}"></span> + I <span id="pid_i_value-{{each_widget.unique_id}}"></span> + D <span id="pid_d_value-{{each_widget.unique_id}}"></span> = <span id="pid_pid_value-{{each_widget.unique_id}}"></span>
    <br/>Last Out: <span id="duration_time-{{each_widget.unique_id}}"></span><span id="duty_cycle-{{each_widget.unique_id}}"></span>, <span style="font-size: {{widget_options['font_em_timestamp']}}em" id="duration_time-timestamp-{{each_widget.unique_id}}"></span><span style="font-size: {{widget_options['font_em_timestamp']}}em" id="duty_cycle-timestamp-{{each_widget.unique_id}}"></span>
    </div>
  </div>
  {% else %}
    <span id="pid_p_value-{{each_widget.unique_id}}" style="display: none"></span>
    <span id="pid_i_value-{{each_widget.unique_id}}" style="display: none"></span>
    <span id="pid_d_value-{{each_widget.unique_id}}" style="display: none"></span>
    <span id="pid_pid_value-{{each_widget.unique_id}}" style="display: none"></span>
    <span id="duration_time-{{each_widget.unique_id}}" style="display: none"></span>
    <span id="duty_cycle-{{each_widget.unique_id}}" style="display: none"></span>
    <span id="duration_time-timestamp-{{each_widget.unique_id}}" style="display: none"></span>
    <span id="duty_cycle-timestamp-{{each_widget.unique_id}}" style="display: none"></span>
  {% endif %}

  <div class="row small-gutters" style="padding: 1em 1.5em 0.5em 1.5em">
    <div id="button-activate-{{each_widget.unique_id}}" class="col-6">
      <input class="btn btn-block btn-sm btn-primary activate_pid" id="activate_pid" name="{{widget_options['pid']}}/activate_pid" type="button" value="{{dict_translation['activate']['title']}}">
    </div>
    <div id="button-deactivate-{{each_widget.unique_id}}" class="col-6">
      <input class="btn btn-block btn-sm btn-primary deactivate_pid" id="deactivate_pid" name="{{widget_options['pid']}}/deactivate_pid" type="button" value="{{dict_translation['deactivate']['title']}}">
    </div>
    <div id="button-resume-{{each_widget.unique_id}}" class="col-6">
      <input class="btn btn-block btn-sm btn-primary resume_pid" id="resume_pid" name="{{widget_options['pid']}}/resume_pid" type="button" value="{{dict_translation['resume']['title']}}">
    </div>
    <div id="button-pause-{{each_widget.unique_id}}" class="col-3">
      <input class="btn btn-block btn-sm btn-primary pause_pid" id="pause_pid" name="{{widget_options['pid']}}/pause_pid" type="button" value="{{dict_translation['pause']['title']}}">
    </div>
    <div id="button-hold-{{each_widget.unique_id}}" class="col-3">
      <input class="btn btn-block btn-sm btn-primary hold_pid" id="hold_pid" name="{{widget_options['pid']}}/hold_pid" type="button" value="{{dict_translation['hold']['title']}}">
    </div>
  </div>

  {% if widget_options['show_set_setpoint'] %}
  <div class="row small-gutters" style="padding: 0.5em 1.5em 0.5em 1.5em">
    <div class="col-6">
      <input class="form-control form-control-sm" id="setpoint_pid_{{widget_options['pid']}}" name="setpoint_pid_{{widget_options['pid']}}" type="number" value="{% if this_pid %}{{this_pid.setpoint}}{% endif %}" title="{{_('A numerical value to set the PID setpoint')}}">
    </div>
    <div class="col-6">
      <input class="btn btn-block btn-sm btn-primary set_setpoint" id="set_setpoint" name="{{widget_options['pid']}}/set_setpoint_pid|" type="button" value="{{_('Set Setpoint')}}">
    </div>
  </div>
  {% endif %}

</div>
""",

    'widget_dashboard_js': """
  // Modify PID Controller
  function modPID(btn_val) {
    $.ajax({
      type: 'GET',
      url: '/pid_mod_unique_id/' + btn_val,
    {% if not misc.hide_alert_success %}
      success: function(data) {
        toastr['success'](data);
      },
    {% endif %}
    {% if not misc.hide_alert_warning %}
      error: function(data) {
        toastr['error'](btn_val.split("/")[0] + ": " + data);
      }
    {% endif %}
    });
  }

  function print_pid_value(data, name, widget_id, decimal_places, units) {
    if (name === 'setpoint' && data['setpoint_band']) {
      data[name][1] = data['setpoint_band']
    }
    if (data[name][0] && document.getElementById(name + '-timestamp-' + widget_id)) {
      document.getElementById(name + '-timestamp-' + widget_id).innerHTML = epoch_to_timestamp(data[name][0]);
    } else if (document.getElementById(name + '-timestamp-' + widget_id)) {
      document.getElementById(name + '-timestamp-' + widget_id).innerHTML = 'MAX AGE EXCEEDED';
    }
    if (data[name][1] && document.getElementById(name + '-' + widget_id)) {
      const value = parseFloat(data[name][1]).toFixed(decimal_places);
      document.getElementById(name + '-' + widget_id).innerHTML = value + units;
    } else if (document.getElementById(name + '-' + widget_id)) {
      document.getElementById(name + '-' + widget_id).innerHTML = 'NULL';
    }
  }

  function print_pid_error(widget_id) {
    document.getElementById('container-pid-' + widget_id).className = "pause-background";
    document.getElementById('setpoint-' + widget_id).innerHTML = 'ERR';
    document.getElementById('setpoint-timestamp-' + widget_id).innerHTML = 'ERR';
    document.getElementById('pid_p_value-' + widget_id).innerHTML = 'ERR';
    document.getElementById('pid_i_value-' + widget_id).innerHTML = 'ERR';
    document.getElementById('pid_d_value-' + widget_id).innerHTML = 'ERR';
    document.getElementById('pid_pid_value-' + widget_id).innerHTML = 'ERR';
    document.getElementById('duration_time-' + widget_id).innerHTML = 'ERR';
    document.getElementById('actual-' + widget_id).innerHTML = 'ERR';
    document.getElementById('actual-timestamp-' + widget_id).innerHTML = 'ERR';
  }

  // Retrieve the latest/last measurement for gauges/outputs
  function getLastDataPID(widget_id, dev_id, max_measure_age_sec, decimal_places, units) {
    const url = '/last_pid/' + dev_id + '/' + max_measure_age_sec.toString();
    $.ajax(url, {
      success: function(data, responseText, jqXHR) {
        if (jqXHR.status === 204) {
          print_pid_error(widget_id);
        }
        else {
          if (data['activated']) {
            if (data['paused']) {
              document.getElementById('text-pid-state-' + widget_id).innerHTML = '({{_('Paused')}})';
              document.getElementById('container-pid-' + widget_id).className = "pause-background";
              document.getElementById('button-activate-' + widget_id).style.display = "none";
              document.getElementById('button-deactivate-' + widget_id).style.display = "block";
              document.getElementById('button-pause-' + widget_id).style.display = "none";
              document.getElementById('button-resume-' + widget_id).style.display = "block";
              document.getElementById('button-hold-' + widget_id).style.display = "none";
              print_pid_value(data, 'setpoint', widget_id, decimal_places, ' ' + units);
              document.getElementById('setpoint-timestamp-' + widget_id).innerHTML = 'PAUSED';
              print_pid_value(data, 'actual', widget_id, decimal_places, ' ' + units);
              print_pid_value(data, 'pid_p_value', widget_id, 1, '');
              print_pid_value(data, 'pid_i_value', widget_id, 1, '');
              print_pid_value(data, 'pid_d_value', widget_id, 1, '');
              print_pid_value(data, 'pid_pid_value', widget_id, 1, '');

              // Find which PID output is more recent, seconds on or duty cycle
              if (data['duration_time'][1] !== null && data['duty_cycle'][1] !== null) {
                if (data['duration_time'][0] > data['duty_cycle'][0]) {
                  document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
                  print_pid_value(data, 'duration_time', widget_id, 1, ' sec');
                } else {
                  document.getElementById('duration_time-' + widget_id).innerHTML = '';
                  print_pid_value(data, 'duty_cycle', widget_id, 1, ' %');
                }
              } else if (data['duration_time'][1] !== null) {
                document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
                print_pid_value(data, 'duration_time', widget_id, 1, ' sec');
              } else if (data['duty_cycle'][1] !== null) {
                document.getElementById('duration_time-' + widget_id).innerHTML = '';
                print_pid_value(data, 'duty_cycle', widget_id, 1, ' %');
              } else {
                document.getElementById('duration_time-' + widget_id).innerHTML = 'NULL';
                document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
              }

            } else if (data['held']) {
              document.getElementById('text-pid-state-' + widget_id).innerHTML = '({{_('Held')}})';
              document.getElementById('container-pid-' + widget_id).className = "pause-background";
              document.getElementById('button-activate-' + widget_id).style.display = "none";
              document.getElementById('button-deactivate-' + widget_id).style.display = "block";
              document.getElementById('button-pause-' + widget_id).style.display = "none";
              document.getElementById('button-resume-' + widget_id).style.display = "block";
              document.getElementById('button-hold-' + widget_id).style.display = "none";
              print_pid_value(data, 'setpoint', widget_id, decimal_places, ' ' + units);
              document.getElementById('setpoint-timestamp-' + widget_id).innerHTML = 'HELD';
              print_pid_value(data, 'actual', widget_id, decimal_places, ' ' + units);
              print_pid_value(data, 'pid_p_value', widget_id, 1, '');
              print_pid_value(data, 'pid_i_value', widget_id, 1, '');
              print_pid_value(data, 'pid_d_value', widget_id, 1, '');
              print_pid_value(data, 'pid_pid_value', widget_id, 1, '');

              {#Find which PID output is more recent, seconds on or duty cycle#}
              if (data['duration_time'][1] !== null && data['duty_cycle'][1] !== null) {
                if (data['duration_time'][0] > data['duty_cycle'][0]) {
                  document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
                  print_pid_value(data, 'duration_time', widget_id, 1, ' sec');
                } else {
                  document.getElementById('duration_time-' + widget_id).innerHTML = '';
                  print_pid_value(data, 'duty_cycle', widget_id, 1, ' %');
                }
              } else if (data['duration_time'][1] !== null) {
                document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
                print_pid_value(data, 'duration_time', widget_id, 1, ' sec');
              } else if (data['duty_cycle'][1] !== null) {
                document.getElementById('duration_time-' + widget_id).innerHTML = '';
                print_pid_value(data, 'duty_cycle', widget_id, 1, ' %');
              } else {
                document.getElementById('duration_time-' + widget_id).innerHTML = 'NULL';
                document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
              }
            } else {
              document.getElementById('text-pid-state-' + widget_id).innerHTML = '({{_('Active')}})';
              document.getElementById('container-pid-' + widget_id).className = "active-background";
              document.getElementById('button-activate-' + widget_id).style.display = "none";
              document.getElementById('button-deactivate-' + widget_id).style.display = "block";
              document.getElementById('button-pause-' + widget_id).style.display = "block";
              document.getElementById('button-resume-' + widget_id).style.display = "none";
              document.getElementById('button-hold-' + widget_id).style.display = "block";
              print_pid_value(data, 'setpoint', widget_id, decimal_places, ' ' + units);
              print_pid_value(data, 'actual', widget_id, decimal_places, ' ' + units);
              print_pid_value(data, 'pid_p_value', widget_id, 1, '');
              print_pid_value(data, 'pid_i_value', widget_id, 1, '');
              print_pid_value(data, 'pid_d_value', widget_id, 1, '');
              print_pid_value(data, 'pid_pid_value', widget_id, 1, '');

              {#Find which PID output is more recent, seconds on or duty cycle#}
              if (data['duration_time'][1] !== null && data['duty_cycle'][1] !== null) {
                if (data['duration_time'][0] > data['duty_cycle'][0]) {
                  document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
                  print_pid_value(data, 'duration_time', widget_id, 1, ' sec');
                } else {
                  document.getElementById('duration_time-' + widget_id).innerHTML = '';
                  print_pid_value(data, 'duty_cycle', widget_id, 1, ' %');
                }
              } else if (data['duration_time'][1] !== null) {
                document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
                print_pid_value(data, 'duration_time', widget_id, 1, ' sec');
              } else if (data['duty_cycle'][1] !== null) {
                document.getElementById('duration_time-' + widget_id).innerHTML = '';
                print_pid_value(data, 'duty_cycle', widget_id, 1, ' %');
              } else {
                document.getElementById('duration_time-' + widget_id).innerHTML = 'NULL';
                document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
              }
            }
          } else {
            document.getElementById('text-pid-state-' + widget_id).innerHTML = '({{_('Inactive')}})';
            document.getElementById('container-pid-' + widget_id).className = "inactive-background";
            document.getElementById('button-activate-' + widget_id).style.display = "block";
            document.getElementById('button-deactivate-' + widget_id).style.display = "none";
            document.getElementById('button-pause-' + widget_id).style.display = "none";
            document.getElementById('button-resume-' + widget_id).style.display = "none";
            document.getElementById('button-hold-' + widget_id).style.display = "none";
            document.getElementById('setpoint-' + widget_id).innerHTML = 'NONE';
            document.getElementById('setpoint-timestamp-' + widget_id).innerHTML = 'INACTIVE';
            document.getElementById('pid_p_value-' + widget_id).innerHTML = '0';
            document.getElementById('pid_i_value-' + widget_id).innerHTML = '0';
            document.getElementById('pid_d_value-' + widget_id).innerHTML = '0';
            document.getElementById('pid_pid_value-' + widget_id).innerHTML = '0';
            document.getElementById('duration_time-' + widget_id).innerHTML = '0';
            document.getElementById('duty_cycle-' + widget_id).innerHTML = '';
            print_pid_value(data, 'actual', widget_id, decimal_places, ' ' + units);
          }
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        print_pid_error(widget_id);
      }
    });
  }

  // Repeat function for getLastDataPID()
  function repeatLastDataPID(widget_id, dev_id, period_sec, max_measure_age_sec, decimal_places, units) {
    setInterval(function () {
      getLastDataPID(widget_id, dev_id, max_measure_age_sec, decimal_places, units)
    }, period_sec * 1000);
  }
""",

    'widget_dashboard_js_ready': """
  $('.activate_pid').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to Activate PID');
    {% endif %}
    modPID(btn_val);
  });
  $('.deactivate_pid').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to Deactivate PID');
    {% endif %}
    modPID(btn_val);
  });
  $('.pause_pid').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to Pause PID');
    {% endif %}
    modPID(btn_val);
  });
  $('.hold_pid').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to Hold PID');
    {% endif %}
    modPID(btn_val);
  });
  $('.resume_pid').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to Resume PID');
    {% endif %}
    modPID(btn_val);
  });
  $('.set_setpoint').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    const setpoint = $('#setpoint_pid_' + id).val();
    if(setpoint) {
      {% if not misc.hide_alert_info %}
      toastr['info']('Command sent to set PID setpoint');
      {% endif %}
      modPID(btn_val + setpoint);
    }
  });
""",

    'widget_dashboard_js_ready_end': """
  {%- for each_pid in pid if each_pid.unique_id == widget_options['pid'] and each_pid.measurement.split(',')|length == 2 %}

  getLastDataPID('{{each_widget.unique_id}}', '{{widget_options['pid']}}', {{widget_options['max_measure_age']}}, {{widget_options['decimal_places']}}, '

      {%- set measurement_id = each_pid.measurement.split(',')[1] -%}
      {%- set device_measurement = table_device_measurements.query.filter(table_device_measurements.unique_id == measurement_id).first() -%}

      {%- if device_measurement -%}
        {%- if device_measurement.conversion_id -%}
          {{dict_units[table_conversion.query.filter(table_conversion.unique_id == device_measurement.conversion_id).first().convert_unit_to]['unit']}}
        {%- elif device_measurement.rescaled_unit -%}
          {{dict_units[device_measurement.rescaled_unit]['unit']}}
        {%- else -%}
          {{dict_units[device_measurement.unit]['unit']}}
        {%- endif -%}
      {%- endif -%}
      ');

  repeatLastDataPID('{{each_widget.unique_id}}', '{{widget_options['pid']}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}}, {{widget_options['decimal_places']}}, '

      {%- set measurement_id = each_pid.measurement.split(',')[1] -%}
      {%- set device_measurement = table_device_measurements.query.filter(table_device_measurements.unique_id == measurement_id).first() -%}

      {%- if device_measurement -%}
        {%- if device_measurement.conversion_id -%}
          {{dict_units[table_conversion.query.filter(table_conversion.unique_id == device_measurement.conversion_id).first().convert_unit_to]['unit']}}
        {%- elif device_measurement.rescaled_unit -%}
          {{dict_units[device_measurement.rescaled_unit]['unit']}}
        {%- else -%}
          {{dict_units[device_measurement.unit]['unit']}}
        {%- endif -%}
      {%- endif -%}
      ');

    {% else %}

    getLastDataPID('{{each_widget.unique_id}}', '{{widget_options['pid']}}', {{widget_options['max_measure_age']}}, {{widget_options['decimal_places']}}, '');
  {%- endfor -%}
"""
}

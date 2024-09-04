import logging

from flask_babel import lazy_gettext

from mycodo.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_measurement_multi',
    'widget_name': 'Measurement (2 Values)',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays two measurement values and timestamps.',

    'widget_width': 5,
    'widget_height': 8,

    'custom_options': [
        {
            'id': 'measurement_1',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'Output_Channels_Measurements',
                'PID'
            ],
            'name': lazy_gettext('Measurement 1'),
            'phrase': lazy_gettext('Select the first measurement to display')
        },
        {
            'id': 'measurement_1_max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Max Age 1'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The maximum age of the first measurement to use')
        },
        {
            'id': 'decimal_places_1',
            'type': 'integer',
            'default_value': 2,
            'name': 'Decimal Places 1',
            'phrase': 'The number of measurement decimal places for first measurement'
        },
        {
            'id': 'measurement_2',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'Output_Channels_Measurements',
                'PID'
            ],
            'name': lazy_gettext('Measurement 2'),
            'phrase': lazy_gettext('Select the second measurement to display')
        },
        {
            'id': 'measurement_2_max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Max Age 2'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The maximum age of the second measurement to use')
        },
        {
            'id': 'decimal_places_2',
            'type': 'integer',
            'default_value': 2,
            'name': 'Decimal Places 2',
            'phrase': 'The number of measurement decimal places for second measurement'
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
            'default_value': 1.5,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Value Font Size (em)',
            'phrase': 'The font size of the measurement'
        },
        {
            'id': 'font_em_unit',
            'type': 'float',
            'default_value': 1.5,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Unit Font Size (em)',
            'phrase': 'The font size of the unit'
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

    'widget_dashboard_title_bar': """<span class="widget-title-bar" style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    'widget_dashboard_body': """
  {%- set device_id_1 = widget_options['measurement_1'].split(",")[0] -%}
  {%- set measurement_id_1 = widget_options['measurement_1'].split(",")[1] -%}
  {%- set device_id_2 = widget_options['measurement_2'].split(",")[0] -%}
  {%- set measurement_id_2 = widget_options['measurement_2'].split(",")[1] -%}

  <div style="text-align: center">

  <!-- Measurement 1 -->
  <div>
  {%- for each_input in input if each_input.unique_id == device_id_1 and measurement_id_1 in device_measurements_dict -%}
    <span class="widget-measurement-value" style="font-size: {{widget_options['font_em_value']}}em" id="1-value-{{each_widget.unique_id}}"></span><span class="widget-measurement-unit" style="font-size: {{widget_options['font_em_unit']}}em">
        {%- if dict_measure_units[measurement_id_1] in dict_units and
               dict_units[dict_measure_units[measurement_id_1]]['unit'] and
               widget_options['enable_unit'] -%}
          {{' ' + dict_units[dict_measure_units[measurement_id_1]]['unit']}}
        {%- endif -%}
    </span>
    <br/>
    {%- if widget_options['enable_name'] -%}
      {{each_input.name + ' '}}
    {%- endif -%}
    {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
      {{'('}}
    {%- endif -%}
    {%- if not device_measurements_dict[measurement_id_1].single_channel and widget_options['enable_channel'] -%}
      {{'CH' + (device_measurements_dict[measurement_id_1].channel|int)|string}}
    {%- endif -%}
    {%- if widget_options['enable_channel'] and widget_options['enable_measurement'] -%}
      {{', '}}
    {%- endif -%}
    {%- if widget_options['enable_measurement'] and device_measurements_dict[measurement_id_1].measurement -%}
      {{dict_measurements[device_measurements_dict[measurement_id_1].measurement]['name']}}
    {%- endif -%}
    {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
      {{')'}}
    {%- endif -%}
  {%- endfor -%}
  </div>

  <!-- Measurement 2 -->
  <div>
  {%- for each_input in input if each_input.unique_id == device_id_2 and measurement_id_2 in device_measurements_dict -%}
    <span class="widget-measurement-value" style="font-size: {{widget_options['font_em_value']}}em" id="2-value-{{each_widget.unique_id}}"></span><span class="widget-measurement-unit" style="font-size: {{widget_options['font_em_unit']}}em">
        {%- if dict_measure_units[measurement_id_2] in dict_units and
               dict_units[dict_measure_units[measurement_id_2]]['unit'] and
               widget_options['enable_unit'] -%}
          {{' ' + dict_units[dict_measure_units[measurement_id_2]]['unit']}}
        {%- endif -%}
    </span>
    <br/>
    {%- if widget_options['enable_name'] -%}
      {{each_input.name + ' '}}
    {%- endif -%}
    {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
      {{'('}}
    {%- endif -%}
    {%- if not device_measurements_dict[measurement_id_2].single_channel and widget_options['enable_channel'] -%}
      {{'CH' + (device_measurements_dict[measurement_id_2].channel|int)|string}}
    {%- endif -%}
    {%- if widget_options['enable_channel'] and widget_options['enable_measurement'] -%}
      {{', '}}
    {%- endif -%}
    {%- if widget_options['enable_measurement'] and device_measurements_dict[measurement_id_2].measurement -%}
      {{dict_measurements[device_measurements_dict[measurement_id_2].measurement]['name']}}
    {%- endif -%}
    {%- if widget_options['enable_channel'] or widget_options['enable_measurement'] -%}
      {{')'}}
    {%- endif -%}
  {%- endfor -%}
  </div>

  <div>
    {%- if widget_options['enable_timestamp'] and measurement_id_1 in last_measure_dict -%}
      <span style="font-size: {{widget_options['font_em_timestamp']}}em" id="1-timestamp-{{each_widget.unique_id}}">{{last_measure_dict[measurement_id_1].timestamp.strftime('%Y-%m-%d %H:%M:%S')}}</span>
    {%- endif -%}
  </div>
  <div>
    {%- if widget_options['enable_timestamp'] and measurement_id_2 in last_measure_dict -%}
      <span style="font-size: {{widget_options['font_em_timestamp']}}em" id="2-timestamp-{{each_widget.unique_id}}">{{last_measure_dict[measurement_id_2].timestamp.strftime('%Y-%m-%d %H:%M:%S')}}</span>
    {%- endif -%}
  </div>

  </div>
  """,

    'widget_dashboard_js': """
  // Retrieve the latest/last measurement for Measurement widget
  function getLastDataMeasurement_multi2(measurement_num,
                       widget_id,
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
          if (document.getElementById(measurement_num + '-value-' + widget_id)) {
            document.getElementById(measurement_num + '-value-' + widget_id).innerHTML = 'NO DATA';
          }
          if (document.getElementById(measurement_num + '-timestamp-' + widget_id)) {
            document.getElementById(measurement_num + '-timestamp-' + widget_id).innerHTML = 'MAX AGE EXCEEDED';
          }
        }
        else {
          const formattedTime = epoch_to_timestamp(data[0] * 1000);
          const measurement = data[1];
          if (document.getElementById(measurement_num + '-value-' + widget_id)) {
            document.getElementById(measurement_num + '-value-' + widget_id).innerHTML = measurement.toFixed(decimal_places);
          }
          if (document.getElementById(measurement_num + '-timestamp-' + widget_id)) {
            document.getElementById(measurement_num + '-timestamp-' + widget_id).innerHTML = formattedTime;
          }
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        if (document.getElementById(measurement_num + '-value-' + widget_id)) {
          document.getElementById(measurement_num + '-value-' + widget_id).innerHTML = 'NO DATA';
        }
        if (document.getElementById(measurement_num + '-timestamp-' + widget_id)) {
          document.getElementById(measurement_num + '-timestamp-' + widget_id).innerHTML = '{{_('Error')}}';
        }
      }
    });
  }

  // Repeat function for getLastData()
  function repeatLastDataMeasurement_multi2(measurement_num,
                          widget_id,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec,
                          decimal_places) {
    setInterval(function () {
      getLastDataMeasurement_multi2(measurement_num,
                  widget_id,
                  dev_id,
                  measure_type,
                  measurement_id,
                  max_measure_age_sec,
                  decimal_places)
    }, period_sec * 1000);
  }
""",

    'widget_dashboard_js_ready': """<!-- No JS ready content -->""",

    'widget_dashboard_js_ready_end': """
  {%- set device_id_1 = widget_options['measurement_1'].split(",")[0] -%}
  {%- set measurement_id_1 = widget_options['measurement_1'].split(",")[1] -%}
  {%- set device_id_2 = widget_options['measurement_2'].split(",")[0] -%}
  {%- set measurement_id_2 = widget_options['measurement_2'].split(",")[1] -%}

  {% for each_input in input %}
    {% if each_input.unique_id == device_id_1 %}
  getLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_input.unique_id}}', 'input', '{{measurement_id_1}}', {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
  repeatLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_input.unique_id}}', 'input', '{{measurement_id_1}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
    {%- endif -%}

    {% if each_input.unique_id == device_id_2 %}
  getLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_input.unique_id}}', 'input', '{{measurement_id_2}}', {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
  repeatLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_input.unique_id}}', 'input', '{{measurement_id_2}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
    {% endif %}
  {%- endfor -%}

  {% for each_function in function %}
    {% if each_function.unique_id == device_id_1 %}
  getLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_function.unique_id}}', 'function', '{{measurement_id_1}}', {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
  repeatLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_function.unique_id}}', 'function', '{{measurement_id_1}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
    {% endif %}

    {% if each_function.unique_id == device_id_2 %}
  getLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_function.unique_id}}', 'function', '{{measurement_id_2}}', {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
  repeatLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_function.unique_id}}', 'function', '{{measurement_id_2}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
    {% endif %}
  {%- endfor -%}

  {% for each_output in output %}
    {% if each_output.unique_id == device_id_1 %}
  getLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_output.unique_id}}', 'output', '{{measurement_id_1}}', {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
  repeatLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_output.unique_id}}', 'output', '{{measurement_id_1}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
    {% endif %}

    {% if each_output.unique_id == device_id_2 %}
  getLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_output.unique_id}}', 'output', '{{measurement_id_2}}', {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
  repeatLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_output.unique_id}}', 'output', '{{measurement_id_2}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
    {% endif %}
  {%- endfor -%}

  {% for each_pid in pid %}
    {% if each_pid.unique_id == device_id_1 %}
  getLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_pid.unique_id}}', 'pid', '{{measurement_id_1}}', {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
  repeatLastDataMeasurement_multi2('1', '{{each_widget.unique_id}}', '{{each_pid.unique_id}}', 'pid', '{{measurement_id_1}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_1_max_age']}}, {{widget_options['decimal_places_1']}});
    {% endif %}

    {% if each_pid.unique_id == device_id_2 %}
  getLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_pid.unique_id}}', 'pid', '{{measurement_id_2}}', {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
  repeatLastDataMeasurement_multi2('2', '{{each_widget.unique_id}}', '{{each_pid.unique_id}}', 'pid', '{{measurement_id_2}}', {{widget_options['refresh_seconds']}}, {{widget_options['measurement_2_max_age']}}, {{widget_options['decimal_places_2']}});
    {% endif %}
  {%- endfor -%}
"""
}

# coding=utf-8
from flask_restx import fields

from mycodo.mycodo_flask.api import api

function_fields = api.model('Function Device Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name': fields.String,
    'device': fields.String,
    'is_activated': fields.Boolean,
    'log_level_debug': fields.Boolean,
    'custom_options': fields.String
})

function_channel_fields = api.model('Function Channel Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'function_id': fields.String,
    'channel': fields.Integer,
    'name': fields.String,
    'custom_options': fields.String,
})

conversion_fields = api.model('Measurement Conversion Fields', {
    'id': fields.Integer,
    'unique_id': fields.String
})

device_measurement_fields = api.model('Device Measurement Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name': fields.String,
    'device_type': fields.String,
    'device_id': fields.String,
    'is_enabled': fields.Boolean,
    'measurement': fields.String,
    'measurement_type': fields.String,
    'unit': fields.String,
    'channel': fields.Integer,
    'invert_scale': fields.Boolean,
    'rescaled_measurement': fields.String,
    'rescaled_unit': fields.String,
    'rescale_method': fields.String,
    'rescale_equation': fields.String,
    'scale_from_min': fields.Float,
    'scale_from_max': fields.Float,
    'scale_to_min': fields.Float,
    'scale_to_max': fields.Float,
    'conversion': fields.Nested(conversion_fields)
})

input_fields = api.model('Input Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name': fields.String,
    'position_y': fields.Integer,
    'is_activated': fields.Boolean,
    'log_level_debug': fields.Boolean,
    'is_preset': fields.Boolean,
    'preset_name': fields.String,
    'device': fields.String,
    'interface': fields.String,
    'period': fields.Float,
    'start_offset': fields.Float,
    'power_output_id': fields.String,
    'resolution': fields.Integer,
    'resolution_2': fields.Integer,
    'sensitivity': fields.Integer,
    'thermocouple_type': fields.String,
    'ref_ohm': fields.Integer,
    'calibrate_sensor_measure': fields.String,
    'location': fields.String,
    'gpio_location': fields.Integer,
    'i2c_location': fields.String,
    'i2c_bus': fields.Integer,
    'ftdi_location': fields.String,
    'uart_location': fields.String,
    'baud_rate': fields.Integer,
    'pin_clock': fields.Integer,
    'pin_cs': fields.Integer,
    'pin_mosi': fields.Integer,
    'pin_miso': fields.Integer,
    'bt_adapter': fields.String,
    'switch_edge': fields.String,
    'switch_bouncetime': fields.Integer,
    'switch_reset_period': fields.Integer,
    'pre_output_id': fields.String,
    'pre_output_duration': fields.Float,
    'pre_output_during_measure': fields.Boolean,
    'sht_voltage': fields.String,
    'adc_gain': fields.Integer,
    'adc_resolution': fields.Integer,
    'adc_sample_speed': fields.String,
    'cmd_command': fields.String,
    'weighting': fields.Float,
    'rpm_pulses_per_rev': fields.Float,
    'sample_time': fields.Float,
    'port': fields.Integer,
    'times_check': fields.Integer,
    'deadline': fields.Integer,
    'datetime': fields.DateTime,
    'custom_options': fields.String
})

input_channel_fields = api.model('Function Channel Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'input_id': fields.String,
    'channel': fields.Integer,
    'name': fields.String,
    'custom_options': fields.String,
})

measurement_fields = api.model('Measurement Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name_safe': fields.String,
    'name': fields.String,
    'units': fields.String
})

output_fields = api.model('Output Device Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'output_type': fields.String,
    'name': fields.String,
    'log_level_debug': fields.Boolean,
    'interface': fields.String,
    'location': fields.String,
    'i2c_location': fields.String,
    'i2c_bus': fields.Integer,
    'ftdi_location': fields.String,
    'uart_location': fields.String,
    'baud_rate': fields.Integer,
    'custom_options': fields.String
})

output_channel_fields = api.model('Output Channel Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'output_id': fields.String,
    'channel': fields.Integer,
    'name': fields.String,
    'custom_options': fields.String,
})

pid_fields = api.model('PID Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name': fields.String,
    'is_activated': fields.Boolean,
    'is_held': fields.Boolean,
    'is_paused': fields.Boolean,
    'is_preset': fields.Boolean,
    'log_level_debug': fields.Boolean,
    'preset_name': fields.String,
    'period': fields.Float,
    'start_offset': fields.Float,
    'max_measure_age': fields.Float,
    'measurement': fields.String,
    'direction': fields.String,
    'setpoint': fields.Float,
    'band': fields.Float,
    'p': fields.Float,
    'i': fields.Float,
    'd': fields.Float,
    'integrator_min': fields.Float,
    'integrator_max': fields.Float,
    'raise_output_id': fields.String,
    'raise_min_duration': fields.Float,
    'raise_max_duration': fields.Float,
    'raise_min_off_duration': fields.Float,
    'lower_output_id': fields.String,
    'lower_min_duration': fields.Float,
    'lower_max_duration': fields.Float,
    'lower_min_off_duration': fields.Float,
    'store_lower_as_negative': fields.Boolean,
    'setpoint_tracking_type': fields.String,
    'setpoint_tracking_id': fields.String,
    'setpoint_tracking_max_age': fields.Float,
    'method_start_time': fields.String,
    'method_end_time': fields.String,
    'autotune_activated': fields.Boolean,
    'autotune_noiseband': fields.Float,
    'autotune_outstep': fields.Float
})

trigger_fields = api.model('Trigger Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'trigger_type': fields.String,
    'name': fields.String,
    'is_activated': fields.Boolean,
    'log_level_debug': fields.Boolean,
    'unique_id_1': fields.String,
    'unique_id_2': fields.String,
    'output_state': fields.String,
    'output_duration': fields.Float,
    'output_duty_cycle': fields.Float,
    'rise_or_set': fields.String,
    'latitude': fields.Float,
    'longitude': fields.Float,
    'zenith': fields.Float,
    'date_offset_days': fields.Integer,
    'time_offset_minutes': fields.Integer,
    'period': fields.Float,
    'timer_start_offset': fields.Integer,
    'timer_start_time': fields.String,
    'timer_end_time': fields.String,
    'program': fields.String,
    'word': fields.String,
    'method_start_time': fields.String,
    'method_end_time': fields.String,
    'trigger_actions_at_period': fields.Boolean,
    'trigger_actions_at_start': fields.Boolean,
    'measurement': fields.String,
    'edge_detected': fields.String,
})

unit_fields = api.model('Unit Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name_safe': fields.String,
    'name': fields.String,
    'unit': fields.String
})

user_fields = api.model('User Settings Fields', {
    "id": fields.Integer,
    "unique_id": fields.String,
    "name": fields.String,
    "email": fields.String,
    "role_id": fields.Integer,
    "theme": fields.String,
    "landing_page": fields.String,
    "index_page": fields.String,
    "language": fields.String
})

# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Measurement
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.databases.models.input import InputSchema
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.databases.models.measurement import MeasurementSchema
from mycodo.databases.models.measurement import UnitSchema
from mycodo.databases.models.output import OutputSchema
from mycodo.databases.models.pid import PIDSchema
from mycodo.databases.models.user import UserSchema
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_settings = Namespace('settings', description='Settings operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    500: 'Internal Server Error'
}

input_fields = ns_settings.model('Input Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name': fields.String,
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

input_list_fields = ns_settings.model('Input Settings Fields List', {
    'inputs': fields.List(fields.Nested(input_fields)),
})

device_measurement_fields = ns_settings.model('Device Measurement Settings Fields', {
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
    'scale_from_min': fields.Float,
    'scale_from_max': fields.Float,
    'scale_to_min': fields.Float,
    'scale_to_max': fields.Float,
    'conversion_id': fields.String,
})

device_measurement_list_fields = ns_settings.model('Device Measurement Settings Fields List', {
    'device measurements': fields.List(fields.Nested(device_measurement_fields)),
})

measurement_fields = ns_settings.model('Measurement Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name_safe': fields.String,
    'name': fields.String,
    'units': fields.String
})

measurement_list_fields = ns_settings.model('Measurement Settings Fields List', {
    'measurements': fields.List(fields.Nested(device_measurement_fields)),
})

output_fields = ns_settings.model('Output Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'output_type': fields.String,
    'output_mode': fields.String,
    'interface': fields.String,
    'location': fields.String,
    'i2c_bus': fields.Integer,
    'baud_rate': fields.Integer,
    'name': fields.String,
    'measurement': fields.String,
    'unit': fields.String,
    'conversion_id': fields.String,
    'channel': fields.Integer,
    'pin': fields.Integer,
    'on_state': fields.Boolean,
    'amps': fields.Float,
    'on_until': fields.DateTime,
    'off_until': fields.DateTime,
    'last_duration': fields.Float,
    'on_duration': fields.Boolean,
    'protocol': fields.Integer,
    'pulse_length': fields.Integer,
    'on_command': fields.String,
    'off_command': fields.String,
    'pwm_command': fields.String,
    'trigger_functions_at_start': fields.Boolean,
    'state_startup': fields.String,
    'startup_value': fields.Float,
    'state_shutdown': fields.String,
    'shutdown_value': fields.Float,
    'pwm_hertz': fields.Integer,
    'pwm_library': fields.String,
    'pwm_invert_signal': fields.Boolean,
    'flow_rate': fields.Float
})

output_list_fields = ns_settings.model('Output Settings Fields List', {
    'outputs': fields.List(fields.Nested(output_fields)),
})

pid_fields = ns_settings.model('PID Settings Fields', {
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

pid_list_fields = ns_settings.model('PID Settings Fields List', {
    'pids': fields.List(fields.Nested(pid_fields)),
})

unit_fields = ns_settings.model('User Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name_safe': fields.String,
    'name': fields.String,
    'unit': fields.String
})

unit_list_fields = ns_settings.model('User Settings Fields List', {
    'units': fields.List(fields.Nested(unit_fields)),
})

user_fields = ns_settings.model('User Settings Fields', {
    "id": fields.Integer,
    "unique_id": fields.String,
    "name": fields.String,
    "email": fields.String,
    "role_id": fields.Integer,
    "theme": fields.String,
    "landing_page": fields.String,
    "language": fields.String
})

user_list_fields = ns_settings.model('User Settings Fields List', {
    'users': fields.List(fields.Nested(user_fields)),
})


@ns_settings.route('/inputs/')
@ns_settings.doc(security='apikey', responses=default_responses)
class InputDump(Resource):
    """Interacts with Input settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(input_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all input settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(InputSchema, Input)
            if list_data:
                return {'inputs': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/inputs/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the input'}
)
class InputSingle(Resource):
    """Interacts with Input settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(input_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an input"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(InputSchema, Input, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/device_measurements/')
@ns_settings.doc(security='apikey', responses=default_responses)
class Measurements(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(device_measurement_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all device measurement settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(
                DeviceMeasurementsSchema, DeviceMeasurements)
            if list_data:
                return {'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/device_measurements/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the measurement'}
)
class MeasurementsUniqueID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(device_measurement_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a device measurement with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(
                DeviceMeasurementsSchema,
                DeviceMeasurements,
                unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/device_measurements/by_device_id/<string:device_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'device_id': 'The unique ID of the controller (Input, Math, '
                         'etc.) for which the measurement belongs.'}
)
class MeasurementsDeviceID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(device_measurement_list_fields)
    @flask_login.login_required
    def get(self, device_id):
        """Show the settings for all device measurements with the device_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            measure_schema = DeviceMeasurementsSchema()
            list_data = return_list_of_dictionaries(
                measure_schema.dump(
                    DeviceMeasurements.query.filter_by(
                        device_id=device_id).all(), many=True))
            if list_data:
                return {'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/measurements/')
@ns_settings.doc(security='apikey', responses=default_responses)
class Measurements(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(measurement_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all measurement settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(MeasurementSchema, Measurement)
            if list_data:
                return {'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/measurements/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the measurement'}
)
class MeasurementsUniqueID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(measurement_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a measurement with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(
                MeasurementSchema, Measurement, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/outputs/')
@ns_settings.doc(security='apikey', responses=default_responses)
class OutputDump(Resource):
    """Interacts with output settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(output_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all output settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(OutputSchema, Output)
            if list_data:
                return {'outputs': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/outputs/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the output'}
)
class OutputSingle(Resource):
    """Interacts with Output settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(output_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an output with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(OutputSchema, Output, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/pids/')
@ns_settings.doc(security='apikey', responses=default_responses)
class PIDDump(Resource):
    """Interacts with PID settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(pid_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all pid settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(PIDSchema, PID)
            if list_data:
                return {'pids': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/pids/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the pid'}
)
class PIDSingle(Resource):
    """Interacts with PID settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(pid_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a pid with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(PIDSchema, PID, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/units/')
@ns_settings.doc(security='apikey', responses=default_responses)
class UnitDump(Resource):
    """Interacts with Unit settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(unit_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all unit settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(UnitSchema, Unit)
            if list_data:
                return {'units': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/units/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the unit'}
)
class UnitSingle(Resource):
    """Interacts with unit settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(unit_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a unit with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(UnitSchema, Unit, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/users/')
@ns_settings.doc(security='apikey', responses=default_responses)
class UserDump(Resource):
    """Interacts with User settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(user_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all user settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(UserSchema, User)
            if list_data:
                return {'users': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/users/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the user'}
)
class UserSingle(Resource):
    """Interacts with user settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(user_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a user with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        try:
            dict_data = get_from_db(UserSchema, User, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

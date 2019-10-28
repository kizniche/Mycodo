# coding=utf-8
import logging
import traceback

import flask_login
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields

from mycodo.databases.models import Input
from mycodo.databases.models.input import InputSchema
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_input = Namespace('inputs', description='Input operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    460: 'Fail',
    461: 'Unknown Response'
}

input_fields = ns_input.model('Input Settings Fields', {
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

input_list_fields = ns_input.model('Input Settings Fields List', {
    'inputs': fields.List(fields.Nested(input_fields)),
})


@ns_input.route('/')
@ns_input.doc(security='apikey', responses=default_responses)
class InputDump(Resource):
    """Interacts with Input settings in the SQL database"""

    @ns_input.marshal_with(input_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all input settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            input_schema = InputSchema()
            return {'inputs': input_schema.dump(
                Input.query.all(), many=True)[0]}, 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_input.route('/by_unique_id/<string:unique_id>')
@ns_input.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the input'}
)
class InputSingle(Resource):
    """Interacts with Input settings in the SQL database"""

    @ns_input.marshal_with(input_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an input"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            input_schema = InputSchema()
            input_ = Input.query.filter_by(unique_id=unique_id).first()
            return input_schema.dump(input_)[0], 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460

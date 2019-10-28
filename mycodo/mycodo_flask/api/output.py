# coding=utf-8
import logging
import traceback

import flask_login
from flask import request
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields

from mycodo.databases.models import Output
from mycodo.databases.models.output import OutputSchema
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_output = Namespace('outputs', description='Output operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    460: 'Fail',
    461: 'Unknown Response'
}


output_fields = ns_output.model('Output Settings Fields', {
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

output_list_fields = ns_output.model('Output Settings Fields List', {
    'outputs': fields.List(fields.Nested(output_fields)),
})

set_state_fields = ns_output.model('OutputSetState', {
    'duration': fields.Float(
        description='The duration to keep the output on, in seconds',
        required=False,
        example=10.0,
        exclusiveMin=0)
})

def return_handler(return_):
    if return_ is None:
        return 'Success', 200
    elif return_[0] in [0, 'success']:
        return 'Success: {}'.format(return_[1]), 200
    elif return_[0] in [1, 'error']:
        return 'Fail: {}'.format(return_[1]), 460
    else:
        return '', 461


@ns_output.route('/')
@ns_output.doc(security='apikey', responses=default_responses)
class OutputDump(Resource):
    """Interacts with output settings in the SQL database"""

    @ns_output.marshal_with(output_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all output settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            output_schema = OutputSchema()
            return {'outputs': output_schema.dump(
                Output.query.all(), many=True)[0]}, 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_output.route('/by_unique_id/<string:unique_id>')
@ns_output.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the output'}
)
class OutputSingle(Resource):
    """Interacts with Output settings in the SQL database"""

    @ns_output.marshal_with(output_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an output with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            output_schema = OutputSchema()
            output_ = Output.query.filter_by(unique_id=unique_id).first()
            return output_schema.dump(output_)[0], 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_output.route('/set_pwm/<string:unique_id>/<duty_cycle>')
@ns_output.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the output.',
        'duty_cycle': 'The duty cycle (percent, %) to set.'
    }
)
class OutputPWM(Resource):
    """Manipulates a PWM Output"""

    @flask_login.login_required
    def post(self, unique_id, duty_cycle):
        """Set the Duty Cycle of a PWM output"""
        if not utils_general.user_has_permission('edit_controllers'):
            return 'You do not have permission to access this.', 401

        try:
            duty_cycle = float(duty_cycle)
        except:
            return 'Fail: duty_cycle does not represent float value', 460

        if duty_cycle < 0 or duty_cycle > 100:
            return 'Fail. Required: 0 <= duty_cycle <= 100.', 460

        try:
            control = DaemonControl()
            return_ = control.output_on(unique_id, duty_cycle=float(duty_cycle))
            return return_handler(return_)
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_output.route('/set_state/<string:unique_id>/<string:state>')
@ns_output.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the output.',
        'state': 'The state to set ("on" or "off").',
        'duration': 'The duration (seconds) to keep the output on before turning off.'
    }
)
class OutputState(Resource):
    """Manipulates an Output"""

    @ns_output.expect(set_state_fields)
    @flask_login.login_required
    def post(self, unique_id, state):
        """Change the state of an on/off output"""
        if not utils_general.user_has_permission('edit_controllers'):
            return 'You do not have permission to access this.', 401
        try:
            duration = float(request.args.get("duration"))
        except:
            duration = 0

        try:
            control = DaemonControl()
            return_ = control.output_on_off(
                unique_id, state, amount=float(duration))
            return return_handler(return_)
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460

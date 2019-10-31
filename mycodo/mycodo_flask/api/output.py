# coding=utf-8
import logging
import traceback

import flask_login
from flask import request
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort
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
    422: 'Unprocessable Entity',
    429: 'Too Many Requests',
    460: 'Fail',
    500: 'Internal Server Error'
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
        return '', 500


@ns_output.route('/')
@ns_output.doc(security='apikey', responses=default_responses)
class OutputDump(Resource):
    """Interacts with output settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.marshal_with(output_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all output settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            output_schema = OutputSchema()
            output_data = output_schema.dump(
                Output.query.all(), many=True)
            if output_data:
                return {'outputs': output_data[0]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_output.route('/by_unique_id/<string:unique_id>')
@ns_output.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the output'}
)
class OutputSingle(Resource):
    """Interacts with Output settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.marshal_with(output_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an output with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            output_schema = OutputSchema()
            output_data = output_schema.dump(
                Output.query.filter_by(unique_id=unique_id).first())
            if output_data:
                return output_data[0], 200
        except Exception:
            abort(500, custom=traceback.format_exc())


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

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def post(self, unique_id, duty_cycle):
        """Set the Duty Cycle of a PWM output"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            duty_cycle = float(duty_cycle)
        except:
            abort(422, custom='duty_cycle does not represent float value')

        if duty_cycle < 0 or duty_cycle > 100:
            abort(422, custom='Required: 0 <= duty_cycle <= 100')

        try:
            control = DaemonControl()
            return_ = control.output_on(
                unique_id, duty_cycle=float(duty_cycle))
            return return_handler(return_)
        except Exception:
            abort(500, custom=traceback.format_exc())


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

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.expect(set_state_fields)
    @flask_login.login_required
    def post(self, unique_id, state):
        """Change the state of an on/off output"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        duration = request.args.get("duration")
        if duration is not None:
            try:
                duration = float(request.args.get("duration"))
            except:
                abort(422, custom='duration does not represent a number')
        else:
            duration = 0

        try:
            control = DaemonControl()
            return_ = control.output_on_off(
                unique_id, state, amount=float(duration))
            return return_handler(return_)
        except Exception:
            abort(500, custom=traceback.format_exc())

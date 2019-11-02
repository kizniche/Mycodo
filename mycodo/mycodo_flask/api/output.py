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

output_status_fields = ns_output.model('Output Status Fields', {
    'state': fields.String
})

output_set_fields = ns_output.model('Output Modulation Fields', {
    'state': fields.Boolean(
        description='Set a non-PWM output state to on (True) or off (False).',
        required=False),
    'duration': fields.Float(
        description='The duration to keep a non-PWM output on, in seconds.',
        required=False,
        example=10.0,
        exclusiveMin=0),
    'duty_cycle': fields.Float(
        description='The duty cycle to set a PWM output, in percent (%).',
        required=False,
        example=50.0,
        min=0)
})


def return_handler(return_):
    if return_ is None:
        return {'message': 'Success'}, 200
    elif return_[0] in [0, 'success']:
        return {'message': 'Success: {}'.format(return_[1])}, 200
    elif return_[0] in [1, 'error']:
        return {'message': 'Fail: {}'.format(return_[1])}, 460
    else:
        return '', 500


@ns_output.route('/<string:unique_id>')
@ns_output.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the output.'}
)
class Outputs(Resource):
    """Output status"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.marshal_with(output_status_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Get the state of an output"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            output_state = control.output_state(unique_id)
            return {'state': output_state}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.expect(output_set_fields)
    @flask_login.login_required
    def post(self, unique_id):
        """Change the state of an output"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        control = DaemonControl()

        state = None
        if 'state' in ns_output.payload:
            state = ns_output.payload["state"]
            if state is not None:
                try:
                    state = bool(state)
                except Exception:
                    abort(422, message='state must represent a bool value')

        duration = None
        if 'duration' in ns_output.payload:
            duration = ns_output.payload["duration"]
            if duration is not None:
                try:
                    duration = float(duration)
                except Exception:
                    abort(422, message='duration does not represent a number')
            else:
                duration = 0

        duty_cycle = None
        if 'duty_cycle' in ns_output.payload:
            duty_cycle = ns_output.payload["duty_cycle"]
            if duty_cycle is not None:
                try:
                    duty_cycle = float(duty_cycle)
                    if duty_cycle < 0 or duty_cycle > 100:
                        abort(422, message='Required: 0 <= duty_cycle <= 100')
                except Exception:
                    abort(422, message='duty_cycle does not represent float value')

        try:
            if state is not None and duration is not None:
                return_ = control.output_on_off(
                    unique_id, state, amount=duration)
            elif state is not None:
                return_ = control.output_on_off(unique_id, state)
            elif duty_cycle is not None:
                return_ = control.output_duty_cycle(
                    unique_id, duty_cycle=duty_cycle)
            else:
                return {'message': 'Insufficient payload'}, 460

            return return_handler(return_)
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

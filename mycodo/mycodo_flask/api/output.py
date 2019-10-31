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

ns_output = Namespace('output', description='Output operations')

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

set_state_fields = ns_output.model('Output Set State', {
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


@ns_output.route('/pwm/<string:unique_id>/<duty_cycle>')
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


@ns_output.route('/state/<string:unique_id>/<string:state>')
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


@ns_output.route('/status/<string:unique_id>')
@ns_output.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the output.'
    }
)
class OutputPWM(Resource):
    """Output status"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self, unique_id):
        """Activate a controller"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            output_state = control.output_state(unique_id)
            return {'state': output_state}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())

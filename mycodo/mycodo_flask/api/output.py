# coding=utf-8
import logging

import flask_login
from flask import request
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields

from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_output = Namespace('output', description='Output operations')


@ns_output.route('/set_pwm/<string:uuid>/<duty_cycle>')
@ns_output.doc(params={
    'uuid': 'The Unique ID.',
    'duty_cycle': 'The duty cycle (percent, %) to set the PWM output.'
})
class OutputPWM(Resource):
    """Manipulates a PWM Output"""
    @ns_output.doc(
        security='apikey',
        responses={
            200: 'Success',
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
            429: 'Too Many Requests',
            460: 'Fail',
            461: 'Unknown Response'
        }
    )
    @flask_login.login_required
    def post(self, uuid, duty_cycle):
        """Change the Duty Cycle of a PWM output with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401

        try:
            duty_cycle = float(duty_cycle)
        except:
            return 'Fail: duty_cycle does not represent float value', 460

        if duty_cycle < 0 or duty_cycle > 100:
            return 'Fail: duty_cycle must be >= 0 and <= 100.', 460

        control = DaemonControl()
        return_ = control.output_on(uuid, duty_cycle=float(duty_cycle))

        if return_ is None:
            return 'Success', 200
        elif return_[0] in [0, 'success']:
            return 'Success: {}'.format(return_[1]), 200
        elif return_[0] in [1, 'error']:
            return 'Fail: {}'.format(return_[1]), 460
        else:
            return '', 461


set_state_fields = ns_output.model('OutputSetState', {
    'duration': fields.Float(
        description='The duration to keep the output on, in seconds',
        required=False,
        example=10.0,
        exclusiveMin=0),
})


@ns_output.route('/set_state/<string:uuid>/<string:state>')
@ns_output.doc(
        security='apikey',
        responses={
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
            429: 'Too Many Requests',
            461: 'Unknown Response'
        }
    )
@ns_output.doc(params={
    'uuid': 'The Unique ID',
    'state': 'The state to set the output ("on" or "off")',
    'duration': 'The duration (seconds) to keep the output on.'
})
class OutputState(Resource):
    """Manipulates an Output"""
    @ns_output.expect(set_state_fields)
    @ns_output.doc(
        security='apikey',
        responses={
            200: 'Success',
            460: 'Fail'
        }
    )
    @flask_login.login_required
    def post(self, uuid, state):
        """Change the state of an on/off output with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            duration = float(request.args.get("duration"))
        except:
            duration = 0

        control = DaemonControl()
        return_ = control.output_on_off(uuid, state, amount=float(duration))

        if return_ is None:
            return 'Success', 200
        elif return_[0] in [0, 'success']:
            return 'Success: {}'.format(return_[1]), 200
        elif return_[0] in [1, 'error']:
            return 'Fail: {}'.format(return_[1]), 460
        else:
            return '', 461

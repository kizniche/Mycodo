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


@ns_output.route('/set_pwm/<string:uuid>/<float:duty_cycle>')
@ns_output.doc(params={
    'uuid': 'The Unique ID',
    'duty_cycle': 'The duty cycle, in percent (%)'
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
            460: 'Fail',
            461: 'Unknown Response'
        }
    )
    @flask_login.login_required
    def post(self, uuid, duty_cycle):
        """Change the state of a PWM output with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
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
    'state': fields.String(
        description='State to set the output',
        required=True,
        enum=['on', 'off']),
    'duration': fields.Float(
        description='The duration to keep the output on, in seconds',
        required=False,
        example=10.0,
        exclusiveMin=0)
})


@ns_output.route('/set_state/<string:uuid>')
@ns_output.doc(
        security='apikey',
        responses={
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
            461: 'Unknown Response'
        }
    )
@ns_output.doc(params={
    'uuid': 'The Unique ID',
    'state': 'State of output, "on" or "off"',
    'duration': 'A duration, in seconds.'
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
    def post(self, uuid):
        """Change the state of an on/off output with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        state = request.args.get("state")
        duration = request.args.get("duration")
        if duration is None:
            duration = 0
        control = DaemonControl()
        return_ = control.output_on_off(uuid, state, float(duration))
        if return_ is None:
            return 'Success', 200
        elif return_[0] in [0, 'success']:
            return 'Success: {}'.format(return_[1]), 200
        elif return_[0] in [1, 'error']:
            return 'Fail: {}'.format(return_[1]), 460
        else:
            return '', 461

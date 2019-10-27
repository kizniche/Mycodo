# coding=utf-8
import logging

import flask_login
from flask import request
from flask_restplus import Namespace
from flask_restplus import Resource

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
        if return_ == 'success':
            return 'Success', 200
        elif return_ == 'error':
            return 'Fail', 460
        else:
            return '', 461


@ns_output.route('/set_state/<string:uuid>/<string:state>')
@ns_output.doc(params={
    'uuid': 'The Unique ID',
    'state': 'State of output, "on" or "off"',
    'duration': 'A duration, in seconds.'
})
class OutputState(Resource):
    """Manipulates an Output"""
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
    def post(self, uuid, state):
        """Change the state of an on/off output with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        duration = request.args.get("duration")
        control = DaemonControl()
        return_ = control.output_on_off(uuid, state, float(duration))
        if return_ == 'success':
            return 'Success', 200
        elif return_ == 'error':
            return 'Fail', 460
        else:
            return '', 461

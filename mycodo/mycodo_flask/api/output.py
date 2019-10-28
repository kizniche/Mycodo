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

ns_output = Namespace('output', description='Output operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    460: 'Fail',
    461: 'Unknown Response'
}

def return_handler(return_):
    if return_ is None:
        return 'Success', 200
    elif return_[0] in [0, 'success']:
        return 'Success: {}'.format(return_[1]), 200
    elif return_[0] in [1, 'error']:
        return 'Fail: {}'.format(return_[1]), 460
    else:
        return '', 461


@ns_output.route('/settings/<string:unique_id>')
@ns_output.doc(security='apikey', responses=default_responses)
@ns_output.doc(params={'unique_id': 'The unique ID of the output'})
class OutputSingle(Resource):
    """Interacts with Output settings in the SQL database"""
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an output"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            output_schema = OutputSchema()
            output_ = Output.query.filter_by(unique_id=unique_id).first()
            return output_schema.dump(output_), 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_output.route('/settings_all')
@ns_output.doc(security='apikey', responses=default_responses)
class OutputDump(Resource):
    """Interacts with output settings in the SQL database"""
    @flask_login.login_required
    def get(self):
        """Show all output settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            output_schema = OutputSchema()
            return output_schema.dump(Output.query.all(), many=True)[0], 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_output.route('/set_pwm/<string:unique_id>/<duty_cycle>')
@ns_output.doc(security='apikey', responses=default_responses)
@ns_output.doc(params={
    'unique_id': 'The unique ID of the output.',
    'duty_cycle': 'The duty cycle (percent, %) to set.'})
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


set_state_fields = ns_output.model('OutputSetState', {
    'duration': fields.Float(
        description='The duration to keep the output on, in seconds',
        required=False,
        example=10.0,
        exclusiveMin=0)
})


@ns_output.route('/set_state/<string:unique_id>/<string:state>')
@ns_output.doc(security='apikey', responses=default_responses)
@ns_output.doc(params={
    'unique_id': 'The unique ID of the output.',
    'state': 'The state to set ("on" or "off").',
    'duration': 'The duration (seconds) to keep the output on before turning off.'})
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

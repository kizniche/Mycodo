# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Output
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.databases.models.output import OutputSchema
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.api.sql_schema_fields import device_measurement_fields
from mycodo.mycodo_flask.api.sql_schema_fields import output_fields
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils.utils_output import get_all_output_states

logger = logging.getLogger(__name__)

ns_output = api.namespace('outputs', description='Output operations')

output_states_fields = ns_output.model('Output States Fields', {
    'unique_id': fields.String,
    'state': fields.String
})

output_list_fields = api.model('Output Fields List', {
    'output settings': fields.List(fields.Nested(output_fields)),
    'output states': fields.Nested(output_states_fields)
})

output_unique_id_fields = ns_output.model('Output Status Fields', {
    'output settings': fields.Nested(output_fields),
    'output device measurements': fields.List(
        fields.Nested(device_measurement_fields)),
    'output state': fields.String
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


@ns_output.route('/')
@ns_output.doc(security='apikey', responses=default_responses)
class Inputs(Resource):
    """Output information"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.marshal_with(output_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all output settings and statuses"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(OutputSchema, Output)
            states = get_all_output_states()
            if list_data:
                return {'output settings': list_data,
                        'output states': states}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_output.route('/<string:unique_id>')
@ns_output.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the output.'}
)
class Outputs(Resource):
    """Output status"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.marshal_with(output_unique_id_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings and status for an output"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            dict_data = get_from_db(OutputSchema, Output, unique_id=unique_id)

            measure_schema = DeviceMeasurementsSchema()
            list_data = return_list_of_dictionaries(
                measure_schema.dump(
                    DeviceMeasurements.query.filter_by(
                        device_id=unique_id).all(), many=True))

            control = DaemonControl()
            output_state = control.output_state(unique_id)
            return {'output settings': dict_data,
                    'output device measurements': list_data,
                    'output state': output_state}, 200
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
                    abort(422,
                          message='duty_cycle does not represent float value')

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

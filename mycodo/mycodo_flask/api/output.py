# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models.output import OutputChannelSchema
from mycodo.databases.models.output import OutputSchema
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.api.sql_schema_fields import output_channel_fields
from mycodo.mycodo_flask.api.sql_schema_fields import output_fields
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils.utils_output import get_all_output_states

logger = logging.getLogger(__name__)

ns_output = api.namespace('outputs', description='Output operations')

MODEL_STATES_STATE = ns_output.model('states', {
    '*': fields.Wildcard(fields.String(description='on, off, or a duty cycle'),)
})
MODEL_STATES_CHAN = ns_output.model('channels', {
    '*': fields.Wildcard(fields.Nested(
        MODEL_STATES_STATE,
        description='Dictionary with channel as key and state data as value.'))
})
output_list_fields = ns_output.model('Output Fields List', {
    'output devices': fields.List(fields.Nested(output_fields)),
    'output channels': fields.List(fields.Nested(output_channel_fields)),
    'output states': fields.Nested(
        MODEL_STATES_CHAN,
        description='Dictionary with ID as key and channel state data as value.')
})

output_unique_id_fields = ns_output.model('Output Device Fields List', {
    'output device': fields.Nested(output_fields),
    'output device channels': fields.List(fields.Nested(output_channel_fields)),
    'output device channel states': fields.Nested(
        MODEL_STATES_STATE,
        description='Dictionary with channel as key and state data as value.')
})

output_set_fields = ns_output.model('Output Modulation Fields', {
    'state': fields.Boolean(
        description='Set a non-PWM output state to on (True) or off (False).',
        required=False),
    'channel': fields.Float(
        description='The output channel to modulate.',
        required=True,
        example=0,
        min=0),
    'duration': fields.Float(
        description='The duration to keep a non-PWM output on, in seconds.',
        required=False,
        example=10.0,
        exclusiveMin=0),
    'duty_cycle': fields.Float(
        description='The duty cycle to set a PWM output, in percent (%).',
        required=False,
        example=50.0,
        min=0),
    'volume': fields.Float(
        description='The volume to send to an output.',
        required=False,
        example=35.0,
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
    """Output information."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.marshal_with(output_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all output settings and statuses."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(OutputSchema, Output)
            list_channels = get_from_db(OutputChannelSchema, OutputChannel)
            states = get_all_output_states()

            # Change integer channel keys to strings (flask-restx limitation?)
            new_state_dict = {}
            for each_id in states:
                new_state_dict[each_id] = {}
                for each_channel in states[each_id]:
                    new_state_dict[each_id][str(each_channel)] = states[each_id][each_channel]

            if list_data:
                return {'output devices': list_data,
                        'output channels': list_channels,
                        'output states': new_state_dict}, 200
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
    """Output status."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.marshal_with(output_unique_id_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings and status for an output."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            list_data = get_from_db(OutputSchema, Output, unique_id=unique_id)

            output_channel_schema = OutputChannelSchema()
            list_channels = return_list_of_dictionaries(
                output_channel_schema.dump(
                    OutputChannel.query.filter_by(
                        output_id=unique_id).all(), many=True))

            states = get_all_output_states()

            # Change integer channel keys to strings (flask-restx limitation?)
            new_state_dict = {}
            for each_channel in states[unique_id]:
                new_state_dict[str(each_channel)] = states[unique_id][each_channel]

            return {'output device': list_data,
                    'output device channels': list_channels,
                    'output device channel states': new_state_dict}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

    @accept('application/vnd.mycodo.v1+json')
    @ns_output.expect(output_set_fields)
    @flask_login.login_required
    def post(self, unique_id):
        """Change the state of an output."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        control = DaemonControl()

        state = None
        channel = None
        duration = None
        duty_cycle = None
        volume = None

        if ns_output.payload:
            if 'state' in ns_output.payload:
                state = ns_output.payload["state"]
                if state is not None:
                    try:
                        state = bool(state)
                    except Exception:
                        abort(422, message='state must represent a bool value')

            if 'channel' in ns_output.payload:
                channel = ns_output.payload["channel"]
                if channel is not None:
                    try:
                        channel = int(channel)
                    except Exception:
                        abort(422, message='channel does not represent a number')
                else:
                    channel = 0

            if 'duration' in ns_output.payload:
                duration = ns_output.payload["duration"]
                if duration is not None:
                    try:
                        duration = float(duration)
                    except Exception:
                        abort(422, message='duration does not represent a number')
                else:
                    duration = 0

            if 'duty_cycle' in ns_output.payload:
                duty_cycle = ns_output.payload["duty_cycle"]
                if duty_cycle is not None:
                    try:
                        duty_cycle = float(duty_cycle)
                        if duty_cycle < 0 or duty_cycle > 100:
                            abort(422, message='Required: 0 <= duty_cycle <= 100')
                    except Exception:
                        abort(422, message='duty_cycle does not represent float value')

            if 'volume' in ns_output.payload:
                volume = ns_output.payload["volume"]
                if volume is not None:
                    try:
                        volume = float(volume)
                    except Exception:
                        abort(422, message='volume does not represent float value')

        try:
            if state is not None and duration is not None:
                return_ = control.output_on_off(
                    unique_id, state, output_channel=channel,
                    output_type='sec', amount=duration)
            elif duty_cycle is not None:
                return_ = control.output_on(
                    unique_id, output_channel=channel, output_type='pwm', amount=duty_cycle)
            elif volume is not None:
                return_ = control.output_on(
                    unique_id, output_channel=channel, output_type='vol', amount=volume)
            elif state is not None:
                return_ = control.output_on_off(
                    unique_id, state, output_channel=channel)
            else:
                return {'message': 'Insufficient payload'}, 460

            return return_handler(return_)
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import InputChannel
from mycodo.databases.models.input import InputChannelSchema
from mycodo.databases.models.input import InputSchema
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.api.sql_schema_fields import device_measurement_fields
from mycodo.mycodo_flask.api.sql_schema_fields import input_channel_fields
from mycodo.mycodo_flask.api.sql_schema_fields import input_fields
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_input = api.namespace('inputs', description='Input operations')

input_single_fields = api.model('Input Status Fields', {
    'input settings': fields.Nested(input_fields),
    'input channels': fields.List(fields.Nested(input_channel_fields)),
    'device measurements': fields.List(
        fields.Nested(device_measurement_fields)),
})

input_list_fields = api.model('Input Fields List', {
    'input settings': fields.List(fields.Nested(input_fields)),
    'input channels': fields.List(fields.Nested(input_channel_fields))
})


@ns_input.route('/')
@ns_input.doc(security='apikey', responses=default_responses)
class Inputs(Resource):
    """Input information."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_input.marshal_with(input_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all input settings."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(InputSchema, Input)
            list_channels = get_from_db(InputChannelSchema, InputChannel)
            if list_data:
                return {
                    'input settings': list_data,
                    'input channels': list_channels
                }, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_input.route('/<string:unique_id>')
@ns_input.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the input'}
)
class SettingsInputsUniqueID(Resource):
    """Interacts with input settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_input.marshal_with(input_single_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an input."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(InputSchema, Input, unique_id=unique_id)

            measure_schema = InputChannelSchema()
            list_channels = return_list_of_dictionaries(
                measure_schema.dump(
                    InputChannel.query.filter_by(
                        input_id=unique_id).all(), many=True))

            measure_schema = DeviceMeasurementsSchema()
            list_measurements = return_list_of_dictionaries(
                measure_schema.dump(
                    DeviceMeasurements.query.filter_by(
                        device_id=unique_id).join(DeviceMeasurements.conversion, isouter=True).all(), many=True))

            return {
                'input settings': list_data,
                'input channels': list_channels,
                'device measurements': list_measurements
            }, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_input.route('/<string:unique_id>/force-measurement')
@ns_input.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the input.'}
)
class InputsUniqueID(Resource):
    """Input with Unique ID."""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def post(self, unique_id):
        """Force an input to acquire measurements."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            return_ = control.input_force_measurements(unique_id)
            if return_[0]:
                return {'message': return_[1]}, 460
            else:
                return {'message': return_[1]}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

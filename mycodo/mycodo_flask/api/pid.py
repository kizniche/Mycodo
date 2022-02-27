# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import PID
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.databases.models.pid import PIDSchema
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.api.sql_schema_fields import device_measurement_fields
from mycodo.mycodo_flask.api.sql_schema_fields import pid_fields
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_pid = api.namespace('pids', description='PID operations')

pid_single_fields = api.model('PID Status Fields', {
    'pid settings': fields.Nested(pid_fields),
    'device measurements': fields.List(
        fields.Nested(device_measurement_fields)),
})

pid_list_fields = api.model('PID Fields List', {
    'pid settings': fields.List(fields.Nested(pid_fields)),
})


@ns_pid.route('/')
@ns_pid.doc(security='apikey', responses=default_responses)
class PIDs(Resource):
    """PID information."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_pid.marshal_with(pid_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all pid settings."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(PIDSchema, PID)
            if list_data:
                return {'pid settings': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_pid.route('/<string:unique_id>')
@ns_pid.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the pid'}
)
class SettingsPIDsUniqueID(Resource):
    """Interacts with pid settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_pid.marshal_with(pid_single_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a pid."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(PIDSchema, PID, unique_id=unique_id)

            measure_schema = DeviceMeasurementsSchema()
            list_data = return_list_of_dictionaries(
                measure_schema.dump(
                    DeviceMeasurements.query.filter_by(
                        device_id=unique_id).all(), many=True))

            return {'pid settings': dict_data,
                    'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

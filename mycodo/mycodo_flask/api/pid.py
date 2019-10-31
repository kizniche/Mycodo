# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus import fields

from mycodo.databases.models import PID
from mycodo.databases.models.pid import PIDSchema
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_pid = Namespace('pids', description='PID operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    461: 'Unknown Response',
    500: 'Internal Server Error'
}


pid_fields = ns_pid.model('PID Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name': fields.String,
    'is_activated': fields.Boolean,
    'is_held': fields.Boolean,
    'is_paused': fields.Boolean,
    'is_preset': fields.Boolean,
    'log_level_debug': fields.Boolean,
    'preset_name': fields.String,
    'period': fields.Float,
    'start_offset': fields.Float,
    'max_measure_age': fields.Float,
    'measurement': fields.String,
    'direction': fields.String,
    'setpoint': fields.Float,
    'band': fields.Float,
    'p': fields.Float,
    'i': fields.Float,
    'd': fields.Float,
    'integrator_min': fields.Float,
    'integrator_max': fields.Float,
    'raise_output_id': fields.String,
    'raise_min_duration': fields.Float,
    'raise_max_duration': fields.Float,
    'raise_min_off_duration': fields.Float,
    'lower_output_id': fields.String,
    'lower_min_duration': fields.Float,
    'lower_max_duration': fields.Float,
    'lower_min_off_duration': fields.Float,
    'store_lower_as_negative': fields.Boolean,
    'setpoint_tracking_type': fields.String,
    'setpoint_tracking_id': fields.String,
    'setpoint_tracking_max_age': fields.Float,
    'method_start_time': fields.String,
    'method_end_time': fields.String,
    'autotune_activated': fields.Boolean,
    'autotune_noiseband': fields.Float,
    'autotune_outstep': fields.Float
})

pid_list_fields = ns_pid.model('PID Settings Fields List', {
    'pids': fields.List(fields.Nested(pid_fields)),
})


@ns_pid.route('/')
@ns_pid.doc(security='apikey', responses=default_responses)
class PIDDump(Resource):
    """Interacts with PID settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_pid.marshal_with(pid_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all pid settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            pid_schema = PIDSchema()
            pid_data = pid_schema.dump(PID.query.all(), many=True)
            if pid_data:
                return {'pids': pid_data[0]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_pid.route('/by_unique_id/<string:unique_id>')
@ns_pid.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the pid'}
)
class PIDSingle(Resource):
    """Interacts with PID settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_pid.marshal_with(pid_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a pid with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            pid_schema = PIDSchema()
            pid_data = pid_schema.dump(
                PID.query.filter_by(unique_id=unique_id).first())
            if pid_data:
                return pid_data[0], 200
        except Exception:
            abort(500, custom=traceback.format_exc())

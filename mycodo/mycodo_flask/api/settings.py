# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Measurement
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.databases.models.input import InputSchema
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.databases.models.measurement import MeasurementSchema
from mycodo.databases.models.measurement import UnitSchema
from mycodo.databases.models.output import OutputSchema
from mycodo.databases.models.pid import PIDSchema
from mycodo.databases.models.user import UserSchema
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api.sql_schema_fields import device_measurement_fields
from mycodo.mycodo_flask.api.sql_schema_fields import input_fields
from mycodo.mycodo_flask.api.sql_schema_fields import measurement_fields
from mycodo.mycodo_flask.api.sql_schema_fields import output_fields
from mycodo.mycodo_flask.api.sql_schema_fields import pid_fields
from mycodo.mycodo_flask.api.sql_schema_fields import unit_fields
from mycodo.mycodo_flask.api.sql_schema_fields import user_fields
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_settings = api.namespace('settings', description='Settings operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    500: 'Internal Server Error'
}

input_list_fields = ns_settings.model('Input Settings Fields List', {
    'inputs': fields.List(fields.Nested(input_fields)),
})

device_measurement_list_fields = ns_settings.model('Device Measurement Settings Fields List', {
    'device measurements': fields.List(fields.Nested(device_measurement_fields)),
})

measurement_list_fields = ns_settings.model('Measurement Settings Fields List', {
    'measurements': fields.List(fields.Nested(device_measurement_fields)),
})

output_list_fields = ns_settings.model('Output Settings Fields List', {
    'outputs': fields.List(fields.Nested(output_fields)),
})

pid_list_fields = ns_settings.model('PID Settings Fields List', {
    'pids': fields.List(fields.Nested(pid_fields)),
})

unit_list_fields = ns_settings.model('User Settings Fields List', {
    'units': fields.List(fields.Nested(unit_fields)),
})

user_list_fields = ns_settings.model('User Settings Fields List', {
    'users': fields.List(fields.Nested(user_fields)),
})


@ns_settings.route('/device_measurements')
@ns_settings.doc(security='apikey', responses=default_responses)
class SettingsDeviceMeasurements(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(device_measurement_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all device measurement settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(
                DeviceMeasurementsSchema, DeviceMeasurements)
            if list_data:
                return {'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/device_measurements/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the measurement'}
)
class SettingsDeviceMeasurementsUniqueID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(device_measurement_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a device measurement with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(
                DeviceMeasurementsSchema,
                DeviceMeasurements,
                unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/device_measurements/by_device_id/<string:device_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'device_id': 'The unique ID of the controller (Input, Math, '
                         'etc.) for which the measurement belongs.'}
)
class SettingsDeviceMeasurementsDeviceID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(device_measurement_list_fields)
    @flask_login.login_required
    def get(self, device_id):
        """Show the settings for all device measurements with the device_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            measure_schema = DeviceMeasurementsSchema()
            list_data = return_list_of_dictionaries(
                measure_schema.dump(
                    DeviceMeasurements.query.filter_by(
                        device_id=device_id).all(), many=True))
            if list_data:
                return {'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/inputs')
@ns_settings.doc(security='apikey', responses=default_responses)
class SettingsInputs(Resource):
    """Interacts with Input settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(input_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all input settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(InputSchema, Input)
            if list_data:
                return {'inputs': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/inputs/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the input'}
)
class SettingsInputsUniqueID(Resource):
    """Interacts with Input settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(input_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an input"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(InputSchema, Input, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/measurements')
@ns_settings.doc(security='apikey', responses=default_responses)
class SettingsMeasurements(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(measurement_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all measurement settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(MeasurementSchema, Measurement)
            if list_data:
                return {'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/measurements/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the measurement'}
)
class SettingsMeasurementsUniqueID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(measurement_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a measurement with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(
                MeasurementSchema, Measurement, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/outputs')
@ns_settings.doc(security='apikey', responses=default_responses)
class SettingsOutputs(Resource):
    """Interacts with output settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(output_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all output settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(OutputSchema, Output)
            if list_data:
                return {'outputs': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/outputs/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the output'}
)
class SettingsOutputsUniqueID(Resource):
    """Interacts with Output settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(output_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an output with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(OutputSchema, Output, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/pids')
@ns_settings.doc(security='apikey', responses=default_responses)
class SettingsPIDs(Resource):
    """Interacts with PID settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(pid_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all pid settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(PIDSchema, PID)
            if list_data:
                return {'pids': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/pids/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the pid'}
)
class SettingsPIDsUniqueID(Resource):
    """Interacts with PID settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(pid_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a pid with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(PIDSchema, PID, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/units')
@ns_settings.doc(security='apikey', responses=default_responses)
class SettingsUnits(Resource):
    """Interacts with Unit settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(unit_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all unit settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(UnitSchema, Unit)
            if list_data:
                return {'units': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/units/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the unit'}
)
class SettingsUnitsUniqueID(Resource):
    """Interacts with unit settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(unit_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a unit with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(UnitSchema, Unit, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/users')
@ns_settings.doc(security='apikey', responses=default_responses)
class SettingsUsers(Resource):
    """Interacts with User settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(user_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all user settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(UserSchema, User)
            if list_data:
                return {'users': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_settings.route('/users/<string:unique_id>')
@ns_settings.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the user'}
)
class SettingsUsersUniqueID(Resource):
    """Interacts with user settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_settings.marshal_with(user_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a user with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        try:
            dict_data = get_from_db(UserSchema, User, unique_id=unique_id)
            if dict_data:
                return dict_data, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

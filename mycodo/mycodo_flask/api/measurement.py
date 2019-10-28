# coding=utf-8
import logging
import traceback
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
import flask_login
from flask import request
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields
from mycodo.utils.influx import write_influxdb_value

from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_measurement = Namespace('measurement', description='Measurement operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    460: 'Fail',
    461: 'Unknown Response'
}

# def return_handler(return_):
#     if return_ is None:
#         return 'Success', 200
#     elif return_[0] in [0, 'success']:
#         return 'Success: {}'.format(return_[1]), 200
#     elif return_[0] in [1, 'error']:
#         return 'Fail: {}'.format(return_[1]), 460
#     else:
#         return '', 461


# set_state_fields = ns_measurement.model('OutputSetState', {
#     'duration': fields.Float(
#         description='The duration to keep the output on, in seconds',
#         required=False,
#         example=10.0,
#         exclusiveMin=0)
# })


# @ns_measurement.route('/set_state/<string:unique_id>/<string:state>')
# @ns_measurement.doc(security='apikey', responses=default_responses)
# @ns_measurement.doc(params={
#     'unique_id': 'The unique ID of the output.',
#     'state': 'The state to set ("on" or "off").',
#     'duration': 'The duration (seconds) to keep the output on before turning off.'})
# class OutputState(Resource):
#     """Manipulates an Output"""
#     @ns_measurement.expect(set_state_fields)
#     @flask_login.login_required
#     def post(self, unique_id, state):
#         """Change the state of an on/off output"""
#         if not utils_general.user_has_permission('edit_controllers'):
#             return 'You do not have permission to access this.', 401
#         try:
#             duration = float(request.args.get("duration"))
#         except:
#             duration = 0
#
#         try:
#             control = DaemonControl()
#             return_ = control.output_on_off(
#                 unique_id, state, amount=float(duration))
#             return return_handler(return_)
#         except Exception:
#             return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_measurement.route('/save_new/<string:unique_id>/<string:unit>/<int:channel>/<value>')
@ns_measurement.doc(security='apikey', responses=default_responses)
@ns_measurement.doc(
    params={
        'unique_id': 'The unique ID of the measurement',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'value': 'the value of the measurement'
    }
)
class MeasurementSave(Resource):
    """Interacts with Measurement settings in the SQL database"""
    @flask_login.login_required
    def post(self, unique_id, unit, channel, value):
        """Save a measurement to the mycodo_db database in InfluxDB"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401

        try:
            value = float(value)
        except:
            return 'Fail: value does not represent a float'

        try:
            return_ = write_influxdb_value(unique_id, unit, value, channel=channel)
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460

        if return_:
            return 'Fail', 460
        else:
            return 'Success', 200


@ns_measurement.route('/settings_unique_id/<string:unique_id>')
@ns_measurement.doc(security='apikey', responses=default_responses)
@ns_measurement.doc(params={'unique_id': 'The unique ID of the measurement'})
class MeasurementUniqueID(Resource):
    """Interacts with Measurement settings in the SQL database"""
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a measurement with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            measure_schema = DeviceMeasurementsSchema()
            measure_ = DeviceMeasurements.query.filter_by(unique_id=unique_id).first()
            return measure_schema.dump(measure_), 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_measurement.route('/settings_device_id/<string:device_id>')
@ns_measurement.doc(security='apikey', responses=default_responses)
@ns_measurement.doc(params={'device_id': 'The unique ID of the controller (Input, Math, etc.) for which the measurement belongs.'})
class MeasurementDeviceID(Resource):
    """Interacts with Measurement settings in the SQL database"""
    @flask_login.login_required
    def get(self, device_id):
        """Show the settings for all measurements with the device_id"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            measure_schema = DeviceMeasurementsSchema()
            measure_ = DeviceMeasurements.query.filter_by(device_id=device_id).first()
            return measure_schema.dump(measure_), 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_measurement.route('/settings_all')
@ns_measurement.doc(security='apikey', responses=default_responses)
class MeasurementDump(Resource):
    """Interacts with Measurement settings in the SQL database"""
    @flask_login.login_required
    def get(self):
        """Show all measurement settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            measure_schema = DeviceMeasurementsSchema()
            return measure_schema.dump(DeviceMeasurements.query.all(), many=True)[0], 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460

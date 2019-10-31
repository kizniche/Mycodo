# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.influx import read_past_influxdb
from mycodo.utils.influx import write_influxdb_value

logger = logging.getLogger(__name__)

ns_measurement = Namespace(
    'measurements', description='Measurement operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    422: 'Unprocessable Entity',
    429: 'Too Many Requests',
    500: 'Internal Server Error'
}

device_measurement_fields = ns_measurement.model('Measurement Settings Fields', {
    'id': fields.Integer,
    'unique_id': fields.String,
    'name': fields.String,
    'device_type': fields.String,
    'device_id': fields.String,
    'is_enabled': fields.Boolean,
    'measurement': fields.String,
    'measurement_type': fields.String,
    'unit': fields.String,
    'channel': fields.Integer,
    'invert_scale': fields.Boolean,
    'rescaled_measurement': fields.String,
    'rescaled_unit': fields.String,
    'scale_from_min': fields.Float,
    'scale_from_max': fields.Float,
    'scale_to_min': fields.Float,
    'scale_to_max': fields.Float,
    'conversion_id': fields.String,
})

device_measurement_list_fields = ns_measurement.model('Measurement Settings Fields List', {
    'measurements': fields.List(fields.Nested(device_measurement_fields)),
})

measurement_fields = ns_measurement.model('Measurement', {
    'time': fields.DateTime(dt_format='iso8601'),
    'value': fields.Float,
})

measurement_list_fields = ns_measurement.model('Measurement List', {
    'measurements': fields.List(fields.Nested(measurement_fields)),
})


@ns_measurement.route('/')
@ns_measurement.doc(security='apikey', responses=default_responses)
class Measurements(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(device_measurement_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all measurement settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            measure_schema = DeviceMeasurementsSchema()
            measure_data = measure_schema.dump(
                DeviceMeasurements.query.all(), many=True)
            if measure_data:
                return {'measurements': measure_data[0]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_measurement.route('/by_device_id/<string:device_id>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={'device_id': 'The unique ID of the controller (Input, Math, '
                         'etc.) for which the measurement belongs.'}
)
class MeasurementsDeviceID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(device_measurement_list_fields)
    @flask_login.login_required
    def get(self, device_id):
        """Show the settings for all measurements with the device_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            measure_schema = DeviceMeasurementsSchema()
            measure_data = measure_schema.dump(
                DeviceMeasurements.query.filter_by(
                    device_id=device_id).all(), many=True)
            if measure_data:
                return {'measurements': measure_data[0]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_measurement.route('/by_unique_id/<string:unique_id>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the measurement'}
)
class MeasurementsUniqueID(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(device_measurement_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a measurement with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            measure_schema = DeviceMeasurementsSchema()
            measure_data = measure_schema.dump(
                DeviceMeasurements.query.filter_by(
                    unique_id=unique_id).first())
            if measure_data:
                return measure_data[0], 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_measurement.route('/create/<string:unique_id>/<string:unit>/<int:channel>/<value>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the measurement',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'value': 'the value of the measurement'
    }
)
class MeasurementsCreate(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def post(self, unique_id, unit, channel, value):
        """Save a measurement to the mycodo_db database in InfluxDB"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        if channel < 0:
            abort(422, custom='channel must be >= 0')

        try:
            value = float(value)
        except:
            abort(422, custom='value does not represent a float')

        try:
            return_ = write_influxdb_value(
                unique_id, unit, value, channel=channel)
        except Exception:
            abort(500, custom=traceback.format_exc())

        if return_:
            abort(500)
        else:
            return 'Success', 200


@ns_measurement.route('/last/<string:unique_id>/<string:unit>/<int:channel>/<int:past_seconds>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the measurement',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'past_seconds': 'How many seconds in the past to query.'
    }
)
class MeasurementsLast(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(measurement_fields)
    @flask_login.login_required
    def get(self, unique_id, unit, channel, past_seconds):
        """Return the last stored measurement from InfluxDB"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        if channel < 0:
            abort(422, custom='channel must be >= 0')
        if past_seconds < 1:
            abort(422, custom='past_seconds must be >= 1')

        try:
            return_ = read_last_influxdb(
                unique_id, unit, channel, duration_sec=past_seconds)
            if return_ and len(return_) == 2:
                return {'time': return_[0], 'value': return_[1]}, 200
            else:
                return return_, 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_measurement.route('/past/<string:unique_id>/<string:unit>/<int:channel>/<int:past_seconds>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the measurement',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'past_seconds': 'How many seconds in the past to query.'
    }
)
class MeasurementsPast(Resource):
    """Interacts with Measurement settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(measurement_list_fields)
    @flask_login.login_required
    def get(self, unique_id, unit, channel, past_seconds):
        """Return a list of the last stored measurements from InfluxDB"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        if channel < 0:
            abort(422, custom='channel must be >= 0')
        if past_seconds < 1:
            abort(422, custom='past_seconds must be >= 1')

        try:
            return_ = read_past_influxdb(
                unique_id, unit, channel, past_seconds)
            if return_ and len(return_) > 0:
                dict_return = {'measurements': []}
                for each_set in return_:
                    dict_return['measurements'].append(
                        {'time': each_set[0], 'value': each_set[1]})
                return dict_return, 200
            else:
                return return_, 200
        except Exception:
            abort(500, custom=traceback.format_exc())

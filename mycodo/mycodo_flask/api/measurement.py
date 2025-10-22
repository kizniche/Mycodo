# coding=utf-8
import datetime
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource, abort, fields

from mycodo.databases.models import Unit
from mycodo.mycodo_flask.api import api, default_responses
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.influx import (read_influxdb_list, read_influxdb_multi,
                                 read_influxdb_single, valid_date_str,
                                 write_influxdb_value)
from mycodo.utils.system_pi import add_custom_units

logger = logging.getLogger(__name__)

ns_measurement = api.namespace(
    'measurements', description='Measurement operations')

measurement_create_fields = ns_measurement.model('Measurement Create Fields', {
    'timestamp': fields.DateTime(
        description='The timestamp of the measurement, in %Y-%m-%dT%H:%M:%S.%fZ format '
                    '(e.g. 2019-04-15T18:07:00.392Z). (Optional; exclude to create a '
                    'measurement with a timestamp of the current time)',
        dt_format='iso8601',
        required=False)
})

measurement_fields = ns_measurement.model('Measurement Fields', {
    'time': fields.Float,
    'value': fields.Float,
})

measurement_list_fields = ns_measurement.model('Measurement Fields List', {
    'measurements': fields.List(fields.Nested(measurement_fields)),
})

measurement_function_fields = ns_measurement.model('Measurement Function Fields', {
    'value': fields.Float,
})

channel_spec_fields = ns_measurement.model('Channel Specification', {
    'unique_id': fields.String(required=True, description='The unique ID of the device'),
    'unit': fields.String(required=True, description='The unit of the measurement'),
    'channel': fields.Integer(required=True, description='The channel number'),
    'measure': fields.String(required=False, description='The measurement type (optional)')
})

multi_measurement_request_fields = ns_measurement.model('Multi Measurement Request', {
    'channels': fields.List(fields.Nested(channel_spec_fields), required=True,
                           description='List of channel specifications to query'),
    'past_seconds': fields.Integer(required=False, default=3600,
                                  description='How many seconds in the past to query (default: 3600)')
})

multi_measurement_channel_result = ns_measurement.model('Multi Measurement Channel Result', {
    'unique_id': fields.String(description='The unique ID of the device'),
    'unit': fields.String(description='The unit of the measurement'),
    'channel': fields.Integer(description='The channel number'),
    'measure': fields.String(description='The measurement type'),
    'time': fields.Float(description='Timestamp of the measurement'),
    'value': fields.Float(description='Value of the measurement')
})

multi_measurement_response_fields = ns_measurement.model('Multi Measurement Response', {
    'measurements': fields.List(fields.Nested(multi_measurement_channel_result),
                               description='List of measurement results')
})


@ns_measurement.route('/create/<string:unique_id>/<string:unit>/<int:channel>/<value>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the device',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'value': 'the value of the measurement'
    }
)
class MeasurementsCreate(Resource):
    """Interacts with Measurement settings in the SQL database."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.expect(measurement_create_fields)
    @flask_login.login_required
    def post(self, unique_id, unit, channel, value):
        """Create a measurement."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        if unit not in add_custom_units(Unit.query.all()):
            abort(422, custom='Unit ID not found')
        if channel < 0:
            abort(422, custom='channel must be >= 0')

        try:
            value = float(value)
        except:
            abort(422, custom='value does not represent a float')

        timestamp = None
        if ns_measurement.payload and 'timestamp' in ns_measurement.payload:
            ts = ns_measurement.payload["timestamp"]
            if ts is not None:
                if valid_date_str(ts):
                    timestamp = datetime.datetime.strptime(
                        ts, '%Y-%m-%dT%H:%M:%S.%fZ')
                else:
                    abort(422, custom='Invalid timestamp format. Must be formatted as %Y-%m-%dT%H:%M:%S.%fZ')

        try:
            return_ = write_influxdb_value(
                unique_id, unit, value, channel=channel, timestamp=timestamp)

            if return_:
                abort(500)
            else:
                return {'message': 'Success'}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_measurement.route('/historical/<string:unique_id>/<string:unit>/<int:channel>/<int:epoch_start>/<int:epoch_end>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the device',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'epoch_start': 'The start time, as epoch. Set to 0 for none.',
        'epoch_end': 'The end time, as epoch. Set to 0 for none.'
    }
)
class MeasurementsHistorical(Resource):
    """Interacts with Measurement settings in the SQL database."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(measurement_list_fields)
    @flask_login.login_required
    def get(self, unique_id, unit, channel, epoch_start, epoch_end):
        """
        Return a list of measurements found within a time range
        """
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        if unit not in add_custom_units(Unit.query.all()):
            abort(422, custom='Unit ID not found')
        if channel < 0:
            abort(422, custom='channel must be >= 0')
        if epoch_start < 0 or epoch_end < 0:
            abort(422, custom='epoch_start and epoch_end must be >= 0')

        utc_offset_timedelta = datetime.datetime.utcnow() - datetime.datetime.now()

        if epoch_start:
            start = datetime.datetime.fromtimestamp(float(epoch_start))
            start += utc_offset_timedelta
            start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            start_str = None

        if epoch_end:
            end = datetime.datetime.fromtimestamp(float(epoch_end))
            end += utc_offset_timedelta
            end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            end_str = None

        try:
            return_ = read_influxdb_list(
                unique_id, unit, channel, start_str=start_str, end_str=end_str)
            if return_ and len(return_) > 0:
                dict_return = {'measurements': []}
                for each_set in return_:
                    dict_return['measurements'].append(
                        {'time': each_set[0], 'value': each_set[1]})
                return dict_return, 200
            else:
                return return_, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_measurement.route('/last/<string:unique_id>/<string:unit>/<int:channel>/<int:past_seconds>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the device',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'past_seconds': 'How many seconds in the past to query.'
    }
)
class MeasurementsLast(Resource):
    """Interacts with Measurement settings in the SQL database."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(measurement_fields)
    @flask_login.login_required
    def get(self, unique_id, unit, channel, past_seconds):
        """
        Return the last measurement found within a duration from the past to the present
        """
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        if unit not in add_custom_units(Unit.query.all()):
            abort(422, custom='Unit ID not found')
        if channel < 0:
            abort(422, custom='channel must be >= 0')
        if past_seconds < 1:
            abort(422, custom='past_seconds must be >= 1')

        try:
            return_ = read_influxdb_single(
                unique_id, unit, channel, duration_sec=past_seconds)
            if return_ and len(return_) == 2:
                return {'time': return_[0], 'value': return_[1]}, 200
            else:
                return return_, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_measurement.route('/past/<string:unique_id>/<string:unit>/<int:channel>/<int:past_seconds>')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the device',
        'unit': 'The unit of the measurement',
        'channel': 'The channel of the measurement',
        'past_seconds': 'How many seconds in the past to query.'
    }
)
class MeasurementsPast(Resource):
    """Interacts with Measurement settings in the SQL database."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.marshal_with(measurement_list_fields)
    @flask_login.login_required
    def get(self, unique_id, unit, channel, past_seconds):
        """
        Return a list of measurements found within a duration from the past to the present
        """
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        if unit not in add_custom_units(Unit.query.all()):
            abort(422, custom='Unit ID not found')
        if channel < 0:
            abort(422, custom='channel must be >= 0')
        if past_seconds < 1:
            abort(422, custom='past_seconds must be >= 1')

        try:
            return_ = read_influxdb_list(
                unique_id, unit, channel, duration_sec=past_seconds)
            if return_ and len(return_) > 0:
                dict_return = {'measurements': []}
                for each_set in return_:
                    dict_return['measurements'].append(
                        {'time': each_set[0], 'value': each_set[1]})
                return dict_return, 200
            else:
                return return_, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_measurement.route('/multi')
@ns_measurement.doc(
    security='apikey',
    responses=default_responses
)
class MeasurementsMulti(Resource):
    """Query multiple measurement channels in a single request."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_measurement.expect(multi_measurement_request_fields)
    @ns_measurement.marshal_with(multi_measurement_response_fields)
    @flask_login.login_required
    def post(self):
        """
        Query multiple measurement channels at once.
        
        Returns the last measurement for each specified channel within the given time period.
        """
        if not utils_general.user_has_permission('view_settings'):
            abort(403)

        if not ns_measurement.payload:
            abort(422, custom='Request body is required')

        channels = ns_measurement.payload.get('channels', [])
        past_seconds = ns_measurement.payload.get('past_seconds', 3600)

        if not channels:
            abort(422, custom='channels list is required and cannot be empty')

        if not isinstance(channels, list):
            abort(422, custom='channels must be a list')

        if past_seconds < 1:
            abort(422, custom='past_seconds must be >= 1')

        # Validate each channel specification
        validated_channels = []
        for idx, channel_spec in enumerate(channels):
            if not isinstance(channel_spec, dict):
                abort(422, custom=f'Channel at index {idx} must be an object')

            unique_id = channel_spec.get('unique_id')
            unit = channel_spec.get('unit')
            channel = channel_spec.get('channel')
            measure = channel_spec.get('measure')

            if not unique_id:
                abort(422, custom=f'unique_id is required for channel at index {idx}')
            if not unit:
                abort(422, custom=f'unit is required for channel at index {idx}')
            if channel is None:
                abort(422, custom=f'channel is required for channel at index {idx}')

            if unit not in add_custom_units(Unit.query.all()):
                abort(422, custom=f'Unit ID not found for channel at index {idx}: {unit}')

            if channel < 0:
                abort(422, custom=f'channel must be >= 0 for channel at index {idx}')

            validated_channels.append({
                'unique_id': unique_id,
                'unit': unit,
                'channel': channel,
                'measure': measure
            })

        try:
            # Query all channels
            results = read_influxdb_multi(
                channels_data=validated_channels,
                past_seconds=past_seconds,
                value='LAST'
            )

            # Format response
            measurements = []
            for idx, channel_spec in enumerate(validated_channels):
                result = results.get(idx, [None, None])
                measurements.append({
                    'unique_id': channel_spec['unique_id'],
                    'unit': channel_spec['unit'],
                    'channel': channel_spec['channel'],
                    'measure': channel_spec.get('measure'),
                    'time': result[0],
                    'value': result[1]
                })

            return {'measurements': measurements}, 200

        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())

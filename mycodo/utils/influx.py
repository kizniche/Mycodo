# coding=utf-8
import datetime
import logging
import threading
import time
from uuid import UUID

import requests
from influxdb import InfluxDBClient

from mycodo.config import INFLUXDB_DATABASE
from mycodo.config import INFLUXDB_HOST
from mycodo.config import INFLUXDB_PASSWORD
from mycodo.config import INFLUXDB_PORT
from mycodo.config import INFLUXDB_USER
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Output
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.logging_utils import set_log_level
from mycodo.utils.system_pi import return_measurement_info

logger = logging.getLogger("mycodo.influx")
logger.setLevel(set_log_level(logging))


def add_measurements_influxdb(unique_id, measurements, use_same_timestamp=True, block=False):
    """
    Parse measurement data into list to be input into influxdb (threaded so returns fast)
    :param unique_id: Unique ID of device
    :param measurements: dict of measurements
    :param use_same_timestamp: Allow influxdb to create the timestamp upon storage
    :param block: wait until measurements are added before returning
    :return:
    """
    if block:
        write_influxdb_data(unique_id, measurements, use_same_timestamp)
    else:
        write_db = threading.Thread(
            target=write_influxdb_data,
            args=(unique_id, measurements, use_same_timestamp,))
        write_db.start()


def write_influxdb_data(unique_id, measurements, use_same_timestamp=True):
    """
    Parse measurement data into list to be input into influxdb (non-threaded so may not return fast)
    :param unique_id: Unique ID of device
    :param measurements: dict of measurements
    :param use_same_timestamp: Allow influxdb to create the timestamp upon storage
    :return:
    """
    data = []

    for each_channel, each_measurement in measurements.items():
        if 'value' in each_measurement and each_measurement['value'] is not None:

            if use_same_timestamp:
                # influxdb will create the timestamp when the data is stored
                timestamp = None
            else:
                # Use timestamp stored with each measurement
                timestamp = each_measurement['timestamp_utc']

            data.append(format_influxdb_data(
                unique_id,
                each_measurement['unit'],
                each_measurement['value'],
                channel=each_channel,
                measure=each_measurement['measurement'],
                timestamp=timestamp))
    if data:
        client = InfluxDBClient(
            INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASSWORD,
            INFLUXDB_DATABASE, timeout=5)
        client.write_points(data)


def write_influxdb_value(unique_id, unit, value, measure=None, channel=None, timestamp=None):
    """
    Write a value into an Influxdb database

    example:
        write_influxdb_value('00000001', 'C', 37.5)

    :return: success (0) or failure (1)
    :rtype: bool

    :param unique_id: What unique_id tag to enter in the Influxdb
        database (ex. '00000001')
    :type unique_id: str
    :param measure: What type of measurement for the Influxdb
        database entry (ex. 'temperature')
    :type measure: str
    :param value: The value being entered into the Influxdb database
    :type value: int or float
    :param unit:
    :type unit:
    :param channel:
    :type channel:
    :param timestamp: If supplied, this timestamp will be used in the influxdb
    :type timestamp: datetime object
    """
    client = InfluxDBClient(
        INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE, timeout=5)

    data = [
        format_influxdb_data(
            unique_id, unit, value,
            channel=channel,
            measure=measure,
            timestamp=timestamp)
    ]

    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug("Failed to write measurements to influxdb with ID {}. "
                     "Retrying in 30 seconds.".format(unique_id))
        time.sleep(30)
        try:
            client.write_points(data)
            logger.debug("Successfully wrote measurements to influxdb after "
                         "30-second wait.")
            return 0
        except:
            logger.debug(
                "Failed to write measurement to influxdb (Device ID: {id}). Data "
                "that was submitted for writing: {data}. Exception: {err}".format(
                    id=unique_id, data=data, err=except_msg))
            return 1


def query_string(unit, unique_id,
                 value=None, measure=None, channel=None, ts_str=None,
                 start_str=None, end_str=None, past_sec=None, group_sec=None,
                 limit=None, function=None):
    """Generate influxdb query string."""
    from influxdb import InfluxDBClient

    dbcon = InfluxDBClient(
        INFLUXDB_HOST,
        INFLUXDB_PORT,
        INFLUXDB_USER,
        INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE)

    query = "SELECT "

    if function:
        query += "{func}(value)".format(func=function)

    elif value:  # value is deprecated. Use function instead.
        if value in ['COUNT', 'LAST', 'MEAN', 'MAX', 'MIN', 'SUM']:
            query += "{value}(value)".format(value=value)
    else:
        query += "value"

    query += " FROM {unit} WHERE device_id='{id}'".format(
        unit=unit, id=unique_id)

    if channel is not None:
        query += " AND channel='{channel}'".format(channel=channel)
    if measure:
        query += " AND measure='{measure}'".format(measure=measure)
    if ts_str:
        query += " AND time = '{ts}'".format(ts=ts_str)
    if start_str:
        query += " AND time >= '{start}'".format(start=start_str)
    if end_str:
        query += " AND time <= '{end}'".format(end=end_str)
    if past_sec:
        query += " AND time > now() - {sec}s".format(sec=int(past_sec))
    if group_sec:
        query += " GROUP BY TIME({sec}s)".format(sec=group_sec)
    if limit:
        query += " GROUP BY * LIMIT {lim}".format(lim=limit)

    raw_data = dbcon.query(query).raw

    if 'series' not in raw_data or not raw_data['series']:
        return None

    return raw_data['series'][0]['values']


def get_last_measurement(device_id, measurement_id, max_age=None):
    device_measurement = db_retrieve_table_daemon(
        DeviceMeasurements).filter(
        DeviceMeasurements.unique_id == measurement_id).first()
    if device_measurement:
        conversion = db_retrieve_table_daemon(
            Conversion, unique_id=device_measurement.conversion_id)
    else:
        conversion = None
    channel, unit, measurement = return_measurement_info(
        device_measurement, conversion)

    last_measurement = read_influxdb_single(
        device_id,
        unit,
        channel,
        measure=measurement,
        duration_sec=max_age,
        value='LAST')

    return last_measurement


def get_past_measurements(device_id, measurement_id, max_age=None):
    device_measurement = db_retrieve_table_daemon(
        DeviceMeasurements).filter(
        DeviceMeasurements.unique_id == measurement_id).first()
    if device_measurement:
        conversion = db_retrieve_table_daemon(
            Conversion, unique_id=device_measurement.conversion_id)
    else:
        conversion = None
    channel, unit, measurement = return_measurement_info(
        device_measurement, conversion)

    past_measurements = read_influxdb_list(
        device_id,
        unit,
        channel,
        measure=measurement,
        duration_sec=max_age)

    return past_measurements


def read_influxdb_list(unique_id, unit, channel,
                       measure=None,
                       duration_sec=None,
                       start_str=None,
                       end_str=None):
    """
    Query Influxdb for a list of entries

    example:
        read_influxdb_list('00000001', 'C', duration_sec=0)

    :return: list of time and value
    :rtype: list

    :param unique_id: What unique_id tag to query in the Influxdb
        database (eg. '00000001')
    :type unique_id: str
    :param unit: What unit to query in the Influxdb
        database (eg. 'C', 's')
    :type unit: str
    :param measure: What measurement to query in the Influxdb
        database (eg. 'temperature', 'duration_time')
    :type measure: str or None
    :param channel: Channel
    :type channel: int or None
    :param duration_sec: How many seconds to look for a past measurement
    :type duration_sec: int or None
    :param start_str: Start time, in influxdb format
    :type start_str: str
    :param end_str: End time, in influxdb format
    :type end_str: str
    """
    try:
        data = query_string(
            unit, unique_id,
            measure=measure,
            channel=channel,
            start_str=start_str,
            end_str=end_str,
            past_sec=duration_sec)

        return data
    except:
        logger.debug("Could not read form influxdb.")


def read_influxdb_single(unique_id, unit, channel,
                         measure=None,
                         duration_sec=None,
                         start_str=None,
                         end_str=None,
                         value='LAST'):
    """
    Query Influxdb for a single entry/value

    example:
        read_influxdb_single('00000001', 'C', duration_sec=0, value='LAST')

    :return: list of time and value
    :rtype: list

    :param unique_id: What unique_id tag to query in the Influxdb
        database (eg. '00000001')
    :type unique_id: str
    :param unit: What unit to query in the Influxdb
        database (eg. 'C', 's')
    :type unit: str
    :param measure: What measurement to query in the Influxdb
        database (eg. 'temperature', 'duration_time')
    :type measure: str or None
    :param channel: Channel
    :type channel: int or None
    :param duration_sec: How many seconds to look for a past measurement
    :type duration_sec: int or None
    :param start_str: Start time, in influxdb format
    :type start_str: str
    :param end_str: End time, in influxdb format
    :type end_str: str
    :param value: What kind of measurement to return (e.g. LAST, SUM, MIN, MAX, etc.)
    :type value: str
    """
    try:
        data = query_string(
            unit,
            unique_id,
            measure=measure,
            channel=channel,
            value=value,
            start_str=start_str,
            end_str=end_str,
            past_sec=duration_sec)

        if data:
            try:
                number = len(data)
                last_time = data[number - 1][0]
                last_measurement = data[number - 1][1]
                return [last_time, last_measurement]
            except Exception:
                logger.exception("Error parsing the last influx measurement")
    except requests.exceptions.ConnectionError:
        logger.debug("Failed to establish a new influxdb connection. Ensure influxdb is running.")


def output_sec_on(output_id, past_seconds, output_channel=0):
    """Return the number of seconds a output has been ON in the past number of seconds."""
    # Get the number of seconds ON stored in the database
    if not output_id:
        return None

    output = db_retrieve_table_daemon(Output, unique_id=output_id)

    # Get the number of seconds not stored in the database (if currently on)
    output_time_on = 0
    try:
        control = DaemonControl()
        if control.output_state(output_id, output_channel=output_channel) == 'on':
            output_time_on = control.output_sec_currently_on(
                output_id, output_channel=output_channel)
    except Exception:
        logger.exception("output_sec_on()")

    data = query_string(
        's', output.unique_id,
        measure='duration_time',
        channel=output_channel,
        value='SUM',
        past_sec=past_seconds)

    sec_recorded_on = 0
    if data:
        sec_recorded_on = data[0][1]

    sec_currently_on = 0
    if output_time_on:
        sec_currently_on = min(output_time_on, past_seconds)

    return sec_recorded_on + sec_currently_on


def average_past_seconds(unique_id, unit, channel, past_seconds, measure=None):
    """Return measurement average for the past x seconds."""
    data = query_string(
        unit, unique_id,
        measure=measure,
        channel=channel,
        value='MEAN',
        past_sec=past_seconds)

    if data:
        return data[0][1]


def average_start_end_seconds(unique_id, unit, channel, str_start, str_end, measure=None):
    """Return measurement average for a period of time."""
    data = query_string(
        unit, unique_id,
        measure=measure,
        channel=channel,
        value='MEAN',
        start_str=str_start,
        end_str=str_end)

    if data:
        return data[0][1]


def sum_past_seconds(unique_id, unit, channel, past_seconds, measure=None):
    """Return measurement sum for the past x seconds."""
    data = query_string(
        unit, unique_id,
        measure=measure,
        channel=channel,
        value='SUM',
        past_sec=past_seconds)

    if data:
        return data[0][1]


def influx_time_str_to_milliseconds(timestamp_str):
    """Converts InfluxDB time string with "Z" from nanoseconds to milliseconds and removes the Z."""
    start_date_time = timestamp_str.split('Z')[0].split('.')[0]
    start_milliseconds = timestamp_str.split('Z')[0].split('.')[1][:3]
    return '{}.{}'.format(start_date_time, start_milliseconds)


def valid_date_str(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        logger.exception(1)
        return False
    return True


def valid_int(test_var):
    try:
        _ = int(test_var)
    except ValueError:
        logger.exception(1)
        return False
    return True


def valid_uuid(uuid_str):
    try:
        val = UUID(uuid_str)
    except Exception:
        logger.exception(1)
        return False
    return val.hex == uuid_str.replace('-', '')

#
# DEPRECATED
# TODO: Remove
#

def read_last_influxdb(unique_id, unit, channel, measure=None, duration_sec=None):
    """
    DEPRECATED: use read_influxdb_single()
    """
    last_measurement = read_influxdb_single(
        unique_id, unit, channel,
        measure=measure, duration_sec=duration_sec, value='LAST')
    return last_measurement


def read_past_influxdb(unique_id, unit, channel, past_seconds, measure=None):
    """
    DEPRECATED: use read_influxdb_list()
    """
    last_measurement = read_influxdb_list(
        unique_id, unit, channel,
        measure=measure, duration_sec=past_seconds)
    return last_measurement


def format_influxdb_data(unique_id, unit, value, channel=None, measure=None, timestamp=None):
    """
    Format data for entry into an Influxdb database

    example:
        format_influxdb_data('00000001', 'C', 37.5, measure='temperature', channel=0)
        format_influxdb_data('00000002', 's', 15.2, measure='duration_time', channel=1)

    :return: list of unit type, tags, and value
    :rtype: list

    :param unique_id: 8-character alpha-numeric ID associated with device
    :type unique_id: str
    :param unit: The type of data being entered into the Influxdb
        database (ex. 'C', 'mg')
    :type unit: str
    :param value: The value being entered into the Influxdb database
    :type value: int or float
    :param measure:
    :type measure: str
    :param channel:
    :type channel: int
    :param timestamp: If supplied, this timestamp will be used in the influxdb
    :type timestamp: datetime object
    """
    checked_value = float(value)

    influx_dict = {
        'measurement': unit,
        'tags': {
            'device_id': unique_id
        },
        'fields': {
            'value': checked_value
        }
    }

    if measure:
        influx_dict['tags']['measure'] = measure

    if channel is not None:
        influx_dict['tags']['channel'] = channel

    if timestamp:
        # Timestamp (UTC) can either be received as:
        # 1. datetime object
        # 2. string in the format %Y-%m-%dT%H:%M:%S.%fZ
        if isinstance(timestamp, str):
            influx_dict['time'] = timestamp
        else:
            influx_dict['time'] = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return influx_dict


#
# For influxdb-client
#

# INFLUXDB_URL = f'http://{INFLUXDB_HOST}:{INFLUXDB_PORT}'
# INFLUXDB_TOKEN = f'{INFLUXDB_USER}:{INFLUXDB_PASSWORD}'
# INFLUXDB_BUCKET = f'{INFLUXDB_DATABASE}/autogen'

# def write_influxdb_value_flux(unique_id, unit, value, measure=None, channel=None, timestamp=None):
#     """
#     Write a value into an Influxdb database (flux edition, using influxdb_client)
#
#     example:
#         write_influxdb_value('00000001', 'C', 37.5)
#
#     :return: success (0) or failure (1)
#     :rtype: bool
#
#     :param unique_id: What unique_id tag to enter in the Influxdb
#         database (ex. '00000001')
#     :type unique_id: str
#     :param measure: What type of measurement for the Influxdb
#         database entry (ex. 'temperature')
#     :type measure: str
#     :param value: The value being entered into the Influxdb database
#     :type value: int or float
#     :param unit:
#     :type unit:
#     :param channel:
#     :type channel:
#     :param timestamp: If supplied, this timestamp will be used in the influxdb
#     :type timestamp: datetime object
#     """
#     from influxdb_client import InfluxDBClient
#     from influxdb_client import Point
#
#     with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org='-', timeout=5000) as client:
#         with client.write_api() as write_api:
#             point = Point(unit).tag("device_id", unique_id)
#
#             if measure:
#                 point = point.tag("measure", measure)
#             if channel is not None:
#                 point = point.tag("channel", channel)
#             if timestamp:
#                 point = point.time(timestamp)
#
#             point = point.field("value", value)
#             write_api.write(bucket=INFLUXDB_BUCKET, record=point)
#
#             try:
#                 write_api.write(bucket=INFLUXDB_BUCKET, record=point)
#                 return 0
#             except Exception as except_msg:
#                 logger.debug("Failed to write measurements to influxdb with ID {}. "
#                              "Retrying in 5 seconds.".format(unique_id))
#                 time.sleep(5)
#                 try:
#                     write_api.write(bucket=INFLUXDB_BUCKET, record=point)
#                     logger.debug("Successfully wrote measurements to influxdb after 5-second wait.")
#                     return 0
#                 except:
#                     logger.debug(
#                         f"Failed to write measurement to influxdb (Device ID: {unique_id}): {except_msg}.")
#                     return 1


# def add_measurements_influxdb_flux(unique_id, measurements, use_same_timestamp=True):
#     """
#     Parse measurement data into list to be input into influxdb (flux edition, using influxdb_client)
#     :param unique_id: Unique ID of device
#     :param measurements: dict of measurements
#     :param use_same_timestamp: Allow influxdb to create the timestamp upon storage
#     :return:
#     """
#     from influxdb_client import InfluxDBClient
#     from influxdb_client import Point
#
#     with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org='-', timeout=5000) as client:
#         with client.write_api() as write_api:
#             for each_channel, each_measurement in measurements.items():
#                 if 'value' not in each_measurement or each_measurement['value'] is None:
#                     continue  # skip to next measurement to add
#
#                 if use_same_timestamp:
#                     # influxdb will create the timestamp when the data is stored
#                     timestamp = None
#                 else:
#                     # Use timestamp stored with each measurement
#                     timestamp = each_measurement['timestamp_utc']
#
#                 point = Point(each_measurement['unit']).tag("device_id", unique_id)
#
#                 if each_measurement['measurement']:
#                     point = point.tag("measure", each_measurement['measurement'])
#                 if each_channel is not None:
#                     point = point.tag("channel", each_channel)
#                 if timestamp:
#                     point = point.time(timestamp)
#
#                 point = point.field("value", each_measurement['value'])
#                 write_api.write(bucket=INFLUXDB_BUCKET, record=point)


# def query_flux(unit, unique_id,
#                value=None, measure=None, channel=None, ts_str=None,
#                start_str=None, end_str=None, past_sec=None, group_sec=None,
#                limit=None):
#     """Generate influxdb query string (flux edition, using influxdb_client)."""
#     from influxdb_client import InfluxDBClient
#
#     client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org='-', timeout=5000)
#     query_api = client.query_api()
#
#     query = f'from(bucket: \"{INFLUXDB_BUCKET}\")'
#
#     if past_sec:
#         query += f' |> range(start: -{past_sec}s)'
#     elif start_str and end_str:
#         query += f' |> range(start: {start_str}, stop: {end_str})'
#     elif start_str:
#         query += f' |> range(start: {start_str})'
#     elif end_str:
#         query += f' |> range(stop: {end_str})'
#     else:
#         query += f' |> range(start: -99999d)'
#
#     query += f' |> filter(fn: (r) => r["_measurement"] == "{unit}")'
#     query += f' |> filter(fn: (r) => r["device_id"] == "{unique_id}")'
#
#     if channel is not None:
#         query += f' |> filter(fn: (r) => r["channel"] == "{channel}")'
#     if measure:
#         query += f' |> filter(fn: (r) => r["measure"] == "{measure}")'
#     if ts_str:
#         query += " AND time = '{ts}'".format(ts=ts_str)
#
#     if group_sec:  # TODO: should be "mean". Fixed in influxdb 2.x, bugged in 1.8
#         query += f' |> aggregateWindow(every: {group_sec}s, fn: max)'
#     if limit:
#         query += f' |> limit(n:{limit})'
#
#     if value:  # value is deprecated. Use function instead.
#         if value == "LAST":
#             query += ' |> last()'
#         elif value == "FIRST":
#             query += ' |> first()'
#         elif value == "MAX":
#             query += ' |> max()'
#         elif value == "MIN":
#             query += ' |> min()'
#         elif value == "COUNT":
#             query += ' |> count()'
#
#         # TODO: fix these
#         # bug in influxdb 1.8: Error: panic: runtime error: invalid memory address or nil pointer dereference
#         # fix this when moving from influxdb 1.8 to 2.x
#         elif value == "SUM":
#             pass
#             # query += ' |> sum(column: "_value")'
#         elif value == "MEAN":
#             pass
#             # query += ' |> mean()'
#
#         else:
#             logger.error(f"query_flux(): Unknown value: '{value}'")
#             return 1
#
#     logger.debug(f"query_flux() query: '{query}'")
#
#     tables = query_api.query(query)
#
#     return tables

# coding=utf-8
import logging
import threading
import time

from influxdb import InfluxDBClient

from mycodo.databases.models import Misc
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.logging_utils import set_log_level

logger = logging.getLogger("mycodo.influxdb_1")
logger.setLevel(set_log_level(logging))


#
# For (influxdb 1.x)
#

def add_measurements_influxdb_1(unique_id, measurements, use_same_timestamp=True, block=False):
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
        settings = db_retrieve_table_daemon(Misc, entry='first')
        client = InfluxDBClient(
            settings.measurement_db_host,
            settings.measurement_db_port,
            settings.measurement_db_user,
            settings.measurement_db_password,
            settings.measurement_db_dbname,
            timeout=5)
        client.write_points(data)


def format_influxdb_data(unique_id, unit, value, channel=None, measure=None, timestamp=None):
    """
    Format data for entry into an Influxdb database

    example:
        format_influxdb_data('00000001', 'C', 37.5, measure='temperature', channel=0)
        format_influxdb_data('00000002', 's', 15.2, measure='duration_time', channel=1)

    :return: list of unit type, tags, and value
    :rtype: list

    :param unique_id: Alphanumeric ID associated with device
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


def write_influxdb_value_influx_1(unique_id, unit, value, measure=None, channel=None, timestamp=None):
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
    settings = db_retrieve_table_daemon(Misc, entry='first')
    client = InfluxDBClient(
        settings.measurement_db_host,
        settings.measurement_db_port,
        settings.measurement_db_user,
        settings.measurement_db_password,
        settings.measurement_db_dbname,
        timeout=5)

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


def query_string_influx_1(unit, unique_id,
                 value=None, measure=None, channel=None, ts_str=None,
                 start_str=None, end_str=None, past_sec=None, group_sec=None,
                 limit=None, function=None):
    """Generate influxdb query string."""
    from influxdb import InfluxDBClient

    settings = db_retrieve_table_daemon(Misc, entry='first')
    dbcon = InfluxDBClient(
        settings.measurement_db_host,
        settings.measurement_db_port,
        settings.measurement_db_user,
        settings.measurement_db_password,
        settings.measurement_db_dbname)

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

    raw_data = dbcon.query(query, epoch='u').raw

    if 'series' not in raw_data or not raw_data['series']:
        return None

    return raw_data['series'][0]['values']

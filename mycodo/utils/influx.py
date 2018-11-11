# coding=utf-8
import datetime
import logging
import threading
from uuid import UUID

import requests
from influxdb import InfluxDBClient

from mycodo.config import INFLUXDB_DATABASE
from mycodo.config import INFLUXDB_HOST
from mycodo.config import INFLUXDB_PASSWORD
from mycodo.config import INFLUXDB_PORT
from mycodo.config import INFLUXDB_USER
from mycodo.databases.models import Output
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon

logger = logging.getLogger("mycodo.influxdb")


def check_if_channel_measurement(measurement):
    if measurement.startswith('channel_'):
        """
        Check if measurement is from an analog-to-digital controller and 
        return proper measurement.
        """
        if (measurement.split('_')[3] == 'electrical_conductivity' and
                measurement.split('_')[4] == 'V'):
            measurement = 'channel_{chan}'.format(
                chan=measurement.split('_')[2])
        else:
            measurement = 'channel_{chan}_{meas}'.format(
                chan=measurement.split('_')[2],
                meas=measurement.split('_')[3])
    return measurement


def add_measurements_influxdb(unique_id, measurements):
    """

    :param unique_id: Unique ID of device
    :param measurements: dict of measurements
    :return:
    """
    data = []

    for each_channel, each_measurement in measurements.items():
        if 'value' in each_measurement:
            data.append(format_influxdb_data(
                unique_id,
                each_measurement['unit'],
                each_measurement['value'],
                channel=each_channel,
                measure=each_measurement['measurement']))

    write_db = threading.Thread(
        target=write_influxdb_list,
        args=(data,))
    write_db.start()


def add_measure_influxdb(unique_id, measurements, unit=None):
    """
    Add a measurement entries to InfluxDB

    :param unique_id:
    :param measurements:
    :param unit:
    :return: None
    """
    data = []
    for each_measurement, each_value in measurements.values.items():
        if unit:
            data.append(format_influxdb_data(unique_id,
                                             each_measurement,
                                             each_value,
                                             unit=unit))
        else:
            data.append(format_influxdb_data(unique_id,
                                             each_measurement,
                                             each_value))
    write_db = threading.Thread(
        target=write_influxdb_list,
        args=(data,))
    write_db.start()


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
        influx_dict['time'] = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return influx_dict


def query_string(unit, unique_id,
                 value=None, measure=None, channel=None,
                 ts_str=None, start_str=None, end_str=None,
                 past_sec=None, group_sec=None, limit=None):
    """Generate influxdb query string"""
    query = "SELECT "

    if value:
        if value in ['COUNT', 'LAST', 'MEAN', 'SUM']:
            query += "{value}(value)".format(value=value)
        else:
            return 1
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
        query += " AND time > now() - {sec}s".format(sec=past_sec)
    if group_sec:
        query += " GROUP BY TIME({sec}s)".format(sec=group_sec)
    if limit:
        query += " GROUP BY * LIMIT {lim}".format(lim=limit)
    return query


def read_past_influxdb(unique_id, unit, measurement, channel, past_seconds):
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    query_str = query_string(unit, unique_id,
                             measure=measurement,
                             channel=channel,
                             past_sec=past_seconds)
    if query_str == 1:
        return '', 204
    raw_data = client.query(query_str).raw
    if raw_data:
        return raw_data['series'][0]['values']


def read_last_influxdb(unique_id, unit, measurement, channel, duration_sec=None):
    """
    Query Influxdb for the last entry.

    example:
        read_last_influxdb('00000001', 'temperature')

    :return: list of time and value
    :rtype: list

    :param unique_id: What unique_id tag to query in the Influxdb
        database (eg. '00000001')
    :type unique_id: str
    :param unit: What unit to query in the Influxdb
        database (eg. 'C', 's')
    :type unit: str
    :param measurement: What measurement to query in the Influxdb
        database (eg. 'temperature', 'duration_time')
    :type measurement: str
    :param channel: Channel
    :type channel: int
    :param duration_sec: How many seconds to look for a past measurement
    :type duration_sec: int
    """
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)

    if duration_sec:
        query = query_string(unit, unique_id,
                             measure=measurement,
                             channel=channel,
                             past_sec=duration_sec)
    else:
        query = query_string(unit, unique_id,
                             measure=measurement,
                             channel=channel,
                             value='LAST')

    try:
        last_measurement = client.query(query).raw
    except requests.exceptions.ConnectionError:
        logger.debug("Failed to establish a new influxdb connection. Ensure influxdb is running.")
        last_measurement = None

    if last_measurement:
        try:
            number = len(last_measurement['series'][0]['values'])
            last_time = last_measurement['series'][0]['values'][number - 1][0]
            last_measurement = last_measurement['series'][0]['values'][number - 1][1]
            return [last_time, last_measurement]
        except KeyError:
            if duration_sec:
                logger.debug("No measurement available in the past "
                             "{sec} seconds.".format(sec=duration_sec))
            else:
                logger.debug("No measurement available.")
        except Exception:
            logger.exception("Error parsing the last influx measurement")


def output_sec_on(output_id, past_seconds):
    """ Return the number of seconds a output has been ON in the past number of seconds """
    # Get the number of seconds ON stored in the database
    output = db_retrieve_table_daemon(Output, unique_id=output_id)
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    if not output_id:
        return None

    # Get the number of seconds not stored in the database (if currently on)
    output_time_on = 0
    if output.is_on():
        control = DaemonControl()
        output_time_on = control.output_sec_currently_on(output_id)

    query = query_string('duration_time', output.unique_id, value='SUM',
                         past_sec=past_seconds)
    query_output = client.query(query)
    sec_recorded_on = 0
    if query_output:
        sec_recorded_on = query_output.raw['series'][0]['values'][0][1]

    sec_currently_on = 0
    if output_time_on:
        sec_currently_on = min(output_time_on, past_seconds)

    return sec_recorded_on + sec_currently_on


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


def write_influxdb_value(unique_id, measurement, value, unit=None, channel=None, timestamp=None):
    """
    Write a value into an Influxdb database

    example:
        write_influxdb_value('00000001', 'temperature', 37.5)

    :return: success (0) or failure (1)
    :rtype: bool

    :param unique_id: What unique_id tag to enter in the Influxdb
        database (ex. '00000001')
    :type unique_id: str
    :param measurement: What type of measurement for the Influxdb
        database entry (ex. 'temperature')
    :type measurement: str
    :param value: The value being entered into the Influxdb database
    :type value: int or float
    :param unit:
    :type unit:
    :param channel:
    :type channel:
    :param timestamp: If supplied, this timestamp will be used in the influxdb
    :type timestamp: datetime object
    """
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    data = [format_influxdb_data(unique_id,
                                 measurement,
                                 value,
                                 unit=unit,
                                 channel=channel,
                                 timestamp=timestamp)]

    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug(
            "Failed to write measurement to influxdb (Device ID: {id}). Data "
            "that was submitted for writing: {data}. Exception: {err}".format(
                id=unique_id, data=data, err=except_msg))
        return 1


def write_influxdb_list(data):
    """
    Write an entry into an Influxdb database

    example:
        write_influxdb('localINFLUXDB_HOST', 8086, 'mycodo', 'INFLUXDB_PASSWORD123',
                       'mycodo_db', data_list_of_dictionaries)

    :return: success (0) or failure (1)
    :rtype: bool

    :param data: The data being entered into Influxdb
    :type data: list of dictionaries
    """
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug(
            "Failed to write measurements to influxdb. Data that was "
            "submitted for writing: {data}. Exception: {err}".format(
                data=data, err=except_msg))
        return 1

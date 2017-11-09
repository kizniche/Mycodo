# coding=utf-8
import datetime
import logging
from uuid import UUID
from influxdb import InfluxDBClient
from mycodo.databases.models import Relay
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon

from mycodo.config import INFLUXDB_HOST
from mycodo.config import INFLUXDB_PORT
from mycodo.config import INFLUXDB_USER
from mycodo.config import INFLUXDB_PASSWORD
from mycodo.config import INFLUXDB_DATABASE

logger = logging.getLogger("mycodo.influxdb")


def format_influxdb_data(device_id, measure_type, value, timestamp=None):
    """
    Format data for entry into an Influxdb database

    example:
        format_influxdb_data('00000001', 'temperature', 37.5)
        format_influxdb_data('00000002', 'duration', 15.2)

    :return: list of measurement type, tags, and value
    :rtype: list

    :param device_id: 8-character alpha-numeric ID associated with device
    :type device_id: str
    :param measure_type: The type of data being entered into the Influxdb
        database (ex. 'temperature', 'duration')
    :type measure_type: str
    :param value: The value being entered into the Influxdb database
    :type value: int or float
    :param timestamp: If supplied, this timestamp will be used in the influxdb
    :type timestamp: datetime object

    """
    if timestamp:
        return {
            "measurement": measure_type,
            "tags": {
                "device_id": device_id
            },
            "time": timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "fields": {
                "value": value
            }
        }
    else:
        return {
            "measurement": measure_type,
            "tags": {
                "device_id": device_id
            },
            "fields": {
                "value": value
            }
        }


def query_string(measurement, unique_id, value=None,
                 start_str=None, end_str=None,
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

    query += " FROM {meas} WHERE device_id='{id}'".format(
        meas=measurement, id=unique_id)
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


def read_last_influxdb(device_id, measure_type, duration_sec=None):
    """
    Query Influxdb for the last entry.

    example:
        read_last_influxdb('00000001', 'temperature')

    :return: list of time and value
    :rtype: list

    :param device_id: What device_id tag to query in the Influxdb
        database (ex. '00000001')
    :type device_id: str
    :param measure_type: What measurement to query in the Influxdb
        database (ex. 'temperature', 'duration')
    :type measure_type: str
    :param duration_sec: How many seconds to look for a past measurement
    :type duration_sec: int
    """
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE)

    if duration_sec:
        query = query_string(measure_type, device_id, past_sec=duration_sec)
    else:
        query = query_string(measure_type, device_id, value='LAST')

    last_measurement = client.query(query).raw

    if last_measurement:
        try:
            number = len(last_measurement['series'][0]['values'])
            last_time = last_measurement['series'][0]['values'][number - 1][0]
            last_measurement = last_measurement['series'][0]['values'][number - 1][1]
            return [last_time, last_measurement]
        except KeyError:
            if duration_sec:
                logger.error("No measurement available in the past "
                             "{sec} seconds.".format(sec=duration_sec))
            else:
                logger.error("No measurement available.")
        except Exception:
            logger.exception("Error parsing the last influx measurement")


def relay_sec_on(relay_id, past_seconds):
    """ Return the number of seconds a relay has been ON in the past number of seconds """
    # Get the number of seconds ON stored in the database
    relay = db_retrieve_table_daemon(Relay, device_id=relay_id)
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE)
    if not relay_id:
        return None

    query = query_string('duration_sec', relay.unique_id, value='SUM',
                         past_sec=past_seconds)
    output = client.query(query)
    sec_recorded_on = 0
    if output:
        sec_recorded_on = output.raw['series'][0]['values'][0][1]

    # Get the number of seconds not stored in the database (if currently on)
    relay_time_on = 0
    if relay.is_on():
        control = DaemonControl()
        relay_time_on = control.relay_sec_currently_on(relay_id)

    sec_currently_on = 0
    if relay_time_on:
        sec_currently_on = min(relay_time_on, past_seconds)

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


def write_influxdb_value(device_id, measure_type, value, timestamp=None):
    """
    Write a value into an Influxdb database

    example:
        write_influxdb_value('00000001', 'temperature', 37.5)

    :return: success (0) or failure (1)
    :rtype: bool

    :param device_id: What device_id tag to enter in the Influxdb
        database (ex. '00000001')
    :type device_id: str
    :param measure_type: What type of measurement for the Influxdb
        database entry (ex. 'temperature')
    :type measure_type: str
    :param value: The value being entered into the Influxdb database
    :type value: int or float
    :param timestamp: If supplied, this timestamp will be used in the influxdb
    :type timestamp: datetime object
    """
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE)
    data = [format_influxdb_data(device_id,
                                 measure_type,
                                 value,
                                 timestamp)]

    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug(
            "Failed to write measurement to influxdb (Device ID: {id}). Data "
            "that was submitted for writing: {data}. Exception: {err}".format(
                id=device_id, data=data, err=except_msg))
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
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE)
    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug(
            "Failed to write measurements to influxdb. Data that was "
            "submitted for writing: {data}. Exception: {err}".format(
                data=data, err=except_msg))
        return 1

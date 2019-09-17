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
from mycodo.databases.models import Output
from mycodo.inputs.sensorutils import convert_units
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon

logger = logging.getLogger("mycodo.influxdb")

if logging.getLevelName(logging.getLogger().getEffectiveLevel()) == 'INFO':
    logger.setLevel(logging.INFO)


def add_measurements_influxdb(unique_id, measurements, use_same_timestamp=True):
    """
    Parse measurement data into list to be input into influxdb
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

    write_db = threading.Thread(
        target=write_influxdb_list,
        args=(data,unique_id,))
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
        # Timestamp (UTC) can either be received as:
        # 1. datetime object
        # 2. string in the format %Y-%m-%dT%H:%M:%S.%fZ
        if isinstance(timestamp, str):
            influx_dict['time'] = timestamp
        else:
            influx_dict['time'] = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return influx_dict


def parse_measurement(conversion,
                      measurement,
                      measurements_record,
                      each_channel,
                      each_measurement,
                      timestamp=None):
    # Unscaled, unconverted measurement
    measurements_record[each_channel] = {
        'measurement': each_measurement['measurement'],
        'unit': each_measurement['unit'],
        'value': each_measurement['value'],
        'timestamp_utc': timestamp
    }

    # Scaling needs to come before conversion
    # Scale measurement
    if (measurement.rescaled_measurement and
            measurement.rescaled_unit):
        scaled_value = measurements_record[each_channel] = rescale_measurements(
            measurement, measurements_record[each_channel]['value'])
        measurements_record[each_channel] = {
            'measurement': measurement.rescaled_measurement,
            'unit': measurement.rescaled_unit,
            'value': scaled_value,
            'timestamp_utc': timestamp
        }

    # Convert measurement
    if measurement.conversion_id not in ['', None] and 'value' in each_measurement:
        converted_value = convert_units(
            measurement.conversion_id,
            measurements_record[each_channel]['value'])
        measurements_record[each_channel] = {
            'measurement': None,
            'unit': conversion.convert_unit_to,
            'value': converted_value,
            'timestamp_utc': timestamp
        }
    return measurements_record


def rescale_measurements(measurement, measurement_value):
    """ Read channels """
    try:

        # Get the difference between min and max volts
        diff_voltage = abs(
            float(measurement.scale_from_max) - float(measurement.scale_from_min))

        # Ensure the value stays within the min/max bounds
        if measurement_value < float(measurement.scale_from_min):
            measured_voltage = measurement.scale_from_min
        elif measurement_value > float(measurement.scale_from_max):
            measured_voltage = float(measurement.scale_from_max)
        else:
            measured_voltage = measurement_value

        # Calculate the percentage of the difference
        percent_diff = ((measured_voltage - float(measurement.scale_from_min)) /
                        diff_voltage)

        # Get the units difference between min and max units
        diff_units = abs(float(measurement.scale_to_max) - float(measurement.scale_to_min))

        # Calculate the measured units from the percent difference
        if measurement.invert_scale:
            converted_units = (float(measurement.scale_to_max) -
                               (diff_units * percent_diff))
        else:
            converted_units = (float(measurement.scale_to_min) +
                               (diff_units * percent_diff))

        # Ensure the units stay within the min/max bounds
        if converted_units < float(measurement.scale_to_min):
            rescaled_measurement = float(measurement.scale_to_min)
        elif converted_units > float(measurement.scale_to_max):
            rescaled_measurement = float(measurement.scale_to_max)
        else:
            rescaled_measurement = converted_units

        return rescaled_measurement

    except Exception as except_msg:
        logger.exception(
            "Error while attempting to rescale measurement: {err}".format(
                err=except_msg))


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
    raw_data = None
    client = InfluxDBClient(
        INFLUXDB_HOST,
        INFLUXDB_PORT,
        INFLUXDB_USER,
        INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE,
        timeout=5)
    query_str = query_string(
        unit,
        unique_id,
        measure=measurement,
        channel=channel,
        past_sec=past_seconds)
    if query_str == 1:
        return '', 204
    try:
        raw_data = client.query(query_str).raw
    except:
        logger.debug(
            "Could not read form influxdb for ID {}, channel {}. "
            "waiting 15 seconds and trying again.".format(unique_id, channel))
        time.sleep(15)
        try:
            raw_data = client.query(query_str).raw
        except:
            logger.debug("Could not read form influxdb after waiting 15 seconds.")

    if raw_data and 'series' in raw_data:
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
    :type measurement: str or None
    :param channel: Channel
    :type channel: int or None
    :param duration_sec: How many seconds to look for a past measurement
    :type duration_sec: int or None
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
        logger.debug(
            "Could not read form influxdb for ID {}, channel {}. "
            "waiting 15 seconds and trying again.".format(unique_id, channel))
        time.sleep(15)
        try:
            last_measurement = client.query(query).raw
        except requests.exceptions.ConnectionError:
            logger.debug("Failed to establish a new influxdb connection. Ensure influxdb is running.")
            last_measurement = None

    if last_measurement and 'series' in last_measurement:
        try:
            number = len(last_measurement['series'][0]['values'])
            last_time = last_measurement['series'][0]['values'][number - 1][0]
            last_measurement = last_measurement['series'][0]['values'][number - 1][1]
            return [last_time, last_measurement]
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

    query = query_string('s', output.unique_id,
                         measure='duration_time',
                         channel=0,
                         value='SUM',
                         past_sec=past_seconds)
    query_output = client.query(query)
    sec_recorded_on = 0
    if query_output:
        sec_recorded_on = query_output.raw['series'][0]['values'][0][1]

    sec_currently_on = 0
    if output_time_on:
        sec_currently_on = min(output_time_on, past_seconds)

    return sec_recorded_on + sec_currently_on


def average_past_seconds(unique_id, unit, channel, past_seconds, measure=None):
    """Return measurement average for the past x seconds"""
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    query = query_string(unit, unique_id,
                         measure=measure,
                         channel=channel,
                         value='MEAN',
                         past_sec=past_seconds)
    query_output = client.query(query)
    if query_output:
        return query_output.raw['series'][0]['values'][0][1]


def average_start_end_seconds(unique_id, unit, channel, str_start, str_end, measure=None):
    """Return measurement average for a period of time"""
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    query = query_string(unit, unique_id,
                         measure=measure,
                         channel=channel,
                         value='MEAN',
                         start_str=str_start,
                         end_str=str_end)
    query_output = client.query(query)
    if query_output:
        return query_output.raw['series'][0]['values'][0][1]


def sum_past_seconds(unique_id, unit, channel, past_seconds, measure=None):
    """Return measurement sum for the past x seconds"""
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    query = query_string(unit, unique_id,
                         measure=measure,
                         channel=channel,
                         value='SUM',
                         past_sec=past_seconds)
    query_output = client.query(query)
    if query_output:
        return query_output.raw['series'][0]['values'][0][1]


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


def write_influxdb_value(
        unique_id, unit, value, measure=None, channel=None, timestamp=None):
    """
    Write a value into an Influxdb database

    example:
        write_influxdb_value('00000001', 'temperature', 37.5)

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
    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    data = [format_influxdb_data(unique_id,
                                 unit,
                                 value,
                                 channel=channel,
                                 measure=measure,
                                 timestamp=timestamp)]

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


def write_influxdb_list(data, unique_id):
    """
    Write an entry into an Influxdb database

    example:
        write_influxdb('localINFLUXDB_HOST', 8086, 'mycodo', 'INFLUXDB_PASSWORD123',
                       'mycodo_db', data_list_of_dictionaries)

    :return: success (0) or failure (1)
    :rtype: bool

    :param data: The data being entered into Influxdb
    :type data: list of dictionaries
    :param unique_id: For logging purposes
    :type unique_id: str
    """
    if not data:
        logger.debug("No data for ID {}. Not writing to influxdb".format(unique_id))
        return

    client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER,
                            INFLUXDB_PASSWORD, INFLUXDB_DATABASE, timeout=5)
    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug("Failed to write measurements to influxdb. "
                     "Retrying in 30 seconds. Data: {}".format(data))
        time.sleep(30)
        try:
            client.write_points(data)
            logger.debug("Successfully wrote measurements to influxdb after "
                         "30-second wait. Data: {}".format(data))
            return 0
        except:
            logger.debug(
                "Failed to write measurements to influxdb. Data that was "
                "submitted for writing: {data}. Exception: {err}".format(
                    data=data, err=except_msg))
            return 1

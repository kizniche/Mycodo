# coding=utf-8
import datetime
import logging

import requests

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influxdb_1 import add_measurements_influxdb_1
from mycodo.utils.influxdb_1 import query_string_influx_1
from mycodo.utils.influxdb_1 import write_influxdb_value_influx_1
from mycodo.utils.influxdb_2 import add_measurements_influxdb_flux
from mycodo.utils.influxdb_2 import query_flux
from mycodo.utils.influxdb_2 import write_influxdb_value_flux
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
    settings = db_retrieve_table_daemon(Misc, entry='first')

    if settings.measurement_db_name == "influxdb":
        if settings.measurement_db_version == "1":
            add_measurements_influxdb_1(
                unique_id, measurements, use_same_timestamp=use_same_timestamp, block=block)
        elif settings.measurement_db_version == "2":
            add_measurements_influxdb_flux(
                unique_id, measurements, use_same_timestamp=use_same_timestamp)


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
    ret_value = None
    settings = db_retrieve_table_daemon(Misc, entry='first')

    if settings.measurement_db_name == "influxdb":
        if settings.measurement_db_version == "1":
            ret_value = write_influxdb_value_influx_1(
                unique_id, unit, value, measure=measure, channel=channel, timestamp=timestamp)
        elif settings.measurement_db_version == "2":
            ret_value = write_influxdb_value_flux(
                unique_id, unit, value, measure=measure, channel=channel, timestamp=timestamp)

    return ret_value


def query_string(unit, unique_id,
                 value=None, measure=None, channel=None, ts_str=None,
                 start_str=None, end_str=None, past_sec=None, group_sec=None,
                 limit=None, function=None):
    """Generate influxdb query string."""
    ret_value = None
    settings = db_retrieve_table_daemon(Misc, entry='first')

    if settings.measurement_db_name == "influxdb":
        if settings.measurement_db_version == "1":
            ret_value = query_string_influx_1(
                unit, unique_id,
                value=value, measure=measure, channel=channel, ts_str=ts_str,
                start_str=start_str, end_str=end_str, past_sec=past_sec, group_sec=group_sec,
                limit=limit, function=function)
        elif settings.measurement_db_version == "2":
            ret_value = query_flux(
                unit, unique_id,
                value=value, measure=measure, channel=channel, ts_str=ts_str,
                start_str=start_str, end_str=end_str, past_sec=past_sec, group_sec=group_sec,
                limit=limit)

    return ret_value


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


def read_influxdb_single(unique_id, unit, channel,
                         measure=None,
                         duration_sec=None,
                         start_str=None,
                         end_str=None,
                         value='LAST',
                         datetime_obj=False):
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
    :param datetime_obj: return a datetime object as a time
    :type datetime_obj: bool
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
                settings = db_retrieve_table_daemon(Misc, entry='first')
                if settings.measurement_db_name == 'influxdb':
                    if settings.measurement_db_version == '2':
                        for table in data:
                            for row in table.records:
                                if datetime_obj:
                                    time = row.values['_time']
                                else:
                                    time = row.values['_time'].timestamp() * 1000
                                return [time, row.values['_value']]

                    elif settings.measurement_db_version == '1':
                        number = len(data)
                        last_time = data[number - 1][0]
                        last_measurement = data[number - 1][1]
                        return [last_time, last_measurement]
            except Exception:
                logger.exception("Error parsing the last influx measurement")
    except requests.exceptions.ConnectionError:
        logger.debug("Failed to establish a new influxdb connection. Ensure influxdb is running.")


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
                       end_str=None,
                       datetime_obj=False):
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
    :param datetime_obj: return a datetime object as a time
    :type datetime_obj: bool
    """
    try:
        data = query_string(
            unit, unique_id,
            measure=measure,
            channel=channel,
            start_str=start_str,
            end_str=end_str,
            past_sec=duration_sec)

        settings = db_retrieve_table_daemon(Misc, entry='first')
        if settings.measurement_db_name == 'influxdb':
            if settings.measurement_db_version == '2':
                list_data = []
                for table in data:
                    for row in table.records:
                        if datetime_obj:
                            time = row.values['_time']
                        else:
                            time = row.values['_time'].timestamp() * 1000
                        list_data.append((time, row.values['_value']))
                return list_data

            elif settings.measurement_db_version == '1':
                return data
    except:
        logger.debug("Could not read form influxdb.")


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
        settings = db_retrieve_table_daemon(Misc, entry='first')
        if settings.measurement_db_name == 'influxdb':
            if settings.measurement_db_version == '2':
                for table in data:
                    for row in table.records:
                        sec_recorded_on = row.values['_value']

            elif settings.measurement_db_version == '1':
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
        settings = db_retrieve_table_daemon(Misc, entry='first')
        if settings.measurement_db_name == 'influxdb':
            if settings.measurement_db_version == '2':
                for table in data:
                    for row in table.records:
                        return row.values['_value']

            elif settings.measurement_db_version == '1':
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
        settings = db_retrieve_table_daemon(Misc, entry='first')
        if settings.measurement_db_name == 'influxdb':
            if settings.measurement_db_version == '2':
                for table in data:
                    for row in table.records:
                        return row.values['_value']

            elif settings.measurement_db_version == '1':
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
        settings = db_retrieve_table_daemon(Misc, entry='first')
        if settings.measurement_db_name == 'influxdb':
            if settings.measurement_db_version == '2':
                for table in data:
                    for row in table.records:
                        return row.values['_value']

            elif settings.measurement_db_version == '1':
                return data[0][1]


def influx_time_str_to_milliseconds(timestamp):
    """Converts InfluxDB time string with "Z" from nanoseconds to milliseconds and removes the Z."""
    if type(timestamp) == datetime:
        start_date_time = timestamp.split('Z')[0].split('.')[0]
        start_milliseconds = timestamp.split('Z')[0].split('.')[1][:3]
    elif type(timestamp) == str:
        start_date_time = timestamp.split('Z')[0].split('.')[0]
        start_milliseconds = timestamp.split('Z')[0].split('.')[1][:3]
    else:
        return
    return '{}.{}'.format(start_date_time, start_milliseconds)


def valid_date_str(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        logger.exception(1)
        return False
    return True


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

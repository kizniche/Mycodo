# coding=utf-8
import datetime
import logging
import threading
import time

import requests

from mycodo.databases.models import (Conversion, DeviceMeasurements, Misc,
                                     Output)
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import return_measurement_info

logger = logging.getLogger("mycodo.influx")


#
# Influxdb using Flux (influxdb versions 1.8+ and 2.x)
#

def write_influxdb_value(unique_id, unit, value, measure=None, channel=None, timestamp=None):
    """
    Write a value into an Influxdb database (flux edition, using influxdb_client)

    example:
        write_influxdb_value('00000001', 'C', 37.5)

    :return: success (0) or failure (1)
    :rtype: bool

    :param unique_id: What unique_id tag to enter into the Influxdb database (ex. '00000001')
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
    from influxdb_client import InfluxDBClient, Point

    settings = db_retrieve_table_daemon(Misc, entry='first')
    influxdb_url = f'http://{settings.measurement_db_host}:{settings.measurement_db_port}'

    if settings.measurement_db_version == '1':
        client = InfluxDBClient(
            url=influxdb_url,
            token=f'{settings.measurement_db_user}:{settings.measurement_db_password}',
            org='mycodo',
            timeout=5000)
        bucket = f'{settings.measurement_db_dbname}/{settings.measurement_db_retention_policy}'
    elif settings.measurement_db_version == '2':
        client = InfluxDBClient(
            url=influxdb_url,
            username=settings.measurement_db_user,
            password=settings.measurement_db_password,
            org='mycodo',
            timeout=5000)
        bucket = settings.measurement_db_dbname
    else:
        logger.error(f"Unknown Influxdb version: {settings.measurement_db_version}")
        return

    with client.write_api(success_callback=write_success, error_callback=write_fail) as write_api:
        point = Point(unit).tag("device_id", unique_id)

        if measure:
            point = point.tag("measure", measure)
        if channel is not None:
            point = point.tag("channel", channel)
        if timestamp:
            point = point.time(timestamp)

        point = point.field("value", value)

        try:
            write_api.write(bucket=bucket, record=point)
            return 0
        except Exception as except_msg:
            logger.debug(f"Failed to write measurements to influxdb with ID {unique_id}. Retrying in 5 seconds.")
            time.sleep(5)
            try:
                write_api.write(bucket=bucket, record=point)
                return 0
            except:
                logger.debug(
                    f"Failed to write measurement to influxdb (Device ID: {unique_id}): {except_msg}.")
                return 1


def add_measurements_influxdb_flux(unique_id, measurements, use_same_timestamp=True, block=False):
    """
    Parse measurement data into list to be input into influxdb (flux edition, using influxdb_client)
    :param unique_id: Unique ID of device
    :param measurements: dict of measurements
    :param use_same_timestamp: Allow influxdb to create the timestamp upon storage
    :return:
    """
    from influxdb_client import InfluxDBClient, Point

    settings = db_retrieve_table_daemon(Misc, entry='first')
    influxdb_url = f'http://{settings.measurement_db_host}:{settings.measurement_db_port}'

    if settings.measurement_db_version == '1':
        client = InfluxDBClient(
            url=influxdb_url,
            token=f'{settings.measurement_db_user}:{settings.measurement_db_password}',
            org='mycodo',
            timeout=5000)
        bucket = f'{settings.measurement_db_dbname}/{settings.measurement_db_retention_policy}'
    elif settings.measurement_db_version == '2':
        client = InfluxDBClient(
            url=influxdb_url,
            username=settings.measurement_db_user,
            password=settings.measurement_db_password,
            org='mycodo',
            timeout=5000)
        bucket = settings.measurement_db_dbname
    else:
        logger.error(f"Unknown Influxdb version: {settings.measurement_db_version}")
        return

    with client.write_api(success_callback=write_success, error_callback=write_fail) as write_api:
        for each_channel, each_measurement in measurements.items():
            if 'value' not in each_measurement or each_measurement['value'] is None:
                continue  # skip to next measurement to add

            if use_same_timestamp:
                # influxdb will create the timestamp when the data is stored
                timestamp = None
            else:
                # Use timestamp stored with each measurement
                timestamp = each_measurement['timestamp_utc']

            point = Point(each_measurement['unit']).tag("device_id", unique_id)

            if each_measurement['measurement']:
                point = point.tag("measure", each_measurement['measurement'])
            if each_channel is not None:
                point = point.tag("channel", each_channel)
            if timestamp:
                point = point.time(timestamp)

            point = point.field("value", each_measurement['value'])
            write_api.write(bucket=bucket, record=point)


def write_fail(point_data, written_data, err):
    logger.debug(f"Write point fail: {err}: {written_data}")


def write_success(point_data, written_data):
    logger.debug(f"Write point success: {written_data}")


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
        add_measurements_influxdb_flux(unique_id, measurements, use_same_timestamp)
    else:
        write_db = threading.Thread(
            target=add_measurements_influxdb_flux,
            args=(unique_id, measurements, use_same_timestamp,))
        write_db.start()


def query_flux(unit, unique_id,
               value=None, measure=None, channel=None, ts_str=None,
               start_str=None, end_str=None, min_value=None, max_value=None, past_sec=None, group_sec=None,
               limit=None):
    """Generate influxdb query string (flux edition, using influxdb_client)."""
    from influxdb_client import InfluxDBClient

    settings = db_retrieve_table_daemon(Misc, entry='first')
    influxdb_url = f'http://{settings.measurement_db_host}:{settings.measurement_db_port}'

    if settings.measurement_db_version == '1':
        client = InfluxDBClient(
            url=influxdb_url,
            token=f'{settings.measurement_db_user}:{settings.measurement_db_password}',
            org='mycodo',
            timeout=60000)
        bucket = f'{settings.measurement_db_dbname}/{settings.measurement_db_retention_policy}'
    elif settings.measurement_db_version == '2':
        client = InfluxDBClient(
            url=influxdb_url,
            username=settings.measurement_db_user,
            password=settings.measurement_db_password,
            org='mycodo',
            timeout=60000)
        bucket = settings.measurement_db_dbname
    else:
        logger.error(f"Unknown Influxdb version: {settings.measurement_db_version}")
        return

    query = f'from(bucket: "{bucket}")'

    if past_sec:
        query += f' |> range(start: -{int(past_sec)}s)'
    elif start_str and end_str:
        query += f' |> range(start: {start_str}, stop: {end_str})'
    elif start_str:
        query += f' |> range(start: {start_str})'
    elif end_str:
        query += f' |> range(stop: {end_str})'
    else:
        query += f' |> range(start: -99999d)'

    if min_value:
        query += f' |> filter(fn: (r) => r._value > {min_value})'
    if max_value:
        query += f' |> filter(fn: (r) => r._value < {max_value})'

    query += f' |> filter(fn: (r) => r["_measurement"] == "{unit}")'
    query += f' |> filter(fn: (r) => r["device_id"] == "{unique_id}")'

    if channel is not None:
        query += f' |> filter(fn: (r) => r["channel"] == "{channel}")'
    if measure:
        query += f' |> filter(fn: (r) => r["measure"] == "{measure}")'
    if ts_str:
        query += " AND time = '{ts}'".format(ts=ts_str)

    if group_sec:
        if settings.measurement_db_version == '1':
            # TODO: Change median to mean when issue is fixed
            # Bug in influxdb/Flux v1.8.10 due to mean
            # Error: panic: runtime error: invalid memory address or nil pointer dereference
            # https://github.com/influxdata/influxdb/issues/21649
            # https://github.com/influxdata/influxdb/pull/23520
            query += f' |> aggregateWindow(every: {group_sec}s, fn: median)'
        elif settings.measurement_db_version == '2':
            query += f' |> aggregateWindow(every: {group_sec}s, fn: mean)'

    if limit:
        query += f' |> limit(n:{limit})'

    if value:
        if value == "LAST":
            query += ' |> last()'
        elif value == "FIRST":
            query += ' |> first()'
        elif value == "MAX":
            query += ' |> max()'
        elif value == "MIN":
            query += ' |> min()'
        elif value == "COUNT":
            query += ' |> count()'
        elif value == "SUM":
            if settings.measurement_db_version == '1':
                # TODO: Change when issue is fixed
                # Bug in influxdb/Flux v1.8.10 due to mean
                # Error: panic: runtime error: invalid memory address or nil pointer dereference
                # https://github.com/influxdata/influxdb/issues/21649
                # https://github.com/influxdata/influxdb/pull/23520
                logger.error("SUM cannot be used with influxdb 1.8.10 without causing an error. "
                             "Returning all measurements for period to manually sum.")
            elif settings.measurement_db_version == '2':
                query += ' |> sum(column: "_value")'
        elif value == "MEAN":
            if settings.measurement_db_version == '1':
                # TODO: Change median to mean when issue is fixed
                # Bug in influxdb/Flux v1.8.10 due to mean
                # Error: panic: runtime error: invalid memory address or nil pointer dereference
                # https://github.com/influxdata/influxdb/issues/21649
                # https://github.com/influxdata/influxdb/pull/23520
                query += ' |> median()'
            elif settings.measurement_db_version == '2':
                query += ' |> mean()'

    logger.debug(f"query_flux() query: '{query}'")

    tables = client.query_api().query(query)
    client.close()

    return tables


def query_string(unit, unique_id,
                 value=None, measure=None, channel=None, ts_str=None,
                 start_str=None, end_str=None, min_value=None, max_value=None,
                 past_sec=None, group_sec=None, limit=None):
    """Generate influxdb query string."""
    ret_value = None
    settings = db_retrieve_table_daemon(Misc, entry='first')

    if settings.measurement_db_name == "influxdb":
        ret_value = query_flux(
            unit, unique_id,
            value=value, measure=measure, channel=channel, ts_str=ts_str,
            start_str=start_str, end_str=end_str, min_value=min_value, max_value=max_value,
            past_sec=past_sec, group_sec=group_sec, limit=limit)

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
                    for table in data:
                        for row in table.records:
                            if datetime_obj:
                                last_time = row.values['_time']
                            else:
                                last_time = row.values['_time'].timestamp()
                            return [last_time, row.values['_value']]
            except Exception:
                logger.exception("Error parsing the last influx measurement")
    except requests.exceptions.ConnectionError:
        logger.debug("Failed to establish a new influxdb connection. Ensure influxdb is running.")

    return [None, None]


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
            list_data = []
            for table in data:
                for row in table.records:
                    if datetime_obj:
                        time = row.values['_time']
                    else:
                        time = row.values['_time'].timestamp()
                    list_data.append((time, row.values['_value']))
            return list_data
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
            if settings.measurement_db_version == '1':
                # TODO: remove when influxdb 1.8.10 issue is fixed
                for table in data:
                    for row in table.records:
                        sec_recorded_on += row.values['_value']
            elif settings.measurement_db_version == '2':
                for table in data:
                    for row in table.records:
                        sec_recorded_on = row.values['_value']

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
            for table in data:
                for row in table.records:
                    return row.values['_value']


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
            for table in data:
                for row in table.records:
                    return row.values['_value']


def sum_past_seconds(unique_id, unit, channel, past_seconds, measure=None):
    """Return measurement sum for the past x seconds."""
    data = query_string(
        unit, unique_id,
        measure=measure,
        channel=channel,
        value='SUM',
        past_sec=past_seconds)

    if data:
        total_seconds = 0
        settings = db_retrieve_table_daemon(Misc, entry='first')
        if settings.measurement_db_name == 'influxdb':
            if settings.measurement_db_version == '1':
                # TODO: remove when influxdb 1.8.10 issue is fixed
                for table in data:
                    for row in table.records:
                        total_seconds += row.values['_value']
                return total_seconds
            elif settings.measurement_db_version == '2':
                for table in data:
                    for row in table.records:
                        total_seconds = row.values['_value']
        return total_seconds


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


def influx_to_list(data):
    list_data = []
    for table in data:
        for row in table.records:
            list_data.append((row.values['_time'].timestamp(), row.values['_value']))
    return list_data


def influxdb_get_count_points(data):
    for table in data:
        for record in table.records:
            return record.values['_value']


def influxdb_get_first_point(data):
    for table in data:
        for record in table.records:
            return record.values['_time']


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

# coding=utf-8
import logging
import time

from mycodo.databases.models import Misc
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.logging_utils import set_log_level

logger = logging.getLogger("mycodo.influxdb_2")
logger.setLevel(set_log_level(logging))

#
# For influxdb-client (influxdb 2.x)
#

def write_influxdb_value_flux(unique_id, unit, value, measure=None, channel=None, timestamp=None):
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
    from influxdb_client import InfluxDBClient
    from influxdb_client import Point

    settings = db_retrieve_table_daemon(Misc, entry='first')
    influxdb_url = f'http://{settings.measurement_db_host}:{settings.measurement_db_port}'

    with InfluxDBClient(
            url=influxdb_url,
            username=settings.measurement_db_user,
            password=settings.measurement_db_password,
            org='mycodo',
            timeout=5000) as client:
        with client.write_api() as write_api:
            point = Point(unit).tag("device_id", unique_id)

            if measure:
                point = point.tag("measure", measure)
            if channel is not None:
                point = point.tag("channel", channel)
            if timestamp:
                point = point.time(timestamp)

            point = point.field("value", value)
            write_api.write(bucket=settings.measurement_db_dbname, record=point)

            try:
                write_api.write(bucket=settings.measurement_db_dbname, record=point)
                return 0
            except Exception as except_msg:
                logger.debug("Failed to write measurements to influxdb with ID {}. "
                             "Retrying in 5 seconds.".format(unique_id))
                time.sleep(5)
                try:
                    write_api.write(bucket=settings.measurement_db_dbname, record=point)
                    logger.debug("Successfully wrote measurements to influxdb after 5-second wait.")
                    return 0
                except:
                    logger.debug(
                        f"Failed to write measurement to influxdb (Device ID: {unique_id}): {except_msg}.")
                    return 1


def add_measurements_influxdb_flux(unique_id, measurements, use_same_timestamp=True):
    """
    Parse measurement data into list to be input into influxdb (flux edition, using influxdb_client)
    :param unique_id: Unique ID of device
    :param measurements: dict of measurements
    :param use_same_timestamp: Allow influxdb to create the timestamp upon storage
    :return:
    """
    from influxdb_client import InfluxDBClient
    from influxdb_client import Point

    settings = db_retrieve_table_daemon(Misc, entry='first')
    influxdb_url = f'http://{settings.measurement_db_host}:{settings.measurement_db_port}'

    with InfluxDBClient(
            url=influxdb_url,
            username=settings.measurement_db_user,
            password=settings.measurement_db_password,
            org='mycodo',
            timeout=5000) as client:
        with client.write_api() as write_api:
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
                write_api.write(bucket=settings.measurement_db_dbname, record=point)


def query_flux(unit, unique_id,
               value=None, measure=None, channel=None, ts_str=None,
               start_str=None, end_str=None, past_sec=None, group_sec=None,
               limit=None):
    """Generate influxdb query string (flux edition, using influxdb_client)."""
    from influxdb_client import InfluxDBClient

    settings = db_retrieve_table_daemon(Misc, entry='first')
    influxdb_url = f'http://{settings.measurement_db_host}:{settings.measurement_db_port}'

    client = InfluxDBClient(
        url=influxdb_url,
        username=settings.measurement_db_user,
        password=settings.measurement_db_password,
        org='mycodo',
        timeout=5000)
    query_api = client.query_api()

    query = f'from(bucket: \"{settings.measurement_db_dbname}\")'

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

    query += f' |> filter(fn: (r) => r["_measurement"] == "{unit}")'
    query += f' |> filter(fn: (r) => r["device_id"] == "{unique_id}")'

    if channel is not None:
        query += f' |> filter(fn: (r) => r["channel"] == "{channel}")'
    if measure:
        query += f' |> filter(fn: (r) => r["measure"] == "{measure}")'
    if ts_str:
        query += " AND time = '{ts}'".format(ts=ts_str)

    if group_sec:
        query += f' |> aggregateWindow(every: {group_sec}s, fn: mean)'
    if limit:
        query += f' |> limit(n:{limit})'

    if value:  # value is deprecated. Use function instead.
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

        # bug in influxdb 1.8: Error: panic: runtime error: invalid memory address or nil pointer dereference
        # fix this when moving from influxdb 1.8 to 2.x
        elif value == "SUM":
            query += ' |> sum(column: "_value")'
        elif value == "MEAN":
            query += ' |> mean()'

        else:
            logger.error(f"query_flux(): Unknown value: '{value}'")
            return 1

    logger.debug(f"query_flux() query: '{query}'")

    tables = query_api.query(query)

    return tables

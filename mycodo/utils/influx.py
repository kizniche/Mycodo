# coding=utf-8

from influxdb import InfluxDBClient


#
# Influxdb
#

def format_influxdb_data(device_type, device_id, measure_type, value, timestamp=None):
    """
    Format data for entry into an Influxdb database

    example:
        format_influxdb_data('tsensor', '00000001', 'temperature', 37.5)
        format_influxdb_data('relay', '00000002', 'duration', 15.2)

    :return: list of measurement type, tags, and value
    :rtype: list

    :param device_type: The type of device (ex. 'tsensor', 'htsensor',
        'co2sensor', 'relay')
    :type device_type: str
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
                "device_id": device_id,
                "device_type": device_type
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
                "device_id": device_id,
                "device_type": device_type
            },
            "fields": {
                "value": value
            }
        }


def read_last_influxdb(host, port, user, password, dbname,
                       device_id, measure_type, duration_sec=None):
    """
    Query Influxdb for the last entry within the past minute,
    for a set of conditions.

    example:
        read_last_influxdb('localhost', 8086, 'mycodo', 'password123',
                           'mycodo_db', '00000001', 'temperature')

    :return: list of time and value
    :rtype: list

    :param host: What influxdb address
    :type host: str
    :param port: What influxdb port
    :type port: int
    :param user: What user to connect to influxdb with
    :type user: str
    :param password: What password to supply for Influxdb user
    :type password: str
    :param dbname: What Influxdb database name to write to
    :type dbname: str
    :param device_id: What device_id tag to query in the Influxdb
        database (ex. '00000001')
    :type device_id: str
    :param measure_type: What measurement to query in the Influxdb
        database (ex. 'temperature', 'duration')
    :type measure_type: str
    :param duration_sec: How many minutes to look for a past measurement
    :type duration_sec: int
    """
    client = InfluxDBClient(host, port, user, password, dbname)

    if duration_sec:
        query = """SELECT value
                       FROM   {}
                       WHERE  device_id = '{}'
                              AND TIME > Now() - {}s
                              ORDER BY time
                              DESC LIMIT 1;
                """.format(measure_type, device_id, duration_sec)
    else:
        query = """SELECT value
                       FROM   {}
                       WHERE  device_id = '{}'
                              ORDER BY time
                              DESC LIMIT 1;
                """.format(measure_type, device_id)

    return client.query(query)


def write_influxdb_value(logger, host, port, user, password,
                         dbname, device_type, device_id,
                         measure_type, value, timestamp=None):
    """
    Write a value into an Influxdb database

    example:
        write_influxdb(logger, 'localhost', 8086, 'mycodo', 'password123',
                       'mycodo_db', 'tsensor', 00000001', 'temperature', 37.5)

    :return: success (0) or failure (1)
    :rtype: bool

    :param logger: Oject to log to
    :type logger: logger object
    :param host: What influxdb address
    :type host: str
    :param port: What influxdb port
    :type port: int
    :param user: What user to connect to influxdb with
    :type user: str
    :param password: What password to supply for Influxdb user
    :type password: str
    :param dbname: What Influxdb database name to write to
    :type dbname: str
    :param device_type: What device_type tag to enter in the Influxdb
        database (ex. 'tsensor', 'relay')
    :type device_type: str
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
    client = InfluxDBClient(host, port, user, password, dbname)
    data = [format_influxdb_data(device_type,
                                 device_id,
                                 measure_type,
                                 value,
                                 timestamp)]
    try:
        client.write_points(data)
        # logger.debug('Write {} {} to {}, '
        #       'device_id={} device_type={}'.format(value,
        #                                            measure_type,
        #                                            dbname,
        #                                            device_id,
        #                                            device_type))
        return 0
    except Exception as except_msg:
        logger.debug('Failed to write measurement to influxdb (Device ID: '
                     '{}). Data that was submitted for writing: {}. '
                     'Exception: {}'.format(device_id, data, except_msg))
        return 1


def write_influxdb_list(logger, host, port, user, password,
                        dbname, data):
    """
    Write an entry into an Influxdb database

    example:
        write_influxdb('localhost', 8086, 'mycodo', 'password123',
                       'mycodo_db', data_list_of_dictionaries)

    :return: success (0) or failure (1)
    :rtype: bool

    :param logger: Oject to log to
    :type logger: logger object
    :param host: What influxdb address
    :type host: str
    :param port: What influxdb port
    :type port: int
    :param user: What user to connect to influxdb with
    :type user: str
    :param password: What password to supply for Influxdb user
    :type password: str
    :param dbname: What Influxdb database name to write to
    :type dbname: str
    :param data: The data being entered into Influxdb
    :type data: list of dictionaries
    """
    client = InfluxDBClient(host, port, user, password, dbname)
    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug('Failed to write measurements to influxdb (Device ID: '
                     '{}). Data that was submitted for writing: {}. '
                     'Exception: {}'.format(device_id, data, except_msg))
        return 1

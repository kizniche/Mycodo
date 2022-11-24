# -*- coding: utf-8 -*-
"""Get measurement database info"""
import argparse
import json
import logging
import os
import subprocess
import sys

import requests

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

logger = logging.getLogger("mycodo.measurement_db")


def get_measurement_db_info():
    dict_info = {
        'db_name': '',
        'db_version': ''
    }
    try:
        from mycodo.databases.models import Misc
        from mycodo.utils.database import db_retrieve_table_daemon
        settings = db_retrieve_table_daemon(Misc, entry='first')
        dict_info['db_name'] = settings.measurement_db_name
        dict_info['db_version'] = settings.measurement_db_version
    except Exception as err:
        logger.debug(f"Could not determine influxdb version: {err}")
        dict_info['db_name'] = "ERROR"
        dict_info['db_version'] = "ERROR"

    return dict_info

def get_influxdb_host():
    try:
        from mycodo.databases.models import Misc
        from mycodo.utils.database import db_retrieve_table_daemon
        settings = db_retrieve_table_daemon(Misc, entry='first')
        if settings and settings.measurement_db_host:
            return settings.measurement_db_host
    except Exception as err:
        logger.debug(f"Could not determine influxdb host from table: {err}")

    list_hosts = [
        'localhost',
        '127.0.0.1',
        'mycodo_influxdb'
    ]
    for host in list_hosts:
        try:
            if requests.get(f"http://{host}:8086/ping").status_code == 204:
                return host
        except Exception as err:
            logger.debug(f"Could not determine localhost as influxdb host: {err}")

def get_influxdb_info():
    settings = None
    dict_info = {
        'influxdb_installed': None,
        'influxdb_retention_policy': None,
        'influxdb_version': None,
        'influxdb_host': None,
        'influxdb_port': None
    }
    try:
        from mycodo.databases.models import Misc
        from mycodo.utils.database import db_retrieve_table_daemon
        settings = db_retrieve_table_daemon(Misc, entry='first')
    except Exception as err:
        logger.debug(f"Could not determine influxdb info from table: {err}")

    try:
        if settings:
            dict_info['influxdb_host'] = settings.measurement_db_host
            dict_info['influxdb_port'] = settings.measurement_db_port
            dict_info['influxdb_retention_policy'] = settings.measurement_db_retention_policy
        else:
            dict_info['influxdb_host'] = get_influxdb_host()
            dict_info['influxdb_port'] = 8086
        r = requests.get(f"http://{dict_info['influxdb_host']}:{dict_info['influxdb_port']}/ping")

        if r.headers and "X-Influxdb-Version" in r.headers:
            dict_info['influxdb_installed'] = True
            dict_info['influxdb_version'] = r.headers["X-Influxdb-Version"]
    except Exception as err:
        logger.debug(f"Could not determine influxdb info: {err}")

    return dict_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform actions with the measurement database")

    options = parser.add_argument_group('Options')
    options.add_argument('-i', '--info', action='store_true',
                         help="Info about the measurement database")

    args = parser.parse_args()

    if args.info:
        dict_db_info = get_measurement_db_info()
        dict_influx = get_influxdb_info()
        dict_info = {**dict_db_info, **dict_influx}
        print(json.dumps(dict_info))

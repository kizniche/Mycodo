# -*- coding: utf-8 -*-
"""Get measurement database info"""
import argparse
import json
import os
import subprocess
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))


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
    except:
        dict_info['db_name'] = "ERROR"
        dict_info['db_version'] = "ERROR"

    return dict_info

def get_influxdb_info():
    dict_info = {
        'influxdb_installed': None,
        'influxdb_version': ''
    }
    try:
        output = subprocess.check_output("influxd version", shell=True)
        if output:
            list_output = str(output).split(" ")
            for i, each_str in enumerate(list_output):
                if i == 1 and each_str.startswith("v"):
                    dict_info['influxdb_installed'] = True
                    dict_info['influxdb_version'] = each_str.split("v")[1]
    except Exception as err:
        print(f"Error: {err}")
        dict_info['influxdb_installed'] = False
        dict_info['influxdb_version'] = ""

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

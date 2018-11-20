# coding=utf-8
import datetime
import grp
import logging
import pwd
import socket
import subprocess
import time
from collections import OrderedDict

import os

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.config_devices_units import UNITS
from mycodo.config_devices_units import UNIT_CONVERSIONS
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

logger = logging.getLogger("mycodo.system_pi")


def add_custom_units(units):
    return_units = UNITS.copy()

    for each_unit in units:
        return_units.update(
            {each_unit.name_safe: {
                'unit': each_unit.unit,
                'name': each_unit.name}})

    # Sort dictionary by keys, ignoring case
    sorted_keys = sorted(list(return_units), key=lambda s: s.casefold())
    sorted_dict_units = OrderedDict()
    for each_key in sorted_keys:
        sorted_dict_units[each_key] = return_units[each_key]

    return sorted_dict_units


def add_custom_measurements(measurements):
    """
    Returns the measurement dictionary appended with custom measurements/units
    """
    return_measurements = MEASUREMENTS

    for each_measure in measurements:
        if each_measure.name_safe not in return_measurements:
            return_measurements.update(
                {each_measure.name_safe: {
                    'meas': each_measure.name_safe,
                    'units': each_measure.units.split(','),
                    'name': each_measure.name}})
        else:
            for each_unit in each_measure.units.split(','):
                if each_unit not in return_measurements[each_measure.name_safe]['units']:
                    return_measurements[each_measure.name_safe]['units'].append(each_unit)

    # Sort dictionary by keys
    sorted_keys = sorted(list(return_measurements), key=lambda s: s.casefold())
    sorted_dict_measurements = OrderedDict()
    for each_key in sorted_keys:
        sorted_dict_measurements[each_key] = return_measurements[each_key]

    return sorted_dict_measurements


def all_conversions(conversions):
    conversions_combined = OrderedDict()
    for each_conversion in conversions:
        convert_str = '{fr}_to_{to}'.format(
            fr=each_conversion.convert_unit_from,
            to=each_conversion.convert_unit_to)
        equation_str = each_conversion.equation
        if convert_str not in UNIT_CONVERSIONS:
            conversions_combined[convert_str] = equation_str

    # Sort dictionary by keys
    sorted_keys = sorted(list(conversions_combined), key=lambda s: s.casefold())
    sorted_dict_conversions = OrderedDict()
    for each_key in sorted_keys:
        sorted_dict_conversions[each_key] = conversions_combined[each_key]

    return sorted_dict_conversions


def get_input_or_math_measurement(measurement_id):
    """ Find measurement """
    device_measurement = db_retrieve_table_daemon(
        DeviceMeasurements).filter(
        DeviceMeasurements.unique_id == measurement_id).first()
    if device_measurement:
        return device_measurement
    else:
        return None


def time_between_range(start_time, end_time):
    """
    Check if the current time is between start_time and end_time

    :return: 1 is within range, 0 if not within range
    :rtype: int
    """
    start_hour = int(start_time.split(":")[0])
    start_min = int(start_time.split(":")[1])
    end_hour = int(end_time.split(":")[0])
    end_min = int(end_time.split(":")[1])
    now_time = datetime.datetime.now().time()
    now_time = now_time.replace(second=0, microsecond=0)
    if ((start_hour < end_hour) or
            (start_hour == end_hour and start_min < end_min)):
        if datetime.time(start_hour, start_min) <= now_time <= datetime.time(end_hour, end_min):
            return 1  # Yes now within range
    else:
        if now_time >= datetime.time(start_hour, start_min) or now_time <= datetime.time(end_hour, end_min):
            return 1  # Yes now within range
    return 0  # No now not within range


def epoch_of_next_time(time_str):
    """
    Take time string (HH:MM:SS) and return the epoch of the time in the future
    """
    try:
        current_epoch = time.time()
        time_parts = time.ctime().split()  # split full time string
        time_parts[3] = time_str  # replace the time component
        new_time = time.mktime(time.strptime(' '.join(time_parts)))  # convert to epoch
        if new_time < current_epoch:  # Add a day if in the past
            new_time += 86400
        return new_time
    except:
        return None


def cmd_output(command, su_mycodo=False, stdout_pipe=True):
    """
    Executed command and returns a list of lines from the output
    """
    full_cmd = '{}'.format(command)
    if su_mycodo:  # TODO: Remove su as I don't beleive it works
        full_cmd = 'su mycodo && {}'.format(command)
    if stdout_pipe:
        cmd = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, shell=True)
    else:
        cmd = subprocess.Popen(full_cmd, shell=True)
    cmd_out, cmd_err = cmd.communicate()
    cmd_status = cmd.wait()
    return cmd_out, cmd_err, cmd_status


def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Checks if there is an internet connection
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET,
                      socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as e:
        logger.error(
            "Function 'internet()' raised exception: {err}".format(err=e))
    return False


#
# Type checking
#


def str_is_float(text):
    """Returns true if the string represents a float value"""
    try:
        if text.isalpha():
            return False
        float(text)
        return True
    except ValueError:
        return False


def is_int(test_var, check_range=None):
    """
    Test if var is integer (and also between range)
    check_range should be a list of minimum and maximum values
    e.g. check_range=[0, 100]
    """
    try:
        _ = int(test_var)
    except ValueError:
        return False
    except TypeError:
        return False

    if check_range:
        if not (check_range[0] <= int(test_var) <= check_range[1]):
            return False

    return True


#
# File tools
#


def assure_path_exists(path):
    """ Create path if it doesn't exist """
    if not os.path.exists(path):
        os.makedirs(path)
        os.chmod(path, 0o774)
        set_user_grp(path, 'mycodo', 'mycodo')
    return path


def can_perform_backup():
    """
    Ensure there is enough space to perform a backup
    Returns value sin bytes
    """
    free_before = get_directory_free_space('/var/Mycodo-backups')
    backup_size = get_directory_size(INSTALL_DIRECTORY, exclude=['env', 'cameras'])
    free_after = free_before - backup_size
    return backup_size, free_before, free_after


def find_owner(filename):
    """ Return the owner of a file """
    return pwd.getpwuid(os.stat(filename).st_uid).pw_name


def get_directory_free_space(path):
    statvfs = os.statvfs(path)
    return statvfs.f_frsize * statvfs.f_bavail


def get_directory_size(start_path='.', exclude=[]):
    """
    Returns the size of a directory
    A list of directories may be excluded
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        skip_dir = False
        for each_exclusion in exclude:
            test_exclude = os.path.join(start_path, each_exclusion)
            if dirpath.startswith(test_exclude + '/'):
                skip_dir = True
        if not skip_dir:
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    return total_size


def set_user_grp(filepath, user, group):
    """ Set the UID and GUID of a file """
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    os.chown(filepath, uid, gid)


#
# Converters
#

def celsius_to_kelvin(celsius):
    try:
        kelvin = celsius + 273.15
        return kelvin
    except TypeError:
        logger.error("Input must be an int or float")


def csv_to_list_of_str(str_csv):
    """ return a list of strings from a string of csv strings """
    if str_csv:
        list_str = []
        for x in str_csv.split(','):
            try:
                list_str.append(x)
            except:
                pass
        return list_str


def list_to_csv(display_order):
    str_csv = [str(i) for i in display_order]
    return ','.join(str_csv)


def get_sec(time_str):
    """ Convert HH:MM:SS string into number of seconds """
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


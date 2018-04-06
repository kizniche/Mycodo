# coding=utf-8
import datetime
import grp
import logging
import pwd
import socket
import subprocess

import os

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import UNITS
from mycodo.mycodo_flask.utils.utils_general import use_unit_generate

logger = logging.getLogger("mycodo.system_pi")


def add_custom_measurements(inputs, maths, measurement_units):
    """
    Returns the measurement dictionary appended with
    input, ADC, and command measurements/units
    """
    return_measurements = measurement_units

    use_unit = use_unit_generate(inputs)

    for each_input in inputs:
        # Add converted measurements/units to measurements dictionary
        if each_input.unique_id in use_unit:
            for each_measure in use_unit[each_input.unique_id]:
                if (use_unit[each_input.unique_id][each_measure] is not None and
                        use_unit[each_input.unique_id][each_measure] in UNITS):
                    return_measurements.update(
                        {use_unit[each_input.unique_id][each_measure]: {
                            'meas': use_unit[each_input.unique_id][each_measure],
                            'unit': UNITS[use_unit[each_input.unique_id][each_measure]]['unit'],
                            'name': UNITS[use_unit[each_input.unique_id][each_measure]]['name']}})

        # Add command measurements/units to measurements dictionary
        elif (each_input.cmd_measurement and
                each_input.cmd_measurement_units and
                each_input.cmd_measurement not in measurement_units):
            return_measurements.update(
                {each_input.cmd_measurement: {
                    'meas': each_input.cmd_measurement,
                    'unit': each_input.cmd_measurement_units,
                    'name': each_input.cmd_measurement}})
        # Add ADC measurements/units to measurements dictionary
        if (each_input.adc_measure and
                each_input.adc_measure_units and
                each_input.adc_measure not in measurement_units):
            return_measurements.update(
                {each_input.adc_measure: {
                    'meas': each_input.adc_measure,
                    'unit': each_input.adc_measure_units,
                    'name': each_input.adc_measure}})

    for each_math in maths:
        # Add Math measurements/units to measurements dictionary
        if (each_math.measure and
                each_math.measure_units and
                each_math.measure not in measurement_units):
            return_measurements.update(
                {each_math.measure: {
                    'meas': each_math.measure,
                    'unit': each_math.measure_units,
                    'name': each_math.measure}})

    return return_measurements


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


def csv_to_list_of_int(str_csv):
    """ return a list of integers from a string of csv integers """
    if str_csv:
        list_int = []
        for x in str_csv.split(','):
            try:
                list_int.append(int(x))
            except:
                pass
        return list_int


def list_to_csv(display_order):
    str_csv = [str(i) for i in display_order]
    return ','.join(str_csv)


def get_sec(time_str):
    """ Convert HH:MM:SS string into number of seconds """
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


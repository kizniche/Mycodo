# coding=utf-8
import base64
import copy
import datetime
import grp
import json
import logging
import os
import pwd
import signal
import socket
import subprocess
import time
import traceback
from collections import OrderedDict
from threading import Timer

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.config_devices_units import UNITS
from mycodo.config_devices_units import UNIT_CONVERSIONS
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Output
from mycodo.utils.database import db_retrieve_table
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.logging_utils import set_log_level

logger = logging.getLogger("mycodo.system_pi")
logger.setLevel(set_log_level(logging))


def parse_custom_option_values(controllers, dict_controller=None):
    # Check if controllers is iterable or a single controller
    try:
        _ = iter(controllers)
    except TypeError:
        iter_controller = [controllers]  # Not iterable
    else:
        iter_controller = controllers  # iterable

    custom_options_values = {}

    for each_controller in iter_controller:
        custom_options_values[each_controller.unique_id] = {}
        if each_controller.custom_options:

            # Determine if custom_options should be parsed as JSON or CSV
            if each_controller.custom_options.startswith("{"):
                custom_options = parse_custom_option_values_json(
                    controllers, dict_controller, unique_id=each_controller.unique_id)
                custom_options_values.update({each_controller.unique_id: custom_options})
            else:
                custom_options = parse_custom_option_values_csv(
                    controllers, dict_controller, unique_id=each_controller.unique_id)
                custom_options_values.update({each_controller.unique_id: custom_options})

    return custom_options_values


# TODO: Remove in place of JSON function, below, in next major version
def parse_custom_option_values_csv(controllers, dict_controller=None, unique_id=None):
    # Check if controllers is iterable or a single controller
    try:
        _ = iter(controllers)
    except TypeError:
        iter_controller = [controllers]  # Not iterable
    else:
        iter_controller = controllers  # iterable

    custom_options_values = {}
    for each_controller in iter_controller:
        custom_options_values[each_controller.unique_id] = {}
        if each_controller.custom_options:
            for each_option in each_controller.custom_options.split(';'):
                option = each_option.split(',')[0]
                if len(each_option.split(',')) > 2:
                    value = ','.join(each_option.split(',')[1:])
                elif len(each_option.split(',')) > 1:
                    value = each_option.split(',')[1]
                else:
                    continue
                custom_options_values[each_controller.unique_id][option] = value

        if dict_controller:
            # Set default values if option not saved in database entry
            if each_controller.__tablename__ in ['custom_controller', 'input']:
                dev_name = each_controller.device
            elif each_controller.__tablename__ == 'output':
                dev_name = each_controller.output_type
            else:
                logger.error("Table name not recognized: {}".format(each_controller.__tablename__))
                continue

            if 'custom_options' in dict_controller[dev_name]:
                dict_custom_options = dict_controller[dev_name]['custom_options']
            else:
                dict_custom_options = {}
            for each_option in dict_custom_options:
                if ('id' in each_option and
                        'default_value' in each_option and
                        each_option['id'] not in custom_options_values[each_controller.unique_id]):
                    custom_options_values[each_controller.unique_id][each_option['id']] = each_option['default_value']

    if unique_id:
        return custom_options_values[unique_id]

    return custom_options_values


def parse_custom_option_values_json(
        controllers,
        dict_controller=None,
        key_name='custom_options',
        unique_id=None):
    # Check if controllers is iterable or a single controller
    try:
        _ = iter(controllers)
    except TypeError:
        iter_controller = [controllers]  # Not iterable
    else:
        iter_controller = controllers  # iterable

    custom_options_values = {}
    for each_controller in iter_controller:
        custom_options_values[each_controller.unique_id] = {}
        if each_controller.custom_options:
            try:
                custom_options_values[each_controller.unique_id] = json.loads(
                    each_controller.custom_options)
            except:
                custom_options_values[each_controller.unique_id] = {}

        if dict_controller:
            # Set default values if option not saved in database entry
            if each_controller.__tablename__ in ['custom_controller', 'input']:
                dev_name = each_controller.device
            elif each_controller.__tablename__ == 'output':
                dev_name = each_controller.output_type
            elif each_controller.__tablename__ == 'widget':
                dev_name = each_controller.graph_type
            else:
                logger.error("Table name not recognized: {}".format(each_controller.__tablename__))
                continue

            if dev_name in dict_controller and key_name in dict_controller[dev_name]:
                dict_custom_options = dict_controller[dev_name][key_name]
            else:
                dict_custom_options = {}
            for each_option in dict_custom_options:
                if ('id' in each_option and
                        'default_value' in each_option and
                        each_option['id'] not in custom_options_values[each_controller.unique_id]):
                    custom_options_values[each_controller.unique_id][each_option['id']] = each_option['default_value']

    if unique_id:
        return custom_options_values[unique_id]

    return custom_options_values


# TODO: Combine these next two functions by naming output_id and input_id the same
def parse_custom_option_values_channels_json(
        controllers,
        dict_controller=None,
        key_name='custom_channel_options'):
    # Check if controllers is iterable or a single controller
    try:
        _ = iter(controllers)
    except TypeError:
        iter_controller = [controllers]  # Not iterable
    else:
        iter_controller = controllers  # iterable

    custom_options_values = {}
    for each_controller in iter_controller:
        if each_controller.output_id not in custom_options_values:
            custom_options_values[each_controller.output_id] = {}
        if each_controller.custom_options:
            custom_options_values[each_controller.output_id][each_controller.channel] = json.loads(
                each_controller.custom_options)

        if dict_controller:
            # Set default values if option not saved in database entry
            output = db_retrieve_table(Output, unique_id=each_controller.output_id)
            if not output:
                continue
            dev_name = output.output_type

            if dev_name in dict_controller and key_name in dict_controller[dev_name]:
                dict_custom_options = dict_controller[dev_name][key_name]
            else:
                dict_custom_options = {}
            for each_option in dict_custom_options:
                if 'id' in each_option and 'default_value' in each_option:
                    if each_controller.channel not in custom_options_values[each_controller.output_id]:
                        custom_options_values[each_controller.output_id][each_controller.channel] = {}
                    if each_option['id'] not in custom_options_values[each_controller.output_id][each_controller.channel]:
                        # If a select type has cast_value set, cast the value as that type
                        if each_option['type'] == 'select' and 'cast_value' in each_option:
                            if each_option['cast_value'] == 'integer':
                                each_option['default_value'] = int(each_option['default_value'])
                            elif each_option['cast_value'] == 'float':
                                each_option['default_value'] = float(each_option['default_value'])
                        custom_options_values[each_controller.output_id][each_controller.channel][each_option['id']] = each_option['default_value']

    return custom_options_values


def parse_custom_option_values_input_channels_json(
        controllers,
        dict_controller=None,
        key_name='custom_channel_options'):
    # Check if controllers is iterable or a single controller
    try:
        _ = iter(controllers)
    except TypeError:
        iter_controller = [controllers]  # Not iterable
    else:
        iter_controller = controllers  # iterable

    custom_options_values = {}
    for each_controller in iter_controller:
        if each_controller.input_id not in custom_options_values:
            custom_options_values[each_controller.input_id] = {}
        if each_controller.custom_options:
            custom_options_values[each_controller.input_id][each_controller.channel] = json.loads(
                each_controller.custom_options)

        if dict_controller:
            # Set default values if option not saved in database entry
            input_dev = db_retrieve_table(Input, unique_id=each_controller.input_id)
            if not input_dev:
                continue
            try:
                input_dev.unique_id
            except:
                continue
            dev_name = input_dev.device

            if dev_name in dict_controller and key_name in dict_controller[dev_name]:
                dict_custom_options = dict_controller[dev_name][key_name]
            else:
                dict_custom_options = {}
            for each_option in dict_custom_options:
                if 'id' in each_option and 'default_value' in each_option:
                    if each_controller.channel not in custom_options_values[each_controller.input_id]:
                        custom_options_values[each_controller.input_id][each_controller.channel] = {}
                    if each_option['id'] not in custom_options_values[each_controller.input_id][each_controller.channel]:
                        # If a select type has cast_value set, cast the value as that type
                        if each_option['type'] == 'select' and 'cast_value' in each_option:
                            if each_option['cast_value'] == 'integer':
                                each_option['default_value'] = int(each_option['default_value'])
                            elif each_option['cast_value'] == 'float':
                                each_option['default_value'] = float(each_option['default_value'])
                        custom_options_values[each_controller.input_id][each_controller.channel][each_option['id']] = each_option['default_value']

    return custom_options_values


def add_custom_units(units):
    return_units = copy.deepcopy(UNITS)

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


def test_python_execute(code_string):
    try:
        exec(code_string, globals())
    except Exception:
        return 1, traceback.format_exc()
    else:
        return 0, None


def dpkg_package_exists(package_name):
    start = "dpkg-query -W -f='${Status}'"
    end = '2>/dev/null | grep -c "ok installed"'
    cmd = "{} {} {}".format(start, package_name, end)
    _, _, stat = cmd_output(cmd)
    if not stat:
        return True


def return_measurement_info(device_measurement, conversion):
    """ Return unit, measurement, and channel of a device measurement"""
    try:
        unit = None
        measurement = None
        channel = None

        if device_measurement:
            channel = device_measurement.channel

        if (device_measurement and
                device_measurement.conversion_id and
                conversion):
            unit = conversion.convert_unit_to
        elif (device_measurement and
                hasattr(device_measurement, 'rescaled_unit') and
                hasattr(device_measurement, 'rescaled_measurement') and
                device_measurement.rescaled_unit and
                device_measurement.rescaled_measurement):
            unit = device_measurement.rescaled_unit
            measurement = device_measurement.rescaled_measurement
        else:
            if device_measurement:
                unit = device_measurement.unit
                measurement = device_measurement.measurement

        return channel, unit, measurement
    except Exception:
        logger.exception("{}, {}".format(device_measurement, conversion))
        return None, None, None


def add_custom_measurements(measurements):
    """
    Returns the measurement dictionary appended with custom measurements/units
    """
    return_measurements = copy.deepcopy(MEASUREMENTS)

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


def get_measurement(measurement_id):
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


def cmd_output(command, stdout_pipe=True, timeout=360, user='mycodo', cwd='/home'):
    """
    Executes a bash command and returns the output

    :param command: Bash command to execute
    :param stdout_pipe: Capture output
    :param timeout: Kill process if it runs longer than this many seconds
    :param user: The user to execute the command as
    :param cwd: The current working directory of the environment
    :return: tuple of output, errors, status
    """
    cmd_success = True

    def report_ids(msg):
        logger.debug('{msg}: uid={uid}, gid={gid}, groups={grp}'.format(
            msg=msg, uid=os.getuid(), gid=os.getgid(), grp=os.getgroups()))

    def getgroups(user):
        gids = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
        gid = pwd.getpwnam(user).pw_gid
        if grp.getgrgid(gid).gr_gid not in gids:
            gids.append(int(grp.getgrgid(gid).gr_gid))
        return gids

    def demote(user_uid, user_gid, user_groups):
        def result():
            report_ids('starting demotion')
            os.setgroups(user_groups)
            os.setgid(user_gid)
            os.setuid(user_uid)
            report_ids('finished demotion')
        return result

    pw_record = pwd.getpwnam(user)
    user_name = pw_record.pw_name
    user_home_dir = pw_record.pw_dir
    user_uid = pw_record.pw_uid
    user_gid = pw_record.pw_gid
    user_groups = getgroups(user)
    env = os.environ.copy()
    env['HOME'] = user_home_dir
    env['LOGNAME'] = user_name
    env['PWD'] = cwd
    env['USER'] = user_name

    if stdout_pipe:
        cmd = subprocess.Popen(command,
                               stdout=subprocess.PIPE,
                               shell=True,
                               preexec_fn=demote(user_uid, user_gid, user_groups),
                               cwd=cwd,
                               env=env)
    else:
        cmd = subprocess.Popen(command,
                               shell=True,
                               preexec_fn=demote(user_uid, user_gid, user_groups),
                               cwd=cwd,
                               env=env)

    def kill_process():
        nonlocal cmd_success
        cmd_success = False
        os.killpg(os.getpgid(cmd.pid), signal.SIGTERM)
        logger.debug("cmd_output() timed out after {} seconds "
                     "with command '{}'".format(timeout, command))

    # Add timeout functionality
    timer = Timer(timeout, kill_process)
    try:
        timer.start()
        cmd_out, cmd_err = cmd.communicate()
    finally:
        timer.cancel()

    cmd_status = cmd.wait()

    if cmd_success:
        return cmd_out, cmd_err, cmd_status
    else:
        return None, None, None


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
        if not text:
            return False
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


def get_directory_size(start_path='.', exclude=None):
    """
    Returns the size of a directory
    A list of directories may be excluded
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        skip_dir = False
        if exclude:
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

def base64_encode_bytes(key_bytes):
    encoded_bytes = base64.b64encode(key_bytes)
    encoded_str = str(encoded_bytes, "utf-8")
    return encoded_str

def celsius_to_kelvin(celsius):
    try:
        kelvin = celsius + 273.15
        return kelvin
    except TypeError:
        logger.error("Input must be an int or float")


def check_missing_ids(current_ids, db_list):
    try:
        ids = current_ids.split(",")
        for each_db in db_list:
            for each_entry in each_db:
                if each_entry.unique_id not in ids:
                    ids.append(each_entry.unique_id)
        return ",".join(ids)
    except:
        return current_ids


def csv_to_list_of_str(str_csv):
    """ return a list of strings from a string of csv strings """
    list_str = []
    if str_csv:
        for x in str_csv.split(','):
            try:
                list_str.append(x)
            except Exception:
                pass
    return list_str


def list_to_csv(display_order):
    str_csv = [str(i) for i in display_order]
    return ','.join(str_csv)


def get_sec(time_str):
    """ Convert HH:MM:SS string into number of seconds """
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


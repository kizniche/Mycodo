# coding=utf-8
import csv
import datetime
import io
import logging
import os
import shutil
import time
import zipfile
from collections import OrderedDict

from dateutil import relativedelta

from mycodo.config import (INSTALL_DIRECTORY, PATH_ACTIONS_CUSTOM,
                           PATH_FUNCTIONS_CUSTOM, PATH_TEMPLATE_USER,
                           PATH_INPUTS_CUSTOM, PATH_OUTPUTS_CUSTOM,
                           PATH_PYTHON_CODE_USER, PATH_USER_SCRIPTS,
                           PATH_WIDGETS_CUSTOM, SQL_DATABASE_MYCODO,
                           USAGE_REPORTS_PATH)
from mycodo.databases.models import (Conversion, DeviceMeasurements,
                                     EnergyUsage, Misc, Output, OutputChannel)
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import (average_past_seconds,
                                 average_start_end_seconds, output_sec_on)
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import (
    assure_path_exists, cmd_output,
    parse_custom_option_values_output_channels_json, return_measurement_info,
    set_user_grp)

logger = logging.getLogger("mycodo.tools")


def create_measurements_export(influxdb_version, save_path=None):
    try:
        data = io.BytesIO()
        influx_backup_dir = os.path.join(INSTALL_DIRECTORY, 'influx_backup')

        # Delete influxdb directory if it exists
        if os.path.isdir(influx_backup_dir):
            shutil.rmtree(influx_backup_dir)

        # Create new directory (make sure it's empty)
        assure_path_exists(influx_backup_dir)

        settings = db_retrieve_table_daemon(Misc, entry='first')

        if influxdb_version.startswith("1."):
            cmd = f"/usr/bin/influxd backup -database {settings.measurement_db_dbname} -portable {influx_backup_dir}"
            out, err, status = cmd_output(cmd, user='root')
        elif influxdb_version.startswith("2."):
            cmd = f"/usr/bin/influx backup --org mycodo {influx_backup_dir}"
            out, err, status = cmd_output(cmd, user='root')
        else:
            logger.error(f"Could not determine influxdb version: {influxdb_version}")
            return
        
        logger.info(f"out: {out}, error: {err}, status: {status}")

        if not status:
            # Zip all files in the influx_backup directory
            with zipfile.ZipFile(data, mode='w') as z:
                for _, _, files in os.walk(influx_backup_dir):
                    for filename in files:
                        z.write(os.path.join(influx_backup_dir, filename),
                                filename)
            data.seek(0)

            # Delete influxdb directory if it exists
            if os.path.isdir(influx_backup_dir):
                shutil.rmtree(influx_backup_dir)

            if save_path:
                with open(save_path, "wb") as f:
                    f.write(data.getbuffer())
                set_user_grp(save_path, 'mycodo', 'mycodo')
                return 0, save_path
            else:
                return 0, data
    except Exception as err:
        logger.exception(f"Error: {err}")
        return 1, err


def create_settings_export(save_path=None):
    try:
        data = io.BytesIO()
        with zipfile.ZipFile(data, mode='w') as z:
            try:
                z.write(SQL_DATABASE_MYCODO,
                        os.path.basename(SQL_DATABASE_MYCODO))
            except:
                logger.error(f"Could not find database file {SQL_DATABASE_MYCODO}")

            export_directories = [
                (PATH_FUNCTIONS_CUSTOM, "custom_functions"),
                (PATH_ACTIONS_CUSTOM, "custom_actions"),
                (PATH_INPUTS_CUSTOM, "custom_inputs"),
                (PATH_OUTPUTS_CUSTOM, "custom_outputs"),
                (PATH_WIDGETS_CUSTOM, "custom_widgets"),
                (PATH_USER_SCRIPTS, "user_scripts"),
                (PATH_TEMPLATE_USER, "user_html"),
                (PATH_PYTHON_CODE_USER, "user_python_code")
            ]
            for each_backup in export_directories:
                if not os.path.exists(each_backup[0]):
                    continue
                for folder_name, sub_folders, filenames in os.walk(each_backup[0]):
                    for filename in filenames:
                        if filename == "__init__.py" or filename.endswith("pyc"):
                            continue
                        file_path = os.path.join(folder_name, filename)
                        z.write(file_path, f"{each_backup[1]}/{os.path.basename(file_path)}")
        data.seek(0)
        if save_path:
            with open(save_path, "wb") as f:
                f.write(data.getbuffer())
            set_user_grp(save_path, 'mycodo', 'mycodo')
            return 0, save_path
        else:
            return 0, data
    except Exception as err:
        logger.error(f"Error: {err}")
        return 1, err


def next_schedule(time_span='daily', set_day=None, set_hour=None):
    """
    Return the next local epoch to schedule a task
    Returns the epoch of the next day or nth day of the week or month

    :param time_span: str, 'daily', 'weekly', or 'monthly'
    :param set_hour: int, hour of the day
    :param set_day: int, day of the week (0 = Monday) or month (1-28)
    :return: float, local epoch of next schedule
    """
    now = time.time()

    time_now = datetime.datetime.now()
    current_day = time_now.day
    current_month = time_now.month
    current_year = time_now.year

    if time_span == 'monthly':
        new_month = current_month
        new_year = current_year
        future_time_test = time.mktime(datetime.datetime(
            year=current_year,
            month=current_month,
            day=set_day,
            hour=set_hour).timetuple())
        if future_time_test < now:
            if current_month == 12:
                new_month = 1
                new_year += 1
            else:
                new_month += 1
            future_time_test = time.mktime(datetime.datetime(
                year=new_year,
                month=new_month,
                day=set_day,
                hour=set_hour).timetuple())
        return future_time_test

    elif time_span == 'weekly':
        today_weekday = datetime.datetime.today().weekday()
        if today_weekday < (set_day - 1):
            days_to_add = (set_day - 1) - today_weekday
        else:
            days_to_add = 7 - (today_weekday - (set_day - 1))

        future_time_test = time.mktime(
            (datetime.date.today() +
             relativedelta.relativedelta(days=days_to_add)).timetuple()) + (3600 * set_hour)
        return future_time_test

    elif time_span == 'daily':
        future_time_test = time.mktime(datetime.datetime(
            year=current_year,
            month=current_month,
            day=current_day,
            hour=set_hour).timetuple())
        if future_time_test < now:
            future_time_test = time.mktime(
                (datetime.date.today() +
                 relativedelta.relativedelta(days=1)).timetuple()) + (3600 * set_hour)

        return future_time_test


def return_energy_usage(energy_usage, device_measurements_all, conversion_all):
    """Calculate energy usage from Inputs measuring amps."""
    energy_usage_stats = {}
    graph_info = {}
    for each_energy in energy_usage:
        graph_info[each_energy.unique_id] = {}
        energy_usage_stats[each_energy.unique_id] = {}
        energy_usage_stats[each_energy.unique_id]['hour'] = 0
        energy_usage_stats[each_energy.unique_id]['day'] = 0
        energy_usage_stats[each_energy.unique_id]['week'] = 0
        energy_usage_stats[each_energy.unique_id]['month'] = 0

        device_measurement = device_measurements_all.filter(
            DeviceMeasurements.unique_id == each_energy.measurement_id).first()
        if device_measurement:
            conversion = conversion_all.filter(
                Conversion.unique_id == device_measurement.conversion_id).first()
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        graph_info[each_energy.unique_id]['main'] = {}
        graph_info[each_energy.unique_id]['main']['device_id'] = each_energy.device_id
        graph_info[each_energy.unique_id]['main']['measurement_id'] = each_energy.measurement_id
        graph_info[each_energy.unique_id]['main']['channel'] = channel
        graph_info[each_energy.unique_id]['main']['unit'] = unit
        graph_info[each_energy.unique_id]['main']['measurement'] = measurement
        graph_info[each_energy.unique_id]['main']['start_time_epoch'] = (
            datetime.datetime.now() -
            datetime.timedelta(seconds=2629800)).strftime('%s')

        if unit == 'A':  # If unit is amps, proceed
            hour = average_past_seconds(
                each_energy.device_id, unit, channel, 3600,
                measure=measurement)
            if hour:
                energy_usage_stats[each_energy.unique_id]['hour'] = hour
            day = average_past_seconds(
                each_energy.device_id, unit, channel, 86400,
                measure=measurement)
            if day:
                energy_usage_stats[each_energy.unique_id]['day'] = day
            week = average_past_seconds(
                each_energy.device_id, unit, channel, 604800,
                measure=measurement)
            if week:
                energy_usage_stats[each_energy.unique_id]['week'] = week
            month = average_past_seconds(
                each_energy.device_id, unit, channel, 2629800,
                measure=measurement)
            if month:
                energy_usage_stats[each_energy.unique_id]['month'] = month

    return energy_usage_stats, graph_info


def calc_energy_usage(
        energy_usage_id,
        graph_info,
        start_string,
        end_string,
        energy_usage,
        device_measurements,
        conversion,
        volts):
    calculate_usage = {}
    picker_start = {}
    picker_end = {}

    start_seconds = int(time.mktime(
        time.strptime(start_string, '%m/%d/%Y %H:%M')))
    end_seconds = int(time.mktime(
        time.strptime(end_string, '%m/%d/%Y %H:%M')))

    utc_offset_timedelta = datetime.datetime.utcnow() - datetime.datetime.now()
    start = datetime.datetime.fromtimestamp(float(start_seconds))
    start += utc_offset_timedelta
    start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.datetime.fromtimestamp(float(end_seconds))
    end += utc_offset_timedelta
    end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    energy_device = energy_usage.filter(
        EnergyUsage.unique_id == energy_usage_id).first()
    device_measurement = device_measurements.filter(
        DeviceMeasurements.unique_id == energy_device.measurement_id).first()
    if device_measurement:
        conversion = conversion.filter(
            Conversion.unique_id == device_measurement.conversion_id).first()
    else:
        conversion = None
    channel, unit, measurement = return_measurement_info(
        device_measurement, conversion)

    picker_start[energy_device.unique_id] = start_string
    picker_end[energy_device.unique_id] = end_string

    if energy_device.unique_id not in graph_info:
        graph_info[energy_device.unique_id] = {}

    graph_info[energy_device.unique_id]['calculate'] = {}
    graph_info[energy_device.unique_id]['calculate']['device_id'] = energy_device.device_id
    graph_info[energy_device.unique_id]['calculate']['measurement_id'] = energy_device.measurement_id
    graph_info[energy_device.unique_id]['calculate']['channel'] = channel
    graph_info[energy_device.unique_id]['calculate']['unit'] = unit
    graph_info[energy_device.unique_id]['calculate']['measurement'] = measurement
    graph_info[energy_device.unique_id]['calculate']['start_time_epoch'] = start_seconds
    graph_info[energy_device.unique_id]['calculate']['end_time_epoch'] = end_seconds

    calculate_usage[energy_device.unique_id] = {}
    calculate_usage[energy_device.unique_id]['average_amps'] = 0
    calculate_usage[energy_device.unique_id]['kwh'] = 0

    average_amps = average_start_end_seconds(
        energy_device.device_id,
        unit,
        channel,
        start_str,
        end_str,
        measure=measurement)

    calculate_usage[energy_device.unique_id]['average_amps'] = 0
    calculate_usage[energy_device.unique_id]['kwh'] = 0
    calculate_usage[energy_device.unique_id]['hours'] = 0
    if average_amps:
        calculate_usage[energy_device.unique_id]['average_amps'] = average_amps
        hours = ((end_seconds - start_seconds) / 3600)
        if hours < 1:
            hours = 1
        calculate_usage[energy_device.unique_id]['kwh'] = volts * average_amps / 1000 * hours
        calculate_usage[energy_device.unique_id]['hours'] = hours

    return calculate_usage, graph_info, picker_start, picker_end


def return_output_usage(
        dict_outputs,
        table_misc,
        outputs,
        table_output_channels,
        custom_options_values_output_channels):
    """Return output usage and cost."""
    date_now = datetime.date.today()
    time_now = datetime.datetime.now()
    past_month_seconds = 0

    if table_misc.output_usage_dayofmonth == datetime.datetime.today().day:
        past_month_seconds = (time_now - time_now.replace(
            hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    elif table_misc.output_usage_dayofmonth > datetime.datetime.today().day:
        first_day = date_now.replace(day=1)
        last_month = first_day - datetime.timedelta(days=1)
        past_month = last_month.replace(day=table_misc.output_usage_dayofmonth)
        past_month_seconds = (date_now - past_month).total_seconds()
    elif table_misc.output_usage_dayofmonth < datetime.datetime.today().day:
        past_month = date_now.replace(day=table_misc.output_usage_dayofmonth)
        past_month_seconds = (date_now - past_month).total_seconds()

    output_stats = OrderedDict()

    # Calculate output on duration for different time periods
    # Use OrderedDict to ensure proper order when saved to csv file
    output_stats['total_duration'] = dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0)
    output_stats['total_kwh'] = dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0)
    output_stats['total_cost'] = dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0)

    for each_output in outputs:
        output_channels = table_output_channels.query.filter(table_output_channels.output_id == each_output.unique_id).all()
        for each_channel in output_channels:
            channel_options = custom_options_values_output_channels[each_output.unique_id][each_channel.channel]
            if ('types' in dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel] and
                    'on_off' in dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]['types'] and
                    'amps' in channel_options):
                past_1d_hours = output_sec_on(
                    each_output.unique_id, 86400, output_channel=each_channel.channel) / 3600
                past_1w_hours = output_sec_on(
                    each_output.unique_id, 604800, output_channel=each_channel.channel) / 3600
                past_1m_hours = output_sec_on(
                    each_output.unique_id, 2629743, output_channel=each_channel.channel) / 3600
                past_1m_date_hours = output_sec_on(
                    each_output.unique_id, int(past_month_seconds), output_channel=each_channel.channel) / 3600
                past_1y_hours = output_sec_on(
                    each_output.unique_id, 31556926, output_channel=each_channel.channel) / 3600

                past_1d_kwh = table_misc.output_usage_volts * channel_options['amps'] * past_1d_hours / 1000
                past_1w_kwh = table_misc.output_usage_volts * channel_options['amps'] * past_1w_hours / 1000
                past_1m_kwh = table_misc.output_usage_volts * channel_options['amps'] * past_1m_hours / 1000
                past_1m_date_kwh = table_misc.output_usage_volts * channel_options['amps'] * past_1m_date_hours / 1000
                past_1y_kwh = table_misc.output_usage_volts * channel_options['amps'] * past_1y_hours / 1000

                if each_output.unique_id not in output_stats:
                    output_stats[each_output.unique_id] = {}
                output_stats[each_output.unique_id][each_channel.unique_id] = {
                    '1d': {
                        'hours_on': past_1d_hours,
                        'kwh': past_1d_kwh,
                        'cost': table_misc.output_usage_cost * past_1d_kwh
                    },
                    '1w': {
                        'hours_on': past_1w_hours,
                        'kwh': past_1w_kwh,
                        'cost': table_misc.output_usage_cost * past_1w_kwh
                    },
                    '1m': {
                        'hours_on': past_1m_hours,
                        'kwh': past_1m_kwh,
                        'cost': table_misc.output_usage_cost * past_1m_kwh
                    },
                    '1m_date': {
                        'hours_on': past_1m_date_hours,
                        'kwh': past_1m_date_kwh,
                        'cost': table_misc.output_usage_cost * past_1m_date_kwh
                    },
                    '1y': {
                        'hours_on': past_1y_hours,
                        'kwh': past_1y_kwh,
                        'cost': table_misc.output_usage_cost * past_1y_kwh
                    }
                }

                output_stats['total_duration']['1d'] += past_1d_hours
                output_stats['total_duration']['1w'] += past_1w_hours
                output_stats['total_duration']['1m'] += past_1m_hours
                output_stats['total_duration']['1m_date'] += past_1m_date_hours
                output_stats['total_duration']['1y'] += past_1y_hours

                output_stats['total_kwh']['1d'] += past_1d_kwh
                output_stats['total_kwh']['1w'] += past_1w_kwh
                output_stats['total_kwh']['1m'] += past_1m_kwh
                output_stats['total_kwh']['1m_date'] += past_1m_date_kwh
                output_stats['total_kwh']['1y'] += past_1y_kwh

                output_stats['total_cost']['1d'] += table_misc.output_usage_cost * past_1d_kwh
                output_stats['total_cost']['1w'] += table_misc.output_usage_cost * past_1w_kwh
                output_stats['total_cost']['1m'] += table_misc.output_usage_cost * past_1m_kwh
                output_stats['total_cost']['1m_date'] += table_misc.output_usage_cost * past_1m_date_kwh
                output_stats['total_cost']['1y'] += table_misc.output_usage_cost * past_1y_kwh

    return output_stats


def generate_output_usage_report():
    """
    Generate output usage report in a csv file

    """
    logger.debug("Generating output usage report...")
    try:
        assure_path_exists(USAGE_REPORTS_PATH)

        misc = db_retrieve_table_daemon(Misc, entry='first')
        output = db_retrieve_table_daemon(Output)
        output_channel = db_retrieve_table_daemon(OutputChannel)
        dict_outputs = parse_output_information()
        custom_options_values_output_channels = parse_custom_option_values_output_channels_json(
            output_channel.query.all(), dict_controller=dict_outputs, key_name='custom_channel_options')

        output_usage = return_output_usage(
            dict_outputs, misc, output.all(), output_channel, custom_options_values_output_channels)

        timestamp = time.strftime("%Y-%m-%d_%H-%M")
        file_name = f'output_usage_report_{timestamp}.csv'
        report_path_file = os.path.join(USAGE_REPORTS_PATH, file_name)

        with open(report_path_file, 'wb') as f:
            w = csv.writer(f)
            # Header row
            w.writerow([
                 'Relay ID',
                 'Relay Unique ID',
                 'Relay Name',
                 'Type',
                 'Past Day',
                 'Past Week',
                 'Past Month',
                 f'Past Month (from {misc.output_usage_dayofmonth})',
                 'Past Year'
            ])
            for key, value in output_usage.items():
                if key in ['total_duration', 'total_cost', 'total_kwh']:
                    # Totals rows
                    w.writerow(['', '', '',
                                key,
                                value['1d'],
                                value['1w'],
                                value['1m'],
                                value['1m_date'],
                                value['1y']])
                else:
                    # Each output rows
                    each_output = output.filter(Output.unique_id == key).first()
                    w.writerow([each_output.unique_id,
                                each_output.unique_id,
                                str(each_output.name).encode("utf-8"),
                                'hours_on',
                                value['1d']['hours_on'],
                                value['1w']['hours_on'],
                                value['1m']['hours_on'],
                                value['1m_date']['hours_on'],
                                value['1y']['hours_on']])
                    w.writerow([each_output.unique_id,
                                each_output.unique_id,
                                str(each_output.name).encode("utf-8"),
                                'kwh',
                                value['1d']['kwh'],
                                value['1w']['kwh'],
                                value['1m']['kwh'],
                                value['1m_date']['kwh'],
                                value['1y']['kwh']])
                    w.writerow([each_output.unique_id,
                                each_output.unique_id,
                                str(each_output.name).encode("utf-8"),
                                'cost',
                                value['1d']['cost'],
                                value['1w']['cost'],
                                value['1m']['cost'],
                                value['1m_date']['cost'],
                                value['1y']['cost']])

        set_user_grp(report_path_file, 'mycodo', 'mycodo')
    except Exception:
        logger.exception("Energy Usage Report Generation ERROR")

# coding=utf-8
import csv
import datetime
import logging
import os
import time
from collections import OrderedDict
from dateutil import relativedelta

from mycodo.databases.models import Misc
from mycodo.databases.models import Relay

from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import relay_sec_on
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import set_user_grp

from mycodo.config import USAGE_REPORTS_PATH

logger = logging.getLogger("mycodo.tools")


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
            year=current_year, month=current_month, day=set_day, hour=set_hour).timetuple())
        if future_time_test < now:
            if current_month == 12:
                new_month = 1
                new_year += 1
            else:
                new_month += 1
            future_time_test = time.mktime(datetime.datetime(
                year=new_year, month=new_month, day=set_day, hour=set_hour).timetuple())
        return future_time_test

    elif time_span == 'weekly':
        today_weekday = datetime.datetime.today().weekday()
        if today_weekday < (set_day - 1):
            days_to_add = (set_day - 1) - today_weekday
        else:
            days_to_add = 7 - (today_weekday - (set_day - 1))

        future_time_test = time.mktime(
            (datetime.date.today() + relativedelta.relativedelta(days=days_to_add)).timetuple()) + (3600 * set_hour)
        return future_time_test

    elif time_span == 'daily':
        future_time_test = time.mktime(datetime.datetime(
            year=current_year, month=current_month, day=current_day, hour=set_hour).timetuple())
        if future_time_test < now:
            future_time_test = time.mktime(
                (datetime.date.today() + relativedelta.relativedelta(days=1)).timetuple()) + (3600 * set_hour)

        return future_time_test


def return_relay_usage(table_misc, table_relays):
    """ Return relay usage and cost """
    date_now = datetime.date.today()
    time_now = datetime.datetime.now()
    past_month_seconds = 0

    if table_misc.relay_usage_dayofmonth == datetime.datetime.today().day:
        past_month_seconds = (time_now - time_now.replace(
            hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    elif table_misc.relay_usage_dayofmonth > datetime.datetime.today().day:
        first_day = date_now.replace(day=1)
        last_month = first_day - datetime.timedelta(days=1)
        past_month = last_month.replace(day=table_misc.relay_usage_dayofmonth)
        past_month_seconds = (date_now - past_month).total_seconds()
    elif table_misc.relay_usage_dayofmonth < datetime.datetime.today().day:
        past_month = date_now.replace(day=table_misc.relay_usage_dayofmonth)
        past_month_seconds = (date_now - past_month).total_seconds()

    relay_stats = OrderedDict()

    for each_relay in table_relays:
        if each_relay.relay_type != 'pwm':
            relay_stats[each_relay.id] = None

    # Calculate relay on duration for different time periods
    # Use OrderedDict to ensure proper order when saved to csv file
    relay_stats['total_duration'] = dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0)
    relay_stats['total_kwh'] = dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0)
    relay_stats['total_cost'] = dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0)

    for each_relay in table_relays:
        if each_relay.relay_type != 'pwm':
            past_1d_hours = relay_sec_on(each_relay.id, 86400) / 3600
            past_1w_hours = relay_sec_on(each_relay.id, 604800) / 3600
            past_1m_hours = relay_sec_on(each_relay.id, 2629743) / 3600
            past_1m_date_hours = relay_sec_on(each_relay.id, int(past_month_seconds)) / 3600
            past_1y_hours = relay_sec_on(each_relay.id, 31556926) / 3600

            past_1d_kwh = table_misc.relay_usage_volts * each_relay.amps * past_1d_hours / 1000
            past_1w_kwh = table_misc.relay_usage_volts * each_relay.amps * past_1w_hours / 1000
            past_1m_kwh = table_misc.relay_usage_volts * each_relay.amps * past_1m_hours / 1000
            past_1m_date_kwh = table_misc.relay_usage_volts * each_relay.amps * past_1m_date_hours / 1000
            past_1y_kwh = table_misc.relay_usage_volts * each_relay.amps * past_1y_hours / 1000

            relay_stats[each_relay.id] = {
                '1d': {
                    'hours_on': past_1d_hours,
                    'kwh': past_1d_kwh,
                    'cost': table_misc.relay_usage_cost * past_1d_kwh
                },
                '1w': {
                    'hours_on': past_1w_hours,
                    'kwh': past_1w_kwh,
                    'cost': table_misc.relay_usage_cost * past_1w_kwh
                },
                '1m': {
                    'hours_on': past_1m_hours,
                    'kwh': past_1m_kwh,
                    'cost': table_misc.relay_usage_cost * past_1m_kwh
                },
                '1m_date': {
                    'hours_on': past_1m_date_hours,
                    'kwh': past_1m_date_kwh,
                    'cost': table_misc.relay_usage_cost * past_1m_date_kwh
                },
                '1y': {
                    'hours_on': past_1y_hours,
                    'kwh': past_1y_kwh,
                    'cost': table_misc.relay_usage_cost * past_1y_kwh
                }
            }

            relay_stats['total_duration']['1d'] += past_1d_hours
            relay_stats['total_duration']['1w'] += past_1w_hours
            relay_stats['total_duration']['1m'] += past_1m_hours
            relay_stats['total_duration']['1m_date'] += past_1m_date_hours
            relay_stats['total_duration']['1y'] += past_1y_hours

            relay_stats['total_kwh']['1d'] += past_1d_kwh
            relay_stats['total_kwh']['1w'] += past_1w_kwh
            relay_stats['total_kwh']['1m'] += past_1m_kwh
            relay_stats['total_kwh']['1m_date'] += past_1m_date_kwh
            relay_stats['total_kwh']['1y'] += past_1y_kwh

            relay_stats['total_cost']['1d'] += table_misc.relay_usage_cost * past_1d_kwh
            relay_stats['total_cost']['1w'] += table_misc.relay_usage_cost * past_1w_kwh
            relay_stats['total_cost']['1m'] += table_misc.relay_usage_cost * past_1m_kwh
            relay_stats['total_cost']['1m_date'] += table_misc.relay_usage_cost * past_1m_date_kwh
            relay_stats['total_cost']['1y'] += table_misc.relay_usage_cost * past_1y_kwh

    return relay_stats


def generate_relay_usage_report():
    """
    Generate relay usage report in a csv file

    """
    logger.debug("Generating relay usage report...")
    try:
        assure_path_exists(USAGE_REPORTS_PATH)

        misc = db_retrieve_table_daemon(Misc, entry='first')
        relay = db_retrieve_table_daemon(Relay)
        relay_usage = return_relay_usage(misc, relay.all())

        timestamp = time.strftime("%Y-%m-%d_%H-%M")
        file_name = 'relay_usage_report_{ts}.csv'.format(ts=timestamp)
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
                 'Past Month (from {})'.format(misc.relay_usage_dayofmonth),
                 'Past Year'
            ])
            for key, value in relay_usage.items():
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
                    # Each relay rows
                    each_relay = relay.filter(Relay.id == key).first()
                    w.writerow([each_relay.id,
                                each_relay.unique_id,
                                unicode(each_relay.name).encode("utf-8"),
                                'hours_on',
                                value['1d']['hours_on'],
                                value['1w']['hours_on'],
                                value['1m']['hours_on'],
                                value['1m_date']['hours_on'],
                                value['1y']['hours_on']])
                    w.writerow([each_relay.id,
                                each_relay.unique_id,
                                unicode(each_relay.name).encode("utf-8"),
                                'kwh',
                                value['1d']['kwh'],
                                value['1w']['kwh'],
                                value['1m']['kwh'],
                                value['1m_date']['kwh'],
                                value['1y']['kwh']])
                    w.writerow([each_relay.id,
                                each_relay.unique_id,
                                unicode(each_relay.name).encode("utf-8"),
                                'cost',
                                value['1d']['cost'],
                                value['1w']['cost'],
                                value['1m']['cost'],
                                value['1m_date']['cost'],
                                value['1y']['cost']])

        set_user_grp(report_path_file, 'mycodo', 'mycodo')
    except Exception:
        logger.exception("Relay Usage Report Generation ERROR")

# coding=utf-8
import logging
import datetime

from mycodo.utils.influx import sum_relay_usage

logger = logging.getLogger("mycodo.tools")


def return_relay_usage(table_misc, table_relays):
    """ Return relay usage and cost """
    now = datetime.date.today()
    past_month_seconds = 0

    if table_misc.relay_stats_dayofmonth == datetime.datetime.today().day:
        dt_now = datetime.datetime.now()
        past_month_seconds = (dt_now - dt_now.replace(
            hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    elif table_misc.relay_stats_dayofmonth > datetime.datetime.today().day:
        first_day = now.replace(day=1)
        last_month = first_day - datetime.timedelta(days=1)
        past_month = last_month.replace(day=table_misc.relay_stats_dayofmonth)
        past_month_seconds = (now - past_month).total_seconds()
    elif table_misc.relay_stats_dayofmonth < datetime.datetime.today().day:
        past_month = now.replace(day=table_misc.relay_stats_dayofmonth)
        past_month_seconds = (now - past_month).total_seconds()

    # Calculate relay on duration for different time periods
    relay_stats = {
        'total_duration': dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0),
        'total_kwh': dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0),
        'total_cost': dict.fromkeys(['1d', '1w', '1m', '1m_date', '1y'], 0)
    }
    for each_relay in table_relays:
        past_1d_sec = sum_relay_usage(each_relay.id, 86400) / 3600
        past_1w_sec = sum_relay_usage(each_relay.id, 604800) / 3600
        past_1m_sec = sum_relay_usage(each_relay.id, 2629743) / 3600
        past_1m_date_sec = sum_relay_usage(each_relay.id, int(past_month_seconds)) / 3600
        past_1y_sec = sum_relay_usage(each_relay.id, 31556926) / 3600

        past_1d_kwh = table_misc.relay_stats_volts * each_relay.amps * past_1d_sec / 1000
        past_1w_kwh = table_misc.relay_stats_volts * each_relay.amps * past_1w_sec / 1000
        past_1m_kwh = table_misc.relay_stats_volts * each_relay.amps * past_1m_sec / 1000
        past_1m_date_kwh = table_misc.relay_stats_volts * each_relay.amps * past_1m_date_sec / 1000
        past_1y_kwh = table_misc.relay_stats_volts * each_relay.amps * past_1y_sec / 1000

        relay_stats[each_relay.id] = {
            '1d': {
                'seconds_on': past_1d_sec,
                'kwh': past_1d_kwh,
                'cost': table_misc.relay_stats_cost * past_1d_kwh
            },
            '1w': {
                'seconds_on': past_1w_sec,
                'kwh': past_1w_kwh,
                'cost': table_misc.relay_stats_cost * past_1w_kwh
            },
            '1m': {
                'seconds_on': past_1m_sec,
                'kwh': past_1m_kwh,
                'cost': table_misc.relay_stats_cost * past_1m_kwh
            },
            '1m_date': {
                'seconds_on': past_1m_date_sec,
                'kwh': past_1m_date_kwh,
                'cost': table_misc.relay_stats_cost * past_1m_date_kwh
            },
            '1y': {
                'seconds_on': past_1y_sec,
                'kwh': past_1y_kwh,
                'cost': table_misc.relay_stats_cost * past_1y_kwh
            }
        }

        relay_stats['total_duration']['1d'] += past_1d_sec
        relay_stats['total_duration']['1w'] += past_1w_sec
        relay_stats['total_duration']['1m'] += past_1m_sec
        relay_stats['total_duration']['1m_date'] += past_1m_date_sec
        relay_stats['total_duration']['1y'] += past_1y_sec

        relay_stats['total_kwh']['1d'] += past_1d_kwh
        relay_stats['total_kwh']['1w'] += past_1w_kwh
        relay_stats['total_kwh']['1m'] += past_1m_kwh
        relay_stats['total_kwh']['1m_date'] += past_1m_date_kwh
        relay_stats['total_kwh']['1y'] += past_1y_kwh

        relay_stats['total_cost']['1d'] += table_misc.relay_stats_cost * past_1d_kwh
        relay_stats['total_cost']['1w'] += table_misc.relay_stats_cost * past_1w_kwh
        relay_stats['total_cost']['1m'] += table_misc.relay_stats_cost * past_1m_kwh
        relay_stats['total_cost']['1m_date'] += table_misc.relay_stats_cost * past_1m_date_kwh
        relay_stats['total_cost']['1y'] += table_misc.relay_stats_cost * past_1y_kwh

    return relay_stats

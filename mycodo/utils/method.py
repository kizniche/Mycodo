# coding=utf-8
import datetime
from math import sin, radians

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.utils import session_scope
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


def bezier_curve_y_out(shift_angle, P0, P1, P2, P3, second_of_day=None):
    """
    For a cubic Bezier segment described by the 2-tuples P0, ..., P3, return
    the y-value associated with the given x-value.

    Ex: getYfromXforBezSegment((10,0), (5,-5), (5,5), (0,0), 3.2)
    """
    try:
        import numpy as np
    except ImportError:
        np = None

    if not np:
        return 0

    seconds_per_day = 24*60*60

    # Check if the second of the day is provided.
    # If provided, calculate y of the Bezier curve with that x
    # Otherwise, use the current second of the day
    if second_of_day is None:
        now = datetime.datetime.now()
        dt = datetime.timedelta(hours=now.hour,
                                minutes=now.minute,
                                seconds=now.second)
        seconds = dt.total_seconds()
    else:
        seconds = second_of_day

    # Shift the entire graph using 0 - 360 to determine the degree
    if shift_angle:
        percent_angle = shift_angle/360
        angle_seconds = percent_angle*seconds_per_day
        if seconds+angle_seconds > seconds_per_day:
            seconds_shifted = seconds+angle_seconds-seconds_per_day
        else:
            seconds_shifted = seconds+angle_seconds
        percent_of_day = seconds_shifted/seconds_per_day
    else:
        percent_of_day = seconds/seconds_per_day

    x = percent_of_day*(P0[0]-P3[0])

    # First, get the t-value associated with x-value, where t is the
    # parameterization of the Bezier curve and ranges from 0 to 1.
    # We need the coefficients of the polynomial describing cubic Bezier
    # (cubic polynomial in t)
    coefficients = [-P0[0] + 3*P1[0] - 3*P2[0] + P3[0],
                    3*P0[0] - 6*P1[0] + 3*P2[0],
                    -3*P0[0] + 3*P1[0],
                    P0[0] - x]
    # Find roots of the polynomial to determine the parameter t
    roots = np.roots(coefficients)
    # Find the root which is between 0 and 1, and is also real
    correct_root = None
    for root in roots:
        if np.isreal(root) and 0 <= root <= 1:
            correct_root = root
    # Check a valid root was found
    if correct_root is None:
        print('Error, no valid root found. Are you sure your Bezier curve '
              'represents a valid function when projected into the xy-plane?')
        return 0
    param_t = correct_root
    # From the value for the t parameter, find the corresponding y-value
    # using the formula for cubic Bezier curves
    y = (1-param_t)**3*P0[1] + 3*(1-param_t)**2*param_t*P1[1] + 3*(1-param_t)*param_t**2*P2[1] + param_t**3*P3[1]
    assert np.isreal(y)
    # Typecast y from np.complex128 to float64
    y = y.real
    return y


def calculate_method_setpoint(method_id, table, this_controller, Method, MethodData, logger):
    """
    Calculates the setpoint from a method
    :param method_id: ID of Method to be used
    :param table: Table of the this_controller using this function
    :param this_controller: The this_controller using this function
    :param logger: The logger to use
    :return: 0 (success) or 1 (error) and a setpoint value
    """
    method = db_retrieve_table_daemon(Method)

    method_key = method.filter(Method.unique_id == method_id).first()

    method_data = db_retrieve_table_daemon(MethodData)
    method_data = method_data.filter(MethodData.method_id == method_id)

    method_data_all = method_data.filter(MethodData.output_id == None).all()
    method_data_first = method_data.filter(MethodData.output_id == None).first()

    now = datetime.datetime.now()

    # Calculate where the current time/date is within the time/date method
    if method_key.method_type == 'Date':
        for each_method in method_data_all:
            start_time = datetime.datetime.strptime(each_method.time_start, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.datetime.strptime(each_method.time_end, '%Y-%m-%d %H:%M:%S')
            if start_time < now < end_time:
                setpoint_start = each_method.setpoint_start
                if each_method.setpoint_end:
                    setpoint_end = each_method.setpoint_end
                else:
                    setpoint_end = each_method.setpoint_start

                setpoint_diff = abs(setpoint_end - setpoint_start)
                total_seconds = (end_time - start_time).total_seconds()
                part_seconds = (now - start_time).total_seconds()
                percent_total = part_seconds / total_seconds

                if setpoint_start < setpoint_end:
                    new_setpoint = setpoint_start + (setpoint_diff * percent_total)
                else:
                    new_setpoint = setpoint_start - (setpoint_diff * percent_total)

                logger.debug("[Method] Start: {start} End: {end}".format(
                    start=start_time, end=end_time))
                logger.debug("[Method] Start: {start} End: {end}".format(
                    start=setpoint_start, end=setpoint_end))
                logger.debug("[Method] Total: {tot} Part total: {par} ({per}%)".format(
                    tot=total_seconds, par=part_seconds, per=percent_total))
                logger.debug("[Method] New Setpoint: {sp}".format(
                    sp=new_setpoint))
                return new_setpoint, False

    # Calculate where the current Hour:Minute:Seconds is within the Daily method
    elif method_key.method_type == 'Daily':
        daily_now = datetime.datetime.now().strftime('%H:%M:%S')
        daily_now = datetime.datetime.strptime(str(daily_now), '%H:%M:%S')
        for each_method in method_data_all:
            start_time = datetime.datetime.strptime(each_method.time_start, '%H:%M:%S')
            end_time = datetime.datetime.strptime(each_method.time_end, '%H:%M:%S')
            if start_time < daily_now < end_time:
                setpoint_start = each_method.setpoint_start
                if each_method.setpoint_end:
                    setpoint_end = each_method.setpoint_end
                else:
                    setpoint_end = each_method.setpoint_start

                setpoint_diff = abs(setpoint_end-setpoint_start)
                total_seconds = (end_time-start_time).total_seconds()
                part_seconds = (daily_now-start_time).total_seconds()
                percent_total = part_seconds/total_seconds

                if setpoint_start < setpoint_end:
                    new_setpoint = setpoint_start+(setpoint_diff*percent_total)
                else:
                    new_setpoint = setpoint_start-(setpoint_diff*percent_total)

                logger.debug("[Method] Start: {start} End: {end}".format(
                    start=start_time.strftime('%H:%M:%S'),
                    end=end_time.strftime('%H:%M:%S')))
                logger.debug("[Method] Start: {start} End: {end}".format(
                    start=setpoint_start, end=setpoint_end))
                logger.debug("[Method] Total: {tot} Part total: {par} ({per}%)".format(
                    tot=total_seconds, par=part_seconds, per=percent_total))
                logger.debug("[Method] New Setpoint: {sp}".format(
                    sp=new_setpoint))
                return new_setpoint, False

    # Calculate sine y-axis value from the x-axis (seconds of the day)
    elif method_key.method_type == 'DailySine':
        new_setpoint = sine_wave_y_out(method_data_first.amplitude,
                                       method_data_first.frequency,
                                       method_data_first.shift_angle,
                                       method_data_first.shift_y)
        return new_setpoint, False

    # Calculate Bezier curve y-axis value from the x-axis (seconds of the day)
    elif method_key.method_type == 'DailyBezier':
        new_setpoint = bezier_curve_y_out(
            method_data_first.shift_angle,
            (method_data_first.x0, method_data_first.y0),
            (method_data_first.x1, method_data_first.y1),
            (method_data_first.x2, method_data_first.y2),
            (method_data_first.x3, method_data_first.y3))
        return new_setpoint, False

    # Calculate the duration in the method based on self.method_start_time
    elif method_key.method_type == 'Duration':
        start_time = datetime.datetime.strptime(
            str(this_controller.method_start_time), '%Y-%m-%d %H:%M:%S.%f')
        ended = False

        # Check if method_end_time is not None
        if this_controller.method_end_time:
            # Convert time string to datetime object
            end_time = datetime.datetime.strptime(
                str(this_controller.method_end_time), '%Y-%m-%d %H:%M:%S.%f')
            if now > start_time:
                ended = True

        seconds_from_start = (now - start_time).total_seconds()
        total_sec = 0
        previous_total_sec = 0
        previous_end = None
        method_restart = False

        for each_method in method_data_all:
            # If duration_sec is 0, method has instruction to restart
            if each_method.duration_sec == 0:
                method_restart = True
            else:
                previous_end = each_method.setpoint_end

            total_sec += each_method.duration_sec
            if previous_total_sec <= seconds_from_start < total_sec:
                row_start_time = float(start_time.strftime('%s')) + previous_total_sec
                row_since_start_sec = (now - (start_time + datetime.timedelta(0, previous_total_sec))).total_seconds()
                percent_row = row_since_start_sec / each_method.duration_sec

                setpoint_start = each_method.setpoint_start
                if each_method.setpoint_end:
                    setpoint_end = each_method.setpoint_end
                else:
                    setpoint_end = each_method.setpoint_start
                setpoint_diff = abs(setpoint_end - setpoint_start)
                if setpoint_start < setpoint_end:
                    new_setpoint = setpoint_start + (setpoint_diff * percent_row)
                else:
                    new_setpoint = setpoint_start - (setpoint_diff * percent_row)

                logger.debug(
                    "[Method] Start: {start} Seconds Since: {sec}".format(
                        start=start_time, sec=seconds_from_start))
                logger.debug(
                    "[Method] Start time of row: {start}".format(
                        start=datetime.datetime.fromtimestamp(row_start_time)))
                logger.debug(
                    "[Method] Sec since start of row: {sec}".format(
                        sec=row_since_start_sec))
                logger.debug(
                    "[Method] Percent of row: {per}".format(
                        per=percent_row))
                logger.debug(
                    "[Method] New Setpoint: {sp}".format(
                        sp=new_setpoint))
                return new_setpoint, False
            previous_total_sec = total_sec

        if this_controller.method_start_time:
            if method_restart:
                if end_time and now > end_time:
                    ended = True
                else:
                    # Method has been instructed to restart
                    with session_scope(MYCODO_DB_PATH) as db_session:
                        mod_method = db_session.query(table)
                        mod_method = mod_method.filter(
                            table.unique_id == this_controller.unique_id).first()
                        mod_method.method_start_time = datetime.datetime.now()
                        db_session.commit()
                        return previous_end, False
            else:
                ended = True

            if ended:
                # Duration method has ended, reset method_start_time locally and in DB
                with session_scope(MYCODO_DB_PATH) as db_session:
                    mod_method = db_session.query(table).filter(
                        table.unique_id == this_controller.unique_id).first()
                    mod_method.method_start_time = 'Ended'
                    mod_method.method_end_time = None
                    db_session.commit()
                return None, True

    # Setpoint not needing to be calculated, use default setpoint
    return None, False


def sine_wave_y_out(amplitude, frequency, shift_angle,
                    shift_y, angle_in=None):
    if angle_in is None:
        now = datetime.datetime.now()
        dt = datetime.timedelta(hours=now.hour,
                                minutes=now.minute,
                                seconds=now.second)
        secs_per_day = 24 * 60 * 60
        angle = dt.total_seconds() / secs_per_day * 360
    else:
        angle = angle_in

    y = (amplitude * sin(radians(frequency * (angle - shift_angle)))) + shift_y
    return y

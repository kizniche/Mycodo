# coding=utf-8
import datetime
import time
from math import sin, radians

from mycodo.utils.system_pi import get_sec
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData


class AbstractMethod(object):
    """
    Basic class for methods. A method is called by controller (trigger, pid) to determine an analogue
    value. A trigger can use this as condition or forward into a pwm output. Pid can use these values
    to allow setpoint tracking functionality.
    The config frontend also displays plots of the method. This class also calculates the necessary values.
    """

    def __init__(self, method_data, method_type, logger=None):
        """
        Initializes the method class
        :param method_data: data queried from method_data table
        :param method_type: method type from method table
        :param logger: The logger to use
        :return: 0 (success) or 1 (error) and a setpoint value
        """
        self.logger = logger

        self.method_type = method_type

        self.method_data = method_data

        self.method_data_all = self.method_data.filter(MethodData.output_id.is_(None)).all()
        self.method_data_first = self.method_data.filter(MethodData.output_id.is_(None)).first()
        self.method_data_repeat = self.method_data.filter(MethodData.duration_sec == 0).first()

    def calculate_setpoint(self, now, method_start_time=None):
        """
        Returns the value for the setpoint for a given point in time and elapsed duration
        :param now: point in time to calculate the value for
        :param method_start_time: when this method started. Must accept datetime and strings
        :return: float value of the setpoint; True if method finished, otherwise False
        """
        return None, False

    def should_restart(self, now, method_start_time=None):
        """
        If a method has signalled to be finished, this method is asked if the controller should restart
        the method processing from the beginning.
        :param now: point in time to calculate the value for
        :param method_start_time: when this method started. Must accept datetime and strings
        :return: True if the method wants to be restarted, otherwise False
        """
        return False

    def get_plot(self, max_points_x=None):
        """
        Called to calculate values to render a plot in the frontend.
        :param max_points_x:
        :return:  2d array with x and y values.
        """
        return []


class DateMethod(AbstractMethod):
    """
    A time/date method allows a specific time/date span to dictate the setpoint.
    This is useful for long-running methods, that may take place over the period of days, weeks, or months.
    """

    def ignore_date(self):
        """
        :return: False -> date part of date-time should be considered
        """
        return False

    def calculate_setpoint(self, now, method_start_time=None):
        # Calculate where the current time/date is within the time/date method

        if self.ignore_date():
            now = datetime.datetime.strptime(str(now.strftime('%H:%M:%S')), '%H:%M:%S')

        for each_method in self.method_data_all:
            if self.ignore_date():
                start_time = datetime.datetime.strptime(each_method.time_start, '%H:%M:%S')
                end_time = datetime.datetime.strptime(each_method.time_end, '%H:%M:%S')
            else:
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

                if self.logger:
                    if self.ignore_date():
                        self.logger.debug("[Method] Start: {start} End: {end}".format(
                            start=start_time.strftime('%H:%M:%S'),
                            end=end_time.strftime('%H:%M:%S')))
                    else:
                        self.logger.debug("[Method] Start: {start} End: {end}".format(
                            start=start_time, end=end_time))
                    self.logger.debug("[Method] Start: {start} End: {end}".format(
                        start=setpoint_start, end=setpoint_end))
                    self.logger.debug("[Method] Total: {tot} Part total: {par} ({per}%)".format(
                        tot=total_seconds, par=part_seconds, per=percent_total))
                    self.logger.debug("[Method] New Setpoint: {sp}".format(
                        sp=new_setpoint))
                return new_setpoint, False

        # Setpoint not needing to be calculated, use default setpoint
        return None, False

    def get_plot(self, max_points_x=None):
        result = []
        for each_method in self.method_data_all:
            if each_method.setpoint_end is None:
                setpoint_end = each_method.setpoint_start
            else:
                setpoint_end = each_method.setpoint_end

            start_time = datetime.datetime.strptime(
                each_method.time_start, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.datetime.strptime(
                each_method.time_end, '%Y-%m-%d %H:%M:%S')

            is_dst = time.daylight and time.localtime().tm_isdst > 0
            utc_offset_ms = (time.altzone if is_dst else time.timezone)
            result.append(
                [(int(start_time.strftime("%s")) - utc_offset_ms) * 1000,
                 each_method.setpoint_start])
            result.append(
                [(int(end_time.strftime("%s")) - utc_offset_ms) * 1000,
                 setpoint_end])
            result.append(
                [(int(start_time.strftime("%s")) - utc_offset_ms) * 1000,
                 None])

        return result


class DailyMethod(DateMethod):
    """
    The daily time-based method is similar to the time/date method, however it will repeat every day.
    Therefore, it is essential that only the span of one day be set in this method.

    The implementation is derived from DateMethod, as the calculation is essentially the same ignoring the date part.
    """

    def ignore_date(self):
        """
        :return: True -> date part of date-time should be ignored aka the method's data repeat on a daily basis.
        """
        return True

    def get_plot(self, max_points_x=None):
        result = []
        for each_method in self.method_data_all:
            if each_method.time_start is None or each_method.time_end is None:
                continue
            if each_method.setpoint_end is None:
                setpoint_end = each_method.setpoint_start
            else:
                setpoint_end = each_method.setpoint_end
            result.append(
                [get_sec(each_method.time_start) * 1000,
                 each_method.setpoint_start])
            result.append(
                [get_sec(each_method.time_end) * 1000,
                 setpoint_end])
            result.append(
                [get_sec(each_method.time_start) * 1000,
                 None])
        return result


class AbstractDailyFormulaMethod(AbstractMethod):
    """
    Abstract base for mathematical function based methods. It offers shared functionality to generate the frontend
    plot by iterating through the x axis and calling the calculate_setpoint function to get the corresponding y values.
    """

    def get_plot(self, max_points_x=700):
        result = []

        seconds_in_day = 60 * 60 * 24
        today = datetime.datetime(1900, 1, 1)
        for n in range(max_points_x):
            percent = n / float(max_points_x)
            now = today + datetime.timedelta(seconds=percent * seconds_in_day)
            y, ended = self.calculate_setpoint(now)
            if not ended:
                result.append([percent * seconds_in_day * 1000, y])

        return result


class DailySineMethod(AbstractDailyFormulaMethod):
    """
    The daily sine wave method defines the setpoint over the day based on a sinusoidal wave.
    The sine wave is defined by y = [A * sin(B * x + C)] + D, where A is amplitude, B is frequency,
    C is the angle shift, and D is the y-axis shift. This method will repeat daily.
    """

    def calculate_setpoint(self, now, method_start_time=None):
        # Calculate sine y-axis value from the x-axis (seconds of the day)
        dt = datetime.timedelta(hours=now.hour,
                                minutes=now.minute,
                                seconds=now.second)
        secs_per_day = 24 * 60 * 60
        angle = dt.total_seconds() / secs_per_day * 360
        new_setpoint = sine_wave_y_out(self.method_data_first.amplitude,
                                       self.method_data_first.frequency,
                                       self.method_data_first.shift_angle,
                                       self.method_data_first.shift_y,
                                       angle)
        return new_setpoint, False


class DailyBezierMethod(AbstractDailyFormulaMethod):
    def calculate_setpoint(self, now, method_start_time=None):
        # Calculate Bezier curve y-axis value from the x-axis (seconds of the day)

        dt = datetime.timedelta(hours=now.hour,
                                minutes=now.minute,
                                seconds=now.second)

        new_setpoint = bezier_curve_y_out(
            self.method_data_first.shift_angle,
            (self.method_data_first.x0, self.method_data_first.y0),
            (self.method_data_first.x1, self.method_data_first.y1),
            (self.method_data_first.x2, self.method_data_first.y2),
            (self.method_data_first.x3, self.method_data_first.y3),
            dt.total_seconds())

        return new_setpoint, False


class DurationMethod(AbstractMethod):
    """
    A daily Bezier curve method define the setpoint over the day based on a cubic Bezier curve.
    The x-axis start (x3) and end (x0) will be automatically stretched or skewed to fit within a
    24-hour period and this method will repeat daily.
    """

    def calculate_setpoint(self, now, method_start_time=None):
        # Calculate the duration in the method based on self.method_start_time

        start_time = datetime.datetime.strptime(str(method_start_time), '%Y-%m-%d %H:%M:%S.%f')

        seconds_from_start = (now - start_time).total_seconds()
        total_sec = 0
        previous_total_sec = 0

        for each_method in self.method_data_all:

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

                if self.logger:
                    self.logger.debug(
                        "[Method] Start: {start} Seconds Since: {sec}".format(
                            start=start_time, sec=seconds_from_start))
                    self.logger.debug(
                        "[Method] Start time of row: {start}".format(
                            start=datetime.datetime.fromtimestamp(row_start_time)))
                    self.logger.debug(
                        "[Method] Sec since start of row: {sec}".format(
                            sec=row_since_start_sec))
                    self.logger.debug(
                        "[Method] Percent of row: {per}".format(
                            per=percent_row))
                    self.logger.debug(
                        "[Method] New Setpoint: {sp}".format(
                            sp=new_setpoint))
                return new_setpoint, False
            previous_total_sec = total_sec

        return None, True

    def should_restart(self, now, method_start_time=None):
        for each_method in self.method_data_all:
            # If duration_sec is 0, method has instruction to restart
            if each_method.duration_sec == 0:
                return True

        return False

    def get_plot(self, max_points_x=None):
        result = []
        first_entry = True
        start_duration = 0
        for each_method in self.method_data_all:
            if each_method.setpoint_end is None:
                setpoint_end = each_method.setpoint_start
            else:
                setpoint_end = each_method.setpoint_end

            if each_method.duration_sec == 0:
                pass  # Method line is repeat command, don't add to method_list
            elif first_entry:
                result.append([0, each_method.setpoint_start])
                result.append([each_method.duration_sec, setpoint_end])
                start_duration += each_method.duration_sec
                first_entry = False
            else:
                end_duration = start_duration + each_method.duration_sec

                result.append(
                    [start_duration, each_method.setpoint_start])
                result.append(
                    [end_duration, setpoint_end])

                start_duration += each_method.duration_sec

        return result


def method_by_type(method_data, method_type, logger=None):
    """
    Looks up a method class suitable to the given method_type and initializes it with the given method_data
    """

    method_class = globals().get(method_type+"Method")
    if not method_class or not issubclass(method_class, AbstractMethod):
        logger.error("Method {} is unknown.".format(method_type))
        method_class = AbstractMethod

    return method_class(method_data, method_type, logger)


def load_method(method_id, logger=None):
    """
    Loads method type and data from database for the given method_id. Then uses method_by_type to create an instance.
    """

    method_type = db_retrieve_table_daemon(Method).filter(Method.unique_id == method_id).first().method_type
    method_data = db_retrieve_table_daemon(MethodData).filter(MethodData.method_id == method_id)

    return method_by_type(method_data, method_type, logger)


def sine_wave_y_out(amplitude, frequency, shift_angle,
                    shift_y, angle_in):
    if angle_in is None:
        raise Exception("angle_in must be specified")
    else:
        angle = angle_in

    y = (amplitude * sin(radians(frequency * (angle - shift_angle)))) + shift_y
    return y


def bezier_curve_y_out(shift_angle, P0, P1, P2, P3, second_of_day):
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
        raise Exception("second_of_day must be specified")
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

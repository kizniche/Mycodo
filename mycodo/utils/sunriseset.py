# coding=utf-8

#    Source:
#    Almanac for Computers, 1990
#    published by Nautical Almanac Office
#    United States Naval Observatory
#    Washington, DC 20392

# Inputs:
#     latitude, longitude: location for sunrise/sunset
#     zenith: Sun's zenith for sunrise/sunset
#       official     = 90 degrees 50'
#       civil        = 96 degrees
#       nautical     = 102 degrees
#       astronomical = 108 degrees

#   NOTE: longitude is positive for East and negative for West
#   NOTE: the algorithm assumes the use of a calculator with the
#         trig functions in "degree" (rather than "radian") mode. Most
#         programming languages assume radian arguments, requiring back
#         and forth conversions. The factor is 180/pi. So, for instance,
#         the equation RA = atan(0.91764 * tan(L)) would be coded as RA
#         = (180/pi)*atan(0.91764 * tan((pi/180)*L)) to give a degree
#         answer with a degree input for L.

import datetime
import logging
import math
from dateutil import tz
from dateutil.parser import parse

from mycodo.utils.logging_utils import set_log_level

logger = logging.getLogger("mycodo.sun_rise_set")
logger.setLevel(set_log_level(logging))


class Sun:
    """
    Calculates sunrise and sunset times based on latitude, longitude,
    and zenith
    """
    def __init__(self, latitude, longitude, zenith=90.0,
                 day=None, month=None, year=None, offset_minutes=None):
        self.latitude = latitude
        self.longitude = longitude
        self.zenith = zenith
        self.offset_minutes = offset_minutes
        if None in (day, month, year):
            self.day, self.month, self.year = self.get_current_uct()
        else:
            self.day = day
            self.month = month
            self.year = year

    @staticmethod
    def get_current_uct():
        """Return day, month, and year of current UTC time."""
        now = datetime.datetime.now()
        return [now.day, now.month, now.year]

    @staticmethod
    def force_range(v, maximum):
        # force v to be >= 0 and < maximum
        if v < 0:
            return v + maximum
        elif v >= maximum:
            return v - maximum
        return v

    def get_sunrise_time(self):
        return self.calc_sun_time(True)

    def get_sunset_time(self):
        return self.calc_sun_time(False)

    def calc_sun_time(self, is_rise_time):
        # is_rise_time == False, returns sunsetTime

        to_rad = math.pi / 180

        # 1. first calculate the day of the year
        n1 = math.floor(275 * self.month / 9)
        n2 = math.floor((self.month + 9) / 12)
        n3 = (1 + math.floor((self.year - 4 * math.floor(self.year / 4) + 2) / 3))
        n = n1 - (n2 * n3) + self.day - 30

        # 2. convert the self.longitude to hour value and calculate an approximate time
        long_hour = self.longitude / 15

        if is_rise_time:
            t = n + ((6 - long_hour) / 24)
        else:  # sunset
            t = n + ((18 - long_hour) / 24)

        # 3. calculate the Sun's mean anomaly
        m = (0.9856 * t) - 3.289

        # 4. calculate the Sun's true self.longitude
        l = m + (1.916 * math.sin(to_rad * m)) + (0.020 * math.sin(to_rad * 2 * m)) + 282.634
        l = self.force_range(l, 360)  # NOTE: l adjusted into the range [0,360)

        # 5a. calculate the Sun's right ascension

        ra = (1 / to_rad) * math.atan(0.91764 * math.tan(to_rad * l))
        ra = self.force_range(ra, 360)  # NOTE: ra adjusted into the range [0,360)

        # 5b. right ascension value needs to be in the same quadrant as l
        l_quadrant = (math.floor(l / 90)) * 90
        ra_quadrant = (math.floor(ra / 90)) * 90
        ra += l_quadrant - ra_quadrant

        # 5c. right ascension value needs to be converted into hours
        ra /= 15

        # 6. calculate the Sun's declination
        sin_dec = 0.39782 * math.sin(to_rad * l)
        cos_dec = math.cos(math.asin(sin_dec))

        # 7a. calculate the Sun's local hour angle
        cos_h = ((math.cos(to_rad * self.zenith) -
                  (sin_dec * math.sin(to_rad * self.latitude))) /
                 (cos_dec * math.cos(to_rad * self.latitude)))

        if cos_h > 1:
            return {'status': False,
                    'msg': 'the sun never rises on this '
                           'location (on the specified date)'}
        elif cos_h < -1:
            return {'status': False,
                    'msg': 'the sun never sets on this '
                           'location (on the specified date)'}

        # 7b. finish calculating H and convert into hours

        if is_rise_time:
            h = 360 - (1/to_rad) * math.acos(cos_h)
        else:  # setting
            h = (1/to_rad) * math.acos(cos_h)

        h /= 15

        # 8. calculate local mean time of rising/setting
        t = h + ra - (0.06571 * t) - 6.622

        # 9. adjust to UTC
        ut = t - long_hour
        ut = self.force_range(ut, 24)  # UTC time in decimal format (e.g. 23.23)
        ut_hour = self.force_range(int(ut), 24)
        ut_minute = round((ut - int(ut)) * 60, 0)
        time_utc = parse('{hour}:{min}'.format(
            hour=ut_hour, min=ut_minute)).replace(tzinfo=tz.tzutc())

        if self.offset_minutes:
            time_utc = time_utc + datetime.timedelta(minutes=self.offset_minutes)

        # 10. calculate local time
        time_local = time_utc.astimezone(tz.tzlocal())

        # Ensure time is in the future
        now = datetime.datetime.now(tz.tz.tzlocal())

        while now > time_local:
            time_utc = time_utc + datetime.timedelta(days=1)
            time_local = time_local + datetime.timedelta(days=1)

        dict_sunriseset = {
            'status': True,
            'utc_time': time_utc,
            'utc_hour': ut_hour,
            'utc_min': ut_minute,
            'time_local': time_local,
            'local_hour': time_local.hour,
            'local_minute': time_local.minute
        }

        return dict_sunriseset


def calculate_next_sunrise_sunset_epoch(latitude, longitude, zenith, date_offset_days, time_offset_minutes, rise_or_set):
    try:
        # Adjust for date offset
        now = datetime.datetime.now()
        new_date = now + datetime.timedelta(days=date_offset_days)

        sun = Sun(latitude=latitude,
                  longitude=longitude,
                  zenith=zenith,
                  day=new_date.day,
                  month=new_date.month,
                  year=new_date.year,
                  offset_minutes=time_offset_minutes)

        if rise_or_set == 'sunrise':
            print(f"Old Sunrise: {sun.calc_sun_time(True)['time_local']}")
            return float(sun.calc_sun_time(True)['time_local'].strftime('%s'))
        elif rise_or_set == 'sunset':
            print(f"Old Sunset: {sun.calc_sun_time(False)['time_local']}")
            return float(sun.calc_sun_time(False)['time_local'].strftime('%s'))
    except Exception:
        logger.exception("Generating next sunrise/sunset time")
        return None


def suntime_calculate_next_sunrise_sunset_epoch(latitude, longitude, date_offset_days, time_offset_minutes, rise_or_set, return_dt=False):
    try:
        from suntime import SunTimeException
        from suntime import Sun as SunTime

        sun = SunTime(latitude, longitude)
        now = datetime.datetime.now()
        new_date = now + datetime.timedelta(days=date_offset_days)
        new_date = new_date + datetime.timedelta(minutes=time_offset_minutes)

        if rise_or_set == 'sunrise':
            sunrise = sun.get_local_sunrise_time(new_date)
            if time_offset_minutes != 0:
                sunrise = sunrise + datetime.timedelta(minutes=time_offset_minutes)
            while sunrise.timestamp() > now.timestamp():  # Find sunrise for yesterday
                sunrise = sunrise - datetime.timedelta(days=1)  # Make sunrise yesterday
            while sunrise.timestamp() < now.timestamp():  # Find sunrise for tomorrow
                sunrise = sunrise + datetime.timedelta(days=1)  # Make sunrise tomorrow
            if return_dt:
                return sunrise
            else:
                return float(sunrise.strftime('%s'))
        elif rise_or_set == 'sunset':
            sunset = sun.get_local_sunset_time(new_date)
            if time_offset_minutes != 0:
                sunset = sunset + datetime.timedelta(minutes=time_offset_minutes)
            while sunset.timestamp() > now.timestamp():  # Find sunset for yesterday
                sunset = sunset - datetime.timedelta(days=1)  # Make sunset yesterday
            while sunset.timestamp() < now.timestamp():  # Find sunset for tomorrow
                sunset = sunset + datetime.timedelta(days=1)  # Make sunset tomorrow
            if return_dt:
                return sunset
            else:
                return float(sunset.strftime('%s'))
    except SunTimeException:
        logger.exception("Generating next sunrise/sunset time")
        return
    except Exception:
        logger.exception("Generating next sunrise/sunset time")
        return


if __name__ == '__main__':
    latitude = 33.749249
    longitude = -84.387314
    zenith = 90.8

    sunrise = calculate_next_sunrise_sunset_epoch(latitude, longitude, zenith, 0, 0, "sunrise")
    sunset = calculate_next_sunrise_sunset_epoch(latitude, longitude, zenith, 0, 0, "sunset")

    print(f"Sunrise: {sunrise}")
    print(f"Sunset:  {sunset}")

    unrise = suntime_calculate_next_sunrise_sunset_epoch(latitude, longitude, 0, 0, "sunrise")
    sunset = suntime_calculate_next_sunrise_sunset_epoch(latitude, longitude, 0, 0, "sunset")

    print(f"Sunrise: {sunrise}")
    print(f"Sunset:  {sunset}")

#!/usr/bin/python
# coding=utf-8
#
# controller_log.py - Log controller to periodically query influxdb
#                     and append a log file
#

import calendar
import os
import threading
import time
import timeit
from dateutil.parser import parse as date_parse

from config import LOG_PATH
from config import SQL_DATABASE_MYCODO
from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from databases.mycodo_db.models import Log
from databases.utils import session_scope

from utils.influx import read_last_influxdb
from utils.system_pi import assure_path_exists
from utils.system_pi import find_owner
from utils.system_pi import set_user_grp

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class LogController(threading.Thread):
    """
    class for controlling the writing of log files from influxdb

    """

    def __init__(self, ready, logger, log_id):
        threading.Thread.__init__(self)

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.logger = logger
        self.log_id = log_id

        with session_scope(MYCODO_DB_PATH) as new_session:
            log = new_session.query(Log).filter(Log.id == self.log_id).first()
            self.name = log.name
            self.sensor_id = log.sensor_id
            self.measure_type = log.measure_type
            self.period = log.period

        self.last_timestamp = 0
        self.timer = time.time() + self.period
        self.running = False
        self.lastUpdate = None


    def run(self):
        self.running = True
        self.logger.info("[Log {}] Activated in {:.1f} ms".format(
            self.log_id,
            (timeit.default_timer()-self.thread_startup_timer)*1000))
        self.ready.set()

        while self.running:
            if time.time() > self.timer:
                self.write_log()
                self.timer = time.time() + self.period
            time.sleep(1)

        self.running = False
        self.logger.info("[Log {}] Deactivated in {:.1f} ms".format(
            self.log_id,
            (timeit.default_timer()-self.thread_shutdown_timer)*1000))


    def write_log(self):
        """
        Append log file with latest measurement if the latest measurement
        timestamp is more recent than the last retrieved timestamp.
        """
        self.logger.debug("Log Controller: {} ({}) {} {} {}".format(
                self.log_id, self.name, self.sensor_id,
                self.measure_type, self.period))
        try:
            self.last_measurement = read_last_influxdb(
                INFLUXDB_HOST,
                INFLUXDB_PORT,
                INFLUXDB_USER,
                INFLUXDB_PASSWORD,
                INFLUXDB_DATABASE,
                self.sensor_id,
                self.measure_type)
            if self.last_measurement:
                measurement_list = list(self.last_measurement.get_points(
                    measurement=self.measure_type))
                self.last_time = measurement_list[0]['time']
                self.last_measurement = measurement_list[0]['value']
            else:
                self.logger.warning("[Log {}] No data returned "
                                    "from influxdb".format(self.log_id))
                return 1

            self.dt =  date_parse(self.last_time)
            self.timestamp = calendar.timegm(self.dt.timetuple())
            if self.last_timestamp != self.timestamp:
                self.last_timestamp = self.timestamp
                self.logger.debug("[Log {}] Time: {}, {} Value: "
                                  "{}".format(self.log_id,
                                              self.last_time,
                                              self.timestamp,
                                              self.last_measurement))
                SENSOR_LOG_FILE = os.path.join(
                    LOG_PATH, "{}-{}.log".format(self.sensor_id,
                                                 self.measure_type))
                assure_path_exists(LOG_PATH)
                with open(SENSOR_LOG_FILE, "a") as log_file:
                    log_file.write("{},{}\n".format(self.timestamp, self.last_measurement))

                # Ensure log is owned by user 'mycodo'
                if find_owner(SENSOR_LOG_FILE) != 'mycodo':
                    set_user_grp(SENSOR_LOG_FILE, 'mycodo', 'mycodo')
            else:
                self.logger.debug("[Log {}] No new data from "
                                    "influxdb could be "
                                    "retrieved.".format(self.log_id))
        except Exception as except_msg:
            self.logger.exception("[Log {}] Could not retrieve influxdb"
                                " data: {}".format(self.log_id,
                                                   except_msg))


    def isRunning(self):
        return self.running


    def stopController(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

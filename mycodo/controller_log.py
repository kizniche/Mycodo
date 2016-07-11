#!/usr/bin/python
# coding=utf-8
#
# controller_log.py - Log controller to periodically query influxdb
#                     and append a log file
#

import calendar
import logging
import os
import sys
import threading
import time
import timeit
from dateutil.parser import parse as date_parse
from influxdb import InfluxDBClient

from config import LOG_PATH
from config import SQL_DATABASE_MYCODO
from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from databases.mycodo_db.models import Log
from databases.utils import session_scope

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
        self.client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT,
                                     INFLUXDB_USER, INFLUXDB_PASSWORD,
                                     INFLUXDB_DATABASE)

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
        self.logger.info("[Log {}] Activated in {}ms".format(
            self.log_id,
            (timeit.default_timer()-self.thread_startup_timer)*1000))
        self.ready.set()
        
        while (self.running):
            if time.time() > self.timer:
                self.write_log()
                self.timer = time.time() + self.period
            time.sleep(1)

        self.running = False
        self.logger.info("[Log {}] Deactivated in {}ms".format(
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
            result = self.client.query("""SELECT last(value)
                                          FROM {}
                                          WHERE device_id='{}' AND
                                                time > now() - 1m;
                                       """.format(self.measure_type,
                                                  self.sensor_id)).raw
            self.time = result['series'][0]['values'][0][0]
            self.value = result['series'][0]['values'][0][1]
            self.dt =  date_parse(self.time)
            self.timestamp = calendar.timegm(self.dt.timetuple())
            if self.last_timestamp != self.timestamp:
                self.last_timestamp = self.timestamp
                self.logger.debug("[Log {}] Time: {}, {} Value: "
                                  "{}".format(self.log_id,
                                              self.time,
                                              self.timestamp,
                                              self.value))
                SENSOR_LOG_FILE = os.path.join(
                    LOG_PATH, "{}-{}.log".format(self.sensor_id,
                                                 self.measure_type))
                if not os.path.exists(LOG_PATH):
                    os.makedirs(LOG_PATH)
                with open(SENSOR_LOG_FILE, "a") as log_file:
                    log_file.write("{},{}\n".format(self.timestamp, self.value))
            else:
                self.logger.warning("[Log {}] No new data from "
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

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodoLog.py - Mycodo Log Module
#
#  Copyright (C) 2015  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com


import datetime
import filecmp
import fileinput
import logging
import os
from lockfile import LockFile

install_directory = os.path.dirname(os.path.abspath(__file__)) + "/.."

log_path = "%s/log" % install_directory # Where generated logs are stored

# Logs that are on the tempfs
daemon_log_file_tmp = "%s/daemon-tmp.log" % log_path
sensor_t_log_file_tmp = "%s/sensor-t-tmp.log" % log_path
sensor_ht_log_file_tmp = "%s/sensor-ht-tmp.log" % log_path
sensor_co2_log_file_tmp = "%s/sensor-co2-tmp.log" % log_path
sensor_press_log_file_tmp = "%s/sensor-press-tmp.log" % log_path
relay_log_file_tmp = "%s/relay-tmp.log" % log_path

# Logs that are periodically concatenated (every 6 hours) to the SD card
daemon_log_file = "%s/daemon.log" % log_path
sensor_t_log_file = "%s/sensor-t.log" % log_path
sensor_ht_log_file = "%s/sensor-ht.log" % log_path
sensor_co2_log_file = "%s/sensor-co2.log" % log_path
sensor_press_log_file = "%s/sensor-press.log" % log_path
relay_log_file = "%s/relay.log" % log_path

# Lockfiles
lock_directory = "/var/lock/mycodo"
sensor_t_log_lock_path = "%s/sensor-t-log" % lock_directory
sensor_ht_log_lock_path = "%s/sensor-ht-log" % lock_directory
sensor_co2_log_lock_path = "%s/sensor-co2-log" % lock_directory
sensor_press_log_lock_path = "%s/sensor-press-log" % lock_directory
relay_log_lock_path = "%s/relay" % lock_directory
daemon_log_lock_path = "%s/logs" % lock_directory

#################################################
#           Sensor and Relay Logging            #
#################################################

# Log temperature sensor reading
def write_t_sensor_log(sensor_t_read_temp_c, sensor):
    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_t_log_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Write Sensor Log] Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write Sensor Log] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()

    logging.debug("[Write Sensor Log] Gained lock: %s", lock.path)

    try:
        with open(sensor_t_log_file_tmp, "ab") as sensorlog:
            sensorlog.write('{0} {1:.1f} {2:d}\n'.format(
                datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),
                sensor_t_read_temp_c[sensor], sensor))
            logging.debug("[Write Sensor Log] Data appended to %s", sensor_t_log_file_tmp)
    except:
        logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_t_log_file_tmp)

    logging.debug("[Write Sensor Log] Removing lock: %s", lock.path)
    lock.release()

# Log temperature/humidity sensor reading
def write_ht_sensor_log(sensor_ht_read_temp_c, sensor_ht_read_hum, sensor_ht_dewpt_c, sensor):
    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_ht_log_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Write Sensor Log] Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write Sensor Log] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()

    logging.debug("[Write Sensor Log] Gained lock: %s", lock.path)

    try:
        with open(sensor_ht_log_file_tmp, "ab") as sensorlog:
            sensorlog.write('{0} {1:.1f} {2:.1f} {3:.1f} {4:d}\n'.format(
                datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),
                sensor_ht_read_temp_c[sensor], sensor_ht_read_hum[sensor], sensor_ht_dewpt_c[sensor], sensor))
            logging.debug("[Write Sensor Log] Data appended to %s", sensor_ht_log_file_tmp)
    except:
        logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_ht_log_file_tmp)

    logging.debug("[Write Sensor Log] Removing lock: %s", lock.path)
    lock.release()

# Log CO2 sensor reading
def write_co2_sensor_log(sensor_co2_read_co2, sensor):
    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_co2_log_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Write CO2 Sensor Log] Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write CO2 Sensor Log] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()

    logging.debug("[Write CO2 Sensor Log] Gained lock: %s", lock.path)

    try:
        with open(sensor_co2_log_file_tmp, "ab") as sensorlog:
            sensorlog.write('{0} {1:d} {2:d}\n'.format(
                datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),
                sensor_co2_read_co2[sensor], sensor))
            logging.debug("[Write CO2 Sensor Log] Data appended to %s", sensor_co2_log_file_tmp)
    except:
        logging.warning("[Write CO2 Sensor Log] Unable to append data to %s", sensor_co2_log_file_tmp)

    logging.debug("[Write CO2 Sensor Log] Removing lock: %s", lock.path)
    lock.release()

# Log pressure sensor reading
def write_press_sensor_log(sensor_press_read_temp_c, sensor_press_read_press, sensor_press_read_alt, sensor):
    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_press_log_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Write Sensor Log] Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write Sensor Log] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()

    logging.debug("[Write Sensor Log] Gained lock: %s", lock.path)

    try:
        with open(sensor_press_log_file_tmp, "ab") as sensorlog:
            sensorlog.write('{0} {1:.1f} {2:d} {3:.1f} {4:d}\n'.format(
                datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),
                sensor_press_read_temp_c[sensor], sensor_press_read_press[sensor], sensor_press_read_alt[sensor], sensor))
            logging.debug("[Write Sensor Log] Data appended to %s", sensor_press_log_file_tmp)
    except:
        logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_press_log_file_tmp)

    logging.debug("[Write Sensor Log] Removing lock: %s", lock.path)
    lock.release()

# Log the relay duration
def write_relay_log(relayNumber, relaySeconds, sensor, gpio):
    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(relay_log_lock_path)

    while not lock.i_am_locking():
        try:
            logging.debug("[Write Relay Log] Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write Relay Log] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()

    logging.debug("[Write Relay Log] Gained lock: %s", lock.path)

    try:
        with open(relay_log_file_tmp, "ab") as relaylog:
            relaylog.write('{0} {1:d} {2:d} {3:d} {4:.2f}\n'.format(
                datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),
                sensor, relayNumber, gpio, relaySeconds))

    except:
        logging.warning("[Write Relay Log] Unable to append data to %s", relay_log_file_tmp)

    logging.debug("[Write Relay Log] Removing lock: %s", lock.path)
    lock.release()

# Combines the logs on the SD card with the logs on the temporary file system
def Concatenate_Logs():
    # Temperature Sensor Logs
    if not filecmp.cmp(sensor_t_log_file_tmp, sensor_t_log_file):
        logging.debug("[Log Backup] Concatenating T sensor logs to %s", sensor_t_log_file)
        lock = LockFile(sensor_t_log_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Log Backup] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Log Backup] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Log Backup] Gained lock: %s", lock.path)

        try:
            with open(sensor_t_log_file, 'a') as fout:
                for line in fileinput.input(sensor_t_log_file_tmp):
                    fout.write(line)
            logging.debug("[Log Backup] Appended T data to %s", sensor_t_log_file)
        except:
            logging.warning("[Log Backup] Unable to append data to %s", sensor_t_log_file)

        open(sensor_t_log_file_tmp, 'w').close()
        logging.debug("[Log Backup] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Log Backup] T Sensor logs the same, skipping.")

    # Humidity/Temperature Sensor Logs
    if not filecmp.cmp(sensor_ht_log_file_tmp, sensor_ht_log_file):
        logging.debug("[Log Backup] Concatenating HT sensor logs to %s", sensor_ht_log_file)
        lock = LockFile(sensor_ht_log_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Log Backup] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Log Backup] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Log Backup] Gained lock: %s", lock.path)

        try:
            with open(sensor_ht_log_file, 'a') as fout:
                for line in fileinput.input(sensor_ht_log_file_tmp):
                    fout.write(line)
            logging.debug("[Log Backup] Appended HT data to %s", sensor_ht_log_file)
        except:
            logging.warning("[Log Backup] Unable to append data to %s", sensor_ht_log_file)

        open(sensor_ht_log_file_tmp, 'w').close()
        logging.debug("[Log Backup] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Log Backup] HT Sensor logs the same, skipping.")

    # CO2 Sensor Logs
    if not filecmp.cmp(sensor_co2_log_file_tmp, sensor_co2_log_file):
        logging.debug("[Log Backup] Concatenating CO2 sensor logs to %s", sensor_co2_log_file)
        lock = LockFile(sensor_co2_log_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Log Backup] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Log Backup] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Log Backup] Gained lock: %s", lock.path)

        try:
            with open(sensor_co2_log_file, 'a') as fout:
                for line in fileinput.input(sensor_co2_log_file_tmp):
                    fout.write(line)
            logging.debug("[Log Backup] Appended CO2 data to %s", sensor_co2_log_file)
        except:
            logging.warning("[Log Backup] Unable to append data to %s", sensor_co2_log_file)

        open(sensor_co2_log_file_tmp, 'w').close()
        logging.debug("[Log Backup] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Log Backup] CO2 Sensor logs the same, skipping.")

    # Pressure Sensor Logs
    if not filecmp.cmp(sensor_press_log_file_tmp, sensor_press_log_file):
        logging.debug("[Log Backup] Concatenating Press sensor logs to %s", sensor_press_log_file)
        lock = LockFile(sensor_press_log_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Log Backup] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Log Backup] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Log Backup] Gained lock: %s", lock.path)

        try:
            with open(sensor_press_log_file, 'a') as fout:
                for line in fileinput.input(sensor_press_log_file_tmp):
                    fout.write(line)
            logging.debug("[Log Backup] Appended Press data to %s", sensor_press_log_file)
        except:
            logging.warning("[Log Backup] Unable to append data to %s", sensor_press_log_file)

        open(sensor_press_log_file_tmp, 'w').close()
        logging.debug("[Log Backup] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Log Backup] Press Sensor logs the same, skipping.")

    # Relay Logs
    if not filecmp.cmp(relay_log_file_tmp, relay_log_file):
        logging.debug("[Log Backup] Concatenating relay logs to %s", relay_log_file)
        lock = LockFile(relay_log_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Log Backup] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Log Backup] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Log Backup] Gained lock: %s", lock.path)

        try:
            with open(relay_log_file, 'a') as fout:
                for line in fileinput.input(relay_log_file_tmp):
                    fout.write(line)
            logging.debug("[Log Backup] Appended data to %s", relay_log_file)
        except:
            logging.warning("[Log Backup] Unable to append data to %s", relay_log_file)

        open(relay_log_file_tmp, 'w').close()
        logging.debug("[Log Backup] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Log Backup] Relay logs the same, skipping.")

    # Daemon Logs
    if not filecmp.cmp(daemon_log_file_tmp, daemon_log_file):
        logging.debug("[Log Backup] Concatenating daemon logs to %s", daemon_log_file)
        lock = LockFile(daemon_log_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Log Backup] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Log Backup] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Log Backup] Gained lock: %s", lock.path)

        try:
            with open(daemon_log_file, 'a') as fout:
                for line in fileinput.input(daemon_log_file_tmp):
                    fout.write(line)
            logging.debug("[Log Backup] Appended daemon log data to %s", daemon_log_file)
        except:
            logging.warning("[Log Backup] Unable to append data to %s", daemon_log_file)

        open(daemon_log_file_tmp, 'w').close()
        logging.debug("[Log Backup] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Log Backup] Daemon logs the same, skipping.")

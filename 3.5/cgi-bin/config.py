#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo-client.py - Client for mycodo.py. Communicates with daemonized
#                     mycodo.py to execute commands and receive status.
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

import os

INSTALL_DIRECTORY = "/var/www/mycodo"
LOCK_DIRECTORY = "/var/lock/mycodo"



LOG_PATH = os.path.join(INSTALL_DIRECTORY, "log") # Where generated logs are stored
IMAGE_PATH = os.path.join(INSTALL_DIRECTORY, "images") # Where generated graphs are stored

# Logs that are on the tempfs and are written to every sensor read
SENSOR_T_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-t-tmp.log")
SENSOR_HT_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-ht-tmp.log")
SENSOR_CO2_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-co2-tmp.log")
SENSOR_PRESS_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-press-tmp.log")
RELAY_LOG_FILE_TMP = os.path.join(LOG_PATH, "relay-tmp.log")

# Logs that are periodically concatenated (every 6 hours) to the SD card
SENSOR_T_LOG_FILE = os.path.join(LOG_PATH, "sensor-t.log")
SENSOR_HT_LOG_FILE = os.path.join(LOG_PATH, "sensor-ht.log")
SENSOR_CO2_LOG_FILE = os.path.join(LOG_PATH, "sensor-co2.log")
SENSOR_PRESS_LOG_FILE = os.path.join(LOG_PATH, "sensor-press.log")
RELAY_LOG_FILE = os.path.join(LOG_PATH, "relay.log")

# Lockfiles
RELAY_LOG_LOCK_PATH = os.path.join(LOCK_DIRECTORY, "relay")
SENSOR_T_LOG_LOCK_PATH = os.path.join(LOCK_DIRECTORY, "sensor-t-log")
SENSOR_HT_LOG_LOCK_PATH = os.path.join(LOCK_DIRECTORY, "sensor-ht-log")
SENSOR_CO2_LOG_LOCK_PATH = os.path.join(LOCK_DIRECTORY, "sensor-co2-log")
SENSOR_PRESS_LOG_LOCK_PATH = os.path.join(LOCK_DIRECTORY, "sensor-press-log")
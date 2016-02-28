#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  GPIO-initialize.py - Initialize GPIO pins connected to relays and
#                       sets them off.
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
import RPi.GPIO as GPIO
import sqlite3

install_directory = os.path.dirname(os.path.abspath(__file__)) + "/.."

sql_database = "%s/config/mycodo.db" % install_directory

# GPIO pins (BCM numbering) and name of devices attached to relay
relay_id = []
relay_pin = []
relay_trigger = []
relay_start_state = []

def readsql():
    global relay_pin
    global relay_trigger
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('SELECT Id, Pin, Trigger, Start_State FROM Relays')
    count = 0
    for row in cur:
        relay_id.append(row[0])
        relay_pin.append(row[1])
        relay_trigger.append(row[2])
        relay_start_state.append(row[3])
        count += 1
    cur.close()

readsql()

# Turn all relays off
# Set all relays to be turned off at startup
for i, each_trigger in enumerate(relay_trigger):
    if each_trigger == 0:
        relay_trigger[i] = 1;
    else:
        relay_trigger[i] = 0

# Turn specific relays on
# If relay is set to be turned on, reverse the trigger
for i, each_trigger in enumerate(relay_trigger):
    if relay_start_state[i]:
        if each_trigger == 0:
            relay_trigger[i] = 1;
        else:
            relay_trigger[i] = 0

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for i, each_pin in enumerate(relay_pin):
    if each_pin != 0:
        GPIO.setup(each_pin, GPIO.OUT)
        GPIO.output(each_pin, relay_trigger[i])

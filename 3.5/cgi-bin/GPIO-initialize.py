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

import RPi.GPIO as GPIO
import sqlite3

#### Configure Install Directory ####
install_directory = "/var/www/mycodo"
#### Configure Install Directory ####

sql_database = '/var/www/mycodo/config/mycodo.db'

# GPIO pins (BCM numbering) and name of devices attached to relay
relay_pin = [0] * 9
relay_trigger = [0] * 9

def ReadSQL():
    global relay_pin
    global relay_trigger
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('SELECT Id, Pin, Trigger, Start_State FROM Relays')
    for row in cur :
        relay_pin[row[0]] = row[1]
        relay_trigger[row[0]] = row[2]
        relay_start_state[row[0]] = row[3]

ReadSQL()

# Turn all relays off
# Set all relays to be turned off at startup
for i in range(1, 9):
    if relay_trigger[i] == 0: relay_trigger[i] = 1;
    else: relay_trigger[i] = 0

# Turn specific relays on
# If relay is set to be turned on, reverse the trigger
for i in range(1, 9):
    if relay_start_state[i]:
        if relay_trigger[i] == 0: relay_trigger[i] = 1;
        else: relay_trigger[i] = 0

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for i in range(1, 9):
    if relay_pin[i] != 0:
        GPIO.setup(relay_pin[i], GPIO.OUT)
        GPIO.output(relay_pin[i], relay_trigger[i])
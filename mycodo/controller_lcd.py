#!/usr/bin/python
# coding=utf-8
#
# controller_lcd.py - Mycodo LCD controller that outputs measurements and other
#                     information to I2C-interfaced LCDs
#
#  Copyright (C) 2016  Kyle T. Gabriel
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
#
#  LCD Code used in part from:
#
# Copyright (c) 2010 cnr437@gmail.com
#
# Licensed under the MIT License <http://opensource.org/licenses/MIT>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# <http://code.activestate.com/recipes/577231-discrete-lcd-controller/>

import calendar
import smbus
import threading
import time
import timeit
import RPi.GPIO as GPIO
import datetime

from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import SQL_DATABASE_MYCODO
from databases.mycodo_db.models import LCD
from databases.mycodo_db.models import PID
from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import Sensor
from databases.utils import session_scope
from devices.tca9548a import TCA9548A
from utils.influx import read_last_influxdb

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class LCDController(threading.Thread):
    """
    Class to operate LCD controller

    """

    def __init__(self, ready, logger, lcd_id):
        threading.Thread.__init__(self)

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.logger = logger
        self.flash_lcd_on = False
        self.lcd_is_on = False

        try:
            with session_scope(MYCODO_DB_PATH) as new_session:
                lcd = new_session.query(LCD).filter(LCD.id == lcd_id).first()
                self.lcd_id = lcd_id
                self.lcd_name = lcd.name
                self.lcd_pin = lcd.pin
                self.lcd_period = lcd.period
                self.lcd_x_characters = lcd.x_characters
                self.lcd_y_lines = lcd.y_lines

                if lcd.multiplexer_address:
                    self.multiplexer_address_string = lcd.multiplexer_address
                    self.multiplexer_address = int(str(lcd.multiplexer_address), 16)
                    self.multiplexer_channel = lcd.multiplexer_channel
                    self.multiplexer = TCA9548A(self.multiplexer_address)
                else:
                    self.multiplexer = None

                self.lcd_line = {}
                for i in range(1, 5):
                    self.lcd_line[i] = {}

                list_sensors = ['sensor_time', 'temperature',
                                'humidity', 'co2', 'pressure',
                                'altitude', 'temperature_die',
                                'temperature_object', 'lux']

                list_PIDs = ['setpoint', 'pid_time']

                list_relays = ['duration_sec', 'relay_time', 'relay_state']

                if self.lcd_y_lines == 2:
                    self.lcd_line[1]['id'] = lcd.line_1_sensor_id
                    self.lcd_line[1]['measurement'] = lcd.line_1_measurement
                    if lcd.line_1_sensor_id:
                        if lcd.line_1_measurement in list_sensors:
                            table = Sensor
                        elif lcd.line_1_measurement in list_PIDs:
                            table = PID
                        elif lcd.line_1_measurement in list_relays:
                            table = Relay
                        sensor_line_1 = new_session.query(table).filter(
                            table.id == lcd.line_1_sensor_id).first()
                        self.lcd_line[1]['name'] = sensor_line_1.name
                        if 'time' in lcd.line_1_measurement:
                            self.lcd_line[1]['measurement'] = 'time'

                    self.lcd_line[2]['id'] = lcd.line_2_sensor_id
                    self.lcd_line[2]['measurement'] = lcd.line_2_measurement
                    if lcd.line_2_sensor_id:
                        if lcd.line_2_measurement in list_sensors:
                            table = Sensor
                        elif lcd.line_2_measurement in list_PIDs:
                            table = PID
                        elif lcd.line_2_measurement in list_relays:
                            table = Relay
                        sensor_line_2 = new_session.query(table).filter(
                            table.id == lcd.line_2_sensor_id).first()
                        self.lcd_line[2]['name'] = sensor_line_2.name
                        if 'time' in lcd.line_2_measurement:
                            self.lcd_line[2]['measurement'] = 'time'

                elif self.lcd_y_lines == 4:
                    self.lcd_line[3]['id'] = lcd.line_3_sensor_id
                    self.lcd_line[3]['measurement'] = lcd.line_3_measurement
                    if lcd.line_3_sensor_id:
                        if lcd.line_3_measurement in list_sensors:
                            table = Sensor
                        elif lcd.line_3_measurement in list_PIDs:
                            table = PID
                        elif lcd.line_3_measurement in list_relays:
                            table = Relay
                        sensor_line_3 = new_session.query(table).filter(
                            table.id == lcd.line_3_sensor_id).first()
                        self.lcd_line[3]['name'] = sensor_line_3.name
                        if 'time' in lcd.line_3_measurement:
                            self.lcd_line[3]['measurement'] = 'time'

                    self.lcd_line[4]['id'] = lcd.line_4_sensor_id
                    self.lcd_line[4]['measurement'] = lcd.line_4_measurement
                    if lcd.line_4_sensor_id:
                        if lcd.line_4_measurement in list_sensors:
                            table = Sensor
                        elif lcd.line_4_measurement in list_PIDs:
                            table = PID
                        elif lcd.line_4_measurement in list_relays:
                            table = Relay
                        sensor_line_4 = new_session.query(table).filter(
                            table.id == lcd.line_4_sensor_id).first()
                        self.lcd_line[4]['name'] = sensor_line_4.name
                        if 'time' in lcd.line_4_measurement:
                            self.lcd_line[4]['measurement'] = 'time'

            self.measurement_unit = {}
            self.measurement_unit['metric'] = {
                "temperature": "C",
                "humidity": "%",
                "co2": "ppmv",
                "pressure": "Pa",
                "altitude": "m",
                "duration_sec": "s",
                "temperature_die": "C",
                "temperature_object": "C",
                "lux": "lux", 
            }
            self.measurement_unit['standard'] = {
                "temperature": "F",
                "humidity": "%",
                "co2": "ppmv",
                "pressure": "atm",
                "altitude": "ft",
                "duration_sec": "s",
                "temperature_die": "F",
                "temperature_object": "F",
                "lux": "lux", 
            }

            self.timer = time.time() + self.lcd_period
            self.backlight_timer = time.time()

            self.lcd_string_line = {}
            for i in range(1, self.lcd_y_lines+1):
                self.lcd_string_line[i] = ''

            self.LCD_WIDTH = self.lcd_x_characters # Maximum characters per line

            self.LCD_LINE = {}
            self.LCD_LINE[1] = 0x80 # LCD RAM address for the 1st line
            self.LCD_LINE[2] = 0xC0 # LCD RAM address for the 2nd line
            self.LCD_LINE[3] = 0x94 # LCD RAM address for the 3rd line
            self.LCD_LINE[4] = 0xD4 # LCD RAM address for the 4th line

            self.LCD_CHR = 1 # Mode - Sending data
            self.LCD_CMD = 0 # Mode - SenLCDding command

            self.LCD_BACKLIGHT = 0x08  # On
            self.LCD_BACKLIGHT_OFF = 0x00  # Off

            self.ENABLE = 0b00000100 # Enable bit

            # Timing constants
            self.E_PULSE = 0.0005
            self.E_DELAY = 0.0005

            # Setup I2C bus
            try:
                if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
                    I2C_bus_number = 1
                else:
                    I2C_bus_number = 0
                self.bus = smbus.SMBus(I2C_bus_number)
            except Exception as except_msg:
                self.logger.exception("Could not initialize I2C bus: {}".format(
                    except_msg))

            self.I2C_ADDR = int(self.lcd_pin, 16)
            self.lcd_init()
            self.lcd_string_write('Mycodo 3.6.0', self.LCD_LINE[1]) 
            self.lcd_string_write('Start {}'.format(
                self.lcd_name), self.LCD_LINE[2])
        except Exception as except_msg:
            self.logger.exception("[LCD {}] Error: {}".format(
                self.lcd_id, except_msg))


    def run(self):
        try:
            self.running = True
            self.logger.info("[LCD {}] Activated in {:.1f} ms".format(
                self.lcd_id,
                (timeit.default_timer()-self.thread_startup_timer)*1000))
            self.ready.set()

            while (self.running):
                if time.time() > self.timer:
                    self.get_lcd_strings()
                    self.output_lcds()
                    self.timer = time.time() + self.lcd_period

                if self.flash_lcd_on:
                    if time.time() > self.backlight_timer:
                        if self.lcd_is_on:
                            self.lcd_backlight(0)
                            seconds = 0.2
                        else:
                            self.output_lcds()
                            seconds = 1.1
                        self.backlight_timer = time.time()+seconds

                time.sleep(1)

            self.lcd_init()  # Blank LCD
            self.lcd_string_write('Mycodo Shut Down', self.LCD_LINE[1]) 
            self.lcd_string_write('{}'.format(self.lcd_name), self.LCD_LINE[2]) 

            self.running = False
            self.logger.info("[LCD {}] Deactivated in {:.1f} ms".format(
                self.lcd_id,
                (timeit.default_timer()-self.thread_shutdown_timer)*1000))
        except Exception as except_msg:
            self.logger.exception("[LCD {}] Exception: {}".format(
                self.lcd_id, except_msg))


    def get_lcd_strings(self):
        """
        Retrieve measurements and/or timestamps and create strings for LCDs
        If no data is retrieveable, create string "NO DATA RETURNED".
        """
        # loop to acquire all measurements required to be displayed on the LCD
        for i in range(1, self.lcd_y_lines+1):
            if self.lcd_line[i]['id']:
                # Get latest measurement (from within the past minute) from influxdb
                # FROM '/.*/' returns any measurement (for grabbing time of last measurement)
                last_measurement_success = False
                try:
                    if self.lcd_line[i]['measurement'] == 'relay_state':
                        self.lcd_line[i]['measurement_value'] = self.relay_state(self.lcd_line[i]['id'])
                        last_measurement_success = True
                    else:
                        if self.lcd_line[i]['measurement'] == 'time':
                            last_measurement = read_last_influxdb(
                                INFLUXDB_HOST,
                                INFLUXDB_PORT,
                                INFLUXDB_USER,
                                INFLUXDB_PASSWORD,
                                INFLUXDB_DATABASE,
                                self.lcd_line[i]['id'],
                                '/.*/').raw
                        else:
                            last_measurement = read_last_influxdb(
                                INFLUXDB_HOST,
                                INFLUXDB_PORT,
                                INFLUXDB_USER,
                                INFLUXDB_PASSWORD,
                                INFLUXDB_DATABASE,
                                self.lcd_line[i]['id'],
                                self.lcd_line[i]['measurement']).raw
                        if last_measurement:
                            number = len(last_measurement['series'][0]['values'])
                            self.lcd_line[i]['time'] = last_measurement['series'][0]['values'][number-1][0]
                            self.lcd_line[i]['measurement_value'] = last_measurement['series'][0]['values'][number-1][1]
                            utc_dt = datetime.datetime.strptime(self.lcd_line[i]['time'].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                            utc_timestamp = calendar.timegm(utc_dt.timetuple())
                            local_timestamp = str(datetime.datetime.fromtimestamp(utc_timestamp))
                            self.logger.debug("[LCD {}] Latest {}: {} @ {}".format(
                                self.lcd_id, self.lcd_line[i]['measurement'],
                                self.lcd_line[i]['measurement_value'], local_timestamp))
                            last_measurement_success = True
                        else:
                            self.lcd_line[i]['time'] = None
                            self.lcd_line[i]['measurement_value'] = None
                            self.logger.debug("[LCD {}] No data returned "
                                "from influxdb".format(self.lcd_id))
                except Exception as except_msg:
                    self.logger.debug("[LCD {}] Failed to read "
                        "measurement from the influxdb database: "
                        "{}".format(self.lcd_id, except_msg))

                try:
                    if last_measurement_success:
                        # Determine if the LCD output will have a value unit
                        measurement = ''
                        if self.lcd_line[i]['measurement'] == 'setpoint':
                            with session_scope(MYCODO_DB_PATH) as new_session:
                                pid = new_session.query(PID).filter(
                                    PID.id == self.lcd_line[i]['id']).first()
                                new_session.expunge_all()
                                new_session.close()
                                measurement = pid.measure_type
                        elif self.lcd_line[i]['measurement'] in ['temperature',
                                                                 'temperature_die',
                                                                 'temperature_object',
                                                                 'humidity',
                                                                 'co2',
                                                                 'lux',
                                                                 'pressure',
                                                                 'altitude']:
                            measurement = self.lcd_line[i]['measurement']
                        elif self.lcd_line[i]['measurement'] == 'duration_sec':
                            measurement = 'duration_sec'
                        
                        # Produce the line that will be displayed on the LCD
                        number_characters = self.lcd_x_characters
                        if self.lcd_line[i]['measurement'] == 'time':
                            # Convert UTC timestamp to local timezone
                            utc_dt = datetime.datetime.strptime(self.lcd_line[i]['time'].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                            utc_timestamp = calendar.timegm(utc_dt.timetuple())
                            self.lcd_string_line[i] = str(datetime.datetime.fromtimestamp(utc_timestamp))
                        elif measurement:
                            value_length = len(str(self.lcd_line[i]['measurement_value']))
                            unit_length = len(self.measurement_unit['metric'][measurement])
                            name_length = number_characters - value_length - unit_length - 2
                            name_cropped = self.lcd_line[i]['name'].ljust(name_length)[:name_length]
                            self.lcd_string_line[i] = '{} {} {}'.format(
                                name_cropped,
                                self.lcd_line[i]['measurement_value'],
                                self.measurement_unit['metric'][measurement])
                        else:
                            value_length = len(str(self.lcd_line[i]['measurement_value']))
                            name_length = number_characters - value_length - 1
                            name_cropped = self.lcd_line[i]['name'][:name_length]
                            self.lcd_string_line[i] = '{} {}'.format(
                                name_cropped,
                                self.lcd_line[i]['measurement_value'])
                    else:
                        self.lcd_string_line[i] = 'NO DATA < 5 MIN'
                except Exception as except_msg:
                    self.logger.exception("[LCD {}] Error ({}): {}".format(
                        self.lcd_id, except_msg))
            else:
                self.lcd_string_line[i] = ''


    def relay_state(self, relay_id):
        with session_scope(MYCODO_DB_PATH) as new_session:
            relay = new_session.query(Relay).filter(Relay.id == relay_id).first()
            gpio_state = ''
            GPIO.setmode(GPIO.BCM)
            if GPIO.input(relay.pin) == relay.trigger:
                gpio_state = 'On'
            else:
                gpio_state = 'Off'
        return gpio_state


    def output_lcds(self):
        """Output to all LCDs all at once"""
        if self.multiplexer:
            self.logger.debug("[LCD {}] Setting multiplexer at "
                              "address {} to channel "
                              "{}".format(self.lcd_id,
                                          self.multiplexer_address_string,
                                          self.multiplexer_channel))
            self.multiplexer_status, self.multiplexer_response = self.multiplexer.setup_lock(self.logger, self.multiplexer_channel)
            if not self.multiplexer_status:
                self.logger.warning("[LCD {}] Could not set channel "
                                    "with multiplexer at address {}. "
                                    "Error: {}".format(self.lcd_id,
                                                       self.multiplexer_address_string,
                                                       self.multiplexer_response))
        self.lcd_init()
        for i in range(1, self.lcd_y_lines+1):
            self.lcd_string_write(self.lcd_string_line[i], self.LCD_LINE[i])


    def flash_lcd(self, state):
        """Enable the LCD to begin or end flashing"""
        if state:
            self.flash_lcd_on = True
            return 1, "LCD {} flashing turned on".format(self.lcd_id)
        else:
            self.flash_lcd_on = False
            time.sleep(0.1)
            self.output_lcds()
            return 1, "LCD {} flashing turned off".format(self.lcd_id)


    def lcd_backlight(self, state):
        """Turn the backlight on or off"""
        if state == 1:
            self.lcd_is_on = True
            self.lcd_byte(0x01, self.LCD_CMD, self.LCD_BACKLIGHT)
        elif state == 0:
            self.lcd_is_on = False
            self.lcd_byte(0x01, self.LCD_CMD, self.LCD_BACKLIGHT_OFF)


    def lcd_init(self):
        """Initialize LCD display"""
        self.lcd_byte(0x33, self.LCD_CMD) # 110011 Initialise
        self.lcd_byte(0x32, self.LCD_CMD) # 110010 Initialise
        self.lcd_byte(0x06, self.LCD_CMD) # 000110 Cursor move direction
        self.lcd_byte(0x0C, self.LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
        self.lcd_byte(0x28, self.LCD_CMD) # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01, self.LCD_CMD) # 000001 Clear display
        time.sleep(self.E_DELAY)
        self.lcd_is_on = True


    def lcd_byte(self, bits, mode, backlight=None):
        """Send byte to data pins"""
        if backlight is None:
            backlight = self.LCD_BACKLIGHT
        # bits = the data
        # mode = 1 for data
        #        0 for command
        bits_high = mode | (bits & 0xF0) | backlight
        bits_low = mode | ((bits<<4) & 0xF0) | backlight
        # High bits
        self.bus.write_byte(self.I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)
        # Low bits
        self.bus.write_byte(self.I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)


    def lcd_toggle_enable(self, bits):
        """Toggle enable"""
        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.I2C_ADDR, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.I2C_ADDR,(bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)


    def lcd_string_write(self, message, line):
        """Send string to display"""
        message = message.ljust(self.LCD_WIDTH," ")
        self.lcd_byte(line, self.LCD_CMD)
        for i in range(self.LCD_WIDTH):
          self.lcd_byte(ord(message[i]),self.LCD_CHR)


    def isRunning(self):
        return self.running


    def stopController(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

# coding=utf-8
#
# controller_lcd.py - Mycodo LCD controller that outputs measurements and other
#                     information to I2C-interfaced LCDs
#
#  Copyright (C) 2017  Kyle T. Gabriel
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
import logging
import smbus
import sqlalchemy
import threading
import time
import timeit
import RPi.GPIO as GPIO
import datetime

from databases.models import Input
from databases.models import LCD
from databases.models import LCDData
from databases.models import Math
from databases.models import Output
from databases.models import PID
from devices.tca9548a import TCA9548A
from utils.database import db_retrieve_table_daemon
from utils.influx import read_last_influxdb
from utils.system_pi import add_custom_measurements

from config import MEASUREMENT_UNITS
from config import MYCODO_VERSION


class LCDController(threading.Thread):
    """
    Class to operate LCD controller

    """
    def __init__(self, ready, lcd_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.lcd_{id}".format(id=lcd_id))

        self.running = False
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.flash_lcd_on = False
        self.lcd_initilized = False
        self.lcd_is_on = False
        self.lcd_id = lcd_id
        self.display_ids = []
        self.display_count = 0

        try:
            lcd = db_retrieve_table_daemon(LCD, device_id=self.lcd_id)
            self.lcd_name = lcd.name
            self.lcd_location = lcd.location
            self.lcd_i2c_bus = lcd.i2c_bus
            self.lcd_period = lcd.period
            self.lcd_x_characters = lcd.x_characters
            self.lcd_y_lines = lcd.y_lines
            self.timer = time.time() + self.lcd_period
            self.backlight_timer = time.time()

            if lcd.multiplexer_address:
                self.multiplexer_address_string = lcd.multiplexer_address
                self.multiplexer_address = int(str(lcd.multiplexer_address),
                                               16)
                self.multiplexer_channel = lcd.multiplexer_channel
                self.multiplexer = TCA9548A(self.multiplexer_address)
            else:
                self.multiplexer = None

            self.list_pids = ['setpoint', 'pid_time']
            self.list_outputs = ['duration_sec', 'relay_time', 'relay_state']

            self.list_inputs = MEASUREMENT_UNITS
            self.list_inputs.update(
                {'sensor_time': {'unit': None, 'name': 'Time'}})

            # Add custom measurement and units to list (From linux command input)
            input_dev = db_retrieve_table_daemon(Input)
            self.list_inputs = add_custom_measurements(
                input_dev, self.list_inputs, MEASUREMENT_UNITS)

            lcd_data = db_retrieve_table_daemon(
                LCDData).filter(LCDData.lcd_id == lcd.id).all()

            self.lcd_string_line = {}
            self.lcd_line = {}
            self.lcd_max_age = {}
            self.lcd_decimal_places = {}

            for each_lcd_display in lcd_data:
                self.display_ids.append(each_lcd_display.id)
                self.lcd_string_line[each_lcd_display.id] = {}
                self.lcd_line[each_lcd_display.id] = {}
                self.lcd_max_age[each_lcd_display.id] = {}
                self.lcd_decimal_places[each_lcd_display.id] = {}

                for i in range(1, self.lcd_y_lines + 1):
                    self.lcd_string_line[each_lcd_display.id][i] = ''
                    self.lcd_line[each_lcd_display.id][i] = {}
                    if i == 1:
                        self.lcd_max_age[each_lcd_display.id][i] = each_lcd_display.line_1_max_age
                        self.lcd_decimal_places[each_lcd_display.id][i] = each_lcd_display.line_1_decimal_places
                    elif i == 2:
                        self.lcd_max_age[each_lcd_display.id][i] = each_lcd_display.line_2_max_age
                        self.lcd_decimal_places[each_lcd_display.id][i] = each_lcd_display.line_2_decimal_places
                    elif i == 3:
                        self.lcd_max_age[each_lcd_display.id][i] = each_lcd_display.line_3_max_age
                        self.lcd_decimal_places[each_lcd_display.id][i] = each_lcd_display.line_3_decimal_places
                    elif i == 4:
                        self.lcd_max_age[each_lcd_display.id][i] = each_lcd_display.line_4_max_age
                        self.lcd_decimal_places[each_lcd_display.id][i] = each_lcd_display.line_4_decimal_places

                if self.lcd_y_lines in [2, 4]:
                    self.setup_lcd_line(
                        each_lcd_display.id, 1,
                        each_lcd_display.line_1_id,
                        each_lcd_display.line_1_measurement)
                    self.setup_lcd_line(
                        each_lcd_display.id, 2,
                        each_lcd_display.line_2_id,
                        each_lcd_display.line_2_measurement)

                if self.lcd_y_lines == 4:
                    self.setup_lcd_line(
                        each_lcd_display.id, 3,
                        each_lcd_display.line_3_id,
                        each_lcd_display.line_3_measurement)
                    self.setup_lcd_line(
                        each_lcd_display.id, 4,
                        each_lcd_display.line_4_id,
                        each_lcd_display.line_4_measurement)

            self.LCD_WIDTH = self.lcd_x_characters  # Max characters per line

            self.LCD_LINE = {
                1: 0x80,
                2: 0xC0,
                3: 0x94,
                4: 0xD4
            }

            self.LCD_CHR = 1  # Mode - Sending data
            self.LCD_CMD = 0  # Mode - SenLCDding command

            self.LCD_BACKLIGHT = 0x08  # On
            self.LCD_BACKLIGHT_OFF = 0x00  # Off

            self.ENABLE = 0b00000100  # Enable bit

            # Timing constants
            self.E_PULSE = 0.0005
            self.E_DELAY = 0.0005

            # Setup I2C bus
            try:
                self.bus = smbus.SMBus(self.lcd_i2c_bus)
            except Exception as except_msg:
                self.logger.exception(
                    "Could not initialize I2C bus: {err}".format(
                        err=except_msg))

            self.I2C_ADDR = int(self.lcd_location, 16)
            self.lcd_init()

            if self.lcd_initilized:
                self.lcd_string_write('Mycodo {}'.format(MYCODO_VERSION),
                                      self.LCD_LINE[1])
                self.lcd_string_write(u'Start {}'.format(
                    self.lcd_name), self.LCD_LINE[2])
        except Exception as except_msg:
            self.logger.exception("Error: {err}".format(err=except_msg))

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            while self.running:
                if time.time() > self.timer and self.lcd_initilized:
                    try:
                        # Acquire all measurements to be displayed on the LCD
                        display_id = self.display_ids[self.display_count]
                        for i in range(1, self.lcd_y_lines + 1):
                            if self.lcd_line[display_id][i]['id'] and self.lcd_line[display_id][i]['setup']:
                                self.create_lcd_line(
                                    self.get_measurement(display_id, i),
                                    display_id,
                                    i)
                            else:
                                self.lcd_string_line[display_id][i] = u'ID NOT FOUND'
                        # Output lines to the LCD
                        self.output_lcds()
                    except KeyError:
                        self.logger.error(
                            "KeyError: Unable to output to LCD.")
                    except IOError:
                        self.logger.error(
                            "IOError: Unable to output to LCD.")
                    except Exception:
                        self.logger.exception(
                            "Exception: Unable to output to LCD.")

                    # Increment display counter to show the next display
                    if len(self.display_ids) > 1:
                        if self.display_count < len(self.display_ids) - 1:
                            self.display_count += 1
                        else:
                            self.display_count = 0

                    self.timer = time.time() + self.lcd_period

                if self.flash_lcd_on:
                    if time.time() > self.backlight_timer:
                        if self.lcd_is_on:
                            self.lcd_backlight(0)
                            seconds = 0.2
                        else:
                            self.output_lcds()
                            seconds = 1.1
                        self.backlight_timer = time.time() + seconds

                time.sleep(1)
        except Exception as except_msg:
            self.logger.exception("Exception: {err}".format(err=except_msg))
        finally:
            self.lcd_init()  # Blank LCD
            self.lcd_string_write('Mycodo {}'.format(MYCODO_VERSION),
                                  self.LCD_LINE[1])
            self.lcd_string_write(u'Stop {}'.format(self.lcd_name),
                                  self.LCD_LINE[2])
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
            self.running = False

    def get_measurement(self, display_id, i):
        try:
            if self.lcd_line[display_id][i]['measure'] == 'relay_state':
                self.lcd_line[display_id][i]['measure_val'] = self.output_state(
                    self.lcd_line[display_id][i]['id'])
                return True
            else:
                if self.lcd_line[display_id][i]['measure'] == 'time':
                    last_measurement = read_last_influxdb(
                        self.lcd_line[display_id][i]['id'],
                        '/.*/',
                        duration_sec=self.lcd_max_age[display_id][i])
                else:
                    last_measurement = read_last_influxdb(
                        self.lcd_line[display_id][i]['id'],
                        self.lcd_line[display_id][i]['measure'],
                        duration_sec=self.lcd_max_age[display_id][i])
                if last_measurement:
                    self.lcd_line[display_id][i]['time'] = last_measurement[0]
                    if self.lcd_decimal_places[display_id][i] == 0:
                        self.lcd_line[display_id][i]['measure_val'] = int(last_measurement[1])
                    else:
                        self.lcd_line[display_id][i]['measure_val'] = round(
                            last_measurement[1], self.lcd_decimal_places[display_id][i])
                    utc_dt = datetime.datetime.strptime(
                        self.lcd_line[display_id][i]['time'].split(".")[0],
                        '%Y-%m-%dT%H:%M:%S')
                    utc_timestamp = calendar.timegm(utc_dt.timetuple())
                    local_timestamp = str(datetime.datetime.fromtimestamp(utc_timestamp))
                    self.logger.debug("Latest {}: {} @ {}".format(
                        self.lcd_line[display_id][i]['measure'],
                        self.lcd_line[display_id][i]['measure_val'], local_timestamp))
                    return True
                else:
                    self.lcd_line[display_id][i]['time'] = None
                    self.lcd_line[display_id][i]['measure_val'] = None
                    self.logger.debug("No data returned from influxdb")
            return False
        except Exception as except_msg:
            self.logger.debug(
                "Failed to read measurement from the influxdb database: "
                "{err}".format(err=except_msg))
            return False

    def create_lcd_line(self, last_measurement_success, display_id, i):
        try:
            if last_measurement_success:
                # Determine if the LCD output will have a value unit
                measurement = ''
                if self.lcd_line[display_id][i]['measure'] == 'setpoint':
                    pid = db_retrieve_table_daemon(
                        PID, unique_id=self.lcd_line[display_id][i]['id'])
                    measurement = pid.measurement.split(',')[1]
                    self.lcd_line[display_id][i]['measure_val'] = '{:.2f}'.format(
                        self.lcd_line[display_id][i]['measure_val'])
                elif self.lcd_line[display_id][i]['measure'] == 'duration_sec':
                    measurement = 'duration_sec'
                    self.lcd_line[display_id][i]['measure_val'] = '{:.2f}'.format(
                        self.lcd_line[display_id][i]['measure_val'])
                elif self.lcd_line[display_id][i]['measure'] in self.list_inputs:
                    measurement = self.lcd_line[display_id][i]['measure']

                # Produce the line that will be displayed on the LCD
                if self.lcd_line[display_id][i]['measure'] == 'time':
                    # Convert UTC timestamp to local timezone
                    utc_dt = datetime.datetime.strptime(
                        self.lcd_line[display_id][i]['time'].split(".")[0],
                        '%Y-%m-%dT%H:%M:%S')
                    utc_timestamp = calendar.timegm(utc_dt.timetuple())
                    self.lcd_string_line[display_id][i] = str(
                        datetime.datetime.fromtimestamp(utc_timestamp))
                elif measurement:
                    value_length = len(str(
                        self.lcd_line[display_id][i]['measure_val']))
                    unit_length = len(self.lcd_line[display_id][i]['unit'].replace(u'°', u''))
                    name_length = self.lcd_x_characters - value_length - unit_length - 2
                    name_cropped = self.lcd_line[display_id][i]['name'].ljust(name_length)[:name_length]
                    self.lcd_string_line[display_id][i] = u'{name} {value} {unit}'.format(
                        name=name_cropped,
                        value=self.lcd_line[display_id][i]['measure_val'],
                        unit=self.lcd_line[display_id][i]['unit'].replace(u'°', u''))
                else:
                    value_length = len(str(
                        self.lcd_line[display_id][i]['measure_val']))
                    name_length = self.lcd_x_characters - value_length - 1
                    name_cropped = self.lcd_line[display_id][i]['name'][:name_length]
                    self.lcd_string_line[display_id][i] = u'{name} {value}'.format(
                        name=name_cropped,
                        value=self.lcd_line[display_id][i]['measure_val'])
            else:
                error = u'NO DATA'
                name_length = self.lcd_x_characters - len(error) - 1
                name_cropped = self.lcd_line[display_id][i]['name'].ljust(name_length)[:name_length]
                self.lcd_string_line[display_id][i] = u'{name} {error}'.format(
                    name=name_cropped, error=error)

        except Exception as except_msg:
            self.logger.exception("Error: {err}".format(err=except_msg))

    def output_lcds(self):
        """ Output to all LCDs all at once """
        if self.multiplexer:
            mult_status, mult_response = self.multiplexer.setup_lock(
                self.logger, self.multiplexer_channel)
            if mult_status:
                self.logger.debug(
                    "Setting multiplexer at address {add} to channel "
                    "{chan}".format(
                        add=self.multiplexer_address_string,
                        chan=self.multiplexer_channel))
            else:
                self.logger.warning(
                    "Could not set channel with multiplexer at address {add}."
                    " Error: {err}".format(
                        add=self.multiplexer_address_string,
                        err=mult_response))
        self.lcd_init()
        display_id = self.display_ids[self.display_count]
        for i in range(1, self.lcd_y_lines + 1):
            self.lcd_string_write(self.lcd_string_line[display_id][i], self.LCD_LINE[i])

    @staticmethod
    def output_state(output_id):
        output = db_retrieve_table_daemon(Output, unique_id=output_id)
        GPIO.setmode(GPIO.BCM)
        if GPIO.input(output.pin) == output.trigger:
            gpio_state = 'On'
        else:
            gpio_state = 'Off'
        return gpio_state

    def setup_lcd_line(self, display_id, line, lcd_id, measurement):
        self.lcd_line[display_id][line]['setup'] = False
        self.lcd_line[display_id][line]['id'] = lcd_id
        self.lcd_line[display_id][line]['name'] = None
        self.lcd_line[display_id][line]['unit'] = None
        self.lcd_line[display_id][line]['measure'] = measurement
        if not lcd_id:
            return

        table = None

        # Find what controller the unique_id of the line belongs to,
        # then determine the unit
        if (db_retrieve_table_daemon(Output, unique_id=lcd_id) and
                measurement in self.list_outputs):
            self.lcd_line[display_id][line]['unit'] = self.list_inputs[measurement]['unit']
            table = Output
        elif (db_retrieve_table_daemon(PID, unique_id=lcd_id) and
                measurement in self.list_pids):
            self.lcd_line[display_id][line]['unit'] = self.list_inputs[measurement]['unit']
            table = PID
        elif (db_retrieve_table_daemon(Input, unique_id=lcd_id) and
                measurement in self.list_inputs):
            self.lcd_line[display_id][line]['unit'] = self.list_inputs[measurement]['unit']
            table = Input
        elif db_retrieve_table_daemon(Math, unique_id=lcd_id):
            if measurement in self.list_inputs:
                self.lcd_line[display_id][line]['unit'] = self.list_inputs[measurement]['unit']
            else:
                self.lcd_line[display_id][line]['unit'] = db_retrieve_table_daemon(
                    Math, unique_id=lcd_id).measure_units
            table = Math
        else:
            self.logger.error("Line {line}: Unique ID not found in any controller".format(line=line))

        try:
            dev_name = db_retrieve_table_daemon(
                table, unique_id=lcd_id)
        except sqlalchemy.exc.InvalidRequestError:
            self.logger.error("Line {line}: Invalid table".format(line=line))
            return

        self.lcd_line[display_id][line]['name'] = dev_name.name
        if 'time' in measurement:
            self.lcd_line[display_id][line]['measure'] = 'time'

        self.lcd_line[display_id][line]['setup'] = True

    def flash_lcd(self, state):
        """ Enable the LCD to begin or end flashing """
        if state:
            self.flash_lcd_on = True
            return 1, "LCD {} flashing turned on".format(self.lcd_id)
        else:
            self.flash_lcd_on = False
            time.sleep(0.1)
            self.output_lcds()
            return 1, "LCD {} flashing turned off".format(self.lcd_id)

    def lcd_backlight(self, state):
        """ Turn the backlight on or off """
        if state == 1:
            self.lcd_is_on = True
            self.lcd_byte(0x01, self.LCD_CMD, self.LCD_BACKLIGHT)
        elif state == 0:
            self.lcd_is_on = False
            self.lcd_byte(0x01, self.LCD_CMD, self.LCD_BACKLIGHT_OFF)

    def lcd_init(self):
        """ Initialize LCD display """
        try:
            self.lcd_byte(0x33, self.LCD_CMD)  # 110011 Initialise
            self.lcd_byte(0x32, self.LCD_CMD)  # 110010 Initialise
            self.lcd_byte(0x06, self.LCD_CMD)  # 000110 Cursor move direction
            self.lcd_byte(0x0C, self.LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
            self.lcd_byte(0x28, self.LCD_CMD)  # 101000 Data length, number of lines, font size
            self.lcd_byte(0x01, self.LCD_CMD)  # 000001 Clear display
            time.sleep(self.E_DELAY)
            self.lcd_initilized = True
            self.lcd_is_on = True
        except Exception as err:
            self.logger.error(
                "Count not initialize LCD. Error: {err}".format(err=err))

    def lcd_byte(self, bits, mode, backlight=None):
        """ Send byte to data pins """
        if backlight is None:
            backlight = self.LCD_BACKLIGHT
        # bits = the data
        # mode = 1 for data
        #        0 for command
        bits_high = mode | (bits & 0xF0) | backlight
        bits_low = mode | ((bits << 4) & 0xF0) | backlight
        # High bits
        self.bus.write_byte(self.I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)
        # Low bits
        self.bus.write_byte(self.I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)

    def lcd_toggle_enable(self, bits):
        """ Toggle enable """
        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.I2C_ADDR, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.I2C_ADDR, (bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)

    def lcd_string_write(self, message, line):
        """ Send string to display """
        message = message.ljust(self.LCD_WIDTH, " ")
        self.lcd_byte(line, self.LCD_CMD)
        for i in range(self.LCD_WIDTH):
            self.lcd_byte(ord(message[i]), self.LCD_CHR)

    def is_running(self):
        """ returns if the controller is running """
        return self.running

    def stop_controller(self):
        """ Stops the controller """
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

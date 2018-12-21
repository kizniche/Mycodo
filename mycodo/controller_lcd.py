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
import datetime
import logging
import threading
import time
import timeit

import RPi.GPIO as GPIO

from mycodo.config import MYCODO_VERSION
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import LCDData
from mycodo.databases.models import Math
from mycodo.databases.models import Measurement
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import return_measurement_info


class LCDController(threading.Thread):
    """
    Class to operate LCD controller

    """
    def __init__(self, ready, lcd_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.lcd_{id}".format(id=lcd_id.split('-')[0]))

        self.running = False
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.flash_lcd_on = False
        self.lcd_initialized = False
        self.lcd_is_on = False
        self.lcd_id = lcd_id
        self.display_sets = []
        self.display_set_count = 0

        try:
            lcd_dev = db_retrieve_table_daemon(LCD, unique_id=self.lcd_id)
            self.lcd_type = lcd_dev.lcd_type
            self.lcd_name = lcd_dev.name
            self.lcd_i2c_address = int(lcd_dev.location, 16)
            self.lcd_i2c_bus = lcd_dev.i2c_bus
            self.lcd_period = lcd_dev.period
            self.lcd_x_characters = lcd_dev.x_characters
            self.lcd_y_lines = lcd_dev.y_lines
            self.timer = time.time() + self.lcd_period
            self.backlight_timer = time.time()

            self.list_pids = ['setpoint', 'pid_time']
            self.list_outputs = ['duration_time', 'output_time', 'output_state']

            # Add custom measurement and units to list
            self.list_inputs = add_custom_measurements(
                db_retrieve_table_daemon(Measurement, entry='all'))

            self.list_inputs.update(
                {'input_time': {'unit': None, 'name': 'Time'}})
            self.list_inputs.update(
                {'pid_time': {'unit': None, 'name': 'Time'}})

            self.dict_units = add_custom_units(
                db_retrieve_table_daemon(Unit, entry='all'))

            lcd_data = db_retrieve_table_daemon(
                LCDData).filter(LCDData.lcd_id == lcd_dev.unique_id).all()

            self.lcd_string_line = {}
            self.lcd_line = {}
            self.lcd_max_age = {}
            self.lcd_decimal_places = {}

            for each_lcd_display in lcd_data:
                self.display_sets.append(each_lcd_display.unique_id)
                self.lcd_string_line[each_lcd_display.unique_id] = {}
                self.lcd_line[each_lcd_display.unique_id] = {}
                self.lcd_max_age[each_lcd_display.unique_id] = {}
                self.lcd_decimal_places[each_lcd_display.unique_id] = {}

                for i in range(1, self.lcd_y_lines + 1):
                    self.lcd_string_line[each_lcd_display.unique_id][i] = ''
                    self.lcd_line[each_lcd_display.unique_id][i] = {}
                    if i == 1:
                        self.lcd_max_age[each_lcd_display.unique_id][i] = each_lcd_display.line_1_max_age
                        self.lcd_decimal_places[each_lcd_display.unique_id][i] = each_lcd_display.line_1_decimal_places
                    elif i == 2:
                        self.lcd_max_age[each_lcd_display.unique_id][i] = each_lcd_display.line_2_max_age
                        self.lcd_decimal_places[each_lcd_display.unique_id][i] = each_lcd_display.line_2_decimal_places
                    elif i == 3:
                        self.lcd_max_age[each_lcd_display.unique_id][i] = each_lcd_display.line_3_max_age
                        self.lcd_decimal_places[each_lcd_display.unique_id][i] = each_lcd_display.line_3_decimal_places
                    elif i == 4:
                        self.lcd_max_age[each_lcd_display.unique_id][i] = each_lcd_display.line_4_max_age
                        self.lcd_decimal_places[each_lcd_display.unique_id][i] = each_lcd_display.line_4_decimal_places

                if self.lcd_y_lines in [2, 4]:
                    self.setup_lcd_line(
                        each_lcd_display.unique_id, 1,
                        each_lcd_display.line_1_id,
                        each_lcd_display.line_1_measurement)
                    self.setup_lcd_line(
                        each_lcd_display.unique_id, 2,
                        each_lcd_display.line_2_id,
                        each_lcd_display.line_2_measurement)

                if self.lcd_y_lines == 4:
                    self.setup_lcd_line(
                        each_lcd_display.unique_id, 3,
                        each_lcd_display.line_3_id,
                        each_lcd_display.line_3_measurement)
                    self.setup_lcd_line(
                        each_lcd_display.unique_id, 4,
                        each_lcd_display.line_4_id,
                        each_lcd_display.line_4_measurement)

            if self.lcd_type in ['16x2_generic',
                                 '16x4_generic']:
                from mycodo.devices.lcd_generic import LCD_Generic
                self.lcd_out = LCD_Generic(lcd_dev)
                self.lcd_init()
            elif self.lcd_type == '128x32_pioled':
                from mycodo.devices.lcd_pioled import LCD_Pioled
                self.lcd_out = LCD_Pioled(lcd_dev)
                self.lcd_init()
            else:
                self.logger.error("Unknown LCD type: {}".format(self.lcd_type))

            if self.lcd_initialized:
                line_1 = 'Mycodo {}'.format(MYCODO_VERSION)
                line_2 = 'Start {}'.format(self.lcd_name)
                self.lcd_out.lcd_write_lines(line_1, line_2, '', '')
        except Exception as except_msg:
            self.logger.exception("Error: {err}".format(err=except_msg))

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            while self.running:
                if not self.lcd_initialized:
                    self.stop_controller()
                elif (self.lcd_is_on and
                        self.lcd_initialized and
                        time.time() > self.timer):
                    try:
                        # Acquire all measurements to be displayed on the LCD
                        display_id = self.display_sets[self.display_set_count]
                        for line in range(1, self.lcd_y_lines + 1):
                            if not self.running:
                                break
                            if self.lcd_line[display_id][line]['id'] and self.lcd_line[display_id][line]['setup']:
                                self.create_lcd_line(
                                    self.get_measurement(display_id, line),
                                    display_id,
                                    line)
                            else:
                                self.lcd_string_line[display_id][line] = 'LCD LINE ERROR'
                        # Output lines to the LCD
                        if self.running:
                            self.output_lcds()
                    except KeyError:
                        self.logger.exception(
                            "KeyError: Unable to output to LCD.")
                    except IOError:
                        self.logger.exception(
                            "IOError: Unable to output to LCD.")
                    except Exception:
                        self.logger.exception(
                            "Exception: Unable to output to LCD.")

                    # Increment display counter to show the next display
                    if len(self.display_sets) > 1:
                        if self.display_set_count < len(self.display_sets) - 1:
                            self.display_set_count += 1
                        else:
                            self.display_set_count = 0

                    self.timer = time.time() + self.lcd_period

                elif not self.lcd_is_on:
                    # Turn backlight off
                    self.lcd_out.lcd_backlight(0)

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
            self.lcd_out.lcd_init()  # Blank LCD
            line_1 = 'Mycodo {}'.format(MYCODO_VERSION)
            line_2 = 'Stop {}'.format(self.lcd_name)
            self.lcd_out.lcd_write_lines(line_1, line_2, '', '')
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
            self.running = False

    def lcd_init(self):
        self.lcd_out.lcd_init()
        self.lcd_initialized = True
        self.lcd_is_on = True

    def get_measurement(self, display_id, i):
        try:
            if self.lcd_line[display_id][i]['measure'] == 'BLANK':
                self.lcd_line[display_id][i]['name'] = ''
                self.lcd_line[display_id][i]['unit'] = ''
                self.lcd_line[display_id][i]['measure_val'] = ''
                return True
            elif self.lcd_line[display_id][i]['measure'] == 'IP':
                str_ip_cmd = "ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/'"
                ip_out, _, _ = cmd_output(str_ip_cmd)
                self.lcd_line[display_id][i]['name'] = ''
                self.lcd_line[display_id][i]['unit'] = ''
                self.lcd_line[display_id][i]['measure_val'] = ip_out.rstrip().decode("utf-8")
                return True
            elif self.lcd_line[display_id][i]['measure'] == 'output_state':
                self.lcd_line[display_id][i]['measure_val'] = self.output_state(
                    self.lcd_line[display_id][i]['id'])
                return True
            else:
                if self.lcd_line[display_id][i]['measure'] == 'time':
                    last_measurement = read_last_influxdb(
                        self.lcd_line[display_id][i]['id'],
                        '/.*/',
                        None,
                        None,
                        duration_sec=self.lcd_max_age[display_id][i])
                else:
                    last_measurement = read_last_influxdb(
                        self.lcd_line[display_id][i]['id'],
                        self.lcd_line[display_id][i]['unit'],
                        self.lcd_line[display_id][i]['measure'],
                        self.lcd_line[display_id][i]['channel'],
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
                if self.lcd_line[display_id][i]['unit']:
                    unit_length = len(self.lcd_line[display_id][i]['unit'].replace('°', u''))
                else:
                    unit_length = 0

                # Produce the line that will be displayed on the LCD
                if self.lcd_line[display_id][i]['measure'] == 'time':
                    # Convert UTC timestamp to local timezone
                    utc_dt = datetime.datetime.strptime(
                        self.lcd_line[display_id][i]['time'].split(".")[0],
                        '%Y-%m-%dT%H:%M:%S')
                    utc_timestamp = calendar.timegm(utc_dt.timetuple())
                    self.lcd_string_line[display_id][i] = str(
                        datetime.datetime.fromtimestamp(utc_timestamp))
                elif unit_length > 0:
                    value_length = len(str(
                        self.lcd_line[display_id][i]['measure_val']))
                    name_length = self.lcd_x_characters - value_length - unit_length - 2
                    name_cropped = self.lcd_line[display_id][i]['name'].ljust(name_length)[:name_length]
                    self.lcd_string_line[display_id][i] = '{name} {value} {unit}'.format(
                        name=name_cropped,
                        value=self.lcd_line[display_id][i]['measure_val'],
                        unit=self.lcd_line[display_id][i]['unit'].replace('°', u''))
                else:
                    value_length = len(str(
                        self.lcd_line[display_id][i]['measure_val']))
                    name_length = self.lcd_x_characters - value_length - 1
                    name_cropped = self.lcd_line[display_id][i]['name'][:name_length]
                    if name_cropped != '':
                        line_str = '{name} {value}'.format(
                            name=name_cropped,
                            value=self.lcd_line[display_id][i]['measure_val'])
                    else:
                        line_str = self.lcd_line[display_id][i]['measure_val']
                    self.lcd_string_line[display_id][i] = line_str

            else:
                error = 'NO DATA'
                name_length = self.lcd_x_characters - len(error) - 1
                name_cropped = self.lcd_line[display_id][i]['name'].ljust(name_length)[:name_length]
                self.lcd_string_line[display_id][i] = '{name} {error}'.format(
                    name=name_cropped, error=error)

        except Exception as except_msg:
            self.logger.exception("Error: {err}".format(err=except_msg))

    def output_lcds(self):
        """ Output to all LCDs all at once """
        line_1 = ''
        line_2 = ''
        line_3 = ''
        line_4 = ''
        self.lcd_out.lcd_init()
        display_id = self.display_sets[self.display_set_count]
        if 1 in self.lcd_string_line[display_id] and self.lcd_string_line[display_id][1]:
            line_1 = self.lcd_string_line[display_id][1]
        if 2 in self.lcd_string_line[display_id] and self.lcd_string_line[display_id][2]:
            line_2 = self.lcd_string_line[display_id][2]
        if 3 in self.lcd_string_line[display_id] and self.lcd_string_line[display_id][3]:
            line_3 = self.lcd_string_line[display_id][3]
        if 4 in self.lcd_string_line[display_id] and self.lcd_string_line[display_id][4]:
            line_4 = self.lcd_string_line[display_id][4]
        self.lcd_out.lcd_write_lines(line_1, line_2, line_3, line_4)

    @staticmethod
    def output_state(output_id):
        output = db_retrieve_table_daemon(Output, unique_id=output_id)
        GPIO.setmode(GPIO.BCM)
        if GPIO.input(output.pin) == output.trigger:
            gpio_state = 'On'
        else:
            gpio_state = 'Off'
        return gpio_state

    def setup_lcd_line(self, display_id, line, device_id, measurement_id):
        if measurement_id == 'output':
            device_measurement = db_retrieve_table_daemon(
                Output, unique_id=device_id)
        elif measurement_id in ['BLANK', 'IP']:
            device_measurement = None
        else:
            device_measurement = db_retrieve_table_daemon(
                DeviceMeasurements, unique_id=measurement_id)

        if device_measurement:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)
        else:
            channel = None
            unit = None
            measurement = None

        self.lcd_line[display_id][line]['setup'] = False
        self.lcd_line[display_id][line]['id'] = device_id
        self.lcd_line[display_id][line]['name'] = None
        self.lcd_line[display_id][line]['unit'] = unit
        self.lcd_line[display_id][line]['measure'] = measurement
        self.lcd_line[display_id][line]['channel'] = channel

        if 'time' in measurement_id:
            self.lcd_line[display_id][line]['measure'] = 'time'
        elif measurement_id in ['BLANK', 'IP']:
            self.lcd_line[display_id][line]['measure'] = measurement_id
            self.lcd_line[display_id][line]['name'] = ''

        if not device_id:
            return

        if unit in self.dict_units:
            self.lcd_line[display_id][line]['unit'] = unit
        else:
            self.lcd_line[display_id][line]['unit'] = ''

        # Determine the name
        controllers = [
            Output,
            PID,
            Input,
            Math
        ]
        for each_controller in controllers:
            controller_found = db_retrieve_table_daemon(each_controller, unique_id=device_id)
            if controller_found:
                self.lcd_line[display_id][line]['name'] = controller_found.name

        if (self.lcd_line[display_id][line]['measure'] in ['BLANK', 'IP', 'time'] or
                None not in [self.lcd_line[display_id][line]['name'],
                             self.lcd_line[display_id][line]['unit']]):
            self.lcd_line[display_id][line]['setup'] = True

    def lcd_backlight(self, state):
        """ Turn the backlight on or off """
        if state:
            self.lcd_out.lcd_backlight(state)
            self.lcd_is_on = True
            self.timer = time.time() - 1  # Induce LCD to update after turning backlight on
        else:
            self.lcd_is_on = False  # Instruct LCD backlight to turn off

    def lcd_flash(self, state):
        """ Enable the LCD to begin or end flashing """
        if state:
            self.flash_lcd_on = True
            return 1, "LCD {} Flashing Turned On".format(self.lcd_id)
        else:
            self.flash_lcd_on = False
            self.lcd_backlight(True)
            return 1, "LCD {} Reset".format(self.lcd_id)

    def is_running(self):
        """ returns if the controller is running """
        return self.running

    def stop_controller(self):
        """ Stops the controller """
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

#!/usr/bin/python
# coding=utf-8
#
# controller_sensor.py - Sensor controller that manages reading sensors and
#                        creating database entries
#

import datetime
import logging
import requests
import threading
import time
import timeit
import RPi.GPIO as GPIO
from lockfile import LockFile

# Classes
from databases.mycodo_db.models_5 import (
    CameraStill,
    CameraStream,
    Relay,
    Sensor,
    SensorConditional,
    SMTP
)
from mycodo_client import DaemonControl
# Sensor/device modules
from devices.tca9548a import TCA9548A
from devices.ads1x15 import ADS1x15Read
from devices.mcp342x import MCP342xRead
from sensors.atlas_pt1000 import AtlasPT1000Sensor
from sensors.am2315 import AM2315Sensor
from sensors.bme280 import BME280Sensor
from sensors.bmp import BMPSensor
from sensors.chirp import ChirpSensor
from sensors.dht11 import DHT11Sensor
from sensors.dht22 import DHT22Sensor
from sensors.ds18b20 import DS18B20Sensor
from sensors.htu21d import HTU21DSensor
from sensors.k30 import K30Sensor
from sensors.raspi import RaspberryPiCPUTemp
from sensors.raspi_cpuload import RaspberryPiCPULoad
from sensors.tmp006 import TMP006Sensor
from sensors.tsl2561 import TSL2561Sensor
from sensors.sht1x_7x import SHT1x7xSensor
from sensors.sht2x import SHT2xSensor

# Functions
from devices.camera_pi import camera_record
from utils.database import db_retrieve_table_daemon
from utils.influx import (
    format_influxdb_data,
    read_last_influxdb,
    write_influxdb_list,
    write_influxdb_value
)
from utils.send_data import send_email
from utils.system_pi import cmd_output

# Config
from config import SQL_DATABASE_MYCODO_5

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO_5


class Measurement:
    """
    Class for holding all measurement values in a dictionary.
    The dictionary is formatted in the following way:

    {'measurement type':measurement value}

    Measurement type: The environmental or physical condition
    being measured, such as 'temperature', or 'pressure'.

    Measurement value: The actual measurement of the condition.
    """

    def __init__(self, raw_data):
        self.rawData = raw_data

    @property
    def values(self):
        return self.rawData


class SensorController(threading.Thread):
    """
    Class for controlling the sensor

    """
    def __init__(self, ready, sensor_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger(
            "mycodo.sensor_{id}".format(id=sensor_id))

        list_devices_i2c = [
            'ADS1x15',
            'AM2315',
            'ATLAS_PT1000',
            'BME280',
            'BMP',
            'CHIRP',
            'HTU21D',
            'MCP342x',
            'SHT2x',
            'TMP006',
            'TSL2561'
        ]

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.lock = {}
        self.measurement = None
        self.updateSuccess = False
        self.sensor_id = sensor_id
        self.control = DaemonControl()
        self.pause_loop = False
        self.verify_pause_loop = True

        self.cond_id = {}
        self.cond_name = {}
        self.cond_activated = {}
        self.cond_period = {}
        self.cond_measurement_type = {}
        self.cond_edge_select = {}
        self.cond_edge_detected = {}
        self.cond_gpio_state = {}
        self.cond_direction = {}
        self.cond_setpoint = {}
        self.cond_relay_id = {}
        self.cond_relay_state = {}
        self.cond_relay_on_duration = {}
        self.cond_execute_command = {}
        self.cond_email_notify = {}
        self.cond_flash_lcd = {}
        self.cond_camera_record = {}
        self.cond_timer = {}
        self.smtp_wait_timer = {}

        self.setup_sensor_conditionals()

        sensor = db_retrieve_table_daemon(Sensor, device_id=self.sensor_id)
        self.unique_id = sensor.unique_id
        self.i2c_bus = sensor.i2c_bus
        self.location = sensor.location
        self.measurements = sensor.measurements
        self.device = sensor.device
        self.period = sensor.period
        self.multiplexer_address_raw = sensor.multiplexer_address
        self.multiplexer_bus = sensor.multiplexer_bus
        self.multiplexer_channel = sensor.multiplexer_channel
        self.adc_channel = sensor.adc_channel
        self.adc_gain = sensor.adc_gain
        self.adc_resolution = sensor.adc_resolution
        self.adc_measure = sensor.adc_measure
        self.adc_measure_units = sensor.adc_measure_units
        self.adc_volts_min = sensor.adc_volts_min
        self.adc_volts_max = sensor.adc_volts_max
        self.adc_units_min = sensor.adc_units_min
        self.adc_units_max = sensor.adc_units_max
        self.sht_clock_pin = sensor.sht_clock_pin
        self.sht_voltage = sensor.sht_voltage

        # Edge detection
        self.switch_edge = sensor.switch_edge
        self.switch_bouncetime = sensor.switch_bouncetime
        self.switch_reset_period = sensor.switch_reset_period

        # Relay that will activate prior to sensor read
        self.pre_relay_id = sensor.pre_relay_id
        self.pre_relay_duration = sensor.pre_relay_duration
        self.pre_relay_setup = False
        self.next_measurement = time.time()
        self.get_new_measurement = False
        self.measurement_acquired = False
        self.pre_relay_activated = False
        self.pre_relay_timer = time.time()

        relay = db_retrieve_table_daemon(Relay, entry='all')
        for each_relay in relay:  # Check if relay ID actually exists
            if each_relay.id == self.pre_relay_id and self.pre_relay_duration:
                self.pre_relay_setup = True

        smtp = db_retrieve_table_daemon(SMTP, entry='first')
        self.smtp_max_count = smtp.hourly_max
        self.email_count = 0
        self.allowed_to_send_notice = True

        # Convert string I2C address to base-16 int
        if self.device in list_devices_i2c:
            self.i2c_address = int(str(self.location), 16)

        # Set up multiplexer if enabled
        if self.device in list_devices_i2c and self.multiplexer_address_raw:
            self.multiplexer_address_string = self.multiplexer_address_raw
            self.multiplexer_address = int(str(self.multiplexer_address_raw), 16)
            self.multiplexer_lock_file = "/var/lock/mycodo_multiplexer_0x{:02X}.pid".format(self.multiplexer_address)
            self.multiplexer = TCA9548A(self.multiplexer_bus,
                                        self.multiplexer_address)
        else:
            self.multiplexer = None

        if self.device in ['ADS1x15', 'MCP342x'] and self.location:
            self.adc_lock_file = "/var/lock/mycodo_adc_bus{}_0x{:02X}.pid".format(self.i2c_bus, self.i2c_address)

        # Set up edge detection of a GPIO pin
        if self.device == 'EDGE':
            if self.switch_edge == 'rising':
                self.switch_edge_gpio = GPIO.RISING
            elif self.switch_edge == 'falling':
                self.switch_edge_gpio = GPIO.FALLING
            else:
                self.switch_edge_gpio = GPIO.BOTH

        # Set up analog-to-digital converter
        elif self.device == 'ADS1x15':
            self.adc = ADS1x15Read(self.i2c_address, self.i2c_bus,
                                   self.adc_channel, self.adc_gain)
        elif self.device == 'MCP342x':
            self.adc = MCP342xRead(self.i2c_address, self.i2c_bus,
                                   self.adc_channel, self.adc_gain,
                                   self.adc_resolution)
        else:
            self.adc = None

        self.device_recognized = True

        # Set up sensor
        if self.device in ['EDGE', 'ADS1x15', 'MCP342x']:
            self.measure_sensor = None
        elif self.device == 'RPiCPULoad':
            self.measure_sensor = RaspberryPiCPULoad()
        elif self.device == 'RPi':
            self.measure_sensor = RaspberryPiCPUTemp()
        elif self.device == 'CHIRP':
            self.measure_sensor = ChirpSensor(self.i2c_address,
                                              self.i2c_bus)
        elif self.device == 'DS18B20':
            self.measure_sensor = DS18B20Sensor(self.location)
        elif self.device == 'DHT11':
            self.measure_sensor = DHT11Sensor(self.sensor_id,
                                              int(self.location))
        elif self.device in ['DHT22', 'AM2302']:
            self.measure_sensor = DHT22Sensor(self.sensor_id,
                                              int(self.location))
        elif self.device == 'HTU21D':
            self.measure_sensor = HTU21DSensor(self.i2c_bus)
        elif self.device == 'AM2315':
            self.measure_sensor = AM2315Sensor(self.i2c_bus)
        elif self.device == 'ATLAS_PT1000':
            self.measure_sensor = AtlasPT1000Sensor(self.i2c_address,
                                                    self.i2c_bus)
        elif self.device == 'K30':
            self.measure_sensor = K30Sensor()
        elif self.device == 'BME280':
            self.measure_sensor = BME280Sensor(self.i2c_address,
                                               self.i2c_bus)
        elif self.device == 'BMP':
            self.measure_sensor = BMPSensor(self.i2c_bus)
        elif self.device == 'SHT1x_7x':
            self.measure_sensor = SHT1x7xSensor(self.location,
                                                self.sht_clock_pin,
                                                self.sht_voltage)
        elif self.device == 'SHT2x':
            self.measure_sensor = SHT2xSensor(self.i2c_address,
                                              self.i2c_bus)
        elif self.device == 'TMP006':
            self.measure_sensor = TMP006Sensor(self.i2c_address,
                                               self.i2c_bus)
        elif self.device == 'TSL2561':
            self.measure_sensor = TSL2561Sensor(self.i2c_address,
                                                self.i2c_bus)
        else:
            self.device_recognized = False
            self.logger.debug("Device '{device}' not recognized".format(
                device=self.device))
            raise Exception("{device} is not a valid device type.".format(
                device=self.device))

        self.edge_reset_timer = time.time()
        self.sensor_timer = time.time()
        self.running = False
        self.lastUpdate = None

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer()-self.thread_startup_timer)*1000))
            self.ready.set()

            # Set up edge detection
            if self.device == 'EDGE':
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(int(self.location), GPIO.IN)
                GPIO.add_event_detect(int(self.location),
                                      self.switch_edge_gpio,
                                      callback=self.edge_detected,
                                      bouncetime=self.switch_bouncetime)

            while self.running:
                # Pause loop to modify conditional statements.
                # Prevents execution of conditional while varibles are
                # being modified.
                if self.pause_loop:
                    self.verify_pause_loop = True
                    while self.pause_loop:
                        time.sleep(0.1)

                if self.device in ['EDGE']:
                    # Sensors that are triggered (simple switch,
                    # PIR motion, reed, hall, etc.)
                    # Check sensor conditionals if their timers have expired
                    for each_cond_id in self.cond_id:
                        if (self.cond_activated[each_cond_id] and
                                self.cond_edge_select[each_cond_id] == 'state'):
                            if time.time() > self.cond_timer[each_cond_id]:
                                self.cond_timer[each_cond_id] = time.time()+self.cond_period[each_cond_id]
                                self.check_conditionals(each_cond_id)

                else:
                    # Sensors that are read at a regular period

                    # Signal that a measurement needs to be obtained
                    if time.time() > self.next_measurement and not self.get_new_measurement:
                        self.get_new_measurement = True
                        self.next_measurement = time.time()+self.period

                    # if signaled and a pre relay is set up correctly, turn the
                    # relay on for the set duration
                    if (self.get_new_measurement and
                            self.pre_relay_setup and
                            not self.pre_relay_activated):
                        relay_on = threading.Thread(
                            target=self.control.relay_on,
                            args=(self.pre_relay_id,
                                  self.pre_relay_duration,))
                        relay_on.start()
                        self.pre_relay_activated = True
                        self.pre_relay_timer = time.time()+self.pre_relay_duration

                    # If using a pre relay, wait for it to complete before
                    # querying the sensor for a measurement
                    if self.get_new_measurement:
                        if ((self.pre_relay_setup and
                                self.pre_relay_activated and
                                time.time() < self.pre_relay_timer) or
                                not self.pre_relay_setup):
                            # Get measurement(s) from sensor
                            self.update_measure()
                            # Add measurement(s) to influxdb
                            self.add_measure_influxdb()
                            self.pre_relay_activated = False
                            self.get_new_measurement = False

                    # Check sensor conditionals if their timers have expired
                    for each_cond_id in self.cond_id:
                        if self.cond_activated[each_cond_id]:
                            if time.time() > self.cond_timer[each_cond_id]:
                                self.cond_timer[each_cond_id] = time.time()+self.cond_period[each_cond_id]
                                self.check_conditionals(each_cond_id)

                time.sleep(0.1)

            self.running = False

            if self.device == 'EDGE':
                GPIO.setmode(GPIO.BCM)
                GPIO.cleanup(int(self.location))

            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer()-self.thread_shutdown_timer)*1000))
        except requests.ConnectionError:
            self.logger.error("Could not connect to influxdb. Check that it "
                              "is running and accepting connections")
        except Exception as except_msg:
            self.logger.exception("Error: {err}".format(
                err=except_msg))

    def add_measure_influxdb(self):
        """
        Add a measurement entries to InfluxDB

        :rtype: None
        """
        if self.updateSuccess:
            data = []
            for each_measurement, each_value in self.measurement.values.iteritems():
                data.append(format_influxdb_data(self.unique_id,
                                                 each_measurement,
                                                 each_value))
            write_db = threading.Thread(
                target=write_influxdb_list,
                args=(data,))
            write_db.start()

    def check_conditionals(self, cond_id):
        """
        Check if any sensor conditional statements are activated and
        execute their actions if the conditional is true.

        For example, if measured temperature is above 30C, notify me@gmail.com

        :rtype: None

        :param cond_id: ID of conditional to check
        :type cond_id: str
        """
        logger_cond = logging.getLogger("mycodo.SensorCond-{id}".format(
            id=cond_id))
        attachment_file = False
        attachment_type = False
        message = ""

        conditional = False
        if self.cond_edge_detected[cond_id]:
            conditional = 'edge'
        elif self.cond_direction[cond_id]:
            conditional = 'measurement'

        now = time.time()
        timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H-%M-%S')

        if conditional == 'measurement':
            last_measurement = self.get_last_measurement(self.cond_measurement_type[cond_id])
            if (last_measurement and
                ((self.cond_direction[cond_id] == 'above' and
                    last_measurement > self.cond_setpoint[cond_id]) or
                 (self.cond_direction[cond_id] == 'below' and
                    last_measurement < self.cond_setpoint[cond_id]))):

                message = "{}\n[Sensor Conditional {}] {}\n{} {} ".format(
                        timestamp, cond_id,
                        self.cond_name[cond_id],
                        self.cond_measurement_type[cond_id],
                        last_measurement)
                if self.cond_direction[cond_id] == 'above':
                    message += ">"
                elif self.cond_direction[cond_id] == 'below':
                    message += "<"
                message += " {} setpoint.".format(self.cond_setpoint[cond_id])
            else:
                logger_cond.debug("Last measurement not found")
                return 1

        elif conditional == 'edge':
            if self.cond_edge_select[cond_id] == 'edge':
                message = "{}\n[Sensor Conditional {}] {}. {} Edge Detected.".format(
                    timestamp, cond_id,
                    self.cond_name[cond_id],
                    self.cond_edge_detected)
            elif self.cond_edge_select[cond_id] == 'state':
                if GPIO.input(int(self.location)) == self.cond_gpio_state[cond_id]:
                    message = "{}\n[Sensor Conditional {}] {}. {} GPIO State Detected.".format(
                        timestamp, cond_id,
                        self.cond_name[cond_id],
                        self.cond_gpio_state[cond_id])
                else:
                    return 0

        if (self.cond_relay_id[cond_id] and
                self.cond_relay_state[cond_id] in ['on', 'off']):
            message += "\nTurning relay {} {}".format(
                    self.cond_relay_id[cond_id],
                    self.cond_relay_state[cond_id])
            if (self.cond_relay_state[cond_id] == 'on' and
                    self.cond_relay_on_duration[cond_id]):
                message += " for {} seconds".format(self.cond_relay_on_duration[cond_id])
            message += ". "
            relay_on_off = threading.Thread(
                target=self.control.relay_on_off,
                args=(self.cond_relay_id[cond_id],
                      self.cond_relay_state[cond_id],
                      self.cond_relay_on_duration[cond_id],))
            relay_on_off.start()

        # Execute command in shell
        if self.cond_execute_command[cond_id]:
            message += "\nExecute '{}'. ".format(
                    self.cond_execute_command[cond_id])
            _, _, cmd_status = cmd_output(self.cond_execute_command[cond_id])
            message += "Status: {}. ".format(cmd_status)

        if self.cond_camera_record[cond_id] in ['photo', 'photoemail']:
            camera_still = db_retrieve_table_daemon(CameraStill, entry='first')
            attachment_file = camera_record(
                'photo', camera_still)
        elif self.cond_camera_record[cond_id] in ['video', 'videoemail']:
            camera_stream = db_retrieve_table_daemon(CameraStream, entry='first')
            attachment_file = camera_record(
                'video', camera_stream, duration_sec=5)

        if self.cond_email_notify[cond_id]:
            if (self.email_count >= self.smtp_max_count and
                    time.time() < self.smtp_wait_timer[cond_id]):
                self.allowed_to_send_notice = False
            else:
                if time.time() > self.smtp_wait_timer[cond_id]:
                    self.email_count = 0
                    self.smtp_wait_timer[cond_id] = time.time()+3600
                self.allowed_to_send_notice = True
            self.email_count += 1

            # If the emails per hour limit has not been exceeded
            if self.allowed_to_send_notice:
                message += "\nNotify {}.".format(
                        self.cond_email_notify[cond_id])
                # attachment_type != False indicates to
                # attach a photo or video
                if self.cond_camera_record[cond_id] == 'photoemail':
                    message += "\nPhoto attached."
                    attachment_type = 'still'
                elif self.cond_camera_record[cond_id] == 'videoemail':
                    message += "\nVideo attached."
                    attachment_type = 'video'

                smtp = db_retrieve_table_daemon(SMTP, entry='first')
                send_email(smtp.host, smtp.ssl, smtp.port,
                           smtp.user, smtp.passw, smtp.email_from,
                           self.cond_email_notify[cond_id], message,
                           attachment_file, attachment_type)
            else:
                logger_cond.debug(
                    "{:.0f} seconds left to be allowed to email "
                    "again.".format(
                        self.smtp_wait_timer[cond_id]-time.time()))

        if self.cond_flash_lcd[cond_id]:
            start_flashing = threading.Thread(
                target=self.control.flash_lcd,
                args=(self.cond_flash_lcd[cond_id], 1,))
            start_flashing.start()

        logger_cond.debug(message)

    def update_measure(self):
        """
        Retrieve measurement from sensor

        :return: None if success, 0 if fail
        :rtype: int or None
        """
        measurements = None

        if not self.device_recognized:
            self.logger.debug("Device not recognized: {device}".format(
                device=self.device))
            self.updateSuccess = False
            return 1

        if self.multiplexer:
            # Acquire a lock for multiplexer
            (lock_status,
             lock_response) = self.setup_lock(self.multiplexer_address,
                                              self.multiplexer_bus,
                                              self.multiplexer_lock_file)
            if not lock_status:
                self.logger.warning("Could not acquire lock for multiplexer. "
                                    "Error: {err}".format(err=lock_response))
                self.updateSuccess = False
                return 1
            self.logger.debug(
                "Setting multiplexer at address {add} to channel "
                "{chan}".format(add=self.multiplexer_address_string,
                                chan=self.multiplexer_channel))
            # Set multiplexer channel
            (multiplexer_status,
             multiplexer_response) = self.multiplexer.setup(
                self.multiplexer_channel)
            if not multiplexer_status:
                self.logger.warning(
                    "Could not set channel with multiplexer at address {add}."
                    " Error: {err}".format(
                        add=self.multiplexer_address_string,
                        err=multiplexer_response))
                self.updateSuccess = False
                return 1

        if self.adc:
            try:
                # Acquire a lock for ADC
                (lock_status,
                 lock_response) = self.setup_lock(self.i2c_address,
                                                  self.i2c_bus,
                                                  self.adc_lock_file)
                if not lock_status:
                    self.logger.warning(
                        "Could not acquire lock for multiplexer. "
                        "Error: {err}".format(err=lock_response))
                    self.updateSuccess = False
                    return 1

                # Get measurement from ADC
                measurements = self.adc.next()
                if measurements is not None:
                    # Get the voltage difference between min and max volts
                    diff_voltage = abs(self.adc_volts_max-self.adc_volts_min)
                    # Ensure the measured voltage stays within the min/max bounds
                    if measurements['voltage'] < self.adc_volts_min:
                        measured_voltage = self.adc_volts_min
                    elif measurements['voltage'] > self.adc_volts_max:
                        measured_voltage = self.adc_volts_max
                    else:
                        measured_voltage = measurements['voltage']
                    # Calculate the percentage of the voltage difference
                    percent_diff = (measured_voltage-self.adc_volts_min)/diff_voltage
                    # Get the units difference between min and max units
                    diff_units = abs(self.adc_units_max-self.adc_units_min)
                    # Calculate the measured units from the percent difference
                    converted_units = self.adc_units_min+(diff_units*percent_diff)
                    if converted_units < self.adc_units_min:
                        measurements[self.adc_measure] = self.adc_units_min
                    elif converted_units > self.adc_units_max:
                        measurements[self.adc_measure] = self.adc_units_max
                    else:
                        measurements[self.adc_measure] = converted_units
            except Exception as except_msg:
                self.logger.exception(
                    "Error while attempting to read adc: {err}".format(
                        err=except_msg))
            finally:
                self.release_lock(self.i2c_address,
                                  self.i2c_bus,
                                  self.adc_lock_file)
        else:
            try:
                # Get measurement from sensor
                measurements = self.measure_sensor.next()
            except StopIteration:
                self.logger.info(
                    "StopIteration raised. Possibly could not read sensor. "
                    "Ensure it's connected properly and detected.")
            except Exception as except_msg:
                self.logger.exception(
                    "Error while attempting to read sensor: {err}".format(
                        err=except_msg))

        if self.multiplexer:
            self.release_lock(self.multiplexer_address,
                              self.multiplexer_bus,
                              self.multiplexer_lock_file)

        if self.device_recognized and measurements is not None:
            self.measurement = Measurement(measurements)
            self.updateSuccess = True
        else:
            self.updateSuccess = False

        self.lastUpdate = time.time()

    def setup_lock(self, i2c_address, i2c_bus, lockfile):
        execution_timer = timeit.default_timer()
        try:
            self.lock[lockfile] = LockFile(lockfile)
            while not self.lock[lockfile].i_am_locking():
                try:
                    self.logger.debug("[Locking bus-{} 0x{:02X}] Acquiring "
                                      "Lock: {}".format(i2c_bus, i2c_address,
                                                        self.lock[lockfile].path))
                    self.lock[lockfile].acquire(timeout=60)    # wait up to 60 seconds
                except Exception as e:
                    self.logger.error("{cls} raised an exception: "
                                      "{err}".format(cls=type(self).__name__, err=e))
                    self.logger.exception("[Locking bus-{} 0x{:02X}] Waited 60 "
                                          "seconds. Breaking lock to acquire "
                                          "{}".format(i2c_bus, i2c_address,
                                                      self.lock[lockfile].path))
                    self.lock[lockfile].break_lock()
                    self.lock[lockfile].acquire()
            self.logger.debug("[Locking bus-{} 0x{:02X}] Acquired Lock: {}".format(
                i2c_bus, i2c_address, self.lock[lockfile].path))
            self.logger.debug("[Locking bus-{} 0x{:02X}] Executed in {:.1f} ms".format(
                i2c_bus, i2c_address, (timeit.default_timer()-execution_timer)*1000))
            return 1, "Success"
        except Exception as msg:
            return 0, "Multiplexer Fail: {}".format(msg)

    def release_lock(self, i2c_address, i2c_bus, lockfile):
        self.logger.debug("[Locking bus-{} 0x{:02X}] Releasing Lock: {}".format(i2c_bus, i2c_address, lockfile))
        self.lock[lockfile].release()

    def get_last_measurement(self, measurement_type):
        """
        Retrieve the latest sensor measurement

        :return: The latest sensor value or None if no data available
        :rtype: float or None

        :param measurement_type: Environmental condition of a sensor (e.g.
            temperature, humidity, pressure, etc.)
        :type measurement_type: str
        """
        last_measurement = read_last_influxdb(
            self.sensor_id, measurement_type, int(self.period*1.5)).raw
        if last_measurement:
            number = len(last_measurement['series'][0]['values'])
            last_value = last_measurement['series'][0]['values'][number-1][1]
            return last_value
        else:
            return None

    def edge_detected(self, pin):
        gpio_state = GPIO.input(int(self.location))
        if time.time() > self.edge_reset_timer:
            self.edge_reset_timer = time.time()+self.switch_reset_period
            if (self.switch_edge == 'rising' or
                    (self.switch_edge == 'both' and gpio_state)):
                rising_or_falling = 1  # Rising edge detected
            else:
                rising_or_falling = -1  # Falling edge detected
            write_db = threading.Thread(
                target=write_influxdb_value,
                args=(self.sensor_id, 'edge', rising_or_falling,))
            write_db.start()

            # Check sensor conditionals
            for each_cond_id in self.cond_id:
                if ((self.cond_activated[each_cond_id] and self.cond_edge_select[each_cond_id] == 'edge') and
                        ((self.cond_edge_detected[each_cond_id] == 'rising' and
                          rising_or_falling == 1) or
                         (self.cond_edge_detected[each_cond_id] == 'falling' and
                          rising_or_falling == -1) or
                         self.cond_edge_detected[each_cond_id] == 'both')):
                    self.check_conditionals(each_cond_id)

    def setup_sensor_conditionals(self, cond_mod='setup', cond_id=None):
        logger_cond = logging.getLogger(
            "mycodo.sensor_{id}_cond_{cond}".format(id=self.sensor_id,
                                                    cond=cond_id))

        # Signal to pause the main loop and wait for verification
        self.pause_loop = True
        while not self.verify_pause_loop:
            time.sleep(0.1)

        if cond_mod == 'del':
            self.cond_id.pop(cond_id, None)
            self.cond_activated.pop(cond_id, None)
            self.cond_period.pop(cond_id, None)
            self.cond_name.pop(cond_id, None)
            self.cond_measurement_type.pop(cond_id, None)
            self.cond_edge_select.pop(cond_id, None)
            self.cond_edge_detected.pop(cond_id, None)
            self.cond_gpio_state.pop(cond_id, None)
            self.cond_direction.pop(cond_id, None)
            self.cond_setpoint.pop(cond_id, None)
            self.cond_relay_id.pop(cond_id, None)
            self.cond_relay_state.pop(cond_id, None)
            self.cond_relay_on_duration.pop(cond_id, None)
            self.cond_execute_command.pop(cond_id, None)
            self.cond_email_notify.pop(cond_id, None)
            self.cond_flash_lcd.pop(cond_id, None)
            self.cond_camera_record.pop(cond_id, None)
            self.cond_timer.pop(cond_id, None)
            self.smtp_wait_timer.pop(cond_id, None)
            logger_cond.debug("Deleted Conditional".format(
                sen=self.sensor_id))
        else:
            if cond_mod == 'setup':
                self.cond_id = {}
                self.cond_name = {}
                self.cond_activated = {}
                self.cond_period = {}
                self.cond_measurement_type = {}
                self.cond_edge_select = {}
                self.cond_edge_detected = {}
                self.cond_gpio_state = {}
                self.cond_direction = {}
                self.cond_setpoint = {}
                self.cond_relay_id = {}
                self.cond_relay_state = {}
                self.cond_relay_on_duration = {}
                self.cond_execute_command = {}
                self.cond_email_notify = {}
                self.cond_flash_lcd = {}
                self.cond_camera_record = {}
                self.cond_timer = {}
                self.smtp_wait_timer = {}

                self.sensor_conditional = db_retrieve_table_daemon(
                    SensorConditional)
                self.sensor_conditional = self.sensor_conditional.filter(
                    SensorConditional.is_activated == True)
            elif cond_mod == 'add':
                self.sensor_conditional = db_retrieve_table_daemon(
                    SensorConditional)
                self.sensor_conditional = self.sensor_conditional.filter(
                    SensorConditional.sensor_id == self.sensor_id)
                self.sensor_conditional = self.sensor_conditional.filter(
                    SensorConditional.is_activated == True)
                self.sensor_conditional = self.sensor_conditional.filter(
                    SensorConditional.id == cond_id)
                logger_cond.debug("Added Conditional".format(
                    sen=self.sensor_id))
            elif cond_mod == 'mod':
                self.sensor_conditional = db_retrieve_table_daemon(
                    SensorConditional)
                self.sensor_conditional = self.sensor_conditional.filter(
                    SensorConditional.sensor_id == self.sensor_id)
                self.sensor_conditional = self.sensor_conditional.filter(
                    SensorConditional.id == cond_id)
                logger_cond.debug("Modified Conditional".format(
                    sen=self.sensor_id))
            else:
                return 1

            for each_cond in self.sensor_conditional.all():
                if cond_mod == 'setup':
                    self.logger.debug("Activated Conditional {cond}".format(
                        cond=each_cond))
                self.cond_id[each_cond.id] = each_cond.id
                self.cond_name[each_cond.id] = each_cond.name
                self.cond_activated[each_cond.id] = each_cond.is_activated
                self.cond_period[each_cond.id] = each_cond.period
                self.cond_measurement_type[each_cond.id] = each_cond.measurement_type
                self.cond_edge_select[each_cond.id] = each_cond.edge_select
                self.cond_edge_detected[each_cond.id] = each_cond.edge_detected
                self.cond_gpio_state[each_cond.id] = each_cond.gpio_state
                self.cond_direction[each_cond.id] = each_cond.direction
                self.cond_setpoint[each_cond.id] = each_cond.setpoint
                self.cond_relay_id[each_cond.id] = each_cond.relay_id
                self.cond_relay_state[each_cond.id] = each_cond.relay_state
                self.cond_relay_on_duration[each_cond.id] = each_cond.relay_on_duration
                self.cond_execute_command[each_cond.id] = each_cond.execute_command
                self.cond_email_notify[each_cond.id] = each_cond.email_notify
                self.cond_flash_lcd[each_cond.id] = each_cond.email_notify
                self.cond_camera_record[each_cond.id] = each_cond.camera_record
                self.cond_timer[each_cond.id] = time.time()+each_cond.period
                self.smtp_wait_timer[each_cond.id] = time.time()+3600

        self.pause_loop = False
        self.verify_pause_loop = False

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        if self.device not in ['EDGE', 'ADS1x15', 'MCP342x']:
            self.measure_sensor.stop_sensor()
        self.running = False

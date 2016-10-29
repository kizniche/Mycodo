#!/usr/bin/python
# coding=utf-8
#
# controller_sensor.py - Sensor controller that manages reading sensors and
#                        creating database entries
#

import datetime
import pigpio
import smbus
import threading
import time
import timeit
import RPi.GPIO as GPIO
from lockfile import LockFile

# Sensor/device modules tested and working
from devices.tca9548a import TCA9548A
from devices.ads1x15 import ADS1x15_read
from devices.mcp342x import MCP342x_read
from sensors.atlas_pt1000 import Atlas_PT1000
from sensors.am2315 import AM2315_read
from sensors.bme280 import BME280
from sensors.bmp import BMP
from sensors.dht22 import DHT22
from sensors.ds18b20 import DS18B20
from sensors.htu21d import HTU21D_read
from sensors.k30 import K30
from sensors.raspi import RaspberryPiCPUTemp
from sensors.raspi_cpuload import RaspberryPiCPULoad
from sensors.tmp006 import TMP006_read
from sensors.tsl2561 import TSL2561_read
from sensors.sht1x_7x import SHT1x_7x_read
from sensors.sht2x import SHT2x_read

# Sensor modules that are untested (don't have these sensors to test)
from sensors.dht11 import DHT11

from config import SQL_DATABASE_MYCODO
from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import INSTALL_DIRECTORY

from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import Sensor
from databases.mycodo_db.models import SensorConditional
from databases.mycodo_db.models import SMTP
from databases.utils import session_scope

from mycodo_client import DaemonControl
from utils.camera import camera_record
from utils.influx import format_influxdb_data, read_last_influxdb, write_influxdb_value, write_influxdb_list
from utils.send_data import send_email
from utils.system_pi import cmd_output

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class Measurement():
    """
    Class for holding all measurement values in a dictionary.
    The dictionary is formatted in the following way:

    {'measurement type':measurement value}

    Measurement type: The environmental or physical condition
    being measured, such as 'temperature', or 'pressure'.

    Measurement value: The actual measurement of the condition.
    """

    def __init__(self, rawData):
        self.rawData = rawData

    @property
    def values(self):
        return self.rawData


class SensorController(threading.Thread):
    """
    Class for controlling the sensor

    """

    def __init__(self, ready, logger, sensor_id):
        threading.Thread.__init__(self)

        list_devices_i2c = ['ADS1x15',
                            'AM2315',
                            'ATLAS_PT1000',
                            'BME280',
                            'BMP',
                            'HTU21D',
                            'MCP342x',
                            'SHT2x',
                            'TMP006',
                            'TSL2561']

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.logger = logger
        self.lock = {}
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

        with session_scope(MYCODO_DB_PATH) as new_session:
            sensor = new_session.query(Sensor)
            sensor = sensor.filter(Sensor.id == self.sensor_id).first()
            self.i2c_bus = sensor.i2c_bus
            self.location = sensor.location
            self.device_type = sensor.device
            self.sensor_type = sensor.device_type
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
            relay = new_session.query(Relay).all()
            for each_relay in relay:  # Check if relay ID actually exists
                if each_relay.id == self.pre_relay_id and self.pre_relay_duration:
                    self.pre_relay_setup = True

            smtp = new_session.query(SMTP).first()
            self.smtp_max_count = smtp.hourly_max
            self.email_count = 0
            self.allowed_to_send_notice = True

        # Convert string I2C address to base-16 int
        if self.device_type in list_devices_i2c:
            self.i2c_address = int(str(self.location), 16)

        # Set up multiplexer if enabled
        if self.device_type in list_devices_i2c and self.multiplexer_address_raw:
            self.multiplexer_address_string = self.multiplexer_address_raw
            self.multiplexer_address = int(str(self.multiplexer_address_raw), 16)
            self.multiplexer_lock_file = "/var/lock/mycodo_multiplexer_0x{:02X}.pid".format(self.multiplexer_address)
            self.multiplexer = TCA9548A(self.multiplexer_bus,
                                        self.multiplexer_address)
        else:
            self.multiplexer = None

        if self.device_type in ['ADS1x15', 'MCP342x'] and self.location:
            self.adc_lock_file = "/var/lock/mycodo_adc_bus{}_0x{:02X}.pid".format(self.i2c_bus, self.i2c_address)

        # Set up edge detection of a GPIO pin
        if self.device_type == 'EDGE':
            if self.switch_edge == 'rising':
                self.switch_edge_gpio = GPIO.RISING
            elif self.switch_edge == 'falling':
                self.switch_edge_gpio = GPIO.FALLING
            else:
                self.switch_edge_gpio = GPIO.BOTH

        # Set up analog-to-digital converter
        elif self.device_type == 'ADS1x15':
            self.adc = ADS1x15_read(self.i2c_address, self.i2c_bus,
                                    self.adc_channel, self.adc_gain)
        elif self.device_type == 'MCP342x':
            self.adc = MCP342x_read(self.i2c_address, self.i2c_bus,
                                    self.adc_channel, self.adc_gain,
                                    self.adc_resolution)
        else:
            self.adc = None

        self.device_recognized = True

        # Set up sensor
        if self.device_type in ['EDGE', 'ADS1x15', 'MCP342x']:
            self.measure_sensor = None
        elif self.device_type == 'RPiCPULoad':
            self.measure_sensor = RaspberryPiCPULoad()
        elif self.device_type == 'RPi':
            self.measure_sensor = RaspberryPiCPUTemp()
        elif self.device_type == 'DS18B20':
            self.measure_sensor = DS18B20(self.location)
        elif self.device_type == 'DHT11':
            self.measure_sensor = DHT11(pigpio.pi(), int(self.location))
        elif self.device_type in ['DHT22', 'AM2302']:
            self.measure_sensor = DHT22(pigpio.pi(), int(self.location))
        elif self.device_type == 'HTU21D':
            self.measure_sensor = HTU21D_read(self.i2c_bus)
        elif self.device_type == 'AM2315':
            self.measure_sensor = AM2315_read(self.i2c_bus)
        elif self.device_type == 'ATLAS_PT1000':
            self.measure_sensor = Atlas_PT1000(self.i2c_address, self.i2c_bus)
        elif self.device_type == 'K30':
            self.measure_sensor = K30()
        elif self.device_type == 'BME280':
            self.measure_sensor = BME280(self.i2c_address, self.i2c_bus)
        elif self.device_type == 'BMP':
            self.measure_sensor = BMP(self.i2c_bus)
        elif self.device_type == 'SHT1x_7x':
            self.measure_sensor = SHT1x_7x_read(self.location,
                                                self.sht_clock_pin,
                                                self.sht_voltage)
        elif self.device_type == 'SHT2x':
            self.measure_sensor = SHT2x_read(self.i2c_address, self.i2c_bus)
        elif self.device_type == 'TMP006':
            self.measure_sensor = TMP006_read(self.i2c_address, self.i2c_bus)
        elif self.device_type == 'TSL2561':
            self.measure_sensor = TSL2561_read(self.i2c_address, self.i2c_bus)
        else:
            self.device_recognized = False
            self.logger.debug("[Sensor {}] Device '{}' not "
                              "recognized:".format(self.sensor_id,
                                                   self.device_type))
            raise Exception("{} is not a valid device type.".format(
                self.device_type))

        self.edge_reset_timer = time.time()
        self.sensor_timer = time.time()
        self.running = False
        self.lastUpdate = None

    def run(self):
        try:
            self.running = True
            self.logger.info("[Sensor {}] Activated in {:.1f} ms".format(
                self.sensor_id,
                (timeit.default_timer()-self.thread_startup_timer)*1000))
            self.ready.set()

            # Set up edge detection
            if self.device_type == 'EDGE':
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

                if self.device_type in ['EDGE']:
                    # Sensors that are triggered (simple switch,
                    # PIR motion, reed, hall, etc.)
                    # Check sensor conditionals if their timers have expired
                    for each_cond_id in self.cond_id:
                        if (self.cond_activated[each_cond_id] and
                                self.cond_edge_select[each_cond_id] == 'state'):
                            if time.time() > self.cond_timer[each_cond_id]:
                                self.cond_timer[each_cond_id] = time.time()+self.cond_period[each_cond_id]
                                self.checkConditionals(each_cond_id)

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
                            self.updateMeasurement()
                            # Add measurement(s) to influxdb
                            self.addMeasurementInfluxdb()
                            self.pre_relay_activated = False
                            self.get_new_measurement = False

                    # Check sensor conditionals if their timers have expired
                    for each_cond_id in self.cond_id:
                        if self.cond_activated[each_cond_id]:
                            if time.time() > self.cond_timer[each_cond_id]:
                                self.cond_timer[each_cond_id] = time.time()+self.cond_period[each_cond_id]
                                self.checkConditionals(each_cond_id)

                time.sleep(0.1)

            self.running = False

            if self.device_type == 'EDGE':
                GPIO.setmode(GPIO.BCM)
                GPIO.cleanup(int(self.location))

            self.logger.info("[Sensor {}] Deactivated in {:.1f} ms".format(
                self.sensor_id,
                (timeit.default_timer()-self.thread_shutdown_timer)*1000))
        except Exception as msg:
            self.logger.exception("[Sensor {}] Error: {}".format(
                self.sensor_id, msg))


    def addMeasurementInfluxdb(self):
        """
        Add a measurement entries to InfluxDB

        :rtype: None
        """
        if self.updateSuccess:
            data = []
            for each_measurement, each_value in self.measurement.values.iteritems():
                data.append(format_influxdb_data(self.sensor_type,
                                                 self.sensor_id,
                                                 each_measurement,
                                                 each_value))
            write_db = threading.Thread(
                target=write_influxdb_list,
                args=(self.logger, INFLUXDB_HOST,
                      INFLUXDB_PORT, INFLUXDB_USER,
                      INFLUXDB_PASSWORD, INFLUXDB_DATABASE,
                      data,))
            write_db.start()


    def checkConditionals(self, cond_id):
        """
        Check if any sensor conditional statements are activated and
        execute their actions if the conditional is true.

        For example, if measured temperature is above 30C, notify me@gmail.com

        :rtype: None

        :param each_cond: Object of SQL table entries for a specific column
        :type each_cond: sqlalchemy object
        """
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
            last_measurement = self.getLastMeasurement(self.cond_measurement_type[cond_id])
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
                self.logger.debug("[Sensor Conditional {}] Last measurement "
                                  "not found".format(cond_id))
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
            attachment_file = camera_record(INSTALL_DIRECTORY, 'photo')
        elif self.cond_camera_record[cond_id] in ['video', 'videoemail']:
            attachment_file = camera_record(INSTALL_DIRECTORY, 'video', duration_sec=5)

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
                with session_scope(MYCODO_DB_PATH) as new_session:
                    smtp = new_session.query(SMTP).first()
                    send_email(self.logger, smtp.host, smtp.ssl, smtp.port,
                          smtp.user, smtp.passw, smtp.email_from,
                          self.cond_email_notify[cond_id], message,
                          attachment_file, attachment_type)
            else:
                self.logger.debug("[Sensor Conditional {}] "
                                  "{:.0f} seconds left to be "
                                  "allowed to email again.".format(
                                  cond_id,
                                  (self.smtp_wait_timer[cond_id]-time.time())))

        if self.cond_flash_lcd[cond_id]:
            start_flashing = threading.Thread(
                target=self.control.flash_lcd,
                args=(self.cond_flash_lcd[cond_id],
                      1,))
            start_flashing.start()

        self.logger.debug(message)


    def updateMeasurement(self):
        """
        Retrieve measurement from sensor

        :return: None if success, 0 if fail
        :rtype: int or None
        """
        if not self.device_recognized:
            self.logger.debug(
                "[Sensor {}] Device not recognized: {}".format(self.sensor_id,
                                                               self.device_type))
            self.updateSuccess = False
            return 1

        if self.multiplexer:
            # Acquire a lock for multiplexer
            (self.lock_status,
            self.lock_response) = self.setup_lock(self.multiplexer_address,
                                                  self.multiplexer_bus,
                                                  self.multiplexer_lock_file)
            if not self.lock_status:
                self.logger.warning("[Sensor {}] Could not acquire lock "
                                    "for multiplexer. Error:"
                                    " {}".format(self.sensor_id,
                                                 self.lock_response))
                self.updateSuccess = False
                return 1
            self.logger.debug("[Sensor {}] Setting multiplexer at address {} to "
                              "channel {}".format(self.sensor_id,
                                                  self.multiplexer_address_string,
                                                  self.multiplexer_channel))
            # Set multiplexer channel
            (self.multiplexer_status,
            self.multiplexer_response) = self.multiplexer.setup(self.multiplexer_channel)
            if not self.multiplexer_status:
                self.logger.warning("[Sensor {}] Could not set channel "
                                    "with multiplexer at address {}. Error:"
                                    " {}".format(self.sensor_id,
                                                 self.multiplexer_address_string,
                                                 self.multiplexer_response))
                self.updateSuccess = False
                return 1

        if self.adc:
            try:
                # Acquire a lock for ADC
                (self.lock_status,
                self.lock_response) = self.setup_lock(self.i2c_address,
                                                      self.i2c_bus,
                                                      self.adc_lock_file)
                if not self.lock_status:
                    self.logger.warning("[Sensor {}] Could not acquire lock "
                                        "for multiplexer. Error:"
                                        " {}".format(self.sensor_id,
                                                     self.lock_response))
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
            except Exception as msg:
                self.logger.exception("[Sensor {}] Error while attempting to read "
                                    "adc: {}".format(self.sensor_id, msg))
            finally:
                self.release_lock(self.i2c_address,
                                  self.i2c_bus,
                                  self.adc_lock_file)
        else:
            try:
                # Get measurement from sensor
                measurements = self.measure_sensor.next()
            except Exception as msg:
                self.logger.exception("[Sensor {}] Error while attempting to read "
                                    "sensor: {}".format(self.sensor_id, msg))

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
        self.execution_timer = timeit.default_timer()
        try:
            self.lock[lockfile] = LockFile(lockfile)
            while not self.lock[lockfile].i_am_locking():
                try:
                    self.logger.debug("[Locking bus-{} 0x{:02X}] Acquiring "
                                      "Lock: {}".format(i2c_bus, i2c_address,
                                                        self.lock[lockfile].path))
                    self.lock[lockfile].acquire(timeout=60)    # wait up to 60 seconds
                except:
                    self.logger.exception("[Locking bus-{} 0x{:02X}] Waited 60 "
                                          "seconds. Breaking lock to acquire "
                                          "{}".format(i2c_bus, i2c_address,
                                                      self.lock[lockfile].path))
                    self.lock[lockfile].break_lock()
                    self.lock[lockfile].acquire()
            self.logger.debug("[Locking bus-{} 0x{:02X}] Acquired Lock: {}".format(
                i2c_bus, i2c_address, self.lock[lockfile].path))
            self.logger.debug("[Locking bus-{} 0x{:02X}] Executed in {:.1f} ms".format(
                i2c_bus, i2c_address, (timeit.default_timer()-self.execution_timer)*1000))
            return 1, "Success"
        except Exception as msg:
            return 0, "Multiplexer Fail: {}".format(msg)


    def release_lock(self, i2c_address, i2c_bus, lockfile):
        self.logger.debug("[Locking bus-{} 0x{:02X}] Releasing Lock: {}".format(i2c_bus, i2c_address, lockfile))
        self.lock[lockfile].release()


    def getLastMeasurement(self, measurement_type):
        """
        Retrieve the latest sensor measurement

        :return: The latest sensor value or None if no data available
        :rtype: float or None

        :param measurement_type: Environmental condition of a sensor (e.g.
            temperature, humidity, pressure, etc.)
        :type measurement_type: str
        """
        last_measurement = read_last_influxdb(INFLUXDB_HOST,
                                              INFLUXDB_PORT,
                                              INFLUXDB_USER,
                                              INFLUXDB_PASSWORD,
                                              INFLUXDB_DATABASE,
                                              self.sensor_id,
                                              measurement_type,
                                              int(self.period*1.5)).raw
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
                args=(self.logger, INFLUXDB_HOST,
                      INFLUXDB_PORT, INFLUXDB_USER,
                      INFLUXDB_PASSWORD, INFLUXDB_DATABASE,
                      self.sensor_type, self.sensor_id,
                      'edge', rising_or_falling,))
            write_db.start()

            # Check sensor conditionals
            for each_cond_id in self.cond_id:
                if ((self.cond_activated[each_cond_id] and self.cond_edge_select[each_cond_id] == 'edge') and
                        ((self.cond_edge_detected[each_cond_id] == 'rising' and
                        rising_or_falling == 1) or
                        (self.cond_edge_detected[each_cond_id] == 'falling' and
                        rising_or_falling == -1) or
                        self.cond_edge_detected[each_cond_id] == 'both')):
                    self.checkConditionals(each_cond_id)


    def setup_sensor_conditionals(self, cond_mod='setup', cond_id=None):
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
            self.logger.debug("[Sensor Conditional {}] Deleted Conditional "
                              "from Sensor {}".format(cond_id, self.sensor_id))
        else:
            with session_scope(MYCODO_DB_PATH) as new_session:
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
                    self.sensor_conditional = new_session.query(
                        SensorConditional).filter(
                            SensorConditional.sensor_id == self.sensor_id)
                    self.sensor_conditional = self.sensor_conditional.filter(
                        SensorConditional.activated == 1)
                elif cond_mod == 'add':
                    self.sensor_conditional = new_session.query(
                        SensorConditional).filter(
                            SensorConditional.sensor_id == self.sensor_id)
                    self.sensor_conditional = self.sensor_conditional.filter(
                        SensorConditional.activated == 1)
                    self.sensor_conditional = self.sensor_conditional.filter(
                        SensorConditional.id == cond_id)
                    self.logger.debug("[Sensor Conditional {}] Added "
                                      "Conditional to Sensor {}".format(
                                            cond_id, self.sensor_id))
                elif cond_mod == 'mod':
                    self.sensor_conditional = new_session.query(
                        SensorConditional).filter(
                            SensorConditional.sensor_id == self.sensor_id)
                    self.sensor_conditional = self.sensor_conditional.filter(
                        SensorConditional.id == cond_id)
                    self.logger.debug("[Sensor Conditional {}] Modified "
                                      "Conditional from Sensor {}".format(
                                            cond_id, self.sensor_id))
                else:
                    return 1

                for each_cond in self.sensor_conditional.all():
                    if cond_mod == 'setup':
                        self.logger.debug("[Sensor Conditional {}] Activated "
                                          "Conditional from Sensor {}".format(
                                                each_cond.id, self.sensor_id))
                    self.cond_id[each_cond.id] = each_cond.id
                    self.cond_name[each_cond.id] = each_cond.name
                    self.cond_activated[each_cond.id] = each_cond.activated
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
                    self.cond_timer[each_cond.id] = time.time()+self.cond_period[each_cond.id]
                    self.smtp_wait_timer[each_cond.id] = time.time()+3600

        self.pause_loop = False
        self.verify_pause_loop = False


    def isRunning(self):
        return self.running


    def stopController(self):
        self.thread_shutdown_timer = timeit.default_timer()
        if self.device_type not in  ['EDGE', 'ADS1x15', 'MCP342x']:
            self.measure_sensor.stopSensor()
        self.running = False

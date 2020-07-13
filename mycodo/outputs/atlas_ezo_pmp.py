# coding=utf-8
#
# atlas_ezo_pmp.py - Output for Atlas Scientific EZO Pump
#
import datetime
import threading
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import DeviceMeasurements
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'volume',
        'unit': 'ml'
    },
    1: {
        'measurement': 'duration_time',
        'unit': 'minute'  # TODO: Change to seconds
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'atlas_ezo_pmp',
    'output_name': "{} (Atlas Scientific)".format(lazy_gettext('Peristaltic Pump')),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['volume', 'on_off'],

    'message': 'Atlas Scientific peristaltic pumps can be set to dispense at their maximum rate or a '
               'rate can be specified. Their minimum flow rate is 0.5 ml/min and their maximum is 105 ml/min.',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'pump_output_mode',
        'pump_flow_rate',
        'button_send_volume',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x67'],
    'i2c_address_editable': True,
    'ftdi_location': '/dev/ttyUSB0',
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.atlas_command = None
        self.ftdi_location = None
        self.uart_location = None
        self.uart_baud_rate = None
        self.i2c_address = None
        self.i2c_bus = None
        self.currently_dispensing = False

        if not testing:
            self.output = output
            self.output_unique_id = output.unique_id
            self.output_interface = output.interface
            self.output_mode = output.output_mode
            self.output_flow_rate = output.flow_rate

    def record_dispersal(self, amount_ml=None, minutes_to_run=None):
        measure_dict = measurements_dict.copy()
        if amount_ml:
            measure_dict[0]['value'] = amount_ml
        if minutes_to_run:
            measure_dict[1]['value'] = minutes_to_run
        add_measurements_influxdb(self.output_unique_id, measure_dict)

    def dispense_duration(self, seconds):
        self.currently_dispensing = True
        timer_dispense = time.time() + seconds

        write_cmd = "D,*"
        self.atlas_command.write(write_cmd)
        self.logger.debug("EZO-PMP command: {}".format(write_cmd))

        while time.time() < timer_dispense and self.currently_dispensing:
            time.sleep(0.1)

        write_cmd = 'X'
        self.atlas_command.write(write_cmd)
        self.logger.debug("EZO-PMP command: {}".format(write_cmd))
        self.currently_dispensing = False

        self.record_dispersal(minutes_to_run=seconds / 60)

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None):
        if state == 'on' and output_type == 'sec' and amount:
            # Only dispense for a duration if output_type is 'sec'
            # Otherwise, refer to output_mode
            write_db = threading.Thread(
                target=self.dispense_duration,
                args=(amount,))
            write_db.start()
            return

        elif state == 'on' and output_type in ['vol', None] and amount:
            if self.output_mode == 'fastest_flow_rate':
                minutes_to_run = amount / 105
                write_cmd = 'D,{ml:.2f}'.format(ml=amount)
            elif self.output_mode == 'specify_flow_rate':
                minutes_to_run = amount / self.output_flow_rate
                write_cmd = 'D,{ml:.2f},{min:.2f}'.format(
                    ml=amount, min=minutes_to_run)
            else:
                self.logger.error("Invalid output_mode: '{}'".format(
                    self.output_mode))
                return

        elif state == 'off' or (amount is not None and amount <= 0):
            self.currently_dispensing = False
            write_cmd = 'X'
            amount = 0
            minutes_to_run = 0

        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Output Type: {ot}, Volume: {vol}, Flow Rate: {fr}".format(
                    state=state, ot=output_type, vol=amount, fr=self.output_flow_rate))
            return

        self.atlas_command.write(write_cmd)
        self.logger.debug("EZO-PMP command: {}".format(write_cmd))

        if amount and minutes_to_run:
            self.record_dispersal(amount_ml=amount, minutes_to_run=minutes_to_run)

    def is_on(self):
        if self.is_setup():
            if self.currently_dispensing:
                return True

            device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == self.output_unique_id)
            for each_dev_meas in device_measurements:
                if each_dev_meas.unit == 'minute':
                    last_measurement = read_last_influxdb(
                        self.output_unique_id,
                        each_dev_meas.unit,
                        each_dev_meas.channel,
                        measure=each_dev_meas.measurement)
                    if last_measurement:
                        try:
                            datetime_ts = datetime.datetime.strptime(
                                last_measurement[0][:-7], '%Y-%m-%dT%H:%M:%S.%f')
                        except:
                            # Sometimes the original timestamp is in milliseconds
                            # instead of nanoseconds. Therefore, remove 3 less digits
                            # past the decimal and try again to parse.
                            datetime_ts = datetime.datetime.strptime(
                                last_measurement[0][:-4], '%Y-%m-%dT%H:%M:%S.%f')
                        minutes_on = last_measurement[1]
                        ts_pmp_off = datetime_ts + datetime.timedelta(minutes=minutes_on)
                        now = datetime.datetime.utcnow()
                        is_on = bool(now < ts_pmp_off)
                        if is_on:
                            return True
            return False

    def is_setup(self):
        if self.atlas_command:
            return True
        return False

    def setup_output(self):
        if self.output_interface == 'FTDI':
            from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
            self.ftdi_location = self.output.ftdi_location
            self.atlas_command = AtlasScientificFTDI(self.ftdi_location)
        elif self.output_interface == 'I2C':
            from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
            self.i2c_address = int(str(self.output.i2c_location), 16)
            self.i2c_bus = self.output.i2c_bus
            self.atlas_command = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)
        elif self.output_interface == 'UART':
            from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
            self.uart_location = self.output.uart_location
            self.output_baud_rate = self.output.baud_rate
            self.atlas_command = AtlasScientificUART(
                self.uart_location, baudrate=self.output_baud_rate)
        else:
            self.logger.error("Unknown interface: {}".format(self.output_interface))

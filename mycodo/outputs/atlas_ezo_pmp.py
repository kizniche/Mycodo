# coding=utf-8
#
# atlas_ezo_pmp.py - Output for Atlas Scientific EZO Pump
#
import datetime
from flask_babel import lazy_gettext
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.influx import read_last_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'volume',
        'unit': 'ml'
    },
    1: {
        'measurement': 'duration_time',
        'unit': 'minute'
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'atlas_ezo_pmp',
    'output_name': lazy_gettext('Atlas Scientific Pump'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['volume'],

    'message': 'Atlas Scientific peristaltic pumps can be set to dispense at their maximum rate or a '
               'rate can be specified.',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'pump_output_mode',
        'pump_flow_rate',
        'button_send_volume'
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

        self.ftdi_location = None
        self.uart_location = None
        self.uart_baud_rate = None
        self.i2c_address = None
        self.i2c_bus = None

        if not testing:
            self.output = output
            self.output_unique_id = output.unique_id
            self.output_interface = output.interface
            self.output_mode = output.output_mode
            self.output_flow_rate = output.flow_rate

    def output_switch(self, state, amount=None, duty_cycle=None):
        measure_dict = measurements_dict.copy()

        if state == 'on' and amount > 0:
            if self.output_mode == 'fastest_flow_rate':
                minutes_to_run = amount * 105
                write_cmd = 'D,{ml:.2f}'.format(ml=amount)
            elif self.output_mode == 'specify_flow_rate':
                minutes_to_run = amount / self.output_flow_rate
                write_cmd = 'D,{ml:.2f},{min:.2f}'.format(
                    ml=amount, min=minutes_to_run)
            else:
                self.logger.error("Invalid output_mode: '{}'".format(
                    self.output_mode))
                return

        elif state == 'off' or amount <= 0:
            write_cmd = 'X'
            amount = 0
            minutes_to_run = 0

        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Volume: {vol}, "
                "Flow Rate: {fr}".format(
                    state=state, vol=amount, fr=self.output_flow_rate))
            return

        self.atlas_command.write(write_cmd)
        self.logger.debug("EZO-PMP command: {}".format(write_cmd))

        if amount and minutes_to_run:
            measure_dict[0]['value'] = amount
            measure_dict[1]['value'] = minutes_to_run
            add_measurements_influxdb(self.output_unique_id, measure_dict)

    def is_on(self):
        if self.is_setup():
            device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == self.output_unique_id)
            for each_dev_meas in device_measurements:
                if each_dev_meas.unit == 'minute':
                    last_measurement = read_last_influxdb(
                        self.output_unique_id,
                        each_dev_meas.unit,
                        each_dev_meas.channel,
                        measure=each_dev_meas.measurement, )
                    if last_measurement:
                        datetime_ts = datetime.datetime.strptime(
                            last_measurement[0][:-7], '%Y-%m-%dT%H:%M:%S.%f')
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

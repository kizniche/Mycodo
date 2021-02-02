# coding=utf-8
#
# pump_atlas_ezo_pmp.py - Output for Atlas Scientific EZO Pump
#
import copy
import datetime
import threading

from flask_babel import lazy_gettext

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'volume',
        'unit': 'ml'
    },
    1: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

channels_dict = {
    0: {
        'types': ['volume', 'on_off'],
        'measurements': [0, 1]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'atlas_ezo_pmp',
    'output_name': "{}: Atlas Scientific".format(lazy_gettext('Peristaltic Pump')),
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['volume', 'on_off'],

    'url_manufacturer': 'https://atlas-scientific.com/peristaltic/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/EZO_PMP_Datasheet.pdf',
    'url_product_purchase': 'https://atlas-scientific.com/peristaltic/ezo-pmp/',

    'message': 'Atlas Scientific peristaltic pumps can be set to dispense at their maximum rate or a '
               'rate can be specified. Their minimum flow rate is 0.5 ml/min and their maximum is 105 ml/min.',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
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
    'uart_baud_rate': 9600,
    
    'custom_channel_options': [
        {
            'id': 'flow_mode',
            'type': 'select',
            'default_value': 'fastest_flow_rate',
            'options_select': [
                ('fastest_flow_rate', 'Fastest Flow Rate'),
                ('specify_flow_rate', 'Specify Flow Rate')
            ],
            'name': lazy_gettext('Flow Rate Method'),
            'phrase': lazy_gettext('The flow rate to use when pumping a volume')
        },
        {
            'id': 'flow_rate',
            'type': 'float',
            'default_value': 10.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Desired Flow Rate (ml/min)',
            'phrase': 'Desired flow rate in ml/minute when Specify Flow Rate set'
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Current (Amps)'),
            'phrase': lazy_gettext('The current draw of the device being controlled')
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.atlas_command = None
        self.currently_dispensing = False
        self.interface = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        self.setup_output_variables(OUTPUT_INFORMATION)
        self.interface = self.output.interface

        if self.interface == 'FTDI':
            from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
            self.atlas_command = AtlasScientificFTDI(self.output.ftdi_location)
        elif self.interface == 'I2C':
            from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
            self.atlas_command = AtlasScientificI2C(
                i2c_address=int(str(self.output.i2c_location), 16),
                i2c_bus=self.output.i2c_bus)
        elif self.interface == 'UART':
            from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
            self.atlas_command = AtlasScientificUART(
                self.output.uart_location,
                baudrate=self.output.baud_rate)
        else:
            self.logger.error("Unknown interface: {}".format(self.interface))
            return

        self.output_setup = True

    def record_dispersal(self, amount_ml=None, seconds_to_run=None):
        measure_dict = copy.deepcopy(measurements_dict)
        if amount_ml:
            measure_dict[0]['value'] = amount_ml
        if seconds_to_run:
            measure_dict[1]['value'] = seconds_to_run
        add_measurements_influxdb(self.unique_id, measure_dict)

    def dispense_duration(self, seconds):
        # timer_dispense = time.time() + seconds
        self.currently_dispensing = True
        write_cmd = "D,*"
        self.atlas_command.write(write_cmd)
        self.logger.debug("EZO-PMP command: {}".format(write_cmd))

        # while time.time() < timer_dispense and self.currently_dispensing:
        #     time.sleep(0.1)
        #
        # write_cmd = 'X'
        # self.atlas_command.write(write_cmd)
        # self.logger.debug("EZO-PMP command: {}".format(write_cmd))
        # self.currently_dispensing = False
        #
        # self.record_dispersal(seconds_to_run=seconds)

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if state == 'on' and output_type == 'sec' and amount:
            # Only dispense for a duration if output_type is 'sec'
            # Otherwise, refer to output_mode
            write_db = threading.Thread(
                target=self.dispense_duration,
                args=(amount,))
            write_db.start()
            return

        elif state == 'on' and output_type in ['vol', None] and amount:
            if self.options_channels['flow_mode'][0] == 'fastest_flow_rate':
                minutes_to_run = amount / 105
                seconds_to_run = minutes_to_run * 60
                write_cmd = 'D,{ml:.2f}'.format(ml=amount)
            elif self.options_channels['flow_mode'][0] == 'specify_flow_rate':
                minutes_to_run = amount / self.options_channels['flow_rate'][0]
                seconds_to_run = minutes_to_run * 60
                write_cmd = 'D,{ml:.2f},{min:.2f}'.format(
                    ml=amount, min=minutes_to_run)
            else:
                self.logger.error("Invalid output_mode: '{}'".format(
                    self.options_channels['flow_mode'][0]))
                return

        elif state == 'off' or (amount is not None and amount <= 0):
            self.currently_dispensing = False
            write_cmd = 'X'
            amount = 0
            seconds_to_run = 0

        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Type: {ot}, Mode: {mod}, Amount: {amt}, Flow Rate: {fr}".format(
                    state=state,
                    ot=output_type,
                    mod=self.options_channels['flow_mode'][0],
                    amt=amount,
                    fr=self.options_channels['flow_rate'][0]))
            return

        self.atlas_command.write(write_cmd)
        self.logger.debug("EZO-PMP command: {}".format(write_cmd))

        if amount and seconds_to_run:
            self.record_dispersal(amount_ml=amount, seconds_to_run=seconds_to_run)

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.currently_dispensing:
                return True

            device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == self.unique_id)
            for each_dev_meas in device_measurements:
                if each_dev_meas.unit == 'minute':
                    last_measurement = read_last_influxdb(
                        self.unique_id,
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

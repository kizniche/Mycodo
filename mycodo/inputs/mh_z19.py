# coding=utf-8
import logging
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device


def constraints_pass_measure_range(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    if value not in ['1000', '2000', '3000', '5000']:
        all_passed = False
        errors.append("Invalid range")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MH_Z19',
    'input_manufacturer': 'Winsen',
    'input_name': 'MH-Z19',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'uart_location',
        'uart_baud_rate',
        'custom_options',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'abc_enable',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Enable ABC'),
            'phrase': lazy_gettext('Enable automatic baseline correction (ABC)')
        },
        {
            'id': 'measure_range',
            'type': 'select',
            'default_value': '5000',
            'options_select': [
                ('1000', '0 - 1000 ppmv'),
                ('2000', '0 - 2000 ppmv'),
                ('3000', '0 - 3000 ppmv'),
                ('5000', '0 - 5000 ppmv'),
            ],
            'required': True,
            'constraints_pass': constraints_pass_measure_range,
            'name': lazy_gettext('Measurement Range'),
            'phrase': lazy_gettext('Set the measuring range of the sensor')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the MH-Z19's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.mh_z19")
        self.measure_range = None
        self.abc_enable = False

        if not testing:
            import serial
            self.logger = logging.getLogger(
                "mycodo.mhz19_{id}".format(
                    id=input_dev.unique_id.split('-')[0]))

            self.uart_location = input_dev.uart_location
            self.baud_rate = input_dev.baud_rate

            # Check if device is valid
            self.serial_device = is_device(self.uart_location)
            if self.serial_device:
                try:
                    self.ser = serial.Serial(
                        self.serial_device,
                        baudrate=self.baud_rate,
                        timeout=1)
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.uart_location))

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'abc_enable':
                        self.abc_enable = bool(value)
                    elif option == 'measure_range':
                        self.measure_range = value

            if self.abc_enable:
                self.abcon()
            else:
                self.abcoff()

            if self.measure_range:
                self.set_measure_range(self.measure_range)

            time.sleep(0.1)

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the MH-Z19's CO2 concentration in ppmv via UART"""
        return_dict = measurements_dict.copy()

        co2 = None

        if not self.serial_device:  # Don't measure if device isn't validated
            return None

        self.ser.flushInput()
        self.ser.write(bytearray([0xff, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]))
        time.sleep(.01)
        resp = self.ser.read(9)

        if resp[0] != 0xff or resp[1] != 0x86:
            self.logger.error("Bad checksum")
        elif len(resp) >= 4:
            high = resp[2]
            low = resp[3]
            co2 = (high * 256) + low
        else:
            self.logger.error("Bad response")

        return_dict[0]['value'] = co2

        return return_dict

    def abcoff(self):
        """
        Turns off Automatic Baseline Correction feature of "B" type sensor.
        Should be run once at the beginning of every activation.
        """
        self.ser.write(bytearray([0xff, 0x01, 0x79, 0x00, 0x00, 0x00, 0x00, 0x00, 0x86]))

    def abcon(self):
        """
        Turns on Automatic Baseline Correction feature of "B" type sensor.
        """
        self.ser.write(bytearray([0xff, 0x01, 0x79, 0xa0, 0x00, 0x00, 0x00, 0x00, 0xe6]))

    def set_measure_range(self, measure_range):
        """
        Sets the measurement range. Options are: '1000', '2000', '3000', or '5000' (ppmv)
        :param measure_range: string
        :return: None
        """
        if measure_range == '1000':
            self.ser.write(bytearray([0xff, 0x01, 0x99, 0x00, 0x00, 0x00, 0x03, 0xe8, 0x7b]))
        elif measure_range == '2000':
            self.ser.write(bytearray([0xff, 0x01, 0x99, 0x00, 0x00, 0x00, 0x07, 0xd0, 0x8f]))
        elif measure_range == '3000':
            self.ser.write(bytearray([0xff, 0x01, 0x99, 0x00, 0x00, 0x00, 0x0b, 0xb8, 0xa3]))
        elif measure_range == '5000':
            self.ser.write(bytearray([0xff, 0x01, 0x99, 0x00, 0x00, 0x00, 0x13, 0x88, 0xcb]))
        else:
            return "out of range"

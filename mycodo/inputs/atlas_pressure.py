# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'pressure',
        'unit': 'psi'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_EZO_PRESS',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Pressure',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Pressure',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/pressure/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/EZO-PRS-Datasheet.pdf',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x6a'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '',

    'custom_options': [
        {
            'id': 'led',
            'type': 'select',
            'default_value': 'on',
            'options_select': [
                ('on', 'Always On'),
                ('off', 'Always Off'),
                ('measure', 'Only On During Measure')
            ],
            'name': lazy_gettext('LED Mode'),
            'phrase': lazy_gettext('When to turn the LED on')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that acquires measurements from the sensor """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.led = None

        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.input_dev = input_dev
            self.interface = input_dev.interface

            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

            if self.atlas_device:
                if self.led == 'on':
                    self.atlas_device.query('L,1')
                elif self.led == 'off':
                    self.atlas_device.query('L,0')

    def initialize_sensor(self):
        if self.interface == 'FTDI':
            from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
            self.atlas_device = AtlasScientificFTDI(self.input_dev.ftdi_location)
        elif self.interface == 'UART':
            from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
            self.atlas_device = AtlasScientificUART(self.input_dev.uart_location)
        elif self.interface == 'I2C':
            from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
            self.atlas_device = AtlasScientificI2C(
                i2c_address=int(str(self.input_dev.i2c_location), 16),
                i2c_bus=self.input_dev.i2c_bus)

    def get_measurement(self):
        """ Gets the Atlas Scientific pressure sensor measurement """
        pressure = None
        self.return_dict = measurements_dict.copy()

        if not self.atlas_device.setup:
            self.logger.error("Sensor not set up")
            return

        if self.led == 'measure':
            self.atlas_device.query('L,1')

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            press_status, press_list = self.atlas_device.query('R')
            if press_list:
                self.logger.debug(
                    "Returned list: {lines}".format(lines=press_list))

            # Find float value in list
            float_value = None
            for each_split in press_list:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in press_list:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                pressure = float(float_value)
                self.logger.debug(
                    'Found float value: {val}'.format(val=pressure))
            else:
                self.logger.error(
                    'Value or "check probe" not found in list: '
                    '{val}'.format(val=press_list))

        elif self.interface == 'I2C':
            pressure_status, pressure_str = self.atlas_device.query('R')
            if pressure_status == 'error':
                self.logger.error(
                    "Sensor read unsuccessful: {err}".format(
                        err=pressure_str))
            elif pressure_status == 'success':
                pressure = float(pressure_str)

        if self.led == 'measure':
            self.atlas_device.query('L,0')

        self.value_set(0, pressure)

        return self.return_dict

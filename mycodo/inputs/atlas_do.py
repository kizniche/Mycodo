# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.system_pi import str_is_float


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
        'measurement': 'dissolved_oxygen',
        'unit': 'mg_L'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_DO',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'DO',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Dissolved Oxygen',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/dissolved-oxygen.html',
    'url_datasheet': 'https://www.atlas-scientific.com/files/DO_EZO_Datasheet.pdf',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'single_input_math',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x66'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '',

    'custom_options': [
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Calibration Max Age'),
            'phrase': lazy_gettext('The Max Age (seconds) of the Input/Math to use for calibration')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor DO"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.atlas_device = None
        self.ftdi_location = None
        self.uart_location = None
        self.i2c_address = None
        self.i2c_bus = None

        # Initialize custom options
        self.max_age = None
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.interface = input_dev.interface
            self.calibrate_sensor_measure = input_dev.calibrate_sensor_measure

            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

            # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
            self.get_measurement()

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
        """ Gets the sensor's DO measurement via UART/I2C """
        do = None
        self.return_dict = measurements_dict.copy()

        if not self.atlas_device.setup:
            return

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            do_status, do_list = self.atlas_device.query('R')
            if do_list:
                self.logger.debug(
                    "Returned list: {lines}".format(lines=do_list))

            # Find float value in list
            float_value = None
            for each_split in do_list:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in do_list:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                do = float(float_value)
                self.logger.debug(
                    'Found float value: {val}'.format(val=do))
            else:
                self.logger.error(
                    'Value or "check probe" not found in list: '
                    '{val}'.format(val=do_list))

        # Read sensor via I2C
        elif self.interface == 'I2C':
            ec_status, ec_str = self.atlas_device.query('R')
            if ec_status == 'error':
                self.logger.error(
                    "Sensor read unsuccessful: {err}".format(
                        err=ec_str))
            elif ec_status == 'success':
                do = float(ec_str)

        self.value_set(0, do)

        return self.return_dict

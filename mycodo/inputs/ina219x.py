# coding=utf-8
# pylint: disable=import-error,super-with-arguments,broad-except

"""
Support for Texas Instruments INA219x devices:
- Adafruit INA219 High Side DC Current Sensor Breakout (Product 904)
"""

import copy
import timeit

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

ADC_OPTIONS = [
    ('00', '(0x00) - 9 Bit / 1 Sample'),
    ('01', '(0x01) - 10 Bit / 1 Sample'),
    ('02', '(0x02) - 11 Bit / 1 Sample'),
    ('03', '(0x03) - 12 Bit / 1 Sample (default)'),
    ('09', '(0x09) - 12 Bit / 2 Samples'),
    ('0A', '(0x0A) - 12 Bit / 4 Samples'),
    ('0B', '(0x0B) - 12 Bit / 8 Samples'),
    ('0C', '(0x0C) - 12 Bit / 16 Samples'),
    ('0D', '(0x0D) - 12 Bit / 32 Samples'),
    ('0E', '(0x0E) - 12 Bit / 64 Samples'),
    ('0F', '(0x0F) - 12 Bit / 128 Samples')
]

def constraints_pass_measurement_repetitions(mod_input, value):
    """
    Check if the Measurement Repetitions is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: integer
    :return: tuple: (bool, errors, mod_input)
    """
    errors = []
    all_passed = True
    # Ensure 1 <= value <= 1000
    if value < 1 or value > 1000:
        all_passed = False
        errors.append("Must be a positive value between 1 and 1000")
    return all_passed, errors, mod_input

def constraints_pass_adc_resolution(mod_input, value):
    """
    Check if the ADC Resolution is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: string
    :return: tuple: (bool, errors, mod_input)
    """
    errors = []
    all_passed = True

    range_pass = [
        '00', '01', '02', '03', '09', '0A', '0B', '0C', '0D', '0E', '0F'
    ]

    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}.".format(range_pass))
    return all_passed, errors, mod_input

def constraints_pass_calibration(mod_input, value):
    """
    Check if the Calibration is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: string
    :return: tuple: (bool, errors, mod_input)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['0','1','2','3']

    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}.".format(range_pass))
    return all_passed, errors, mod_input

def constraints_pass_bus_voltage_range(mod_input, value):
    """
    Check if the Bus Voltage Range is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: string
    :return: tuple: (bool, errors, mod_input)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['0','1']

    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}.".format(range_pass))
    return all_passed, errors, mod_input

# Measurements
measurements_dict = {
    0: {
        'measurement': 'electrical_current',
        'unit': 'mA',
        'name': 'Current (mA)'
    },
    1: {
        'measurement': 'electrical_potential',
        'unit': 'V',
        'name': 'Bus Voltage (V)',
    },
    2: {
        'measurement': 'electrical_potential',
        'unit': 'mV',
        'name': 'Shunt Voltage (mV)',
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'INA219_CP',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'INA219x',
    'input_library': 'Adafruit_CircuitPython',
    'measurements_name': 'Electrical Current (DC)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.ti.com/product/INA219',
    'url_datasheet': 'https://www.ti.com/lit/gpn/ina219',
    'measurements_rescale': True,
    'scale_from_min': 0.0,
    'scale_from_max': 32000.0,

    'options_enabled': [
        'i2c_location',
        'period',
        'pre_output',
        'measurements_select'
    ],
    'options_disabled': ['interface'],

    # adafruit-circuitpython-ina219 also installs adafruit-blinka
    'dependencies_module': [
        ('pip-pypi', 'adafruit_ina219', 'adafruit-circuitpython-ina219'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit_Extended_Bus')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40', '0x41', '0x44', '0x45'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'measurements_for_average',
            'type': 'integer',
            'default_value': 5,
            'name': lazy_gettext('Measurements to Average'),
            'phrase': lazy_gettext(
                'The number of times to measure. An average of the measurements will be stored.'),
            'constraints_pass': constraints_pass_measurement_repetitions
        },
        {
            'id': 'calibration',
            'type': 'select',
            'default_value': '0',
            'options_select': [
                ('0', '32V @ 2A max (default)'),
                ('1', '32V @ 1A max'),
                ('2', '16V @ 400mA max'),
                ('3', '16V @ 5A max')
            ],
            'name': lazy_gettext('Calibration Range'),
            'phrase': lazy_gettext('Set the device calibration range'),
            'constraints_pass': constraints_pass_calibration
        },
        {
            'id': 'bus_voltage_range',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('0', '(0x00) - 16V'),
                ('1', '(0x01) - 32V (default)')
            ],
            'name': lazy_gettext('Bus Voltage Range'),
            'phrase': lazy_gettext('Set the bus voltage range'),
            'constraints_pass': constraints_pass_bus_voltage_range
        },
        {
            'id': 'bus_adc_resolution',
            'type': 'select',
            'default_value': '03',
            'options_select': ADC_OPTIONS,
            'name': lazy_gettext('Bus ADC Resolution'),
            'phrase': lazy_gettext('Set the Bus ADC Resolution.'),
            'constraints_pass': constraints_pass_adc_resolution
        },
        {
            'id': 'shunt_adc_resolution',
            'type': 'select',
            'default_value': '03',
            'options_select': ADC_OPTIONS,
            'name': lazy_gettext('Shunt ADC Resolution'),
            'phrase': lazy_gettext('Set the Shunt ADC Resolution.'),
            'constraints_pass': constraints_pass_adc_resolution
        }
    ]
}

class InputModule(AbstractInput):
    """
    INA219x sensor module
    """
    def __init__(self, input_dev, testing=False,):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.calibration = None
        self.bus_voltage_range = None
        self.bus_adc_resolution = None
        self.shunt_adc_resolution = None
        self.measurements_for_average = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        """
        Initialize INA219x sensor
        """
        from adafruit_ina219 import INA219, ADCResolution, BusVoltageRange
        from adafruit_extended_bus import ExtendedI2C

        try:
            self.sensor = INA219(ExtendedI2C(self.input_dev.i2c_bus),
                addr=int(str(self.input_dev.i2c_location), 16))
        except (ValueError, OSError) as msg:
            self.logger.exception("INA219x Exception: %s", msg)
            return None

        if not self.sensor:
            self.logger.error("INA219x sensor unable to initialize.")
            return None

        self.measurements_for_average = self.measurements_for_average

        # calibrate voltage and current detection range
        if self.calibration   == '1':
            self.sensor.set_calibration_32V_1A()
            self.logger.debug("INA219x: set_calibration_32V_1A()")
        elif self.calibration == '2':
            self.sensor.set_calibration_16V_400mA()
            self.logger.debug("INA219x: set_calibration_16V_400mA()")
        elif self.calibration == '3':
            self.sensor.set_calibration_16V_5A()
            self.logger.debug("INA219x: set_calibration_16V_5A()")
        else:
            # use default sensor calibration of 32V / 2A
            self.sensor.set_calibration_32V_2A()
            self.logger.debug("INA219x: set_calibration_32V_2A()")

        BUS_VOLTAGE_RANGE = {
            '0': BusVoltageRange.RANGE_16V,
            '1': BusVoltageRange.RANGE_32V
        }

        # calibrate sensor bus voltage range
        self.sensor.bus_voltage_range = BUS_VOLTAGE_RANGE.get(
            self.bus_voltage_range, BUS_VOLTAGE_RANGE['1'])

        ADC_RESOLUTION = {
            '00': ADCResolution.ADCRES_9BIT_1S,
            '01': ADCResolution.ADCRES_10BIT_1S,
            '02': ADCResolution.ADCRES_11BIT_1S,
            '03': ADCResolution.ADCRES_12BIT_1S,
            '09': ADCResolution.ADCRES_12BIT_2S,
            '0A': ADCResolution.ADCRES_12BIT_4S,
            '0B': ADCResolution.ADCRES_12BIT_8S,
            '0C': ADCResolution.ADCRES_12BIT_16S,
            '0D': ADCResolution.ADCRES_12BIT_32S,
            '0E': ADCResolution.ADCRES_12BIT_64S,
            '0F': ADCResolution.ADCRES_12BIT_128S
        }

        # calibrate sensor ADC resolutions
        self.sensor.bus_adc_resolution = ADC_RESOLUTION.get(
            self.bus_adc_resolution, ADC_RESOLUTION['03'])
        self.sensor.shunt_adc_resolution = ADC_RESOLUTION.get(
            self.shunt_adc_resolution, ADC_RESOLUTION['03'])

    def get_measurement(self):
        """
        Read INA219x sensor values (current, bus voltage, shunt voltage)
        """

        if not self.sensor:
            self.logger.error("INA219x sensor not set up.")
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        measurement_range = 1
        if self.measurements_for_average:
            measurement_range = self.measurements_for_average

        # Conduct multiple measurements for averaging
        measurement_totals = {'current':0, 'bus_v':0, 'shunt_v':0}

        time_start = timeit.default_timer()
        for j in range(measurement_range):
            current = bus_v = shunt_v = 0

            try:
                current = self.sensor.current
                bus_v   = self.sensor.bus_voltage
                shunt_v = self.sensor.shunt_voltage * 1000.0 # we want to return mV, not V
            except Exception as msg:
                self.logger.exception("Input read failure: %s", msg)

            self.logger.debug("[reading %d] Current (mA): %.3f, Bus Voltage (V): %.3f, Shunt Voltage (mV): %.3f",
                j, current, bus_v, shunt_v
                )

            # accumulate readings
            measurement_totals['current'] += current
            measurement_totals['bus_v']   += bus_v
            measurement_totals['shunt_v'] += shunt_v

        self.logger.debug("%d measurement(s) completed in %.3f seconds",
            measurement_range, (timeit.default_timer() - time_start))
        self.logger.debug("[avg] Current (mA): %.3f, Bus Voltage (V): %.3f, Shunt Voltage (mV): %.3f",
            measurement_totals['current'] / measurement_range,
            measurement_totals['bus_v'] / measurement_range,
            measurement_totals['shunt_v'] / measurement_range
            )

        # set values
        if self.is_enabled(0):
            self.value_set(0, measurement_totals['current'] / measurement_range)
        if self.is_enabled(1):
            self.value_set(1, measurement_totals['bus_v'] / measurement_range)
        if self.is_enabled(2):
            self.value_set(2, measurement_totals['shunt_v'] / measurement_range)

        return self.return_dict

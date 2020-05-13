# coding=utf-8
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.system_pi import str_is_float


def constraints_pass_rate(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['h', 'm', 's']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


def constraints_pass_meter_type(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['3/8', '1/4', '1/2', '3/4', 'non-atlas']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


def constraints_pass_resistor(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['atlas', '0', '1', '-1', '10', '-10', '100', '-100']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


def constraints_pass_custom_k_value_time_base(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['disabled', 'h', 'm', 's']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'volume',
        'unit': 'l'
    },
    1: {
        'measurement': 'rate_volume',
        'unit': 'l_min'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_FLOW',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Flow Meter',
    'measurements_name': 'Total Volume, Flow Rate',
    'measurements_dict': measurements_dict,

    'message': 'Note: Set the Measurement Time Base to a value most appropriate for your anticipated flow (it will affect accuracy). This flow rate time base that is set and returned from the sensor will be converted to liters per minute, which is the default unit for this input module. If you desire a different rate to be stored in the database (such as liters per second or hour), then use the Convert to Unit option.',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'measurements_select',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x68'],
    'i2c_address_editable': True,
    'ftdi_location': '/dev/ttyUSB0',
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'flow_meter_type',
            'type': 'select',
            'default_value': '3/8',
            'options_select': [
                ('3/8', 'Atlas Scientific 3/8" Flow Meter'),
                ('1/4', 'Atlas Scientific 1/4" Flow Meter'),
                ('1/2', 'Atlas Scientific 1/2" Flow Meter'),
                ('3/4', 'Atlas Scientific 3/4" Flow Meter'),
                ('non-atlas', 'Non-Atlas Scientific Flow Meter')
            ],
            'constraints_pass': constraints_pass_meter_type,
            'name': lazy_gettext('Flow Meter Type'),
            'phrase': lazy_gettext('Set the type of flow meter used')
        },
        {
            'id': 'flow_rate_unit',
            'type': 'select',
            'default_value': 'm',
            'options_select': [
                ('s', 'Liters per Second'),
                ('m', 'Liters per Minute'),
                ('h', 'Liters per Hour')
            ],
            'constraints_pass': constraints_pass_rate,
            'name': lazy_gettext('Atlas Meter Time Base'),
            'phrase': lazy_gettext('If using an Atlas Scientific flow meter, set the flow rate/time base')
        },
        {
            'id': 'internal_resistor',
            'type': 'select',
            'default_value': 'atlas',
            'options_select': [
                ('atlas', 'Use Atlas Scientific Flow Meter'),
                ('0', 'Disable Internal Resistor'),
                ('1', '1 K Ω Pull-Up'),
                ('-1', '1 K Ω Pull-Down'),
                ('10', '10 K Ω Pull-Up'),
                ('-10', '10 K Ω Pull-Down'),
                ('100', '100 K Ω Pull-Up'),
                ('-100', '100 K Ω Pull-Down')
            ],
            'constraints_pass': constraints_pass_resistor,
            'name': lazy_gettext('Internal Resistor'),
            'phrase': lazy_gettext('Set an internal resistor for the flow meter')
        },
        {
            'id': 'custom_k_values',
            'type': 'text',
            'default_value': '',
            'name': lazy_gettext('Custom K Value(s)'),
            'phrase': lazy_gettext("If using a non-Atlas Scientific flow meter, enter the meter's K value(s). For a single K value, enter '[volume per pulse],[number of pulses]'. For multiple K values (up to 16), enter '[volume at frequency],[frequency in Hz];[volume at frequency],[frequency in Hz];...'. Leave blank to disable.")
        },
        {
            'id': 'custom_k_value_time_base',
            'type': 'select',
            'default_value': 'disabled',
            'options_select': [
                ('disabled', 'Use Atlas Scientific Flow Meter'),
                ('s', 'Liters per Second'),
                ('m', 'Liters per Minute'),
                ('h', 'Liters per Hour')
            ],
            'constraints_pass': constraints_pass_custom_k_value_time_base,
            'name': lazy_gettext('K Value Time Base'),
            'phrase': lazy_gettext('If using a non-Atlas Scientific flow meter, set the flow rate/time base for the custom K values entered.')
        },
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor ElectricalConductivity"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.atlas_sensor = None
        self.sensor_is_measuring = False
        self.sensor_is_clearing = False

        # Initialize custom options
        self.flow_meter_type = None
        self.flow_rate_unit = None
        self.internal_resistor = None
        self.custom_k_values = None
        self.custom_k_value_time_base = None
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.input_dev = input_dev
            self.interface = input_dev.interface

            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

    def initialize_sensor(self):
        from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        if self.interface == 'FTDI':
            self.ftdi_location = self.input_dev.ftdi_location
            self.atlas_sensor = AtlasScientificFTDI(self.ftdi_location)
        elif self.interface == 'UART':
            self.uart_location = self.input_dev.uart_location
            self.atlas_sensor = AtlasScientificUART(self.uart_location)
        elif self.interface == 'I2C':
            self.i2c_address = int(str(self.input_dev.i2c_location), 16)
            self.i2c_bus = self.input_dev.i2c_bus
            self.atlas_sensor = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)

        if self.is_enabled(0):
            self.atlas_sensor.query('O,TV,1')
            self.logger.debug("Enabling Total Volume measurement")
        else:
            self.atlas_sensor.query('O,TV,0')
            self.logger.debug("Disabling Total Volume measurement")

        if self.is_enabled(1):
            self.atlas_sensor.query('O,FR,1')
            self.logger.debug("Enabling Flow Rate measurement")
        else:
            self.atlas_sensor.query('O,FR,0')
            self.logger.debug("Disabling Flow Rate measurement")

        if self.flow_meter_type:
            if self.flow_meter_type == 'non-atlas':
                if ';' in self.custom_k_values:
                    list_k_values = self.custom_k_values.split(';')
                    self.atlas_sensor.query('K,clear')
                    self.logger.debug("Cleared K Values")
                    for each_k in list_k_values:
                        if ',' in each_k:
                            self.atlas_sensor.query('K,{}'.format(each_k))
                            self.logger.debug("Set K Value: {}".format(each_k))
                        else:
                            self.logger.error(
                                "Improperly-formatted K-value: {}".format(
                                    each_k))
                elif ',' in self.custom_k_values:
                    self.atlas_sensor.query('K,clear')
                    self.logger.debug("Cleared K Values")
                    self.atlas_sensor.query('K,{}'.format(
                        self.custom_k_values))
                    self.logger.debug("Set K Value: {}".format(
                        self.custom_k_values))
                else:
                    self.logger.error(
                        "Improperly-formatted K-value: {}".format(
                            self.custom_k_values))
                self.atlas_sensor.query('Vp,{}'.format(
                    self.custom_k_value_time_base))
                self.logger.debug("Set Custom Time Base: {}".format(
                    self.custom_k_value_time_base))
            else:
                self.atlas_sensor.query('Set,{}'.format(
                    self.flow_meter_type))
                self.logger.debug("Set Flow Meter: {}".format(
                    self.flow_meter_type))

        if self.flow_rate_unit:
            self.atlas_sensor.query('Frp,{}'.format(
                self.flow_rate_unit))
            self.logger.debug("Set Flow Rate: l/{}".format(
                self.flow_rate_unit))

        if self.internal_resistor and self.internal_resistor != 'atlas':
            self.atlas_sensor.query('P,{}'.format(
                int(self.internal_resistor)))
            if self.internal_resistor == '0':
                self.logger.debug("Internal Resistor disabled")
            else:
                self.logger.debug("Internal Resistor set: {} K".format(
                    self.internal_resistor))

    def get_measurement(self):
        """ Gets the sensor's Electrical Conductivity measurement via UART/I2C """
        return_string = None
        self.return_dict = measurements_dict.copy()

        while self.sensor_is_clearing:
            time.sleep(0.1)
        self.sensor_is_measuring = True

        # Read sensor via FTDI
        if self.interface == 'FTDI':
            if self.atlas_sensor.setup:
                lines = self.atlas_sensor.query('R')
                if lines:
                    self.logger.debug(
                        "All Lines: {lines}".format(lines=lines))

                    # 'check probe' indicates an error reading the sensor
                    if 'check probe' in lines:
                        self.logger.error(
                            '"check probe" returned from sensor')
                    # if a string resembling a float value is returned, this
                    # is out measurement value
                    elif str_is_float(lines[0]):
                        return_string = lines[0]
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=return_string))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            return_string = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            return_string = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=return_string))
            else:
                self.logger.error('FTDI device is not set up.'
                                  'Check the log for errors.')

        # Read sensor via UART
        elif self.interface == 'UART':
            if self.atlas_sensor.setup:
                lines = self.atlas_sensor.query('R')
                if lines:
                    self.logger.debug(
                        "All Lines: {lines}".format(lines=lines))

                    # 'check probe' indicates an error reading the sensor
                    if 'check probe' in lines:
                        self.logger.error(
                            '"check probe" returned from sensor')
                    # if a string resembling a float value is returned, this
                    # is out measurement value
                    elif str_is_float(lines[0]):
                        return_string = lines[0]
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=return_string))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            return_string = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            return_string = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=return_string))
            else:
                self.logger.error('UART device is not set up.'
                                  'Check the log for errors.')

        # Read sensor via I2C
        elif self.interface == 'I2C':
            if self.atlas_sensor.setup:
                return_status, return_string = self.atlas_sensor.query('R')
                if return_status == 'error':
                    self.logger.error(
                        "Sensor read unsuccessful: {err}".format(
                            err=return_string))
                elif return_status == 'success':
                    return_string = return_string
            else:
                self.logger.error(
                    'I2C device is not set up. Check the log for errors.')

        self.sensor_is_measuring = False

        self.logger.debug("Raw Return String: {}".format(return_string))
        total_volume = None
        flow_rate_raw = None
        flow_rate = None

        if self.is_enabled(0) and self.is_enabled(1):
            return_list = return_string.split(',')
            total_volume = float(return_list[0])
            flow_rate_raw = float(return_list[1])
            flow_rate = self.convert_to_l_m(flow_rate_raw)
            self.value_set(0, total_volume)
            self.value_set(1, flow_rate)
        elif self.is_enabled(0) and not self.is_enabled(1):
            total_volume = float(return_string)
            self.value_set(0, total_volume)
        elif not self.is_enabled(0) and self.is_enabled(1):
            flow_rate_raw = float(return_string)
            flow_rate = self.convert_to_l_m(flow_rate_raw)
            self.value_set(1, flow_rate)

        if total_volume is not None:
            self.logger.debug("Total Volume: {} l".format(total_volume))
        if flow_rate_raw is not None:
            self.logger.debug("Flow Rate (from sensor): {:.5f} l/{}".format(flow_rate_raw, self.flow_rate_unit))
        if flow_rate is not None:
            self.logger.debug("Flow Rate (converted to l/m): {:.5f} l/m".format(flow_rate))

        return self.return_dict

    def clear_total_volume(self):
        while self.sensor_is_measuring:
            time.sleep(0.1)
        self.sensor_is_clearing = True
        self.logger.debug("Clearing total volume")
        return_status, return_string = self.atlas_sensor.query('Clear')
        self.sensor_is_clearing = False
        if return_status == 'error':
            return 1, "Error: {}".format(return_string)
        elif return_status == 'success':
            return 0, "Success"

    def convert_to_l_m(self, amount):
        if (self.custom_k_value_time_base and
                self.custom_k_value_time_base != 'disabled'):
            # Custom K values used for non-Atlas Scientific meter
            # use the custom time base
            time_base_unit = self.custom_k_value_time_base
        else:
            # Use time base set for Atlas Scientific meter
            time_base_unit = self.flow_rate_unit

        if time_base_unit == 'h':
            return amount / 60
        elif time_base_unit == 'm':
            return amount
        elif time_base_unit == 's':
            return amount * 60

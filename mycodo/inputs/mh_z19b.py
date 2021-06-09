# coding=utf-8
import time

import copy

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
    'input_name_unique': 'MH_Z19B',
    'input_manufacturer': 'Winsen',
    'input_name': 'MH-Z19B',
    'input_library': 'serial',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.winsen-sensor.com/sensors/co2-sensor/mh-z19b.html',
    'url_datasheet': 'https://www.winsen-sensor.com/d/files/MH-Z19B.pdf',

    'message': 'This is the B version of the sensor that includes the ability to conduct '
               'automatic baseline correction (ABC).',

    'options_enabled': [
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
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
            'name': 'Automatic Baseline Correction',
            'phrase': 'Enable automatic baseline correction (ABC)'
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
            'name': 'Measurement Range',
            'phrase': 'Set the measuring range of the sensor'
        }
    ],

    'custom_actions_message': 'Zero point calibration: activate the sensor in a 400 ppmv CO2 environment, allow to run '
                              'for 20 minutes, then press the Calibrate Zero Point button.<br>Span point calibration: '
                              'activate the sensor in an environment with a stable CO2 concentration in the 1000 to '
                              '2000 ppmv range, allow to run for 20 minutes, enter the ppmv value in the Span Point '
                              '(ppmv) input field, then press the Calibrate Span Point button. If running a span '
                              'point calibration, run a zero point calibration first.',
    'custom_actions': [
        {
            'id': 'calibrate_zero_point',
            'type': 'button',
            'name': 'Calibrate Zero Point'
        },
        {
            'id': 'span_point_value_ppmv',
            'type': 'integer',
            'default_value': 1500,
            'name': 'Span Point (ppmv)',
            'phrase': 'The ppmv concentration for a span point calibration'
        },
        {
            'id': 'calibrate_span_point',
            'type': 'button',
            'name': 'Calibrate Span Point'
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the MH-Z19's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.ser = None
        self.measuring = None
        self.calibrating = None

        self.measure_range = None
        self.abc_enable = False

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import serial

        if is_device(self.input_dev.uart_location):
            try:
                self.ser = serial.Serial(
                    port=self.input_dev.uart_location,
                    baudrate=self.input_dev.baud_rate,
                    timeout=1,
                    writeTimeout=5)
            except serial.SerialException:
                self.logger.exception('Opening serial')
        else:
            self.logger.error('Could not open "{dev}". Check the device location is correct.'.format(
                dev=self.input_dev.uart_location))

        if self.abc_enable:
            self.abcon()
        else:
            self.abcoff()

        if self.measure_range:
            self.set_measure_range(self.measure_range)

        time.sleep(0.1)

    def get_measurement(self):
        """ Gets the MH-Z19's CO2 concentration in ppmv """
        if not self.ser:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        while self.calibrating:
            time.sleep(0.1)
        self.measuring = True

        try:
            self.ser.flushInput()
            self.ser.write(bytearray([0xff, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]))
            time.sleep(.01)
            resp = self.ser.read(9)

            if not resp:
                self.logger.debug("No response")
            elif len(resp) < 4:
                self.logger.debug("Too few values in response '{}'".format(resp))
            elif resp[0] != 0xff or resp[1] != 0x86:
                self.logger.error("Bad checksum")
            elif len(resp) >= 4:
                high = resp[2]
                low = resp[3]
                co2 = (high * 256) + low
                self.value_set(0, co2)
        except:
            self.logger.exception("get_measurement()")
        finally:
            self.measuring = False

        return self.return_dict

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

    def calibrate_span_point(self, args_dict):
        """
        Span Point Calibration
        from https://github.com/UedaTakeyuki/mh-z19
        """
        if 'span_point_value_ppmv' not in args_dict:
            self.logger.error("Cannot conduct span point calibration without a ppmv value")
            return
        if not isinstance(args_dict['span_point_value_ppmv'], int):
            self.logger.error("ppmv value does not represent an integer: '{}', type: {}".format(
                args_dict['span_point_value_ppmv'], type(args_dict['span_point_value_ppmv'])))
            return

        while self.measuring:
            time.sleep(0.1)
        self.calibrating = True

        try:
            self.logger.info("Conducting span point calibration with a value of {} ppmv".format(
                args_dict['span_point_value_ppmv']))
            b3 = args_dict['span_point_value_ppmv'] // 256
            b4 = args_dict['span_point_value_ppmv'] % 256
            c = self.checksum([0x01, 0x88, b3, b4])
            self.ser.write(bytearray([0xff, 0x01, 0x88, b3, b4, 0x00, 0x0b, 0xb8, c]))
            time.sleep(0.1)
        except:
            self.logger.exception()
        finally:
            self.calibrating = False
        # byte3 = struct.pack('B', b3)
        # byte4 = struct.pack('B', b4)
        # request = b"\xff\x01\x88" + byte3 + byte4 + b"\x00\x00\x00" + c
        # self.ser.write(request)

    def calibrate_zero_point(self, args_dict):
        """
        Zero Point Calibration
        from https://github.com/UedaTakeyuki/mh-z19
        """
        while self.measuring:
            time.sleep(0.1)
        self.calibrating = True

        try:
            self.logger.info("Conducting zero point calibration")
            self.ser.write(bytearray([0xff, 0x01, 0x87, 0x00, 0x00, 0x00, 0x00, 0x00, 0x78]))
            time.sleep(0.1)
        except:
            self.logger.exception()
        finally:
            self.calibrating = False
        # request = b"\xff\x01\x87\x00\x00\x00\x00\x00\x78"
        # self.ser.write(request)

    @staticmethod
    def checksum(array):
        return 0xff - (sum(array) % 0x100) + 1
        # return struct.pack('B', 0xff - (sum(array) % 0x100) + 1)

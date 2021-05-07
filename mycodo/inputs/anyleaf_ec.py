# coding=utf-8
import copy

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_value

# todo: This does not yet include temperature compensation
# todo or calibration

# Measurements
measurements_dict = {
    0: {
        'measurement': 'electrical_conductivity',
        'unit': 'uS_cm'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ANYLEAF_EC',
    'input_manufacturer': 'AnyLeaf',
    'input_name': 'AnyLeaf EC',
    'input_library': 'anyleaf',
    'measurements_name': 'Electrical Conductivity',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.anyleaf.org/ec-module',
    'url_datasheet': 'https://www.anyleaf.org/static/ec-module-datasheet.pdf',

    'options_enabled': [
        'uart_location',
        'period',
    ],
    'options_disabled': [],

    'dependencies_module': [
        # These aren't explicitly required for ec measurements,
        # but are required by the multi-sensor`AnyLeaf` module.
        ('apt', 'python3-numpy', 'python3-numpy'),
        ('apt', 'python3-scipy', 'python3-scipy'),
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.1'),
        ('pip-pypi', 'anyleaf', 'anyleaf')
    ],

    'interfaces': ['UART'],
    'uart_location': '/dev/serial0',
    'uart_baud_rate': 9600,

    'custom_options': [
        # todo: Look at this once you implement calibration.
        # {
        #     'id': 'cal_v',
        #     'type': 'float',
        #     'default_value': 0.4,
        #     'name': "{}: {} ({})".format(lazy_gettext('Calibrate'), lazy_gettext('Voltage'), lazy_gettext('Internal')),
        #     'phrase': 'Calibration data: internal voltage'
        # },
        # {
        #     'id': 'cal_orp',
        #     'type': 'float',
        #     'default_value': 400.0,
        #     'name': "{}: {} ({})".format(lazy_gettext('Calibrate'), lazy_gettext('ORP'), lazy_gettext('Internal')),
        #     'phrase': 'Calibration data: internal ORP'
        # },
        {
            'id': 'K',
            'type': 'float',
            'default_value': 1.0,
            'name': "{}".format(lazy_gettext('K')),  # todo: What should this be?
            'phrase': 'Conductivity constant K',
        }
        # {
        #     'id': 'temperature_comp_meas',
        #     'type': 'select_measurement',
        #     'default_value': '',
        #     'options_select': [
        #         'Input',
        #         'Math'
        #     ],
        #     'name': "{}: {}".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Measurement')),
        #     'phrase': lazy_gettext('Select a measurement for temperature compensation')
        # },
        # {
        #     'id': 'max_age',
        #     'type': 'integer',
        #     'default_value': 120,
        #     'required': True,
        #     'constraints_pass': constraints_pass_positive_value,
        #     'name': "{}: {}".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Max Age')),
        #     'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use for temperature compensation')
        # }
    ],
    'custom_actions_message': """""",
    'custom_actions': [
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor conductivity (EC)"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        from anyleaf import EcSensor

        if self.get_custom_option("K"):
            k = self.get_custom_option("K")
        else:
            k = 1.0

        self.sensor = EcSensor(K=k)


    # todo: Implement calibration procedure here.
    # def calibrate(self, args_dict):
    #     """ Auto-calibrate """
    #     if 'calibration_orp' not in args_dict:
    #         self.logger.error("Cannot conduct calibration without a buffer ORP value")
    #         return
    #     if not isinstance(args_dict['calibration_orp'], float) and not isinstance(args_dict['calibration_orp'], int):
    #         self.logger.error("buffer value does not represent a number: '{}', type: {}".format(
    #             args_dict['calibration_orp'], type(args_dict['calibration_orp'])))
    #         return
    #
    #     v = self.sensor.calibrate(args_dict['calibration_orp'])  # For this session
    #
    #     # For future sessions
    #     self.set_custom_option("cal_orp", args_dict['calibration_orp'])
    #     self.set_custom_option("cal_v", v)

    def get_measurement(self):
        """ Gets the measurement """
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        # todo: Adjust this line once you've added temperature compensation.
        # self.value_set(0, self.sensor.read(OnBoard()))
        self.value_set(0, self.sensor.read())

        return self.return_dict

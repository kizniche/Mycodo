# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

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
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libjpeg-dev', 'libjpeg-dev'),
        ('apt', 'zlib1g-dev', 'zlib1g-dev'),
        ('pip-pypi', 'PIL', 'Pillow==8.1.2'),
        ('pip-pypi', 'scipy', 'scipy==1.8.0'),
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'anyleaf', 'anyleaf==0.1.9')
    ],

    'interfaces': ['UART'],
    'uart_location': '/dev/serial0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'constant_k',
            'type': 'float',
            'default_value': 1.0,
            'name': "Conductivity Constant",
            'phrase': 'Conductivity constant K',
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor conductivity (EC)"""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.constant_k = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from anyleaf import EcSensor

        self.sensor = EcSensor(K=self.constant_k)

    def get_measurement(self):
        """Gets the measurement."""
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        # todo: Adjust this line once you've added temperature compensation.
        # self.value_set(0, self.sensor.read(OnBoard()))
        self.value_set(0, self.sensor.read())

        return self.return_dict

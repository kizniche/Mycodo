# coding=utf-8
import logging
import time

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Channels
channels = {}
for each_channel in range(4):
    channels[each_channel] = {}

# Measurements
measurements = {
    'electrical_potential': {
        'V': channels
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP342x',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP342x',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements,
    'measurements_convert_enabled': True,
    'measurements_rescale': True,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'measurements_convert',
        'adc_gain',
        'adc_resolution',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2'),
        ('pip-pypi', 'MCP342x', 'MCP342x==0.3.3')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x68',
        '0x6A',
        '0x6C',
        '0x6E',
        '0x6F'
    ],
    'i2c_address_editable': False,

    'adc_gain': [
        (1, '1'),
        (2, '2'),
        (4, '4'),
        (8, '8')
    ],
    'adc_resolution': [
        (12, '12'),
        (14, '14'),
        (16, '16'),
        (18, '18')
    ]
}


class InputModule(AbstractInput):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger('mycodo.mcp342x')
        self.acquiring_measurement = False
        self._measurements = None

        self.i2c_address = int(str(input_dev.i2c_location), 16)
        self.i2c_bus = input_dev.i2c_bus
        self.adc_gain = input_dev.adc_gain
        self.adc_resolution = input_dev.adc_resolution

        if not testing:
            from smbus2 import SMBus
            from MCP342x import MCP342x
            self.logger = logging.getLogger(
                'mycodo.mcp342x_{id}'.format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id).all()

            self.MCP342x = MCP342x
            self.bus = SMBus(self.i2c_bus)

    def get_measurement(self):
        self._measurements = None

        return_dict = {
            'electrical_potential': {
                'V': {}
            }
        }

        # for each_measure in self.input_measurements:
        #     if each_measure.is_enabled:
        #         adc = self.MCP342x(self.bus,
        #                            self.i2c_address,
        #                            channel=each_measure.channel,
        #                            gain=self.adc_gain,
        #                            resolution=self.adc_resolution)
        #         return_dict['electrical_potential']['V'][each_measure.channel] = adc.convert_and_read()

        # Dummy data for testing
        import random
        for _ in range(4):
            return_dict['electrical_potential']['V'][0] = random.uniform(1.5, 1.9)
            return_dict['electrical_potential']['V'][1] = random.uniform(2.3, 2.5)
            return_dict['electrical_potential']['V'][2] = random.uniform(0.5, 0.6)
            return_dict['electrical_potential']['V'][3] = random.uniform(3.5, 6.2)

        if return_dict['electrical_potential']['V']:
            return return_dict


if __name__ == "__main__":
    class Data:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    settings = Data(id='00001',
                    unique_id='asdf-ghjk',
                    i2c_address='0x68',
                    i2c_bus=1,
                    channels=4,
                    measurements_selected='0,1,2,3',
                    gain=1,
                    resolution=12)

    mcp = ADCModule(settings)

    while 1:
        print("Voltages: {}".format(mcp.next()))
        time.sleep(1)

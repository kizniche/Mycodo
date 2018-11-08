# coding=utf-8
import logging

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
    'input_name_unique': 'ADS1x15',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1x15',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements,
    'measurements_convert_enabled': True,
    'measurements_rescale': True,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096,

    'options_enabled': [
        'measurements_select',
        'channels_convert',
        'adc_gain',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-pypi', 'Adafruit_ADS1x15', 'Adafruit_ADS1x15')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49', '0x4A', '0x4B'],
    'i2c_address_editable': False,

    'adc_gain': [(1, '1'),
                 (2, '2'),
                 (3, '3'),
                 (4, '4'),
                 (8, '8'),
                 (16, '16')]
}


class InputModule(AbstractInput):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger('mycodo.ads1x15')
        self._measurements = None

        if not testing:
            import Adafruit_ADS1x15
            self.logger = logging.getLogger(
                'mycodo.ads1x15_{id}'.format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.adc_gain = input_dev.adc_gain
            self.adc = Adafruit_ADS1x15.ADS1115(address=self.i2c_address,
                                                busnum=self.i2c_bus)

        # Choose a gain of 1 for reading measurements from 0 to 4.09V.
        # Or pick a different gain to change the range of measurements that are read:
        #  - 2/3 = +/-6.144V
        #  -   1 = +/-4.096V
        #  -   2 = +/-2.048V
        #  -   4 = +/-1.024V
        #  -   8 = +/-0.512V
        #  -  16 = +/-0.256V
        # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
        self.running = True

    def get_measurement(self):
        self._measurements = None

        return_dict = {
            'electrical_potential': {
                'V': {}
            }
        }

        for each_measure in self.input_measurements.all():
            if each_measure.is_enabled:
                return_dict['electrical_potential']['V'][each_measure.channel] = self.adc.read_adc(
                    each_measure.channel, gain=self.adc_gain) / 10000.0

        if return_dict['electrical_potential']['V']:
            return return_dict


if __name__ == "__main__":
    from types import SimpleNamespace
    settings = SimpleNamespace()
    settings.id = 1
    settings.location = '0x48'
    settings.i2c_bus = 1
    settings.adc_gain = 1
    settings.channels = 4
    settings.measurements_selected = '0,1,2,3'

    ads = InputModule(settings)
    print("Voltages: {}".format(ads.next()))

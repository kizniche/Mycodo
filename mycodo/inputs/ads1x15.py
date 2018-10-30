# coding=utf-8
import logging

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADS1x15',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1x15',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': ['channel_{}'.format(i) for i in range(4)],  # 4 Channels
    'channels': 4,
    'options_enabled': [
        'measurements_select',
        'channels_convert',
        'adc_gain',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'measurements_convert_enabled': True,
    'channels_measurement': 'electrical_potential',
    'channels_unit': 'V',
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
                 (16, '16')],
    'scale_from_min': -4.096,
    'scale_from_max': 4.096
}


class ChannelModule(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.ads1x15')
        self.acquiring_measurement = False
        self._voltages = None

        self.i2c_address = int(str(input_dev.location), 16)
        self.i2c_bus = input_dev.i2c_bus
        self.adc_gain = input_dev.adc_gain
        self.channels = input_dev.channels

        self.measurements_selected = []
        for each_channel in input_dev.measurements_selected.split(','):
            self.measurements_selected.append(int(each_channel))

        if not testing:
            import Adafruit_ADS1x15
            self.logger = logging.getLogger(
                'mycodo.ads1x15_{id}'.format(id=input_dev.unique_id.split('-')[0]))
            self.adc = Adafruit_ADS1x15.ADS1115(address=self.i2c_address,
                                                busnum=self.i2c_bus)

        # Choose a gain of 1 for reading voltages from 0 to 4.09V.
        # Or pick a different gain to change the range of voltages that are read:
        #  - 2/3 = +/-6.144V
        #  -   1 = +/-4.096V
        #  -   2 = +/-2.048V
        #  -   4 = +/-1.024V
        #  -   8 = +/-0.512V
        #  -  16 = +/-0.256V
        # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
        self.running = True

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return voltage information.
        """
        if self.read():
            return None
        return self._voltages

    @property
    def voltages(self):
        return self._voltages

    def get_measurement(self):
        self._voltages = None
        voltages_dict = {}

        for each_channel in self.measurements_selected:
            voltages_dict['channel_{}'.format(each_channel)] = self.adc.read_adc(
                each_channel, gain=self.adc_gain) / 10000.0

        if voltages_dict:
            return voltages_dict

    def read(self):
        """
        Takes a reading

        :returns: None on success or 1 on error
        """
        if self.acquiring_measurement:
            self.logger.error("Attempting to acquire a measurement when a"
                              " measurement is already being acquired.")
            return 1
        try:
            self.acquiring_measurement = True
            self._voltages = self.get_measurement()
            if self._voltages:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        finally:
            self.acquiring_measurement = False
        return 1

    def stop_sensor(self):
        self.running = False


if __name__ == "__main__":
    from types import SimpleNamespace
    settings = SimpleNamespace()
    settings.id = 1
    settings.location = '0x48'
    settings.i2c_bus = 1
    settings.adc_gain = 1
    settings.channels = 4
    settings.measurements_selected = '0,1,2,3'

    ads = ADCModule(settings)
    print("Voltages: {}".format(ads.next()))

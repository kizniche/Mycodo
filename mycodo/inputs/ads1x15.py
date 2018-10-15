# coding=utf-8
import logging

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADS1x15',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1x15',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_list': ['voltage'],
    'options_enabled': ['adc_channel', 'adc_gain', 'adc_options', 'period', 'pre_output'],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_ADS1x15', 'Adafruit_ADS1x15'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49', '0x4A', '0x4B'],
    'i2c_address_editable': False,
    'analog_to_digital_converter': True,
    'adc_channel': [(0, 'Channel 0'),
                    (1, 'Channel 1'),
                    (2, 'Channel 2'),
                    (3, 'Channel 3')],
    'adc_gain': [(1, '1'),
                 (2, '2'),
                 (3, '3'),
                 (4, '4'),
                 (8, '8'),
                 (16, '16')],
    'adc_volts_min': -4.096,
    'adc_volts_max': 4.096
}


class ADCModule(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.ads1x15')
        self.acquiring_measurement = False
        self._voltage = None

        self.i2c_address = int(str(input_dev.location), 16)
        self.i2c_bus = input_dev.i2c_bus
        self.adc_gain = input_dev.adc_gain
        self.adc_channel = input_dev.adc_channel

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
        return dict(voltage=float('{0:.4f}'.format(self._voltage)))

    @property
    def voltage(self):
        return self._voltage

    def get_measurement(self):
        self._voltage = None
        voltage = self.adc.read_adc(
            self.adc_channel, gain=self.adc_gain) / 10000.0
        return voltage

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
            self._voltage = self.get_measurement()
            if self._voltage is not None:
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
    input_dev = SimpleNamespace()
    input_dev.id = 1
    input_dev.location = '0x48'
    input_dev.i2c_bus = 1
    input_dev.adc_gain = 1
    input_dev.adc_channel = 1

    ads = ADS1x15Read(input_dev)
    print("Channel 0: {}".format(ads.next()))
    ads = ADS1x15Read(input_dev)
    print("Channel 1: {}".format(ads.next()))
    ads = ADS1x15Read(input_dev)
    print("Channel 2: {}".format(ads.next()))
    ads = ADS1x15Read(input_dev)
    print("Channel 3: {}".format(ads.next()))

# coding=utf-8
import logging

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADS1256',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1256',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_list': ['voltage'],
    'options_enabled': ['adc_channel', 'adc_gain', 'adc_sample_speed', 'adc_options', 'period', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /usr/local/include/bcm2835.h', 'bcm2835'),
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO'),
        ('pip-git', 'pyadda', 'git://github.com/jaxbulsara/pyadda.git#egg=pyadda')
    ],
    'interfaces': ['UART'],
    'analog_to_digital_converter': True,
    'adc_channel': [
        (0, 'Channel 0'),
        (1, 'Channel 1'),
        (2, 'Channel 2'),
        (3, 'Channel 3'),
        (4, 'Channel 4'),
        (5, 'Channel 5'),
        (6, 'Channel 6'),
        (7, 'Channel 7')
    ],
    'adc_gain': [
        (1, '1'),
        (2, '2'),
        (4, '4'),
        (8, '8'),
        (16, '16'),
        (32, '32'),
        (64, '64')
    ],
    'adc_sample_speed': [
        ('30000', '30,000'),
        ('15000', '15,000'),
        ('7500', '7,500'),
        ('3750', '3,750'),
        ('2000', '2,000'),
        ('1000', '1,000'),
        ('500', '500'),
        ('100', '100'),
        ('60', '60'),
        ('50', '50'),
        ('30', '30'),
        ('25', '25'),
        ('15', '15'),
        ('10', '10'),
        ('5', '5'),
        ('2d5', '2.5')
    ],
    'adc_volts_min': -5.0,
    'adc_volts_max': 5.0
}


class ADCModule(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.ads1x15')
        self.acquiring_measurement = False
        self._voltage = None

        self.adc_gain = input_dev.adc_gain
        self.adc_sample_speed = input_dev.adc_sample_speed
        self.adc_channel = input_dev.adc_channel

        if not testing:
            import RPi.GPIO as GPIO
            import pyadda
            from adc_consts import ADS1256_GAIN
            from adc_consts import ADS1256_DRATE
            from adc_consts import ADS1256_SMODE

            self.logger = logging.getLogger(
                'mycodo.ads1256_{id}'.format(id=input_dev.id))

            self.ads1256 = pyadda

            # Raspberry pi pin numbering setup
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            PIN_DRDY = 17

            GPIO.setup(PIN_DRDY, GPIO.IN)

            # define gain, sampling rate, and scan mode
            gain = ADS1256_GAIN[str(self.adc_gain)]
            samplingRate = ADS1256_DRATE[str(self.adc_sample_speed)]
            scanMode = ADS1256_SMODE['SINGLE_ENDED']

            self.ads1256.startADC(gain, samplingRate, scanMode)

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

        if self.ads1256.collectData() is None:
            self.logger.error("Could not read chip")
        else:
            voltage = self.ads1256.readChannelVolts(self.adc_channel)
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
    input_dev_ = SimpleNamespace()
    input_dev_.id = 1
    input_dev_.adc_gain = '1'
    input_dev_.adc_channel = 0
    input_dev_.adc_sample_speed = '30000'

    ads = ADCModule(input_dev_)
    print("Channel 0: {}".format(ads.next()))

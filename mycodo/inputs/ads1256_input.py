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
        ('pip-pypi', 'wiringpi', 'wiringpi'),
        ('pip-git', 'pipyadc_py3', 'git://github.com/kizniche/PiPyADC-py3.git#egg=pipyadc_py3')  # PiPyADC ported to Python3
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
            from ADS1256_definitions import POS_AIN0
            from ADS1256_definitions import POS_AIN1
            from ADS1256_definitions import POS_AIN2
            from ADS1256_definitions import POS_AIN3
            from ADS1256_definitions import POS_AIN4
            from ADS1256_definitions import POS_AIN5
            from ADS1256_definitions import POS_AIN6
            from ADS1256_definitions import POS_AIN7
            from ADS1256_definitions import POS_AINCOM
            from ADS1256_definitions import NEG_AINCOM
            from ADS1256_definitions import NEG_AIN0

            from pipyadc_py3 import ADS1256
            import glob

            ################################################################################
            ###  STEP 0: CONFIGURE CHANNELS AND USE DEFAULT OPTIONS FROM CONFIG FILE: ###
            #
            # For channel code values (bitmask) definitions, see ADS1256_definitions.py.
            # The values representing the negative and positive input pins connected to
            # the ADS1256 hardware multiplexer must be bitwise OR-ed to form eight-bit
            # values, which will later be sent to the ADS1256 MUX register. The register
            # can be explicitly read and set via ADS1256.mux property, but here we define
            # a list of differential channels to be input to the ADS1256.read_sequence()
            # method which reads all of them one after another.
            #
            # ==> Each channel in this context represents a differential pair of physical
            # input pins of the ADS1256 input multiplexer.
            #
            # ==> For single-ended measurements, simply select AINCOM as the negative input.
            #
            # AINCOM does not have to be connected to AGND (0V), but it is if the jumper
            # on the Waveshare board is set.
            #
            # Input pin for the potentiometer on the Waveshare Precision ADC board:
            POTI = POS_AIN0 | NEG_AINCOM
            # Light dependant resistor of the same board:
            LDR = POS_AIN1 | NEG_AINCOM
            # The other external input screw terminals of the Waveshare board:
            EXT2, EXT3, EXT4 = POS_AIN2 | NEG_AINCOM, POS_AIN3 | NEG_AINCOM, POS_AIN4 | NEG_AINCOM
            EXT5, EXT6, EXT7 = POS_AIN5 | NEG_AINCOM, POS_AIN6 | NEG_AINCOM, POS_AIN7 | NEG_AINCOM

            # You can connect any pin as well to the positive as to the negative ADC input.
            # The following reads the voltage of the potentiometer with negative polarity.
            # The ADC reading should be identical to that of the POTI channel, but negative.
            POTI_INVERTED = POS_AINCOM | NEG_AIN0

            # For fun, connect both ADC inputs to the same physical input pin.
            # The ADC should always read a value close to zero for this.
            SHORT_CIRCUIT = POS_AIN0 | NEG_AIN0

            # Specify here an arbitrary length list (tuple) of arbitrary input channel pair
            # eight-bit code values to scan sequentially from index 0 to last.
            # Eight channels fit on the screen nicely for this example..
            self.CH_SEQUENCE = (POTI, LDR, EXT2, EXT3, EXT4, EXT7, POTI_INVERTED, SHORT_CIRCUIT)
            ################################################################################

            self.logger = logging.getLogger(
                'mycodo.ads1256_{id}'.format(id=input_dev.unique_id.split('-')[0]))

            if glob.glob('/dev/spi*'):
                self.ads = ADS1256()
                self.ads.cal_self()
                self.running = True
            else:
                raise Exception(
                    "SPI device /dev/spi* not found. Ensure SPI is enabled "
                    "and the device is recognized/setup by linux.")

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

        raw_channels = self.ads.read_sequence(self.CH_SEQUENCE)
        voltages = [i * self.ads.v_per_digit for i in raw_channels]

        return voltages[self.adc_channel]


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
            self.logger.exception(
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
    input_dev_.unique_id = '1234-5678'
    input_dev_.adc_gain = '1'
    input_dev_.adc_sample_speed = '10'
    input_dev_.adc_channel = 0

    ads = ADCModule(input_dev_)
    print("Channel 0: {}".format(ads.next()))

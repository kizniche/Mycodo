# coding=utf-8
import logging
import time
import sys

from flask_babel import lazy_gettext

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADS1256',
    'input_manufacturer': 'Waveshare',
    'input_name': 'ADS1256',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_list': ['adc_channels'],
    'options_enabled': ['adc_channels', 'adc_gain', 'adc_sample_speed', 'custom_options', 'adc_options', 'period', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'wiringpi', 'wiringpi'),
        ('pip-git', 'pipyadc_py3', 'git://github.com/kizniche/PiPyADC-py3.git#egg=pipyadc_py3')  # PiPyADC ported to Python3
    ],
    'interfaces': ['UART'],
    'analog_to_digital_converter': True,
    'adc_channels': 8,
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
    'adc_volts_min': 0.0,
    'adc_volts_max': 5.0,

    'custom_options': [
        {
            'id': 'adc_calibration',
            'type': 'select',
            'default_value': '',
            'options_select': [
                ('', 'No Calibration'),
                ('SELFOCAL', 'Self Offset'),
                ('SELFGCAL', 'Self Gain)'),
                ('SELFCAL', 'Self Offset + Self Gain'),
                ('SYSOCAL', 'System Offset'),
                ('SYSGCAL', 'System Gain')
            ],
            'name': lazy_gettext('Calibration'),
            'phrase': lazy_gettext('Set the calibration method to perform during Input activation')
        }
    ]
}


class ADCModule(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.ads1256')
        self.acquiring_measurement = False
        self._voltages = None

        self.adc_gain = input_dev.adc_gain
        self.adc_sample_speed = input_dev.adc_sample_speed
        self.adc_channels = input_dev.adc_channels

        self.adc_channels_selected = []
        for each_channel in input_dev.adc_channels_selected.split(','):
            self.adc_channels_selected.append(int(each_channel))

        if not testing:
            from ADS1256_definitions import POS_AIN0
            from ADS1256_definitions import POS_AIN1
            from ADS1256_definitions import POS_AIN2
            from ADS1256_definitions import POS_AIN3
            from ADS1256_definitions import POS_AIN4
            from ADS1256_definitions import POS_AIN5
            from ADS1256_definitions import POS_AIN6
            from ADS1256_definitions import POS_AIN7
            from ADS1256_definitions import NEG_AINCOM
            from pipyadc_py3 import ADS1256
            import glob

            # Input pin for the potentiometer on the Waveshare Precision ADC board
            POTI = POS_AIN0 | NEG_AINCOM
            # Light dependant resistor
            LDR = POS_AIN1 | NEG_AINCOM
            EXT2, EXT3, EXT4 = POS_AIN2 | NEG_AINCOM, POS_AIN3 | NEG_AINCOM, POS_AIN4 | NEG_AINCOM
            EXT5, EXT6, EXT7 = POS_AIN5 | NEG_AINCOM, POS_AIN6 | NEG_AINCOM, POS_AIN7 | NEG_AINCOM
            self.CH_SEQUENCE = (POTI, LDR, EXT2, EXT3, EXT4, EXT5, EXT6, EXT7)

            self.logger = logging.getLogger(
                'mycodo.ads1256_{id}'.format(id=input_dev.unique_id.split('-')[0]))

            self.adc_calibration = None

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'adc_calibration':
                        self.adc_calibration = value

            if glob.glob('/dev/spi*'):
                self.ads = ADS1256()

                # Perform selected calibration
                if self.adc_calibration == 'SELFOCAL':
                    self.ads.cal_self_offset()
                elif self.adc_calibration == 'SELFGCAL':
                    self.ads.cal_self_gain()
                elif self.adc_calibration == 'SELFCAL':
                    self.ads.cal_self()
                elif self.adc_calibration == 'SYSOCAL':
                    self.ads.cal_system_offset()
                elif self.adc_calibration == 'SYSGCAL':
                    self.ads.cal_system_gain()

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
        self.logger.error("Voltages returned: {}".format(self._voltages))
        return self._voltages

    @property
    def voltages(self):
        return self._voltages

    def get_measurement(self):
        self._voltages = {}
        voltages_list = []
        voltages_dict = {}
        count = 0

        # 2 attempts to get valid measurement
        while (self.running and count < 2 and
               (not any(voltages_dict.values()) or 0 in voltages_dict.values())):
            raw_channels = self.ads.read_sequence(self.CH_SEQUENCE)
            voltages_list = [i * self.ads.v_per_digit for i in raw_channels]
            count += 1

            for each_channel, each_voltage in enumerate(voltages_list, 1):
                if each_channel in self.adc_channels_selected:
                    voltages_dict['adc_channel_{}'.format(each_channel)] = each_voltage

            time.sleep(0.85)

        if 0 not in voltages_dict.values():
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

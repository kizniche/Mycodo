# coding=utf-8
import logging
import time
from datetime import datetime

import os

from mycodo.config import PATH_CAMERAS
from mycodo.utils.system_pi import assure_path_exists

from mycodo.utils.image import generate_thermal_image_from_pixels

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'AMG8833',
    'input_manufacturer': 'Panasonic',
    'input_name': 'AMG8833',
    'measurements_name': '8x8 Temperature Grid',
    'measurements_list': ['adc_channels'],
    'options_enabled': ['i2c_location', 'adc_channels', 'period', 'adc_options', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libjpeg-dev', 'libjpeg-dev'),
        ('apt', 'zlib1g-dev', 'zlib1g-dev'),
        ('pip-pypi', 'colour', 'colour'),
        ('pip-pypi', 'PIL', 'Pillow'),
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor'),
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x69', '0x68'],
    'i2c_address_editable': False,

    'analog_to_digital_converter': True,
    'adc_channels': 64,
}


class ADCModule(object):
    """ A sensor support class that monitors the AMG8833's temperature """

    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger("mycodo.inputs.amg8833")
        self._temperatures = None

        self.save_image = False
        self.temp_max = None
        self.temp_min = None
        self.report = False
        self.scale = 2
        self.nx = 8
        self.ny = 8

        self.adc_channels_selected = []
        for each_channel in input_dev.adc_channels_selected.split(','):
            self.adc_channels_selected.append(int(each_channel))

        if not testing:
            from Adafruit_AMG88xx import Adafruit_AMG88xx
            self.logger = logging.getLogger(
                "mycodo.ds18b20_{id}".format(id=input_dev.unique_id.split('-')[0]))
            self.Adafruit_AMG88xx = Adafruit_AMG88xx
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.input_dev = input_dev
            self.sensor = self.Adafruit_AMG88xx(address=self.i2c_address,
                                                busnum=self.i2c_bus)
            time.sleep(.1)  # wait for it to boot

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__, temp="{0:.2f}".format(self._temperatures))

    def __str__(self):
        """ Return temperature information """
        return "Temperatures: {}".format("{0:.2f}".format(self._temperatures))

    def __iter__(self):  # must return an iterator
        """ DS18B20Sensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return self._temperatures

    @property
    def temperatures(self):
        """ AMG8833 temperature in celsius """
        if self._temperatures is None:  # update if needed
            self.read()
        return self._temperatures

    def get_measurement(self):
        """ Gets the AMG8833's measurements """
        self._temperatures = None
        pixels_dict = {}

        pixels = self.sensor.readPixels()

        if self.report:
            self.logger.error("Min Pixel = {0} C".format(min(pixels)))
            self.logger.error("Max Pixel = {0} C".format(max(pixels)))
            self.logger.error("Thermistor = {0} C".format(self.sensor.readThermistor()))

        for index, each_pixel in enumerate(pixels):
            if index in self.adc_channels_selected:
                pixels_dict['adc_channel_{}'.format(index)] = each_pixel

        if self.save_image:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            assure_path_exists(PATH_CAMERAS)
            camera_path = assure_path_exists(
                os.path.join(PATH_CAMERAS, '{uid}'.format(uid=self.input_dev.unique_id)))
            filename = 'Still-{uid}-{ts}.jpg'.format(
                uid=self.input_dev.unique_id,
                ts=timestamp).replace(" ", "_")
            save_path = assure_path_exists(os.path.join(camera_path, 'thermal'))
            assure_path_exists(save_path)
            path_file = os.path.join(save_path, filename)
            generate_thermal_image_from_pixels(
                pixels,
                self.nx,
                self.ny,
                path_file,
                scale=self.scale,
                temp_min=self.temp_min,
                temp_max=self.temp_max)

        if pixels_dict:
            return pixels_dict

    def read(self):
        """
        Takes a reading from the AMG8833 and updates the self._temperature value

        :returns: None on success or 1 on error
        """
        try:
            self._temperatures = self.get_measurement()
            if self._temperatures:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1



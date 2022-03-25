# coding=utf-8
#
# From https://github.com/CRImier/python-MLX90614
#
# MIT License
#
# Copyright (c) 2016 Arsenijs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Ambient'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Object'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MLX90614',
    'input_manufacturer': 'Melexis',
    'input_name': 'MLX90614',
    'input_library': 'smbus2',
    'measurements_name': 'Temperature (Ambient/Object)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.melexis.com/en/product/MLX90614/Digital-Plug-Play-Infrared-Thermometer-TO-Can',
    'url_datasheet': 'https://www.melexis.com/-/media/files/documents/datasheets/mlx90614-datasheet-melexis.pdf',
    'url_product_purchase': 'https://www.sparkfun.com/products/9570',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x5a'],
    'i2c_address_editable': True,
}


class InputModule(AbstractInput):
    """A sensor support class that measure the MLX90614's ambient and object temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.MLX90614_RAWIR1=0x04
        self.MLX90614_RAWIR2=0x05
        self.MLX90614_TA=0x06
        self.MLX90614_TOBJ1=0x07
        self.MLX90614_TOBJ2=0x08
        
        self.MLX90614_TOMAX=0x20
        self.MLX90614_TOMIN=0x21
        self.MLX90614_PWMCTRL=0x22
        self.MLX90614_TARANGE=0x23
        self.MLX90614_EMISS=0x24
        self.MLX90614_CONFIG=0x25
        self.MLX90614_ADDR=0x0E
        self.MLX90614_ID1=0x3C
        self.MLX90614_ID2=0x3D
        self.MLX90614_ID3=0x3E
        self.MLX90614_ID4=0x3F

        if not testing:
            self.try_initialize()

    def initialize(self):
        from smbus2 import SMBus

        self.i2c_address = int(str(self.input_dev.i2c_location), 16)
        self.bus = SMBus(self.input_dev.i2c_bus)

    def read_reg(self, reg_addr):
        return self.bus.read_word_data(self.i2c_address, reg_addr)

    @staticmethod
    def data_to_temp(data):
        temp = (data*0.02) - 273.15
        return temp
 
    def get_amb_temp(self):
        data = self.read_reg(self.MLX90614_TA)
        return self.data_to_temp(data)
 
    def get_obj_temp(self):
        data = self.read_reg(self.MLX90614_TOBJ1)
        return self.data_to_temp(data)

    def get_measurement(self):
        """Gets the ambient (ch0) and object (ch1) temperatures."""
        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.get_amb_temp())

        if self.is_enabled(1):
            self.value_set(1, self.get_obj_temp())

        return self.return_dict

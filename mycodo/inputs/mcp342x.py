# coding=utf-8
import logging
import time

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP342x',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP342x',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_list': ['adc_channels'],
    'options_enabled': ['i2c_location', 'adc_channels', 'adc_gain', 'adc_resolution', 'adc_options', 'period', 'pre_output'],
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
    'analog_to_digital_converter': True,
    'adc_channels': 4,
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
    ],
    'adc_volts_min': -4.096,
    'adc_volts_max': 4.096
}


class ADCModule(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.mcp342x')
        self.acquiring_measurement = False
        self._voltages = None

        self.i2c_address = int(str(input_dev.i2c_location), 16)
        self.i2c_bus = input_dev.i2c_bus
        self.adc_gain = input_dev.adc_gain
        self.adc_resolution = input_dev.adc_resolution
        self.adc_channels = input_dev.adc_channels

        self.adc_channels_selected = []
        for each_channel in input_dev.adc_channels_selected.split(','):
            self.adc_channels_selected.append(int(each_channel))

        if not testing:
            from smbus2 import SMBus
            from MCP342x import MCP342x
            self.logger = logging.getLogger(
                'mycodo.mcp342x_{id}'.format(id=input_dev.unique_id.split('-')[0]))
            self.MCP342x = MCP342x
            self.bus = SMBus(self.i2c_bus)

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
        # voltages = {}
        # voltage_index = 0
        # for each_channel in self.adc_channels_selected:
        #     adc = self.MCP342x(self.bus,
        #                        self.i2c_address,
        #                        channel=each_channel,
        #                        gain=self.adc_gain,
        #                        resolution=self.adc_resolution)
        #     voltages['adc_channel_{}'.format(each_channel)] = adc.convert_and_read()
        #     voltage_index += 1

        import random
        voltages = {
            'adc_channel_0': random.uniform(1.5, 1.9),
            'adc_channel_1': random.uniform(2.3, 2.5),
            'adc_channel_2': random.uniform(0.5, 0.6),
            'adc_channel_3': random.uniform(3.5, 6.2),
        }

        if voltages:
            return voltages

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


if __name__ == "__main__":
    class Data:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    settings = Data(id='00001',
                    unique_id='asdf-ghjk',
                    i2c_address='0x68',
                    i2c_bus=1,
                    adc_channels=4,
                    adc_channels_selected='0,1,2,3',
                    adc_gain=1,
                    adc_resolution=12)

    mcp = ADCModule(settings)

    while 1:
        print("Voltages: {}".format(mcp.next()))
        time.sleep(1)

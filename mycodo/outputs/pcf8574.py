# coding=utf-8
#
# pcf8574.py - Output for PCF8574
#
from flask_babel import lazy_gettext
from mycodo.outputs.base_output import AbstractOutput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    1: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    2: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    3: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    4: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    5: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    6: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    7: {
        'measurement': 'duration_time',
        'unit': 's',
    }
}

outputs_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    },
    1: {
        'types': ['on_off'],
        'measurements': [1]
    },
    2: {
        'types': ['on_off'],
        'measurements': [2]
    },
    3: {
        'types': ['on_off'],
        'measurements': [3]
    },
    4: {
        'types': ['on_off'],
        'measurements': [4]
    },
    5: {
        'types': ['on_off'],
        'measurements': [5]
    },
    6: {
        'types': ['on_off'],
        'measurements': [6]
    },
    7: {
        'types': ['on_off'],
        'measurements': [7]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'PCF8574',
    'output_name': "{} PCF8574 (8 Channels)".format(lazy_gettext('On/Off')),
    'output_library': 'smbus2',
    'measurements_dict': measurements_dict,
    'outputs_dict': outputs_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.ti.com/product/PCF8574',
    'url_datasheet': 'https://www.ti.com/lit/ds/symlink/pcf8574.pdf',
    'url_product_purchase': 'https://www.amazon.com/gp/product/B07JGSNWFF',

    'message': 'Turns the specified channel of the PCF8574 on or off.',

    'options_enabled': [
        'i2c_location',
        'on_off_state_on',
        'on_off_state_startup',
        'on_off_state_shutdown',
        'trigger_functions_startup',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x20', '0x21', '0x22', '0x23', '0x24', '0x25', '0x26', '0x27',
        '0x38', '0x39', '0x3a', '0x3b', '0x3c', '0x3d', '0x3e', '0x3f'
    ],
    'i2c_address_editable': False,
    'i2c_address_default': '0x20',
}


class OutputModule(AbstractOutput):
    """ An output support class that operates an output """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.sensor = None
        self.output_on_state = None
        self.state_startup = None
        self.state_shutdown = None

    def setup_output(self):
        import smbus2

        self.setup_on_off_output(OUTPUT_INFORMATION)
        self.output_on_state = self.output.on_state
        self.state_startup = self.output.state_startup
        self.state_shutdown = self.output.state_shutdown

        if self.output.i2c_location:
            self.sensor = PCF8574(smbus2, self.output.i2c_bus, int(str(self.output.i2c_location), 16))
            self.output_setup = True

        for each_output_channel in self.output_states:
            if self.state_startup == '1':
                self.output_switch('on', output_channel=each_output_channel)
            elif self.state_startup == '0':
                self.output_switch('off', output_channel=each_output_channel)

    def output_switch(self,
                      state,
                      output_type=None,
                      amount=None,
                      duty_cycle=None,
                      output_channel=None):
        if output_channel is None:
            self.logger.error("Output channel needs to be specified")
            return

        try:
            if state == 'on':
                list_states = []
                for each_channel in self.output_states:
                    if output_channel == each_channel:
                        self.output_states[each_channel] = self.output_on_state
                        list_states.append(self.output_states[each_channel])
                    else:
                        list_states.append(self.output_states[each_channel])
                self.sensor.port = list_states
            elif state == 'off':
                list_states = []
                for each_channel in self.output_states:
                    if output_channel == each_channel:
                        self.output_states[each_channel] = not self.output_on_state
                        list_states.append(self.output_states[each_channel])
                    else:
                        list_states.append(self.output_states[each_channel])
                self.sensor.port = list_states
        except Exception as e:
            self.logger.error("State change error: {}".format(e))

    def is_on(self, output_channel=None):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        for each_output_channel in self.output_states:
            if self.state_shutdown == '1':
                self.output_switch('on', output_channel=each_output_channel)
            elif self.state_shutdown == '0':
                self.output_switch('off', output_channel=each_output_channel)
        self.running = False


class IOPort(list):
    """ Represents the PCF8574 IO port as a list of boolean values """
    def __init__(self, pcf8574, *args, **kwargs):
        super(IOPort, self).__init__(*args, **kwargs)
        self.pcf8574 = pcf8574

    def __setitem__(self, key, value):
        """ Set an individual output pin """
        self.pcf8574.set_output(key, value)

    def __repr__(self):
        """ Represent port as a list of booleans """
        state = self.pcf8574.bus.read_byte(self.pcf8574.address)
        ret = []
        for i in range(8):
            ret.append(bool(state & 1 << 7-i))
        return repr(ret)

    def __len__(self):
        return 8

    def __iter__(self):
        for i in range(8):
            yield self[i]

    def __reversed__(self):
        for i in range(8):
            yield self[7-i]


class PCF8574(object):
    """ A software representation of a single PCF8574 IO expander chip """
    def __init__(self, smbus, i2c_bus, i2c_address):
        self.bus_no = i2c_bus
        self.bus = smbus.SMBus(i2c_bus)
        self.address = i2c_address

    def __repr__(self):
        return "PCF8574(i2c_bus_no=%r, address=0x%02x)" % (self.bus_no, self.address)

    @property
    def port(self):
        """ Represent IO port as a list of boolean values """
        return IOPort(self)

    @port.setter
    def port(self, value):
        """ Set the whole port using a list """
        assert isinstance(value, list)
        assert len(value) == 8
        new_state = 0
        for i, val in enumerate(value):
            if val:
                new_state |= 1 << 7-i
        self.bus.write_byte(self.address, new_state)

    def set_output(self, output_number, value):
        """ Set a specific output high (True) or low (False) """
        assert output_number in range(8), "Output number must be an integer between 0 and 7"
        current_state = self.bus.read_byte(self.address)
        bit = 1 << 7-output_number
        new_state = current_state | bit if value else current_state & (~bit & 0xff)
        self.bus.write_byte(self.address, new_state)

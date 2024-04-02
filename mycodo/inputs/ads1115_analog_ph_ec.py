# coding=utf-8
import copy
import traceback

from flask_babel import lazy_gettext

from mycodo.databases.models import Conversion
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info


def execute_at_modification(
        messages,
        mod_input,
        request_form,
        custom_options_dict_presave,
        custom_options_channels_dict_presave,
        custom_options_dict_postsave,
        custom_options_channels_dict_postsave):
    try:
        if (custom_options_dict_postsave['adc_channel_ph'] ==
                custom_options_dict_postsave['adc_channel_ec']):
            messages["error"].append("Cannot set pH and EC to be measured from the same channel.")
    except Exception:
        messages["error"].append("execute_at_modification() Error: {}".format(traceback.print_exc()))

    return (messages,
            mod_input,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave)


# Measurements
measurements_dict = {
    0: {
        'measurement': 'ion_concentration',
        'unit': 'pH'
    },
    1: {
        'measurement': 'electrical_conductivity',
        'unit': 'uS_cm'
    },
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ANALOG_PH_EC',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1115: Generic Analog pH/EC',
    'input_name_short': 'ADS1115 pH/EC',
    'input_library': 'Adafruit_CircuitPython_ADS1x15',
    'measurements_name': 'Ion Concentration/Electrical Conductivity',
    'measurements_dict': measurements_dict,
    'execute_at_modification': execute_at_modification,

    'message': 'This input relies on an ADS1115 analog-to-digital converter (ADC) to measure pH '
               'and/or electrical conductivity (EC) from analog sensors. You can enable or disable '
               'either measurement if you want to only connect a pH sensor or an EC sensor by '
               'selecting which measurements you want to under Measurements Enabled. Select which '
               'channel each sensor is connected to on the ADC. There are default calibration values '
               'initially set for the Input. There are also functions to allow you to easily '
               'calibrate your sensors with calibration solutions. If you use the Calibrate Slot '
               'actions, these values will be calculated and will replace the currently-set values. '
               'You can use the Clear Calibration action to delete the database values and return '
               'to using the default values. If you delete the Input or create a new Input to use '
               'your ADC/sensors with, you will need to recalibrate in order to store new calibration data.',

    'options_enabled': [
        'measurements_select',
        'i2c_location',
        'adc_gain',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_ads1x15', 'adafruit-circuitpython-ads1x15==2.2.25')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49', '0x4A', '0x4B'],
    'i2c_address_editable': False,

    # TODO: Next major revision, move settings such as these to custom_options
    'adc_gain': [(0, '2/3 (±6.144 V)'),
                 (1, '1 (±4.096 V)'),
                 (2, '2 (±2.048 V)'),
                 (4, '4 (±1.024 V)'),
                 (8, '8 (±0.512 V)'),
                 (16, '16 (±0.256 V)')],

    'custom_options': [
        {
            'id': 'adc_channel_ph',
            'type': 'select',
            'default_value': '0',
            'options_select': [
                ('0', 'Channel 0'),
                ('1', 'Channel 1'),
                ('2', 'Channel 2'),
                ('3', 'Channel 3'),
            ],
            'name': 'ADC Channel: pH',
            'phrase': 'The ADC channel the pH sensor is connected'
        },
        {
            'id': 'adc_channel_ec',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('0', 'Channel 0'),
                ('1', 'Channel 1'),
                ('2', 'Channel 2'),
                ('3', 'Channel 3'),
            ],
            'name': 'ADC Channel: EC',
            'phrase': 'The ADC channel the EC sensor is connected'
        },
        {
            'type': 'message',
            'default_value': 'Temperature Compensation',
        },
        {
            'id': 'temperature_comp_meas',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function'
            ],
            'name': "{}: {}".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Measurement')),
            'phrase': lazy_gettext('Select a measurement for temperature compensation')
        },
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{}: {} ({})".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Max Age'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The maximum age of the measurement to use')
        },
        {
            'type': 'message',
            'default_value': 'pH Calibration Data',
        },
        {
            'id': 'ph_cal_v1',
            'type': 'float',
            'default_value': 1.500,
            'name': 'Cal data: V1 (internal)',
            'phrase': 'Calibration data: Voltage'
        },
        {
            'id': 'ph_cal_ph1',
            'type': 'float',
            'default_value': 7.0,
            'name': 'Cal data: pH1 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'ph_cal_t1',
            'type': 'float',
            'default_value': 25.0,
            'name': 'Cal data: T1 (internal)',
            'phrase': 'Calibration data: Temperature'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'ph_cal_v2',
            'type': 'float',
            'default_value': 2.032,
            'name': 'Cal data: V2 (internal)',
            'phrase': 'Calibration data: Voltage'
        },
        {
            'id': 'ph_cal_ph2',
            'type': 'float',
            'default_value': 4.0,
            'name': 'Cal data: pH2 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'ph_cal_t2',
            'type': 'float',
            'default_value': 25.0,
            'name': 'Cal data: T2 (internal)',
            'phrase': 'Calibration data: Temperature'
        },
        {
            'type': 'message',
            'default_value': 'EC Calibration Data'
        },
        {
            'id': 'ec_cal_v1',
            'type': 'float',
            'default_value': 0.232,
            'name': 'EC cal data: V1 (internal)',
            'phrase': 'EC calibration data: Voltage'
        },
        {
            'id': 'ec_cal_ec1',
            'type': 'float',
            'default_value': 1413.0,
            'name': 'EC cal data: EC1 (internal)',
            'phrase': 'EC calibration data: EC'
        },
        {
            'id': 'ec_cal_t1',
            'type': 'float',
            'default_value': 25.0,
            'name': 'EC cal data: T1 (internal)',
            'phrase': 'EC calibration data: EC'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'ec_cal_v2',
            'type': 'float',
            'default_value': 2.112,
            'name': 'EC cal data: V2 (internal)',
            'phrase': 'EC calibration data: Voltage'
        },
        {
            'id': 'ec_cal_ec2',
            'type': 'float',
            'default_value': 12880.0,
            'name': 'EC cal data: EC2 (internal)',
            'phrase': 'EC calibration data: EC'
        },
        {
            'id': 'ec_cal_t2',
            'type': 'float',
            'default_value': 25.0,
            'name': 'EC cal data: T2 (internal)',
            'phrase': 'EC calibration data: EC'
        },
    ],
    'custom_commands': [
        {
            'type': 'message',
            'default_value': """pH Calibration Actions: Place your probe in a solution of known pH.
            Set the known pH value in the "Calibration buffer pH" field, and press "Calibrate pH, slot 1".
            Repeat with a second buffer, and press "Calibrate pH, slot 2".
            You don't need to change the values under "Custom Options"."""
        },
        {
            'id': 'calibration_ph',
            'type': 'float',
            'default_value': 7.0,
            'name': 'Calibration buffer pH',
            'phrase': 'This is the nominal pH of the calibration buffer, usually labelled on the bottle.'
        },
        {
            'id': 'calibrate_ph_slot_1',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate pH, slot 1'
        },
        {
            'id': 'calibrate_ph_slot_2',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate pH, slot 2'
        },
        {
            'id': 'clear_ph_calibrate_slots',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Clear pH Calibration Slots'
        },
        {
            'type': 'message',
            'default_value': """EC Calibration Actions: Place your probe in a solution of known EC.
            Set the known EC value in the "Calibration standard EC" field, and press "Calibrate EC, slot 1".
            Repeat with a second standard, and press "Calibrate EC, slot 2".
            You don't need to change the values under "Custom Options"."""
        },
        {
            'id': 'calibration_ec',
            'type': 'float',
            'default_value': 1413.0,
            'name': 'Calibration standard EC',
            'phrase': 'This is the nominal EC of the calibration standard, usually labelled on the bottle.'
        },
        {
            'id': 'calibrate_ec_slot_1',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate EC, slot 1'
        },
        {
            'id': 'calibrate_ec_slot_2',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate EC, slot 2'
        },
        {
            'id': 'clear_ec_calibrate_slots',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Clear EC Calibration Slots'
        }
    ]
}


class InputModule(AbstractInput):
    """
    Read ADC

    Choose a gain of 1 for reading measurements from 0 to 4.09V.
    Or pick a different gain to change the range of measurements that are read:
     - 2/3 = ±6.144 V
     -   1 = ±4.096 V
     -   2 = ±2.048 V
     -   4 = ±1.024 V
     -   8 = ±0.512 V
     -  16 = ±0.256 V
    See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.adc = None
        self.analog_in = None
        self.ads = None
        self.adc_gain = None

        self.dict_gains = {
            2/3: 0.1875,
            1: 0.125,
            2: 0.0625,
            4: 0.03125,
            8: 0.015625,
            16: 0.0078125,
        }

        self.adc_channel_ph = None
        self.adc_channel_ec = None
        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None

        self.ph_cal_v1 = None
        self.ph_cal_ph1 = None
        self.ph_cal_t1 = None
        self.ph_cal_v2 = None
        self.ph_cal_ph2 = None
        self.ph_cal_t2 = None

        self.ec_cal_v1 = None
        self.ec_cal_ec1 = None
        self.ec_cal_t1 = None
        self.ec_cal_v2 = None
        self.ec_cal_ec2 = None
        self.ec_cal_t2 = None

        self.slope = None
        self.intercept = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn
        from adafruit_extended_bus import ExtendedI2C

        self.analog_in = AnalogIn
        self.ads = ADS

        if self.input_dev.adc_gain == 0:
            self.adc_gain = 2/3
        else:
            self.adc_gain = self.input_dev.adc_gain

        try:
            self.adc = ADS.ADS1115(
                ExtendedI2C(self.input_dev.i2c_bus),
                address=int(str(self.input_dev.i2c_location), 16))
        except Exception as err:
            self.logger.error("Error while initializing: {}".format(err))

    def calibrate_ph(self, cal_slot, args_dict):
        """Calibration helper method."""
        if 'calibration_ph' not in args_dict:
            self.logger.error("Cannot conduct calibration without a buffer pH value")
            return
        if (not isinstance(args_dict['calibration_ph'], float) and
                not isinstance(args_dict['calibration_ph'], int)):
            self.logger.error("buffer value does not represent a number: '{}', type: {}".format(
                args_dict['calibration_ph'], type(args_dict['calibration_ph'])))
            return

        v = self.get_volt_data(int(self.adc_channel_ph))  # pH
        temp = self.get_temp_data()
        if temp is not None:
            # Use measured temperature
            t = temp
        else:
            # Assume room temperature of 25C
            t = 25
        self.logger.debug("Assigning voltage {} and temperature {} to pH {}".format(
            v, t, args_dict['calibration_ph']))

        if cal_slot == 1:
            # set values currently being used
            self.ph_cal_v1 = v
            self.ph_cal_ph1 = args_dict['calibration_ph']
            self.ph_cal_t1 = t
            # save values for next startup
            self.set_custom_option("ph_cal_v1", v)
            self.set_custom_option("ph_cal_ph1", args_dict['calibration_ph'])
            self.set_custom_option("ph_cal_t1", t)
        elif cal_slot == 2:
            # set values currently being used
            self.ph_cal_v2 = v
            self.ph_cal_ph2 = args_dict['calibration_ph']
            self.ph_cal_t2 = t
            # save values for next startup
            self.set_custom_option("ph_cal_v2", v)
            self.set_custom_option("ph_cal_ph2", args_dict['calibration_ph'])
            self.set_custom_option("ph_cal_t2", t)

    def calibrate_ph_slot_1(self, args_dict):
        """calibrate."""
        self.calibrate_ph(1, args_dict)

    def calibrate_ph_slot_2(self, args_dict):
        """calibrate."""
        self.calibrate_ph(2, args_dict)

    def clear_ph_calibrate_slots(self, args_dict):
        self.delete_custom_option("ph_cal_v1")
        self.delete_custom_option("ph_cal_ph1")
        self.delete_custom_option("ph_cal_t1")
        self.delete_custom_option("ph_cal_v2")
        self.delete_custom_option("ph_cal_ph2")
        self.delete_custom_option("ph_cal_t2")
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], self.input_dev)

    def calibrate_ec(self, cal_slot, args_dict):
        """Calibration helper method."""
        if 'calibration_ec' not in args_dict:
            self.logger.error("Cannot conduct calibration without a standard EC value")
            return
        if (not isinstance(args_dict['calibration_ec'], float) and
                not isinstance(args_dict['calibration_ec'], int)):
            self.logger.error("standard value does not represent a number: '{}', type: {}".format(
                args_dict['calibration_ec'], type(args_dict['calibration_ec'])))
            return

        v = self.get_volt_data(int(self.adc_channel_ec))  # EC
        temp = self.get_temp_data()
        if temp is not None:
            # Use measured temperature
            t = temp
        else:
            # Assume room temperature of 25C
            t = 25
        self.logger.debug("Assigning voltage {} and temperature {} to EC {}".format(
            v, t, args_dict['calibration_ec']))

        # For future sessions
        if cal_slot == 1:
            # set values currently being used
            self.ec_cal_v1 = v
            self.ec_cal_ec1 = args_dict['calibration_ec']
            self.ec_cal_t1 = t
            # save values for next startup
            self.set_custom_option("ec_cal_v1", v)
            self.set_custom_option("ec_cal_ec1", args_dict['calibration_ec'])
            self.set_custom_option("ec_cal_t1", t)
        elif cal_slot == 2:
            self.ec_cal_v2 = v
            self.ec_cal_ec2 = args_dict['calibration_ec']
            self.ec_cal_t2 = t
            self.set_custom_option("ec_cal_v2", v)
            self.set_custom_option("ec_cal_ec2", args_dict['calibration_ec'])
            self.set_custom_option("ec_cal_t2", t)

    def calibrate_ec_slot_1(self, args_dict):
        """calibrate."""
        self.calibrate_ec(1, args_dict)

    def calibrate_ec_slot_2(self, args_dict):
        """calibrate."""
        self.calibrate_ec(2, args_dict)

    def clear_ec_calibrate_slots(self, args_dict):
        self.delete_custom_option("ec_cal_v1")
        self.delete_custom_option("ec_cal_ec1")
        self.delete_custom_option("ec_cal_t1")
        self.delete_custom_option("ec_cal_v2")
        self.delete_custom_option("ec_cal_ec2")
        self.delete_custom_option("ec_cal_t2")
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], self.input_dev)

    @staticmethod
    def nernst_correction(volt, temp):
        """Apply temperature correction for pH. This provides the voltage as if it were measured at 25C.
        Based on the Nernst equation: E = E0 - ln(10) * RT/nF * pH; this gives E = E0 - 0.198 * T * pH.
        The correction is a simple ratio of absolute temperature."""
        volt_25C = volt * 298/(temp+273)

        return volt_25C

    @staticmethod
    def viscosity_correction(volt, temp):
        """Apply temperature correction for EC. This provides the voltage as if it were measured at 25C.
        Based on the Nernst-Einstein and Stokes-Einstein relations, related to viscosity: EC/EC25 = vis25/vis.
        The correction is a linear approximation to the full curve, valid for 10-30C."""
        volt_25C = volt / (1 + 0.020 * (temp - 25))

        return volt_25C

    def get_temp_data(self):
        """Get the temperature."""
        if self.temperature_comp_meas_measurement_id:
            self.logger.debug("Temperature corrections will be applied")

            last_measurement = self.get_last_measurement(
                self.temperature_comp_meas_device_id,
                self.temperature_comp_meas_measurement_id,
                max_age=self.max_age)

            if last_measurement and len(last_measurement) > 1:
                device_measurement = get_measurement(
                    self.temperature_comp_meas_measurement_id)
                conversion = db_retrieve_table_daemon(
                    Conversion, unique_id=device_measurement.conversion_id)
                _, unit, _ = return_measurement_info(
                    device_measurement, conversion)

                if unit != "C":
                    out_value = convert_from_x_to_y_unit(
                        unit, "C", last_measurement[1])
                else:
                    out_value = last_measurement[1]

                self.logger.debug("Latest temperature: {temp} C".format(
                    temp=out_value))
            else:
                self.logger.error(
                    "Temperature measurement not found within the "
                    "past {} seconds".format(self.max_age))
                out_value = None

        else:
            self.logger.debug("No temperature corrections applied")
            out_value = None

        return out_value

    def get_volt_data(self, channel):
        """Measure voltage at ADC channel."""
        chan = self.analog_in(self.adc, channel)
        self.adc.gain = self.adc_gain
        self.logger.debug("Channel {}: Gain {}, {} raw, {} volts".format(
            channel, self.adc_gain, chan.value, chan.voltage))
        volt_data = chan.voltage

        return volt_data

    def convert_volt_to_ph(self, volt, temp):
        """Convert voltage to pH."""
        # Calculate slope and intercept from calibration points.
        self.slope = ((self.ph_cal_ph1 - self.ph_cal_ph2) /
                      (self.nernst_correction(self.ph_cal_v1, self.ph_cal_t1) -
                       self.nernst_correction(self.ph_cal_v2, self.ph_cal_t2)))
        self.intercept = (self.ph_cal_ph1 -
                          self.slope *
                          self.nernst_correction(self.ph_cal_v1, self.ph_cal_t1))
        if temp is not None:
            # Perform temperature corrections
            ph = self.slope * self.nernst_correction(volt, temp) + self.intercept
        else:
            # Don't perform temperature corrections
            ph = self.slope * volt + self.intercept

        return ph

    def convert_volt_to_ec(self, volt, temp):
        """Convert voltage to EC."""
        # Calculate slope and intercept from calibration points.
        self.slope = ((self.ec_cal_ec1 - self.ec_cal_ec2) /
                      (self.viscosity_correction(self.ec_cal_v1, self.ec_cal_t1) -
                       self.viscosity_correction(self.ec_cal_v2, self.ec_cal_t2)))
        self.intercept = (self.ec_cal_ec1 -
                          self.slope *
                          self.viscosity_correction(self.ec_cal_v1, self.ec_cal_t1))
        if temp is not None:
            # Perform temperature corrections
            ec = self.slope * self.viscosity_correction(volt, temp) + self.intercept
        else:
            # Don't perform temperature corrections
            ec = self.slope * volt + self.intercept

        return ec

    def get_measurement(self):
        """Gets the measurement."""
        if not self.adc:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        # Store measurement for each channel
        if self.is_enabled(0):  # pH
            self.value_set(
                0,
                self.convert_volt_to_ph(
                    self.get_volt_data(int(self.adc_channel_ph)),
                    self.get_temp_data()))

        if self.is_enabled(1):  # EC
            self.value_set(
                1,
                self.convert_volt_to_ec(
                    self.get_volt_data(int(self.adc_channel_ec)),
                    self.get_temp_data()))

        return self.return_dict

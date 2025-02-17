# coding=utf-8
import copy
import time
from collections import OrderedDict
from mycodo.utils.lockfile import LockFile

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = OrderedDict()
measurements_dict[0] = {
    'measurement': 'electrical_potential',
    'unit': 'V'
}
channel = 1
for ct in range(1, 7):
    measurements_dict[channel] = {
        'measurement': 'power',
        'unit': 'W',
        'name': f'CT{ct}'
    }
    measurements_dict[channel] = {
        'measurement': 'energy',
        'unit': 'kWh',
        'name': f'CT{ct} Total'
    }
    measurements_dict[channel + 1] = {
        'measurement': 'electrical_current',
        'unit': 'A',
        'name': f'CT{ct}'
    }
    measurements_dict[channel + 2] = {
        'measurement': 'power_factor',
        'unit': 'unitless',
        'name': f'CT{ct}'
    }
    channel += 4

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'input_rpi_power_monitor_2',
    'input_manufacturer': 'Power Monitor',
    'input_name': 'RPi 6-Channel Power Monitor (v0.4.0)',
    'input_name_short': 'RPi Power Monitor v0.4.0',
    'input_library': 'rpi-power-monitor',
    'measurements_name': 'AC Voltage, Power, Energy, Current, Power Factor',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://github.com/David00/rpi-power-monitor',
    'url_product_purchase': 'https://power-monitor.dalbrecht.tech/',
    'measurements_use_same_timestamp': True,

    'message': "See https://david00.github.io/rpi-power-monitor/docs/v0.3.0/calibration.html for calibration documentation.",

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'rpi_power_monitor', 'git+https://github.com/David00/rpi-power-monitor.git@eeb3143fba6452de916407ae94a0a6e8834a7d67')
    ],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """Clear the running kWh totals."""
        },
        {
            'id': 'channel_to_clear',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('all', 'All Channels'),
                ('1', 'Channel 1'),
                ('2', 'Channel 2'),
                ('3', 'Channel 3'),
                ('4', 'Channel 4'),
                ('5', 'Channel 5'),
                ('6', 'Channel 6')

            ],
            'name': 'Channel to Clear',
            'phrase': 'The channel(s) to clear the kWh total and start back at 0.'
        },
        {
            'id': 'clear_channel',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Clear kWh Total'
        }
    ],

    'custom_options': [
        {
            'id': 'kwh_measure_period_sec',
            'type': 'integer',
            'default_value': 5,
            'required': True,
            'name': 'Period (Seconds) for kWh Measuring',
            'phrase': 'How often to acquire measurements to calculate kWh'
        },
        {
            'id': 'grid_voltage',
            'type': 'float',
            'default_value': 124.2,
            'required': True,
            'name': 'Grid Voltage',
            'phrase': 'The AC voltage measured at the outlet'
        },
        {
            'id': 'transformer_voltage',
            'type': 'float',
            'default_value': 10.2,
            'required': True,
            'name': 'Transformer Voltage',
            'phrase': 'The AC voltage measured at the barrel plug of the 9 VAC transformer'
        },
        {
            'id': 'ac_frequency',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'name': 'AC Frequency (Hz)',
            'phrase': 'The frequency of the AC voltage'
        },
        {
            'id': 'ct1_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT1 Calibration',
            'phrase': 'The calibration value for CT1'
        },
        {
            'id': 'ct2_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT2 Calibration',
            'phrase': 'The calibration value for CT2'
        },
        {
            'id': 'ct3_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT3 Calibration',
            'phrase': 'The calibration value for CT3'
        },
        {
            'id': 'ct4_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT4 Calibration',
            'phrase': 'The calibration value for CT4'
        },
        {
            'id': 'ct5_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT5 Calibration',
            'phrase': 'The calibration value for CT5'
        },
        {
            'id': 'ct6_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT6 Calibration',
            'phrase': 'The calibration value for CT6'
        },
        {
            'id': 'ac_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'AC Calibration',
            'phrase': 'The calibration value for AC'
        }
    ]
}

class InputModule(AbstractInput):
    """ Input module to read the Raspberry Pi Power Monitor HAT """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.kwh_measure_period_sec = None
        self.grid_voltage = None
        self.transformer_voltage = None
        self.ac_frequency = None

        self.ct1_accuracy_calibration = None
        self.ct2_accuracy_calibration = None
        self.ct3_accuracy_calibration = None
        self.ct4_accuracy_calibration = None
        self.ct5_accuracy_calibration = None
        self.ct6_accuracy_calibration = None
        self.ac_accuracy_calibration = None

        self.timer_kwh_measure = 0
        self.kwh_saved = None
        self.lock_file = '/var/lock/power_kwh.lock'

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from power_monitor import RPiPowerMonitor, logger, ch

        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)

        self.kwh_saved = self.get_custom_option("kwh_saved")

        if self.kwh_saved is None:
            self.kwh_saved = {
                1: 0,
                2: 0,
                3: 0,
                4: 0,
                5: 0,
                6: 0
            }

        config = {
            'general': {
                'name': 'Power-Monitor'
            },
            'database': {
                'enabled': False,
                'host': 'localhost',
                'port': 8086,
                'username': 'root',
                'password': 'password',
                'database_name': 'power_monitor',
                'influx_version': 1,
                # The Influx V2 configuration is only required if influx_version (above) is set to 1.
                # Set influx_version = 2, and fill in your InfluxDB v2 parameters below, to use InfluxDB v2.
                'influx_v2': {
                    'bucket': 'power_monitor',
                    'org': '<your Influx Cloud email or custom defined org>',
                    'token': '<an API token with at least r/w permissions for all buckets and all tasks>',
                    'url': '<your unique Influx Cloud or self-hosted InfluxDB v2 server URL>',
                }
            },
            'grid_voltage': {
                'grid_voltage': self.grid_voltage,
                'ac_transformer_output_voltage': self.transformer_voltage,
                'frequency': self.ac_frequency,
                'voltage_calibration': self.ac_accuracy_calibration
            },
            'current_transformers': {
                'channel_1': {
                    'name': 'Channel 1',
                    'rating': 100,
                    'type': 'consumption',
                    'two_pole': False,
                    'enabled': self.is_enabled(0),
                    'calibration': self.ct1_accuracy_calibration,
                    'amps_cutoff_threshold': 0.01,
                    'reversed': False,
                    'phase_angle': 0
                },
                'channel_2': {
                    'name': 'Channel 2',
                    'rating': 100,
                    'type': 'consumption',
                    'two_pole': False,
                    'enabled': self.is_enabled(1),
                    'calibration': self.ct2_accuracy_calibration,
                    'amps_cutoff_threshold': 0.01,
                    'reversed': False,
                    'phase_angle': 0
                },
                'channel_3': {
                    'name': 'Channel 3',
                    'rating': 100,
                    'type': 'consumption',
                    'two_pole': False,
                    'enabled': self.is_enabled(2),
                    'calibration': self.ct3_accuracy_calibration,
                    'amps_cutoff_threshold': 0.01,
                    'reversed': False,
                    'phase_angle': 0
                },
                'channel_4': {
                    'name': 'Channel 4',
                    'rating': 100,
                    'type': 'consumption',
                    'two_pole': False,
                    'enabled': self.is_enabled(3),
                    'calibration': self.ct4_accuracy_calibration,
                    'amps_cutoff_threshold': 0.01,
                    'reversed': False,
                    'phase_angle': 0
                },
                'channel_5': {
                    'name': 'Channel 5',
                    'rating': 100,
                    'type': 'consumption',
                    'two_pole': False,
                    'enabled': self.is_enabled(4),
                    'calibration': self.ct5_accuracy_calibration,
                    'amps_cutoff_threshold': 0.01,
                    'reversed': False,
                    'phase_angle': 0
                },
                'channel_6': {
                    'name': 'Channel 6',
                    'rating': 100,
                    'type': 'consumption',
                    'two_pole': False,
                    'enabled': self.is_enabled(5),
                    'calibration': self.ct6_accuracy_calibration,
                    'amps_cutoff_threshold': 0.01,
                    'reversed': False,
                    'phase_angle': 0
                },
            }
        }

        self.sensor = RPiPowerMonitor(config=config)

    def listener(self):
        while self.running:
            if time.time() - self.timer_kwh_measure >= self.kwh_measure_period_sec:
                while time.time() - self.timer_kwh_measure >= self.kwh_measure_period_sec:
                    self.timer_kwh_measure += self.kwh_measure_period_sec

                results = self.sensor.get_power_measurements(duration=0.5)

                per_hour_fraction = self.kwh_measure_period_sec / 3600

                lf = LockFile()
                if lf.lock_acquire(self.lock_file, timeout=10):
                    try:
                        chan = 1
                        for measure_channel in range(1, 7):
                            if self.is_enabled(measure_channel - 1) and measure_channel in results:
                                kilo_watts = results[measure_channel]['power'] / 1000
                                kwh_calculated = kilo_watts * per_hour_fraction
                                self.kwh_saved[measure_channel] += kwh_calculated
                            chan += 4
                    except:
                        self.logger.exception("acquiring measurements")
                    finally:
                        lf.lock_release(self.lock_file)
            time.sleep(0.01)

    def get_measurement(self):
        self.return_dict = copy.deepcopy(measurements_dict)

        results = self.sensor.get_power_measurements(duration=0.5)

        if self.is_enabled(0):
            self.value_set(0, results['voltage'])

        chan = 1
        for measure_channel in range(1, 7):
            if self.is_enabled(measure_channel - 1) and measure_channel in results:
                self.value_set(chan, results[measure_channel]['power'])
                self.value_set(chan + 2, results[measure_channel]['current'])
                self.value_set(chan + 3, results[measure_channel]['pf'])
            chan += 4

        # Save kWh calculations to DB
        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=10):
            try:
                self.set_custom_option("kwh_saved", self.kwh_saved)
            except:
                self.logger.exception("acquiring measurements")
            finally:
                lf.lock_release(self.lock_file)

        return self.return_dict

    def clear_channel(self, args_dict):
        if 'channel_to_clear' not in args_dict or not args_dict['channel_to_clear']:
            self.logger.error("channel_to_clear is required")
            return
        try:
            lf = LockFile()
            if lf.lock_acquire(self.lock_file, timeout=10):
                try:
                    if args_dict['channel_to_clear'] == 'all':
                        self.kwh_saved[1] = 0
                        self.kwh_saved[2] = 0
                        self.kwh_saved[3] = 0
                        self.kwh_saved[4] = 0
                        self.kwh_saved[5] = 0
                        self.kwh_saved[6] = 0
                    else:
                        self.kwh_saved[int(args_dict['channel_to_clear'])] = 0

                    self.set_custom_option("kwh_saved", self.kwh_saved)
                except:
                    self.logger.exception(f"Clearing kWH for channel: {args_dict['channel_to_clear']}")
                finally:
                    lf.lock_release(self.lock_file)
        except Exception as err:
            self.logger.error(f"Error clearing kWh for channel {args_dict['channel_to_clear']}: {err}")

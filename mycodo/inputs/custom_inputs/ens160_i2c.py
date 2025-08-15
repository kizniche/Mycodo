# coding=utf-8
"""
Custom Input: ENS160 Gas Sensor (I2C via Adafruit CircuitPython)

This custom Input reads eCO2 (ppm) and TVOC (ppb) from the ScioSense/ENSO ENS160
sensor using the Adafruit CircuitPython ENS160 library and Adafruit-extended-bus
for selecting the I2C bus by number.

Installation notes:
- Declare and install dependencies from the Mycodo UI before activating this Input.
- Wire the sensor to your device's I2C interface and select the correct I2C bus
  and address (default address is typically 0x53 for many ENS160 breakouts; check
  your board's documentation).

References:
- Adafruit ENS160 library: https://github.com/adafruit/Adafruit_CircuitPython_ENS160
- Product Learn Guide: https://learn.adafruit.com

This module follows patterns used by other CircuitPython-based inputs in Mycodo.
"""

import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements: mirror common gas sensor IDs used in other inputs (e.g., CCS811)
# 0: eCO2 in ppm (measurement ID: 'co2')
# 1: TVOC in ppb (measurement ID: 'voc')
# 2: AQI as a unitless index (measurement ID: 'unitless')
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    },
    1: {
        'measurement': 'voc',
        'unit': 'ppb'
    },
    2: {
        'measurement': 'unitless',
        'unit': 'none'
    }
}

INPUT_INFORMATION = {
    'input_name_unique': 'ENS160_CP',
    'input_manufacturer': 'ScioSense',
    'input_name': 'ENS160 (CO2/VOC/AQI)',
    'input_name_short': 'ENS160',
    'input_library': 'Adafruit_CircuitPython_ENS160',
    'measurements_name': 'CO2/VOC/AQI',
    'measurements_dict': measurements_dict,

    'message': 'Reads eCO2 (ppm), TVOC (ppb), and AQI (index) from the ENS160 over I2C. '
               'Optionally configure temperature/humidity compensation by selecting other Inputs that provide '
               'Temperature (C) and Humidity (%) measurements.',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        # Extended I2C bus selection by bus number
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        # ENS160 CircuitPython library
        ('pip-pypi', 'adafruit_ens160', 'adafruit-circuitpython-ens160==1.0.12')
    ],

    'interfaces': ['I2C'],
    # Common default address for ENS160 breakouts (verify for your board)
    'i2c_location': ['0x53', '0x52'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'temp_comp_measurement',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': 'Temperature Compensation Source',
            'phrase': 'Enter DeviceID,MeasurementID (e.g. 12345678,abcd-efgh...) providing Temperature.'
        },
        {
            'id': 'temp_comp_max_age',
            'type': 'integer',
            'default_value': 600,
            'required': False,
            'name': 'Temp Source Max Age (s)',
            'phrase': 'Maximum age in seconds for the temperature value to be considered valid.'
        },
        {
            'id': 'humid_comp_measurement',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': 'Humidity Compensation Source',
            'phrase': 'Enter DeviceID,MeasurementID providing Humidity (% or decimal).'
        },
        {
            'id': 'humid_comp_max_age',
            'type': 'integer',
            'default_value': 600,
            'required': False,
            'name': 'Humidity Source Max Age (s)',
            'phrase': 'Maximum age in seconds for the humidity value to be considered valid.'
        },
        {  # Calibration: eCO2
            'id': 'eco2_offset_ppm',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'name': 'eCO2 Offset (ppm)',
            'phrase': 'Additive offset applied to eCO2 after scaling.'
        },
        {
            'id': 'eco2_scale',
            'type': 'float',
            'default_value': 1.0,
            'required': False,
            'name': 'eCO2 Scale',
            'phrase': 'Multiplicative scale applied to eCO2 before offset.'
        },
        {  # Calibration: TVOC
            'id': 'tvoc_offset_ppb',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'name': 'TVOC Offset (ppb)',
            'phrase': 'Additive offset applied to TVOC after scaling.'
        },
        {
            'id': 'tvoc_scale',
            'type': 'float',
            'default_value': 1.0,
            'required': False,
            'name': 'TVOC Scale',
            'phrase': 'Multiplicative scale applied to TVOC before offset.'
        },
        {  # Calibration: AQI
            'id': 'aqi_offset',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'name': 'AQI Offset',
            'phrase': 'Additive offset applied to AQI after scaling.'
        },
        {
            'id': 'aqi_scale',
            'type': 'float',
            'default_value': 1.0,
            'required': False,
            'name': 'AQI Scale',
            'phrase': 'Multiplicative scale applied to AQI before offset.'
        }
    ],

    'custom_commands_message': 'Calibration tools: set a target to compute offsets from current raw readings, or reset.',
    'custom_commands': [
        { 'type': 'message', 'default_value': 'Calibration: Enter a target value and press Calibrate to set offset based on current raw reading.' },
        { 'id': 'eco2_target', 'type': 'float', 'default_value': 400.0, 'name': 'eCO2 Target (ppm)', 'phrase': 'Typical fresh air baseline ~400 ppm' },
        { 'id': 'calibrate_eco2_to_target', 'type': 'button', 'name': 'Calibrate eCO2 to Target', 'wait_for_return': True },
        { 'type': 'new_line' },
        { 'id': 'tvoc_target', 'type': 'float', 'default_value': 0.0, 'name': 'TVOC Target (ppb)', 'phrase': 'Often calibrated to 0 ppb in clean air' },
        { 'id': 'calibrate_tvoc_to_target', 'type': 'button', 'name': 'Calibrate TVOC to Target', 'wait_for_return': True },
        { 'type': 'new_line' },
        { 'id': 'aqi_target', 'type': 'float', 'default_value': 1.0, 'name': 'AQI Target (index)', 'phrase': 'Library AQI scale; adjust if needed' },
        { 'id': 'calibrate_aqi_to_target', 'type': 'button', 'name': 'Calibrate AQI to Target', 'wait_for_return': True },
        { 'type': 'new_line' },
        { 'id': 'reset_calibration', 'type': 'button', 'name': 'Reset Calibration (Offsets=0, Scales=1)', 'wait_for_return': True }
    ]
}


class InputModule(AbstractInput):
    """ENS160 sensor support class (I2C, Adafruit CircuitPython)."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        # Custom options for compensation
        self.temp_comp_measurement = None
        self.temp_comp_max_age = None
        self.humid_comp_measurement = None
        self.humid_comp_max_age = None

        if not testing:
            # Load custom options
            if 'custom_options' in INPUT_INFORMATION:
                self.setup_custom_options(INPUT_INFORMATION['custom_options'], input_dev)
            # Attempt to initialize immediately so activation can start reading
            self.try_initialize()

    def initialize(self):
        # Import CircuitPython libraries at runtime to avoid import errors during discovery
        from adafruit_ens160 import ENS160
        from adafruit_extended_bus import ExtendedI2C

        # Create sensor with selected bus and address from Mycodo's Input config
        i2c = ExtendedI2C(self.input_dev.i2c_bus)
        address = int(str(self.input_dev.i2c_location), 16)
        self.sensor = ENS160(i2c, address=address)

        # ENS160 supports operation modes; default is standard mode. If needed:
        # self.sensor.operation_mode = 0x02  # Standard mode

    def _apply_compensation(self):
        """Fetch compensation values from other Inputs and set them on the sensor, if available."""
        try:
            if not self.sensor:
                return

            # Lazy imports to avoid overhead
            from mycodo.utils.system_pi import get_measurement as get_dev_meas, return_measurement_info
            from mycodo.utils.influx import read_influxdb_single
            from mycodo.databases.models import Conversion
            from mycodo.utils.database import db_retrieve_table_daemon
            from mycodo.inputs.sensorutils import convert_from_x_to_y_unit

            # Temperature compensation
            if self.temp_comp_measurement and ',' in str(self.temp_comp_measurement):
                dev_id, meas_id = [x.strip() for x in str(self.temp_comp_measurement).split(',', 1)]
                device_measurement = get_dev_meas(meas_id)
                if device_measurement:
                    conversion = db_retrieve_table_daemon(Conversion, unique_id=device_measurement.conversion_id)
                    channel, unit, measurement = return_measurement_info(device_measurement, conversion)
                    last = read_influxdb_single(
                        dev_id,
                        unit,
                        channel,
                        measure=measurement,
                        duration_sec=int(self.temp_comp_max_age) if self.temp_comp_max_age else None,
                        value='LAST'
                    )
                    temp_c = None
                    if last and last[1] is not None:
                        # Convert to Celsius if needed
                        try:
                            temp_c = convert_from_x_to_y_unit(unit, 'C', float(last[1])) if unit != 'C' else float(last[1])
                        except Exception:
                            temp_c = float(last[1]) if unit == 'C' else None
                    if temp_c is not None:
                        # Try several attribute names for compatibility across library versions
                        for attr in ('temperature_compensation', 'compensated_temperature', 'ambient_temperature'):
                            if hasattr(self.sensor, attr):
                                try:
                                    setattr(self.sensor, attr, float(temp_c))
                                    break
                                except Exception:
                                    pass

            # Humidity compensation
            if self.humid_comp_measurement and ',' in str(self.humid_comp_measurement):
                dev_id, meas_id = [x.strip() for x in str(self.humid_comp_measurement).split(',', 1)]
                device_measurement = get_dev_meas(meas_id)
                if device_measurement:
                    conversion = db_retrieve_table_daemon(Conversion, unique_id=device_measurement.conversion_id)
                    channel, unit, measurement = return_measurement_info(device_measurement, conversion)
                    last = read_influxdb_single(
                        dev_id,
                        unit,
                        channel,
                        measure=measurement,
                        duration_sec=int(self.humid_comp_max_age) if self.humid_comp_max_age else None,
                        value='LAST'
                    )
                    rh = None
                    if last and last[1] is not None:
                        try:
                            rh = convert_from_x_to_y_unit(unit, 'percent', float(last[1])) if unit != 'percent' else float(last[1])
                        except Exception:
                            # Fallback: if decimal 0-1, convert to percent
                            try:
                                val = float(last[1])
                                if 0.0 <= val <= 1.0:
                                    rh = val * 100.0
                            except Exception:
                                rh = None
                    if rh is not None:
                        for attr in ('humidity_compensation', 'relative_humidity_compensation', 'ambient_humidity'):
                            if hasattr(self.sensor, attr):
                                try:
                                    setattr(self.sensor, attr, float(rh))
                                    break
                                except Exception:
                                    pass
        except Exception:
            self.logger.exception("Error applying temperature/humidity compensation")

    def _read_raw_current(self):
        """Read raw values directly from sensor properties without calibration.
        Returns dict with keys: eco2, tvoc, aqi (aqi may be None if not available).
        """
        if not self.sensor:
            return None
        try:
            eco2 = getattr(self.sensor, 'eco2', None)
            tvoc = getattr(self.sensor, 'tvoc', None)
            # Try both names for AQI
            aqi_val = None
            try:
                aqi_val = getattr(self.sensor, 'aqi', None)
                if aqi_val is None:
                    aqi_val = getattr(self.sensor, 'AQI', None)
            except Exception:
                aqi_val = None
            return {'eco2': eco2, 'tvoc': tvoc, 'aqi': aqi_val}
        except Exception:
            self.logger.exception("_read_raw_current() failed")
            return None

    def calibrate_eco2_to_target(self, args_dict):
        try:
            target = float(args_dict.get('eco2_target'))
        except Exception:
            self.logger.error("Calibration: Invalid eCO2 target")
            return "Invalid eCO2 target"
        vals = self._read_raw_current()
        if not vals or vals.get('eco2') is None:
            self.logger.error("Calibration: Could not read raw eCO2 from sensor")
            return "No raw eCO2 available"
        try:
            scale = float(self.eco2_scale) if self.eco2_scale is not None else 1.0
            offset = target - (float(vals['eco2']) * scale)
            self.set_custom_option('eco2_offset_ppm', offset)
            self.eco2_offset_ppm = offset
            self.logger.info(f"eCO2 calibration set. Scale={scale}, Offset={offset}")
            return f"eCO2 offset set to {offset:.3f}"
        except Exception:
            self.logger.exception("calibrate_eco2_to_target() failed")
            return "Calibration error"

    def calibrate_tvoc_to_target(self, args_dict):
        try:
            target = float(args_dict.get('tvoc_target'))
        except Exception:
            self.logger.error("Calibration: Invalid TVOC target")
            return "Invalid TVOC target"
        vals = self._read_raw_current()
        if not vals or vals.get('tvoc') is None:
            self.logger.error("Calibration: Could not read raw TVOC from sensor")
            return "No raw TVOC available"
        try:
            scale = float(self.tvoc_scale) if self.tvoc_scale is not None else 1.0
            offset = target - (float(vals['tvoc']) * scale)
            self.set_custom_option('tvoc_offset_ppb', offset)
            self.tvoc_offset_ppb = offset
            self.logger.info(f"TVOC calibration set. Scale={scale}, Offset={offset}")
            return f"TVOC offset set to {offset:.3f}"
        except Exception:
            self.logger.exception("calibrate_tvoc_to_target() failed")
            return "Calibration error"

    def calibrate_aqi_to_target(self, args_dict):
        try:
            target = float(args_dict.get('aqi_target'))
        except Exception:
            self.logger.error("Calibration: Invalid AQI target")
            return "Invalid AQI target"
        vals = self._read_raw_current()
        if not vals or vals.get('aqi') is None:
            self.logger.error("Calibration: Could not read raw AQI from sensor")
            return "No raw AQI available"
        try:
            scale = float(self.aqi_scale) if self.aqi_scale is not None else 1.0
            offset = target - (float(vals['aqi']) * scale)
            self.set_custom_option('aqi_offset', offset)
            self.aqi_offset = offset
            self.logger.info(f"AQI calibration set. Scale={scale}, Offset={offset}")
            return f"AQI offset set to {offset:.3f}"
        except Exception:
            self.logger.exception("calibrate_aqi_to_target() failed")
            return "Calibration error"

    def reset_calibration(self, args_dict):
        try:
            for key, val in [('eco2_offset_ppm', 0.0), ('tvoc_offset_ppb', 0.0), ('aqi_offset', 0.0),
                             ('eco2_scale', 1.0), ('tvoc_scale', 1.0), ('aqi_scale', 1.0)]:
                self.set_custom_option(key, val)
                setattr(self, key, val)
            self.logger.info("Calibration reset to defaults: offsets=0, scales=1")
            return "Calibration reset"
        except Exception:
            self.logger.exception("reset_calibration() failed")
            return "Calibration reset failed"

    def get_measurement(self):
        """Gets the eCO2 and TVOC measurements from the sensor."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        # Prepare fresh return dict
        self.return_dict = copy.deepcopy(measurements_dict)

        # Apply compensation if configured
        self._apply_compensation()

        # Read values from the sensor. Library properties expected: .eco2, .tvoc
        try:
            # Raw readings
            eco2_raw = getattr(self.sensor, 'eco2', None)
            tvoc_raw = getattr(self.sensor, 'tvoc', None)
            try:
                aqi_raw = getattr(self.sensor, 'aqi', None)
                if aqi_raw is None:
                    aqi_raw = getattr(self.sensor, 'AQI', None)
            except Exception:
                aqi_raw = None

            # Apply calibration: value = scale * raw + offset
            eco2_scale = float(self.eco2_scale) if getattr(self, 'eco2_scale', None) is not None else 1.0
            eco2_offset = float(self.eco2_offset_ppm) if getattr(self, 'eco2_offset_ppm', None) is not None else 0.0
            tvoc_scale = float(self.tvoc_scale) if getattr(self, 'tvoc_scale', None) is not None else 1.0
            tvoc_offset = float(self.tvoc_offset_ppb) if getattr(self, 'tvoc_offset_ppb', None) is not None else 0.0
            aqi_scale = float(self.aqi_scale) if getattr(self, 'aqi_scale', None) is not None else 1.0
            aqi_offset = float(self.aqi_offset) if getattr(self, 'aqi_offset', None) is not None else 0.0

            if eco2_raw is not None and self.is_enabled(0):
                self.value_set(0, eco2_scale * float(eco2_raw) + eco2_offset)

            if tvoc_raw is not None and self.is_enabled(1):
                self.value_set(1, tvoc_scale * float(tvoc_raw) + tvoc_offset)

            if aqi_raw is not None and self.is_enabled(2):
                self.value_set(2, aqi_scale * float(aqi_raw) + aqi_offset)

            return self.return_dict
        except Exception as exc:
            self.logger.error(f"Exception reading ENS160: {exc}")
            return

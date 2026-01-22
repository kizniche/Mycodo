# coding=utf-8
#
# hx711.py - Input for HX711 load cell amplifier
#
import copy

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'mass',
        'unit': 'g'
    }
}


def filter_outliers(values, mad_threshold=3.5):
    if not values:
        return values, []
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    median = sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    abs_dev = [abs(v - median) for v in values]
    abs_dev_sorted = sorted(abs_dev)
    mad = abs_dev_sorted[n // 2] if n % 2 else (abs_dev_sorted[n // 2 - 1] + abs_dev_sorted[n // 2]) / 2

    if mad == 0:
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        if std == 0:
            return values, []
        threshold = 3 * std
        keep_mask = [abs(v - mean) <= threshold for v in values]
    else:
        keep_mask = [abs(0.6745 * (v - median) / mad) <= mad_threshold for v in values]

    kept = [v for v, keep in zip(values, keep_mask) if keep]
    removed = [v for v, keep in zip(values, keep_mask) if not keep]
    if not kept:
        return values, []
    return kept, removed

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HX711',
    'input_manufacturer': 'Avia Semiconductor',
    'input_name': 'HX711 (RPi.GPIO, Legacy)',
    'input_library': 'hx711',
    'measurements_name': 'Mass',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.aviaic.com/',
    'url_datasheet': 'https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf',
    'url_product_purchase': 'https://www.amazon.com/s?k=hx711',

    'message': 'Legacy Raspberry Pi GPIO input (Pi 4 and earlier). '
               'For Raspberry Pi 5 and broad compatibility, use the HX711 (CircuitPython) input. '
               'Connect DT to a GPIO data pin and SCK to a GPIO clock pin. '
               'Use a load cell rated for your target range.',
    # Additional information hidden behind a collapsible accordion in the UI
    'message_extra':
        '<h4>4x half-bridge set (bathroom-scale style)</h4>'
        '<table class="table table-sm">'
        '<tr><th>Wire</th><th>Connect to</th></tr>'
        '<tr><td>All red</td><td>E+</td></tr>'
        '<tr><td>All black</td><td>E-</td></tr>'
        '<tr><td>Top sensor signal</td><td>A-</td></tr>'
        '<tr><td>Bottom sensor signals</td><td>A+</td></tr>'
        '</table>'
        '<p><strong>Do not</strong> short A- to E- when using a 4-loadcell set.</p>'
        '<h4>Wire identification (2 kΩ method)</h4>'
        '<p>Measure resistance between <strong>red</strong> and <strong>black</strong> on each sensor. '
        'It should be about <strong>2 kΩ</strong>. The remaining wire (yellow/white/green) is the '
        '<strong>signal</strong> lead.</p>'
        '<h4>How it works</h4>'
        '<p>A load cell uses strain gauges in a half-bridge. The HX711 measures tiny resistance changes '
        'and outputs a raw value. Apply the calibration factor to convert raw values to grams.</p>'
        '<h4>Quick verification</h4>'
        '<ol>'
        '<li>Check raw values with no load (should be stable).</li>'
        '<li>Place a known weight and confirm the raw value shifts consistently.</li>'
        '<li>Adjust the calibration factor until the reading matches grams.</li>'
        '</ol>'
        '<h4>Recommended ranges</h4>'
        '<p>This setup has been validated for heavier ranges (e.g., 1–200 kg). '
        'Calibrate near your target range (e.g., 25–40 kg if that is your target).<br>'
        'Lower ranges (e.g., 1–20 kg or 0.01–1 kg) have not been tested in this setup yet. '
        'If you use a different range, ensure the load cell and amplifier are rated for it and recalibrate accordingly.</p>'
        '<h4>Calibration findings</h4>'
        '<ul>'
        '<li>Use a rigid, flat load plate to distribute weight evenly. Point loads (wheels/feet) and flexible surfaces increase drift and variability.</li>'
        '<li>Reposition the weight between calibration runs and average multiple runs to reduce placement bias.</li>'
        '<li>Disable zero tracking during calibration to avoid auto-adjusting tare mid-run.</li>'
        '<li>Ensure the raw value increases when weight is added. If it decreases, check wiring (A+/A- swapped or inverted bridge).</li>'
        '<li>Calibrate within your intended measurement range; very light or very heavy loads reduce accuracy.</li>'
        '</ul>'
        '<h4>Hardware notes</h4>'
        '<ul>'
        '<li>Bathroom scales are a good donor platform: four load cells with a rigid frame. You can replace the onboard ADC with an HX711 and reuse the mechanical structure.</li>'
        '<li>If you retrofit a scale, disconnect the original battery pack and power the HX711 from the Raspberry Pi 3.3V rail (do not connect both).</li>'
        '<li>Keep the load cells firmly mounted and avoid any shifting between calibrations.</li>'
        '</ul>'
        '<h4>Do</h4>'
        '<ul>'
        '<li>Calibrate with a known, stable weight in your target range.</li>'
        '<li>Keep the load placement consistent and use a flat, rigid plate to distribute weight.</li>'
        '<li>Reposition the weight between calibration runs for better averaging.</li>'
        '<li>Disable zero tracking during calibration and re-enable afterward if needed.</li>'
        '</ul>'
        '<h4>Don\'t</h4>'
        '<ul>'
        '<li>Use point loads (wheels/feet) or flexible surfaces that bend under load.</li>'
        '<li>Mix tare and calibration measurements with different placements/orientation.</li>'
        '<li>Expect stable factors if raw values drift or the signal is saturated.</li>'
        '</ul>'
        '<p>Advanced calibration runs: <code>mycodo/inputs/scripts/hx711_test.py</code>.</p>',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1'),
        ('pip-pypi', 'hx711', 'hx711==1.1.2.3')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'pin_data',
            'type': 'integer',
            'default_value': 27,
            'name': lazy_gettext('Data Pin (DT)'),
            'phrase': lazy_gettext('The GPIO pin connected to the HX711 data pin (DT/DOUT)')
        },
        {
            'id': 'pin_clock',
            'type': 'integer',
            'default_value': 21,
            'name': lazy_gettext('Clock Pin (SCK)'),
            'phrase': lazy_gettext('The GPIO pin connected to the HX711 clock pin (SCK/PD_SCK)')
        },
        {
            'id': 'channel',
            'type': 'select',
            'default_value': 'A',
            'options_select': [
                ('A', 'Channel A'),
                ('B', 'Channel B')
            ],
            'name': lazy_gettext('Channel'),
            'phrase': lazy_gettext('The HX711 channel to read from')
        },
        {
            'id': 'gain',
            'type': 'select',
            'default_value': '128',
            'options_select': [
                ('128', '128 (Channel A)'),
                ('64', '64 (Channel A)'),
                ('32', '32 (Channel B)')
            ],
            'name': lazy_gettext('Gain'),
            'phrase': lazy_gettext('The gain for the HX711. Channel A supports 128 or 64, Channel B supports 32.')
        },
        {
            'id': 'samples',
            'type': 'integer',
            'default_value': 3,
            'name': lazy_gettext('Samples'),
            'phrase': lazy_gettext('The number of samples to average for each measurement')
        },
        {
            'id': 'outlier_filter_enabled',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Outlier Filter Enabled'),
            'phrase': lazy_gettext('Filter spikes using a robust median/MAD filter before averaging')
        },
        {
            'id': 'outlier_mad_threshold',
            'type': 'float',
            'default_value': 3.5,
            'name': lazy_gettext('Outlier MAD Threshold'),
            'phrase': lazy_gettext('Lower is stricter. Typical range: 2.5–5.0')
        },
        {
            'id': 'tare_value',
            'type': 'float',
            'default_value': 0.0,
            'name': lazy_gettext('Tare Value'),
            'phrase': lazy_gettext('The raw value to subtract (tare). Set to 0 for no tare.')
        },
        {
            'id': 'calibration_factor',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Calibration Factor'),
            'phrase': lazy_gettext('The factor to convert raw value to grams. Raw value / calibration_factor = grams')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class for the HX711 load cell amplifier.
    
    The HX711 is a precision 24-bit analog-to-digital converter (ADC)
    designed for weigh scales and industrial control applications.
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.hx711 = None

        # Custom options
        self.pin_data = None
        self.pin_clock = None
        self.channel = None
        self.gain = None
        self.samples = None
        self.outlier_filter_enabled = None
        self.outlier_mad_threshold = None
        self.tare_value = None
        self.calibration_factor = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import RPi.GPIO as GPIO
        from hx711 import HX711

        GPIO.setwarnings(False)

        # Validate samples parameter
        if self.samples is None or self.samples < 1:
            self.samples = 3
            self.logger.warning("Invalid samples value, defaulting to 3")

        # Normalize and validate channel/gain combination
        channel = str(self.channel).upper() if self.channel is not None else 'A'
        try:
            gain = int(self.gain) if self.gain is not None else 128
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid HX711 gain value: {!r}".format(self.gain)
            )

        if channel not in ("A", "B"):
            raise ValueError(
                "Invalid HX711 channel: {!r}. Expected 'A' or 'B'.".format(self.channel)
            )

        if (channel == "A" and gain not in (128, 64)) or (channel == "B" and gain != 32):
            raise ValueError(
                "Invalid HX711 channel/gain combination: channel {} does not support gain {}"
                .format(channel, gain)
            )

        self.hx711 = HX711(
            dout_pin=self.pin_data,
            pd_sck_pin=self.pin_clock,
            channel=channel,
            gain=gain
        )
        self.hx711.reset()

    def get_measurement(self):
        """Get the mass measurement from the HX711."""
        if not self.hx711:
            self.logger.error(
                "Error 101: Device not set up. "
                "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            )
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            # Get raw data, averaging over samples
            # Note: get_raw_data returns a list of raw values
            raw_data = self.hx711.get_raw_data(times=self.samples or 3)

            # Validate raw_data is a non-empty list before arithmetic operations
            if not isinstance(raw_data, list) or not raw_data:
                self.logger.error("No data received from HX711")
                return None

            # Optionally filter outliers before averaging
            if self.outlier_filter_enabled:
                threshold = self.outlier_mad_threshold if self.outlier_mad_threshold is not None else 3.5
                filtered, removed = filter_outliers(raw_data, mad_threshold=threshold)
                if removed and hasattr(self, "logger") and self.logger:
                    self.logger.debug(
                        "HX711 outlier filter removed %s samples (threshold=%s)",
                        len(removed),
                        threshold
                    )
                raw_data = filtered

            # Calculate average from the list of samples
            raw_average = sum(raw_data) / len(raw_data)

            # Apply tare
            tare = self.tare_value if self.tare_value is not None else 0.0
            tared_value = raw_average - tare

            # Apply calibration factor to get grams
            cal_factor = self.calibration_factor if self.calibration_factor else 1.0
            if cal_factor != 0:
                mass_grams = tared_value / cal_factor
            else:
                mass_grams = tared_value

            self.value_set(0, mass_grams)

            return self.return_dict

        except Exception as e:
            self.logger.error("Error reading HX711: {err}".format(err=e))
            return None

    def stop_input(self):
        """Called when the input is stopped."""
        try:
            import RPi.GPIO as GPIO
            # Only cleanup the specific pins used by this HX711 instance
            pins_to_cleanup = [pin for pin in (self.pin_data, self.pin_clock) if pin is not None]
            if pins_to_cleanup:
                GPIO.cleanup(pins_to_cleanup)
        except Exception as exc:
            # Ignore GPIO cleanup errors during shutdown but log for diagnostics
            if hasattr(self, "logger") and self.logger:
                self.logger.debug("HX711 GPIO cleanup failed: %s", exc, exc_info=True)

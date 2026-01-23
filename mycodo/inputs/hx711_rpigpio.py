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
        'unit': 'g',
        'name': 'Channel A'
    },
    1: {
        'measurement': 'mass',
        'unit': 'g',
        'name': 'Channel B'
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
    'measurements_name': 'Mass (Channel A, Channel B)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.aviaic.com/',
    'url_datasheet': 'https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf',
    'url_product_purchase': 'https://www.amazon.com/s?k=hx711',

    'message': 'Dual-channel HX711 input using legacy RPi.GPIO (Pi 4 and earlier only). '
               'For Raspberry Pi 5 and broad compatibility, use the HX711 (CircuitPython) input. '
               'Supports simultaneous measurement on Channel A and Channel B. '
               'Each channel has independent tare and calibration settings.',
    # Additional information hidden behind a collapsible accordion in the UI
    'message_extra':
        '<h4>Dual-Channel Operation</h4>'
        '<p>The HX711 has two input channels:</p>'
        '<ul>'
        '<li><strong>Channel A</strong>: Supports gain 128 or 64. Connect your primary load cell(s) here.</li>'
        '<li><strong>Channel B</strong>: Fixed gain 32. Use for a second load cell or load cell group.</li>'
        '</ul>'
        '<p>Each channel has its own tare value and calibration factor. Enable both channels to measure '
        'two independent weights simultaneously (e.g., water reservoir on A, nutrient tank on B).</p>'
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
        '<li><strong>Calibrate each channel separately</strong> if using dual-channel mode.</li>'
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
            'id': 'section_general',
            'type': 'message',
            'default_value': '<strong>General Settings</strong>',
        },
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
            'type': 'new_line'
        },
        {
            'id': 'section_channel_a',
            'type': 'message',
            'default_value': '<strong>Channel A Settings</strong>',
        },
        {
            'id': 'channel_a_enabled',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Channel A Enabled'),
            'phrase': lazy_gettext('Enable Channel A measurement')
        },
        {
            'id': 'gain_a',
            'type': 'select',
            'default_value': '128',
            'options_select': [
                ('128', '128'),
                ('64', '64')
            ],
            'name': lazy_gettext('Gain (Channel A)'),
            'phrase': lazy_gettext('The gain for Channel A (128 or 64)')
        },
        {
            'id': 'tare_value_a',
            'type': 'float',
            'default_value': 0.0,
            'name': lazy_gettext('Tare Value (Channel A)'),
            'phrase': lazy_gettext('The raw value to subtract for Channel A. Set to 0 for no tare.')
        },
        {
            'id': 'calibration_factor_a',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Calibration Factor (Channel A)'),
            'phrase': lazy_gettext('The factor to convert Channel A raw value to grams')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'section_channel_b',
            'type': 'message',
            'default_value': '<strong>Channel B Settings</strong>',
        },
        {
            'id': 'channel_b_enabled',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Channel B Enabled'),
            'phrase': lazy_gettext('Enable Channel B measurement')
        },
        {
            'id': 'tare_value_b',
            'type': 'float',
            'default_value': 0.0,
            'name': lazy_gettext('Tare Value (Channel B)'),
            'phrase': lazy_gettext('The raw value to subtract for Channel B. Set to 0 for no tare.')
        },
        {
            'id': 'calibration_factor_b',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Calibration Factor (Channel B)'),
            'phrase': lazy_gettext('The factor to convert Channel B raw value to grams')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'section_sampling',
            'type': 'message',
            'default_value': '<strong>Sampling & Filtering</strong>',
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
        }
    ],

    'custom_commands_message':
        '<strong>Calibration Wizard</strong><br>'
        'Use these buttons to calibrate your load cell. The wizard uses MAD outlier filtering '
        'for robust measurements. For best results:<br>'
        '<ul>'
        '<li>Ensure the scale is stable and not vibrating</li>'
        '<li>Remove all weight before tare calibration</li>'
        '<li>Use a known, accurate calibration weight</li>'
        '<li>Reposition the weight between factor calibration runs</li>'
        '</ul>'
        '<em>💡 Press F5 after calibration to see the new values in the settings fields.</em>',

    'custom_commands': [
        {
            'id': 'section_tare_cal',
            'type': 'message',
            'default_value': '<strong>Tare Calibration</strong> — Remove all weight from scale',
        },
        {
            'id': 'tare_channel_select',
            'type': 'select',
            'default_value': 'a',
            'options_select': [
                ('a', 'Channel A'),
                ('b', 'Channel B')
            ],
            'name': lazy_gettext('Channel for Tare'),
            'phrase': lazy_gettext('Select which channel to calibrate')
        },
        {
            'id': 'tare_samples',
            'type': 'integer',
            'default_value': 20,
            'name': lazy_gettext('Tare Samples'),
            'phrase': lazy_gettext('Number of samples to collect for tare (default: 20)')
        },
        {
            'id': 'calibrate_tare',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Calibrate Tare')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'section_factor_cal',
            'type': 'message',
            'default_value': '<strong>Factor Calibration</strong> — Place known weight on scale',
        },
        {
            'id': 'factor_channel_select',
            'type': 'select',
            'default_value': 'a',
            'options_select': [
                ('a', 'Channel A'),
                ('b', 'Channel B')
            ],
            'name': lazy_gettext('Channel for Factor'),
            'phrase': lazy_gettext('Select which channel to calibrate')
        },
        {
            'id': 'known_weight_grams',
            'type': 'float',
            'default_value': 1000.0,
            'name': lazy_gettext('Known Weight (grams)'),
            'phrase': lazy_gettext('The exact weight of your calibration object in grams')
        },
        {
            'id': 'factor_samples_per_run',
            'type': 'integer',
            'default_value': 20,
            'name': lazy_gettext('Samples per Run'),
            'phrase': lazy_gettext('Number of samples per calibration run (default: 20)')
        },
        {
            'id': 'factor_runs',
            'type': 'integer',
            'default_value': 3,
            'name': lazy_gettext('Number of Runs'),
            'phrase': lazy_gettext('Number of runs to average (default: 3, total 60 samples)')
        },
        {
            'id': 'calibrate_factor',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Calibrate Factor')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'section_quick_actions',
            'type': 'message',
            'default_value': '<strong>Quick Actions</strong>',
        },
        {
            'id': 'clear_calibration_channel',
            'type': 'select',
            'default_value': 'a',
            'options_select': [
                ('a', 'Channel A'),
                ('b', 'Channel B'),
                ('both', 'Both Channels')
            ],
            'name': lazy_gettext('Channel to Clear'),
            'phrase': lazy_gettext('Select which channel calibration to reset')
        },
        {
            'id': 'clear_calibration',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Reset Calibration to Defaults')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class for the HX711 load cell amplifier.

    The HX711 is a precision 24-bit analog-to-digital converter (ADC)
    designed for weigh scales and industrial control applications.
    Supports dual-channel measurement (A and B).
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.hx711_a = None
        self.hx711_b = None

        # Custom options
        self.pin_data = None
        self.pin_clock = None
        self.channel_a_enabled = None
        self.gain_a = None
        self.channel_b_enabled = None
        self.samples = None
        self.outlier_filter_enabled = None
        self.outlier_mad_threshold = None
        self.tare_value_a = None
        self.calibration_factor_a = None
        self.tare_value_b = None
        self.calibration_factor_b = None

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

        # Validate at least one channel is enabled
        if not self.channel_a_enabled and not self.channel_b_enabled:
            raise ValueError("At least one channel must be enabled")

        # Initialize Channel A if enabled
        if self.channel_a_enabled:
            try:
                gain_a = int(self.gain_a) if self.gain_a is not None else 128
            except (TypeError, ValueError):
                gain_a = 128

            if gain_a not in (128, 64):
                gain_a = 128

            self.hx711_a = HX711(
                dout_pin=self.pin_data,
                pd_sck_pin=self.pin_clock,
                channel='A',
                gain=gain_a
            )
            self.hx711_a.reset()

        # Initialize Channel B if enabled
        if self.channel_b_enabled:
            self.hx711_b = HX711(
                dout_pin=self.pin_data,
                pd_sck_pin=self.pin_clock,
                channel='B',
                gain=32  # Channel B only supports gain 32
            )
            self.hx711_b.reset()

    def get_measurement(self):
        """Get the mass measurement from the HX711 (both channels if enabled)."""
        if not self.hx711_a and not self.hx711_b:
            self.logger.error(
                "Error 101: Device not set up. "
                "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            )
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            # Read Channel A if enabled
            if self.channel_a_enabled and self.hx711_a:
                mass_a = self._read_channel(
                    self.hx711_a,
                    self.tare_value_a,
                    self.calibration_factor_a,
                    'A'
                )
                if mass_a is not None:
                    self.value_set(0, mass_a)

            # Read Channel B if enabled
            if self.channel_b_enabled and self.hx711_b:
                mass_b = self._read_channel(
                    self.hx711_b,
                    self.tare_value_b,
                    self.calibration_factor_b,
                    'B'
                )
                if mass_b is not None:
                    self.value_set(1, mass_b)

            return self.return_dict

        except Exception as e:
            self.logger.error("Error reading HX711: {err}".format(err=e))
            return None

    def _read_channel(self, hx711_instance, tare_value, calibration_factor, channel_label):
        """Read and process data from a single HX711 channel."""
        try:
            # Get raw data, averaging over samples
            raw_data = hx711_instance.get_raw_data(times=self.samples or 3)

            # Validate raw_data
            if not isinstance(raw_data, list) or not raw_data:
                self.logger.error("No data received from HX711 Channel {}".format(channel_label))
                return None

            # Optionally filter outliers before averaging
            if self.outlier_filter_enabled:
                threshold = self.outlier_mad_threshold if self.outlier_mad_threshold is not None else 3.5
                filtered, removed = filter_outliers(raw_data, mad_threshold=threshold)
                if removed and hasattr(self, "logger") and self.logger:
                    self.logger.debug(
                        "HX711 Ch%s outlier filter removed %s samples (threshold=%s)",
                        channel_label,
                        len(removed),
                        threshold
                    )
                raw_data = filtered

            if not raw_data:
                return None

            # Calculate average from the list of samples
            raw_average = sum(raw_data) / len(raw_data)

            # Apply tare
            tare = tare_value if tare_value is not None else 0.0
            tared_value = raw_average - tare

            # Apply calibration factor to get grams
            cal_factor = calibration_factor if calibration_factor else 1.0
            if cal_factor != 0:
                mass_grams = tared_value / cal_factor
            else:
                mass_grams = tared_value

            return mass_grams

        except Exception as e:
            self.logger.error("Error reading HX711 Channel {}: {}".format(channel_label, e))
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

    # =====================================================================
    # Calibration Wizard Methods
    # =====================================================================

    def calibrate_tare(self, args_dict):
        """
        Calibrate the tare (zero) value for a channel.
        Collects samples with MAD outlier filtering and saves the average.
        """
        channel = args_dict.get('tare_channel_select', 'a').lower()
        num_samples = int(args_dict.get('tare_samples', 20))
        num_samples = max(5, min(num_samples, 100))  # Clamp to reasonable range

        self.logger.info("Starting tare calibration for Channel %s with %d samples",
                         channel.upper(), num_samples)

        # Select correct HX711 instance
        if channel == 'a':
            hx711_instance = self.hx711_a
            if not self.channel_a_enabled or not hx711_instance:
                self.logger.error("Channel A is not enabled. Enable it first.")
                return "Error: Channel A is not enabled"
        else:
            hx711_instance = self.hx711_b
            if not self.channel_b_enabled or not hx711_instance:
                self.logger.error("Channel B is not enabled. Enable it first.")
                return "Error: Channel B is not enabled"

        # Collect samples
        self.logger.info("Collecting %d tare samples...", num_samples)

        raw_values = hx711_instance.get_raw_data(times=num_samples)

        if not raw_values or len(raw_values) < 5:
            self.logger.error("Tare calibration failed: only %d valid samples collected",
                              len(raw_values) if raw_values else 0)
            return "Error: Not enough valid samples (got {}, need at least 5)".format(
                len(raw_values) if raw_values else 0)

        # Apply MAD outlier filter
        threshold = self.outlier_mad_threshold if self.outlier_mad_threshold else 3.5
        filtered, removed = filter_outliers(raw_values, mad_threshold=threshold)

        if removed:
            self.logger.info("Tare calibration: filtered out %d outliers", len(removed))

        if not filtered:
            filtered = raw_values

        # Calculate tare value
        tare_value = sum(filtered) / len(filtered)

        # Calculate statistics for logging
        raw_min = min(filtered)
        raw_max = max(filtered)
        raw_spread = raw_max - raw_min

        self.logger.info("Tare calibration results:")
        self.logger.info("  Samples: %d collected, %d after filtering", len(raw_values), len(filtered))
        self.logger.info("  Raw range: %d to %d (spread: %d)", int(raw_min), int(raw_max), int(raw_spread))
        self.logger.info("  Tare value: %.0f", tare_value)

        # Save the tare value
        if channel == 'a':
            self.tare_value_a = tare_value
            self.set_custom_option("tare_value_a", tare_value)
        else:
            self.tare_value_b = tare_value
            self.set_custom_option("tare_value_b", tare_value)

        return (
            "SUCCESS! Channel {ch} Tare Value saved: {val:.0f}\n"
            "The value is now active. Refresh the page to see it in the settings field."
        ).format(ch=channel.upper(), val=tare_value)

    def calibrate_factor(self, args_dict):
        """
        Calibrate the conversion factor for a channel using a known weight.
        Collects samples across multiple runs with MAD outlier filtering.
        """
        import time

        channel = args_dict.get('factor_channel_select', 'a').lower()
        known_weight = float(args_dict.get('known_weight_grams', 1000.0))
        samples_per_run = int(args_dict.get('factor_samples_per_run', 20))
        num_runs = int(args_dict.get('factor_runs', 3))

        # Clamp to reasonable ranges
        samples_per_run = max(5, min(samples_per_run, 50))
        num_runs = max(1, min(num_runs, 10))

        if known_weight <= 0:
            self.logger.error("Known weight must be greater than 0")
            return "Error: Known weight must be greater than 0"

        self.logger.info("Starting factor calibration for Channel %s", channel.upper())
        self.logger.info("  Known weight: %.2f g", known_weight)
        self.logger.info("  Samples per run: %d, Number of runs: %d (total: %d)",
                         samples_per_run, num_runs, samples_per_run * num_runs)

        # Select correct HX711 instance
        if channel == 'a':
            hx711_instance = self.hx711_a
            tare_value = self.tare_value_a if self.tare_value_a else 0.0
            if not self.channel_a_enabled or not hx711_instance:
                self.logger.error("Channel A is not enabled. Enable it first.")
                return "Error: Channel A is not enabled"
        else:
            hx711_instance = self.hx711_b
            tare_value = self.tare_value_b if self.tare_value_b else 0.0
            if not self.channel_b_enabled or not hx711_instance:
                self.logger.error("Channel B is not enabled. Enable it first.")
                return "Error: Channel B is not enabled"

        threshold = self.outlier_mad_threshold if self.outlier_mad_threshold else 3.5

        run_factors = []
        run_raw_averages = []

        for run in range(1, num_runs + 1):
            self.logger.info("Factor calibration run %d/%d...", run, num_runs)

            # Short delay between runs
            if run > 1:
                time.sleep(0.5)

            # Collect samples for this run
            raw_values = hx711_instance.get_raw_data(times=samples_per_run)

            if not raw_values or len(raw_values) < 5:
                self.logger.warning("Run %d: only %d valid samples, skipping",
                                    run, len(raw_values) if raw_values else 0)
                continue

            # Apply MAD filter
            filtered, removed = filter_outliers(raw_values, mad_threshold=threshold)
            if removed:
                self.logger.debug("Run %d: filtered out %d outliers", run, len(removed))

            if not filtered:
                filtered = raw_values

            # Calculate run statistics
            run_avg = sum(filtered) / len(filtered)
            run_raw_averages.append(run_avg)

            # Calculate factor for this run
            tared_value = run_avg - tare_value
            if tared_value == 0:
                self.logger.warning("Run %d: tared value is 0, cannot calculate factor", run)
                continue

            run_factor = tared_value / known_weight
            run_factors.append(run_factor)

            self.logger.info("  Run %d: raw avg=%.0f, tared=%.0f, factor=%.4f",
                             run, run_avg, tared_value, run_factor)

        if not run_factors:
            self.logger.error("Factor calibration failed: no valid runs completed")
            return "Error: No valid calibration runs completed"

        # Average all run factors
        calibration_factor = sum(run_factors) / len(run_factors)
        calibration_factor = round(calibration_factor, 4)  # Round to 4 decimals
        avg_raw = sum(run_raw_averages) / len(run_raw_averages)

        # Calculate factor spread for quality assessment
        if len(run_factors) > 1:
            factor_spread = max(run_factors) - min(run_factors)
            factor_spread_pct = (factor_spread / calibration_factor) * 100 if calibration_factor else 0
            self.logger.info("Factor spread: %.4f (%.2f%%)", factor_spread, factor_spread_pct)
            if factor_spread_pct > 5:
                self.logger.warning("High factor variation detected. Consider repositioning weight more consistently.")

        self.logger.info("Factor calibration results:")
        self.logger.info("  Successful runs: %d/%d", len(run_factors), num_runs)
        self.logger.info("  Tare value used: %.0f", tare_value)
        self.logger.info("  Average raw with weight: %.0f", avg_raw)
        self.logger.info("  Calibration factor: %.4f", calibration_factor)

        # Save the calibration factor
        if channel == 'a':
            self.calibration_factor_a = calibration_factor
            self.set_custom_option("calibration_factor_a", calibration_factor)
        else:
            self.calibration_factor_b = calibration_factor
            self.set_custom_option("calibration_factor_b", calibration_factor)

        return (
            "SUCCESS! Channel {ch} Calibration Factor saved: {val:.4f}\n"
            "Runs: {runs}/{total}, Tare used: {tare:.0f}, Avg raw: {raw:.0f}\n"
            "The value is now active. Refresh the page to see it in the settings field."
        ).format(
            ch=channel.upper(),
            val=calibration_factor,
            runs=len(run_factors),
            total=num_runs,
            tare=tare_value,
            raw=avg_raw
        )

    def clear_calibration(self, args_dict):
        """
        Reset calibration values to defaults for the selected channel(s).
        """
        channel = args_dict.get('clear_calibration_channel', 'a').lower()

        channels_to_clear = []
        if channel == 'both':
            channels_to_clear = ['a', 'b']
        else:
            channels_to_clear = [channel]

        for ch in channels_to_clear:
            if ch == 'a':
                self.tare_value_a = 0.0
                self.calibration_factor_a = 1.0
                self.delete_custom_option("tare_value_a")
                self.delete_custom_option("calibration_factor_a")
                self.logger.info("Channel A calibration reset to defaults (tare=0, factor=1.0)")
            else:
                self.tare_value_b = 0.0
                self.calibration_factor_b = 1.0
                self.delete_custom_option("tare_value_b")
                self.delete_custom_option("calibration_factor_b")
                self.logger.info("Channel B calibration reset to defaults (tare=0, factor=1.0)")

        # Reload defaults
        self.setup_custom_options(INPUT_INFORMATION['custom_options'], self.input_dev)

        if channel == 'both':
            return "Calibration reset for both channels"
        return "Calibration reset for Channel {}".format(channel.upper())

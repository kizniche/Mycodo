# coding=utf-8
#
# hx711_circuitpython.py - Input for HX711 load cell amplifier (CircuitPython)
#
import copy
import os
import sys
import time

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


def is_saturated(value):
    return value in (0x7FFFFF, 0xFFFFFFFF, -1, -0x800000)


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HX711_CIRCUITPYTHON',
    'input_manufacturer': 'Avia Semiconductor',
    'input_name': 'HX711 (CircuitPython)',
    'input_library': 'Adafruit_CircuitPython_HX711',
    'measurements_name': 'Mass (Channel A, Channel B)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.aviaic.com/',
    'url_datasheet': 'https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf',
    'url_product_purchase': 'https://www.amazon.com/s?k=hx711',

    'message': 'Uses CircuitPython/Blinka GPIO for broad compatibility. '
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
        '<h4>Zero tracking (optional)</h4>'
        '<p>Enable zero tracking to slowly correct small drift when the scale returns to empty. '
        'Use a small threshold (e.g., 1–5 g) so real loads are not auto-tared.</p>'
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
        ('apt', 'libgpiod-dev', 'libgpiod-dev'),
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_hx711', 'adafruit-circuitpython-hx711==1.1.0')
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
            'id': 'channel_b_enabled',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Channel B Enabled'),
            'phrase': lazy_gettext('Enable Channel B measurement')
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
            'id': 'zero_tracking_enabled',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Zero Tracking Enabled'),
            'phrase': lazy_gettext('Slowly correct tare drift when the scale returns to empty')
        },
        {
            'id': 'zero_tracking_threshold_g',
            'type': 'float',
            'default_value': 2.0,
            'name': lazy_gettext('Zero Tracking Threshold (g)'),
            'phrase': lazy_gettext('Only adjust tare when the measured weight is within this range')
        },
        {
            'id': 'zero_tracking_rate',
            'type': 'float',
            'default_value': 0.05,
            'name': lazy_gettext('Zero Tracking Rate'),
            'phrase': lazy_gettext('Fraction of offset corrected per measurement (0.0–1.0)')
        },
        {
            'id': 'read_delay_ms',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Read Delay (ms)'),
            'phrase': lazy_gettext('Delay between raw samples to improve stability on Linux GPIO')
        },
        {
            'id': 'max_retries',
            'type': 'integer',
            'default_value': 3,
            'name': lazy_gettext('Max Retries'),
            'phrase': lazy_gettext('Retries for saturated or invalid samples')
        },
        {
            'id': 'clock_delay_us',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Clock Delay (µs)'),
            'phrase': lazy_gettext('Delay per HX711 clock pulse')
        },
        {
            'id': 'ready_timeout_ms',
            'type': 'float',
            'default_value': 100.0,
            'name': lazy_gettext('Ready Timeout (ms)'),
            'phrase': lazy_gettext('Timeout waiting for HX711 ready')
        },
        {
            'id': 'invalid_sample_filter',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Filter Invalid Samples'),
            'phrase': lazy_gettext('Discard saturated samples (0x7FFFFF/0x800000)')
        },
        {
            'id': 'auto_gain_fallback',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Auto Gain Fallback'),
            'phrase': lazy_gettext('Retry A/64 and B/32 when saturated samples occur')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class for the HX711 load cell amplifier.

    Uses the Adafruit CircuitPython HX711 library, which supports Raspberry Pi 5
    and other platforms via Blinka.
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.hx711 = None
        self.data_pin = None
        self.clock_pin = None
        self.channel_gain_a = None
        self.channel_gain_b = None

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
        self.read_delay_ms = None
        self.max_retries = None
        self.clock_delay_us = None
        self.ready_timeout_ms = None
        self.invalid_sample_filter = None
        self.auto_gain_fallback = None
        self.zero_tracking_enabled = None
        self.zero_tracking_threshold_g = None
        self.zero_tracking_rate = None
        self.tare_value_runtime_a = None
        self.tare_value_runtime_b = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        self._ensure_rpi_module()

        import board
        import digitalio
        import microcontroller
        from adafruit_hx711.hx711 import HX711

        if getattr(microcontroller, "disable_interrupts", None) is None:
            setattr(microcontroller, "disable_interrupts", lambda: None)
        if getattr(microcontroller, "enable_interrupts", None) is None:
            setattr(microcontroller, "enable_interrupts", lambda: None)

        # Validate samples parameter
        if self.samples is None or self.samples < 1:
            self.samples = 3
            if hasattr(self, "logger") and self.logger:
                self.logger.warning("Invalid samples value, defaulting to 3")

        if self.read_delay_ms is None or self.read_delay_ms < 0:
            self.read_delay_ms = 1.0
        if self.max_retries is None or self.max_retries < 0:
            self.max_retries = 3
        if self.clock_delay_us is None or self.clock_delay_us < 0:
            self.clock_delay_us = 1.0
        if self.ready_timeout_ms is None or self.ready_timeout_ms < 0:
            self.ready_timeout_ms = 100.0
        if self.invalid_sample_filter is None:
            self.invalid_sample_filter = True
        if self.auto_gain_fallback is None:
            self.auto_gain_fallback = True
        if self.zero_tracking_enabled is None:
            self.zero_tracking_enabled = False
        if self.zero_tracking_threshold_g is None or self.zero_tracking_threshold_g < 0:
            self.zero_tracking_threshold_g = 2.0
        if self.zero_tracking_rate is None or self.zero_tracking_rate < 0:
            self.zero_tracking_rate = 0.05
        if self.zero_tracking_rate > 1.0:
            self.zero_tracking_rate = 1.0
        if self.tare_value_runtime_a is None:
            self.tare_value_runtime_a = self.tare_value_a if self.tare_value_a is not None else 0.0
        if self.tare_value_runtime_b is None:
            self.tare_value_runtime_b = self.tare_value_b if self.tare_value_b is not None else 0.0

        def _delay_us(us):
            target_us = max(float(us), float(self.clock_delay_us or 0.0))
            start_ns = time.perf_counter_ns()
            target_ns = int(target_us * 1000.0)
            while (time.perf_counter_ns() - start_ns) < target_ns:
                pass

        microcontroller.delay_us = _delay_us

        # Validate at least one channel is enabled
        if not self.channel_a_enabled and not self.channel_b_enabled:
            raise ValueError("At least one channel must be enabled")

        if self.pin_data is None or self.pin_clock is None:
            raise ValueError("Both data and clock pins must be set")

        # Set up channel gains
        try:
            gain_a = int(self.gain_a) if self.gain_a is not None else 128
        except (TypeError, ValueError):
            gain_a = 128

        if gain_a not in (128, 64):
            gain_a = 128

        self.channel_gain_a = HX711.CHAN_A_GAIN_128 if gain_a == 128 else HX711.CHAN_A_GAIN_64
        self.channel_gain_b = HX711.CHAN_B_GAIN_32  # Channel B only supports gain 32

        bcm_to_board = [
            board.D1,
            board.D2,
            board.D3,
            board.D4,
            board.D5,
            board.D6,
            board.D7,
            board.D8,
            board.D9,
            board.D10,
            board.D11,
            board.D12,
            board.D13,
            board.D14,
            board.D15,
            board.D16,
            board.D17,
            board.D18,
            board.D19,
            board.D20,
            board.D21,
            board.D22,
            board.D23,
            board.D24,
            board.D25,
            board.D26,
            board.D27
        ]

        self.data_pin = digitalio.DigitalInOut(bcm_to_board[self.pin_data - 1])
        self.data_pin.direction = digitalio.Direction.INPUT
        self.clock_pin = digitalio.DigitalInOut(bcm_to_board[self.pin_clock - 1])
        self.clock_pin.direction = digitalio.Direction.OUTPUT
        self.clock_pin.value = False

        self.hx711 = HX711(self.data_pin, self.clock_pin)
        # Initialize by reading once
        try:
            if self.channel_a_enabled:
                _ = self.hx711.read(self.channel_gain_a)
            elif self.channel_b_enabled:
                _ = self.hx711.read(self.channel_gain_b)
        except Exception:
            pass

    @staticmethod
    def _ensure_rpi_module():
        try:
            import RPi.GPIO  # noqa: F401
            return
        except Exception:
            pass

        for candidate in ("/usr/lib/python3/dist-packages", "/usr/lib/python3.11/dist-packages"):
            if os.path.isdir(candidate) and candidate not in sys.path:
                sys.path.append(candidate)

        try:
            import RPi.GPIO as _RPi_check  # noqa: F401,F811
        except Exception:
            pass

    def get_measurement(self):
        """Get the mass measurement from the HX711 (both channels if enabled)."""
        if not self.hx711:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(
                    "Error 101: Device not set up. "
                    "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
                )
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            delay_s = max(0.0, (self.read_delay_ms or 0) / 1000.0)
            retries = max(0, int(self.max_retries or 0))
            samples_target = self.samples or 3
            max_attempts = max(samples_target * max(retries, 1), samples_target)

            # Read Channel A if enabled
            if self.channel_a_enabled:
                raw_data_a = self._read_channel_samples(
                    self.channel_gain_a, samples_target, max_attempts, delay_s
                )
                if raw_data_a:
                    mass_a = self._process_channel_data(
                        raw_data_a,
                        self.tare_value_a,
                        self.calibration_factor_a,
                        'a'
                    )
                    if mass_a is not None:
                        self.value_set(0, mass_a)

            # Read Channel B if enabled
            if self.channel_b_enabled:
                raw_data_b = self._read_channel_samples(
                    self.channel_gain_b, samples_target, max_attempts, delay_s
                )
                if raw_data_b:
                    mass_b = self._process_channel_data(
                        raw_data_b,
                        self.tare_value_b,
                        self.calibration_factor_b,
                        'b'
                    )
                    if mass_b is not None:
                        self.value_set(1, mass_b)

            return self.return_dict

        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error("Error reading HX711: {err}".format(err=e))
            return None

    def _read_channel_samples(self, channel_gain, samples_target, max_attempts, delay_s):
        """Read raw samples from a specific channel."""
        raw_data = []
        attempts = 0

        while len(raw_data) < samples_target and attempts < max_attempts:
            attempts += 1
            sample = self._read_with_timeout(channel_gain)
            if is_saturated(sample):
                if self.auto_gain_fallback:
                    sample = self._read_fallback_sample(channel_gain)
                if self.invalid_sample_filter and is_saturated(sample):
                    if delay_s:
                        time.sleep(delay_s)
                    continue
            if sample is None:
                if delay_s:
                    time.sleep(delay_s)
                continue
            raw_data.append(sample)
            if delay_s:
                time.sleep(delay_s)

        return raw_data

    def _process_channel_data(self, raw_data, tare_config, cal_factor_config, channel_id):
        """Process raw data into calibrated mass value with optional zero tracking."""
        if not raw_data:
            return None

        # Apply outlier filter if enabled
        if self.outlier_filter_enabled:
            threshold = self.outlier_mad_threshold if self.outlier_mad_threshold is not None else 3.5
            filtered, removed = filter_outliers(raw_data, mad_threshold=threshold)
            if removed and hasattr(self, "logger") and self.logger:
                self.logger.debug(
                    "HX711 Ch%s outlier filter removed %s samples (threshold=%s)",
                    channel_id.upper(),
                    len(removed),
                    threshold
                )
            raw_data = filtered

        if not raw_data:
            return None

        raw_average = sum(raw_data) / len(raw_data)

        # Get runtime tare (allows for zero tracking adjustment)
        tare_runtime_attr = 'tare_value_runtime_{}'.format(channel_id)
        tare_config_val = tare_config if tare_config is not None else 0.0
        if getattr(self, tare_runtime_attr, None) is None:
            setattr(self, tare_runtime_attr, tare_config_val)
        tare = getattr(self, tare_runtime_attr)
        tared_value = raw_average - tare

        # Apply calibration factor
        cal_factor = cal_factor_config if cal_factor_config else 1.0
        if cal_factor != 0:
            mass_grams = tared_value / cal_factor
        else:
            mass_grams = tared_value

        # Zero tracking
        if self.zero_tracking_enabled and cal_factor:
            threshold_g = self.zero_tracking_threshold_g if self.zero_tracking_threshold_g is not None else 0.0
            if abs(mass_grams) <= threshold_g:
                rate = self.zero_tracking_rate if self.zero_tracking_rate is not None else 0.0
                rate = max(0.0, min(rate, 1.0))
                if rate:
                    new_tare = getattr(self, tare_runtime_attr) + tared_value * rate
                    setattr(self, tare_runtime_attr, new_tare)
                    tared_value = raw_average - new_tare
                    mass_grams = tared_value / cal_factor if cal_factor != 0 else tared_value

        return mass_grams

    def stop_input(self):
        """Called when the input is stopped."""
        try:
            if self.data_pin:
                self.data_pin.deinit()
            if self.clock_pin:
                self.clock_pin.deinit()
        except Exception as exc:
            if hasattr(self, "logger") and self.logger:
                self.logger.debug("HX711 GPIO cleanup failed: %s", exc, exc_info=True)

    def _read_fallback_sample(self, primary_gain):
        """Try alternate gains quickly if the primary sample is saturated."""
        if not self.hx711:
            return None
        fallbacks = [
            (self.channel_gain_a, "A"),
            (self.channel_gain_b, "B/32")
        ]
        for gain_value, label in fallbacks:
            if gain_value == primary_gain:
                continue
            if gain_value is None:
                continue
            try:
                value = self._read_with_timeout(gain_value)
                if not is_saturated(value):
                    return value
            except Exception:
                if hasattr(self, "logger") and self.logger:
                    self.logger.debug("HX711 fallback read failed (%s)", label)
        return self._read_with_timeout(primary_gain)

    def _read_with_timeout(self, channel_gain):
        if not self.hx711:
            return None
        timeout_s = max(0.001, (self.ready_timeout_ms or 100.0) / 1000.0)
        start = time.perf_counter()
        while self.data_pin and self.data_pin.value:
            if (time.perf_counter() - start) > timeout_s:
                return None
        return self.hx711.read(channel_gain)

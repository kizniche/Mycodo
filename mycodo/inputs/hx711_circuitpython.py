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


def is_saturated(value):
    return value in (0x7FFFFF, 0xFFFFFFFF, -1, -0x800000)


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HX711_CIRCUITPYTHON',
    'input_manufacturer': 'Avia Semiconductor',
    'input_name': 'HX711 (CircuitPython)',
    'input_library': 'Adafruit_CircuitPython_HX711',
    'measurements_name': 'Mass',
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
        '<h4>Range guidance</h4>'
        '<ul>'
        '<li>Validated for heavier ranges (e.g., 1–200 kg) with calibration near your target range.</li>'
        '<li>Lower ranges (e.g., 1–20 kg or 0.01–1 kg) are not yet tested in this setup.</li>'
        '<li>If you use a lower range, ensure the load cell and amplifier are rated for it and recalibrate.</li>'
        '</ul>'
        '<h4>Calibration do/don\'t</h4>'
        '<ul>'
        '<li>Do use a rigid, flat load plate and keep placement consistent.</li>'
        '<li>Do reposition the weight between calibration runs and average multiple runs.</li>'
        '<li>Don\'t use point loads or flexible surfaces that bend under load.</li>'
        '<li>Don\'t calibrate with a different placement/orientation than you measure.</li>'
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
        self.channel_gain = None
        self.gain_a_64 = None
        self.gain_b_32 = None

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
        self.read_delay_ms = None
        self.max_retries = None
        self.clock_delay_us = None
        self.ready_timeout_ms = None
        self.invalid_sample_filter = None
        self.auto_gain_fallback = None
        self.zero_tracking_enabled = None
        self.zero_tracking_threshold_g = None
        self.zero_tracking_rate = None
        self.tare_value_runtime = None

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
        if self.tare_value_runtime is None:
            self.tare_value_runtime = self.tare_value if self.tare_value is not None else 0.0

        def _delay_us(us):
            target_us = max(float(us), float(self.clock_delay_us or 0.0))
            start_ns = time.perf_counter_ns()
            target_ns = int(target_us * 1000.0)
            while (time.perf_counter_ns() - start_ns) < target_ns:
                pass

        microcontroller.delay_us = _delay_us

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

        if self.pin_data is None or self.pin_clock is None:
            raise ValueError("Both data and clock pins must be set")

        self.channel_gain = HX711.CHAN_A_GAIN_128 if (channel == "A" and gain == 128) else \
            HX711.CHAN_A_GAIN_64 if (channel == "A" and gain == 64) else HX711.CHAN_B_GAIN_32
        self.gain_a_64 = HX711.CHAN_A_GAIN_64
        self.gain_b_32 = HX711.CHAN_B_GAIN_32

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
        try:
            _ = self.hx711.read(self.channel_gain)
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
            import RPi.GPIO  # noqa: F401
        except Exception:
            pass

    def get_measurement(self):
        """Get the mass measurement from the HX711."""
        if not self.hx711:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(
                    "Error 101: Device not set up. "
                    "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
                )
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            raw_data = []
            channel_gain = self.channel_gain if self.channel_gain is not None else 1
            delay_s = max(0.0, (self.read_delay_ms or 0) / 1000.0)
            retries = max(0, int(self.max_retries or 0))
            samples_target = self.samples or 3
            max_attempts = max(samples_target * max(retries, 1), samples_target)
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

            if not raw_data:
                if hasattr(self, "logger") and self.logger:
                    self.logger.error("No data received from HX711")
                return None

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

            raw_average = sum(raw_data) / len(raw_data)

            tare_config = self.tare_value if self.tare_value is not None else 0.0
            if self.tare_value_runtime is None:
                self.tare_value_runtime = tare_config
            tare = self.tare_value_runtime
            tared_value = raw_average - tare

            cal_factor = self.calibration_factor if self.calibration_factor else 1.0
            if cal_factor != 0:
                mass_grams = tared_value / cal_factor
            else:
                mass_grams = tared_value

            if self.zero_tracking_enabled and cal_factor:
                threshold_g = self.zero_tracking_threshold_g if self.zero_tracking_threshold_g is not None else 0.0
                if abs(mass_grams) <= threshold_g:
                    rate = self.zero_tracking_rate if self.zero_tracking_rate is not None else 0.0
                    rate = max(0.0, min(rate, 1.0))
                    if rate:
                        self.tare_value_runtime += tared_value * rate
                        tared_value = raw_average - self.tare_value_runtime
                        mass_grams = tared_value / cal_factor if cal_factor != 0 else tared_value

            self.value_set(0, mass_grams)
            return self.return_dict

        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error("Error reading HX711: {err}".format(err=e))
            return None

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
            (self.gain_a_64, "A/64"),
            (self.gain_b_32, "B/32")
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
        while self.data_pin.value:
            if (time.perf_counter() - start) > timeout_s:
                return None
        return self.hx711.read(channel_gain)

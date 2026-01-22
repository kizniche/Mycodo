#!/usr/bin/env python3
"""
HX711 Test Script
Usage: sudo python3 hx711_test.py
"""
import curses
import os
import sys
import time

GPIO = None

# CONFIGURATION - adjust as needed
DT_PIN = 17   # Data pin (DOUT)
SCK_PIN = 21  # Clock pin (PD_SCK)

# TUI defaults
TUI_SAMPLES = 5
TUI_USE_FILTER = True
TUI_MAD_THRESHOLD = 3.5
TUI_ZERO_TRACKING_ENABLED = False
TUI_ZERO_TRACKING_THRESHOLD_G = 2.0
TUI_ZERO_TRACKING_RATE = 0.05


class HX711Backend:
    def get_raw_data(self, times=3):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def cleanup(self):
        pass


class HX711RPiBackend(HX711Backend):
    def __init__(self, dout_pin, sck_pin, channel='A', gain=128):
        global GPIO
        import RPi.GPIO as GPIO_module
        from hx711 import HX711

        GPIO = GPIO_module
        GPIO.setwarnings(False)

        self._hx = HX711(dout_pin=dout_pin, pd_sck_pin=sck_pin, channel=channel, gain=gain)

    def get_raw_data(self, times=3):
        return self._hx.get_raw_data(times=times)

    def reset(self):
        self._hx.reset()

    def cleanup(self):
        if GPIO is not None:
            GPIO.cleanup()


class HX711CircuitPythonBackend(HX711Backend):
    def __init__(self, dout_pin, sck_pin, channel='A', gain=128):
        self._ensure_rpi_module()
        import board
        import digitalio
        import microcontroller
        from adafruit_hx711.hx711 import HX711

        if getattr(microcontroller, "disable_interrupts", None) is None:
            setattr(microcontroller, "disable_interrupts", lambda: None)
        if getattr(microcontroller, "enable_interrupts", None) is None:
            setattr(microcontroller, "enable_interrupts", lambda: None)

        self._clock_delay_us = 1.0

        def _delay_us(us):
            target_us = max(float(us), float(self._clock_delay_us))
            start_ns = time.perf_counter_ns()
            target_ns = int(target_us * 1000.0)
            while (time.perf_counter_ns() - start_ns) < target_ns:
                pass

        microcontroller.delay_us = _delay_us

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

        if channel == 'A' and gain == 128:
            self._chan_gain = HX711.CHAN_A_GAIN_128
        elif channel == 'A' and gain == 64:
            self._chan_gain = HX711.CHAN_A_GAIN_64
        else:
            self._chan_gain = HX711.CHAN_B_GAIN_32

        self._gain_a_64 = HX711.CHAN_A_GAIN_64
        self._gain_b_32 = HX711.CHAN_B_GAIN_32

        self._data_pin = digitalio.DigitalInOut(bcm_to_board[dout_pin - 1])
        self._data_pin.direction = digitalio.Direction.INPUT
        self._clock_pin = digitalio.DigitalInOut(bcm_to_board[sck_pin - 1])
        self._clock_pin.direction = digitalio.Direction.OUTPUT
        self._clock_pin.value = False

        self._hx = HX711(self._data_pin, self._clock_pin)
        self._read_delay_s = 0.0
        self._max_retries = 0
        self._allow_saturated = True

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

    def get_raw_data(self, times=3):
        values = []
        raw_all = []
        attempts = 0
        max_attempts = max(times * max(self._max_retries, 1), times)
        while len(values) < times and attempts < max_attempts:
            attempts += 1
            value = self._read_with_timeout(self._chan_gain)
            raw_all.append(value)
            if value in (0x7FFFFF, -0x800000, -1, 0xFFFFFFFF):
                value = self._fallback_read(value)
                if value in (0x7FFFFF, -0x800000, -1, 0xFFFFFFFF):
                    if self._read_delay_s:
                        time.sleep(self._read_delay_s)
                    continue
            values.append(value)
            if self._read_delay_s:
                time.sleep(self._read_delay_s)
        if values:
            return values
        if self._allow_saturated and raw_all:
            return raw_all
        return []

    def _fallback_read(self, primary_value):
        for gain in (self._gain_a_64, self._gain_b_32):
            if gain == self._chan_gain:
                continue
            try:
                value = self._read_with_timeout(gain)
                if value not in (0x7FFFFF, -0x800000, -1, 0xFFFFFFFF):
                    return value
            except Exception:
                continue
        return primary_value

    def _read_with_timeout(self, gain_pulses):
        start = time.perf_counter()
        while self._data_pin.value:
            if (time.perf_counter() - start) > 0.1:
                return None
        return self._hx.read(gain_pulses)

    def reset(self):
        try:
            import lgpio
            lgpio.gpio_write(self._chip, self._sck_pin, 1)
            time.sleep(0.001)
            lgpio.gpio_write(self._chip, self._sck_pin, 0)
        except Exception:
            pass

    def cleanup(self):
        try:
            self._data_pin.deinit()
            self._clock_pin.deinit()
        except Exception:
            pass


def init_backend(backend, channel='A', gain=128):
    if backend == 'circuitpython':
        return HX711CircuitPythonBackend(DT_PIN, SCK_PIN, channel=channel, gain=gain)
    return HX711RPiBackend(DT_PIN, SCK_PIN, channel=channel, gain=gain)


def test_stability(hx, num_samples=10):
    """Test sensor stability."""
    print(f"\nStability test ({num_samples} samples):")
    print("-" * 50)

    values = []
    for i in range(num_samples):
        raw = [v for v in hx.get_raw_data(times=5) if v is not None]
        if not raw:
            print("  No valid data received (saturated/invalid samples)")
            return None, None
        avg = sum(raw) / len(raw)
        values.append(avg)
        print(f"  {i+1:2d}: {avg:>14,.0f}")
        time.sleep(0.3)

    avg = sum(values) / len(values)
    spread = max(values) - min(values)

    print("-" * 50)
    print(f"  Average: {avg:>14,.0f}")
    print(f"  Spread:  {spread:>14,.0f}")

    return avg, spread


def live_monitor(hx):
    """Live monitoring - press Ctrl+C to stop."""
    print("\nLive monitoring - Press Ctrl+C to stop")
    print("Move the wires to detect loose connections")
    print("-" * 50)

    try:
        while True:
            raw = [v for v in hx.get_raw_data(times=3) if v is not None]
            if not raw:
                print("\r⚠️  NO DATA", end="", flush=True)
                time.sleep(0.15)
                continue
            avg = sum(raw) / len(raw)

            if abs(avg) > 1000000:
                status = "❌ BAD"
            elif abs(avg) > 100000:
                status = "⚠️  WARN"
            else:
                status = "✓  OK "

            print(f"\r{status} | {avg:>14,.0f}", end="", flush=True)
            time.sleep(0.15)
    except KeyboardInterrupt:
        print("\n\nStopped.")


def tui_dashboard(hx, samples=5, use_filter=True, mad_threshold=3.5,
                  zero_tracking_enabled=False, zero_tracking_threshold_g=2.0, zero_tracking_rate=0.05):
    """Interactive TUI dashboard with live stats and weight in kg."""
    if not sys.stdin.isatty() or os.environ.get("TERM") in (None, "", "dumb"):
        simple_dashboard(
            hx,
            samples=samples,
            use_filter=use_filter,
            mad_threshold=mad_threshold,
            zero_tracking_enabled=zero_tracking_enabled,
            zero_tracking_threshold_g=zero_tracking_threshold_g,
            zero_tracking_rate=zero_tracking_rate
        )
        return

    def _run(screen):
        nonlocal samples, use_filter, mad_threshold
        curses.curs_set(0)
        screen.nodelay(True)
        screen.timeout(200)

        tare_value = 0.0
        calibration_factor = 1.0
        zt_enabled = zero_tracking_enabled
        zt_threshold = zero_tracking_threshold_g
        zt_rate = zero_tracking_rate
        last_raw_avg = 0.0
        last_tick = time.time()
        refresh_hz = 0.0

        def safe_addstr(y, x, text, attr=0):
            try:
                height, width = screen.getmaxyx()
                if y < 0 or y >= height or x >= width:
                    return
                if x < 0:
                    text = text[-x:]
                    x = 0
                max_len = max(0, width - x - 1)
                if max_len <= 0:
                    return
                screen.addstr(y, x, text[:max_len], attr)
            except Exception:
                return

        def draw_box(y, x, w, h, title, lines):
            if w < 4 or h < 3:
                return
            top = "+" + "-" * (w - 2) + "+"
            bottom = "+" + "-" * (w - 2) + "+"
            safe_addstr(y, x, top)
            safe_addstr(y + h - 1, x, bottom)
            title_text = f"[{title}]"
            if len(title_text) < (w - 2):
                safe_addstr(y, x + 2, title_text)
            for i in range(1, h - 1):
                safe_addstr(y + i, x, "|")
                safe_addstr(y + i, x + w - 1, "|")
            for idx, line in enumerate(lines):
                if idx >= h - 2:
                    break
                safe_addstr(y + 1 + idx, x + 1, line)

        while True:
            screen.erase()
            now = time.time()
            dt = now - last_tick
            if dt > 0:
                refresh_hz = 1.0 / dt
            last_tick = now

            height, width = screen.getmaxyx()
            show_right_panel = width >= 90
            panel_gap = 1
            settings_width = 40
            stats_width = width - settings_width - panel_gap if show_right_panel else width
            stats_width = max(10, stats_width)
            settings_x = stats_width + panel_gap if show_right_panel else 0
            settings_start_y = 0 if show_right_panel else min(10, max(0, height - 1))
            prompt_y = min(14, max(0, height - 2))
            if not show_right_panel and settings_start_y > 0:
                prompt_y = min(prompt_y, settings_start_y - 1)

            safe_addstr(0, 0, "HX711 Live Dashboard - press q to quit")
            safe_addstr(1, 0, f"Refresh: {refresh_hz:5.1f} Hz")

            zt_status = 'ON' if zt_enabled else 'OFF'
            settings_lines = [
                "Settings",
                f"Samples: {samples}",
                f"Filter: {'ON' if use_filter else 'OFF'}",
                f"MAD: {mad_threshold:.2f}",
                f"Tare: {tare_value:.0f}",
                f"Factor: {calibration_factor:.4f}",
                f"Zero Tracking: {zt_status}",
                f"ZT Threshold: {zt_threshold:.2f} g",
                f"ZT Rate: {zt_rate:.2f}",
                "",
                "Keys",
                "q quit",
                "t tare current",
                "g set tare",
                "f set factor",
                "m toggle filter",
                "d set MAD",
                "z toggle zero",
                "y set ZT threshold",
                "u set ZT rate",
                "+/- samples",
                "r reset HX711",
            ]

            settings_height = min(height - settings_start_y, len(settings_lines) + 2)
            draw_box(settings_start_y, settings_x, settings_width, settings_height, "Settings", settings_lines)

            raw_data = [v for v in hx.get_raw_data(times=samples) if v is not None]
            if not raw_data:
                stats_lines = ["No data from HX711"]
                stats_height = min(height, len(stats_lines) + 2)
                draw_box(2, 0, stats_width, stats_height, "Stats", stats_lines)
                screen.refresh()
                if screen.getch() == ord('q'):
                    break
                continue

            raw_avg = sum(raw_data) / len(raw_data)
            raw_min = min(raw_data)
            raw_max = max(raw_data)
            raw_spread = raw_max - raw_min
            raw_variance = sum((v - raw_avg) ** 2 for v in raw_data) / len(raw_data)
            raw_std = raw_variance ** 0.5

            filtered = raw_data
            removed = []
            if use_filter:
                filtered, removed = filter_outliers(raw_data, mad_threshold=mad_threshold)

            filtered_avg = sum(filtered) / len(filtered)
            tared = filtered_avg - tare_value
            if calibration_factor != 0:
                grams = tared / calibration_factor
            else:
                grams = tared

            if zt_enabled and calibration_factor != 0:
                if abs(grams) <= zt_threshold:
                    rate = max(0.0, min(zt_rate, 1.0))
                    if rate:
                        tare_value += tared * rate
                        tared = filtered_avg - tare_value
                        grams = tared / calibration_factor
            kg = grams / 1000.0

            last_raw_avg = raw_avg

            stats_lines = [
                f"Raw avg:     {raw_avg:>12.0f}",
                f"Raw min/max:{raw_min:>8.0f} / {raw_max:>8.0f}",
                f"Raw spread: {raw_spread:>12.0f}  std: {raw_std:>9.1f}",
                f"Filtered:   {filtered_avg:>12.0f} (removed {len(removed)})",
                f"Weight:     {grams:>12.2f} g  |  {kg:>9.3f} kg",
            ]
            stats_height = min(height, len(stats_lines) + 2)
            draw_box(2, 0, stats_width, stats_height, "Stats", stats_lines)

            key = screen.getch()
            if key == ord('q'):
                break
            if key == ord('t'):
                tare_value = last_raw_avg
            if key == ord('m'):
                use_filter = not use_filter
            if key == ord('r'):
                hx.reset()
            if key == ord('+'):
                samples = min(samples + 1, 50)
            if key == ord('-'):
                samples = max(samples - 1, 1)
            if key == ord('g'):
                curses.echo()
                safe_addstr(prompt_y, 0, "Enter tare (raw): ")
                screen.clrtoeol()
                try:
                    tare_str = screen.getstr(prompt_y, 19, 20).decode().strip()
                    tare_value = float(tare_str)
                except Exception:
                    pass
                curses.noecho()
            if key == ord('f'):
                curses.echo()
                safe_addstr(prompt_y, 0, "Enter factor: ")
                screen.clrtoeol()
                try:
                    factor_str = screen.getstr(prompt_y, 14, 20).decode().strip()
                    calibration_factor = float(factor_str)
                except Exception:
                    pass
                curses.noecho()
            if key == ord('d'):
                curses.echo()
                safe_addstr(prompt_y, 0, "Enter MAD threshold: ")
                screen.clrtoeol()
                try:
                    mad_str = screen.getstr(prompt_y, 22, 20).decode().strip()
                    mad_threshold = float(mad_str)
                except Exception:
                    pass
                curses.noecho()
            if key == ord('z'):
                zt_enabled = not zt_enabled
            if key == ord('y'):
                curses.echo()
                safe_addstr(prompt_y, 0, "Enter ZT threshold (g): ")
                screen.clrtoeol()
                try:
                    thr_str = screen.getstr(prompt_y, 27, 20).decode().strip()
                    zt_threshold = max(0.0, float(thr_str))
                except Exception:
                    pass
                curses.noecho()
            if key == ord('u'):
                curses.echo()
                safe_addstr(prompt_y, 0, "Enter ZT rate (0-1): ")
                screen.clrtoeol()
                try:
                    rate_str = screen.getstr(prompt_y, 24, 20).decode().strip()
                    zt_rate = float(rate_str)
                except Exception:
                    pass
                zt_rate = max(0.0, min(zt_rate, 1.0))
                curses.noecho()

            screen.refresh()

    try:
        curses.wrapper(_run)
    except Exception:
        simple_dashboard(
            hx,
            samples=samples,
            use_filter=use_filter,
            mad_threshold=mad_threshold,
            zero_tracking_enabled=zero_tracking_enabled,
            zero_tracking_threshold_g=zero_tracking_threshold_g,
            zero_tracking_rate=zero_tracking_rate
        )


def simple_dashboard(hx, samples=5, use_filter=True, mad_threshold=3.5,
                    zero_tracking_enabled=False, zero_tracking_threshold_g=2.0, zero_tracking_rate=0.05):
    """Fallback dashboard for terminals without curses support."""
    print("\nSimple dashboard (no curses). Press Ctrl+C to stop.")
    tare_value = 0.0
    calibration_factor = 1.0
    zt_enabled = zero_tracking_enabled
    zt_threshold = zero_tracking_threshold_g
    zt_rate = zero_tracking_rate
    while True:
        raw_data = [v for v in hx.get_raw_data(times=samples) if v is not None]
        if not raw_data:
            print("No data from HX711")
            time.sleep(0.5)
            continue

        raw_avg = sum(raw_data) / len(raw_data)
        raw_min = min(raw_data)
        raw_max = max(raw_data)
        raw_spread = raw_max - raw_min

        filtered = raw_data
        removed = []
        if use_filter:
            filtered, removed = filter_outliers(raw_data, mad_threshold=mad_threshold)

        filtered_avg = sum(filtered) / len(filtered)
        tared = filtered_avg - tare_value
        grams = tared / calibration_factor if calibration_factor != 0 else tared

        if zt_enabled and calibration_factor != 0:
            if abs(grams) <= zt_threshold:
                rate = max(0.0, min(zt_rate, 1.0))
                if rate:
                    tare_value += tared * rate
                    tared = filtered_avg - tare_value
                    grams = tared / calibration_factor

        kg = grams / 1000.0

        sys.stdout.write("\033[2J\033[H")
        print("HX711 Simple Dashboard")
        print(f"Samples: {samples}  Filter: {'ON' if use_filter else 'OFF'}  MAD: {mad_threshold:.2f}")
        print(f"Tare: {tare_value:.0f}  Factor: {calibration_factor:.4f}")
        print(f"Zero Tracking: {'ON' if zt_enabled else 'OFF'}")
        print(f"ZT Threshold: {zt_threshold:.2f} g  ZT Rate: {zt_rate:.2f}")
        print("")
        print(f"Raw avg:     {raw_avg:>12.0f}")
        print(f"Raw min/max:{raw_min:>8.0f} / {raw_max:>8.0f}")
        print(f"Raw spread: {raw_spread:>12.0f}")
        print(f"Filtered:   {filtered_avg:>12.0f} (removed {len(removed)})")
        print(f"Weight:     {grams:>12.2f} g  |  {kg:>9.3f} kg")
        print("")
        print("Note: interactive controls require curses. Use the main menu to adjust tare/factor.")
        time.sleep(0.5)


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


def calibration_wizard(hx, tare_samples=20, weight_samples=20, weight_runs=5):
    """Calibration wizard."""
    print("\n" + "=" * 50)
    print("CALIBRATION WIZARD")
    print("=" * 50)

    tare = tare_calibration(hx, tare_samples=tare_samples, tare_runs=1, filter_outliers=filter_outliers)
    factor_calibration(
        hx,
        tare_value=tare,
        weight_samples=weight_samples,
        weight_runs=weight_runs,
        filter_outliers=filter_outliers
    )


def tare_calibration(hx, tare_samples=20, tare_runs=3, filter_outliers=None):
    """Tare-only calibration."""
    input("\nRemove all weight from the scale.\nPress Enter when ready...")

    run_averages = []
    for run in range(1, tare_runs + 1):
        print(f"\n   Tare run {run}/{tare_runs}")
        tare_values = []
        for i in range(tare_samples):
            raw = [v for v in hx.get_raw_data(times=5) if v is not None]
            if not raw:
                continue
            tare_values.append(sum(raw) / len(raw))
            time.sleep(0.1)

        print("   Tare samples:")
        for i, value in enumerate(tare_values, start=1):
            print(f"     {i:2d}: {value:>14,.0f}")

        if tare_values:
            if filter_outliers:
                tare_for_dev, _ = filter_outliers(tare_values)
            else:
                tare_for_dev = tare_values
            tare_mean = sum(tare_for_dev) / len(tare_for_dev)
            tare_devs = [v - tare_mean for v in tare_for_dev]
            min_dev = min(tare_devs)
            max_dev = max(tare_devs)
            print(f"   Deviation from mean: min {min_dev:+.0f} max {max_dev:+.0f}")

        if filter_outliers:
            tare_filtered, tare_removed = filter_outliers(tare_values)
        else:
            tare_filtered, tare_removed = tare_values, []

        if tare_removed:
            print(f"   Excluded tare samples: {len(tare_removed)}")
            print("   Excluded values:")
            for value in tare_removed:
                print(f"     - {value:>14,.0f}")

        if not tare_filtered:
            print("   No valid tare samples collected. Check wiring/gain/timing.")
            return None
        run_average = sum(tare_filtered) / len(tare_filtered)
        print(f"   Tare run average: {run_average:.0f}")
        run_averages.append(run_average)

        if run < tare_runs:
            input("   Press Enter for the next tare run...")

    tare = sum(run_averages) / len(run_averages)

    print("\n" + "=" * 50)
    print("RESULT:")
    print(f"  Tare Value: {tare:.0f}")
    print("=" * 50)
    print("\nUse this value in Mycodo:")
    print(f"  - Tare Value: {tare:.0f}")
    return tare


def factor_calibration(hx, tare_value, weight_samples=20, weight_runs=5, filter_outliers=None):
    """Calibration factor only (requires known tare value)."""
    if filter_outliers is None:
        filter_outliers = globals().get("filter_outliers")

    known_weight = input("\nHow many grams is your calibration weight? ")
    try:
        known_weight = float(known_weight)
    except ValueError:
        print("   Invalid input!")
        return

    input(f"   Place {known_weight}g on the scale.\n   Press Enter when ready...")

    print("   Measuring weight...")
    run_factors = []
    run_raws = []
    for run in range(1, weight_runs + 1):
        if run == 1:
            input("   Reposition the weight for this run, then press Enter...")
        else:
            input("   Reposition the weight for the next run, then press Enter...")
        weight_values = []
        for i in range(weight_samples):
            raw = [v for v in hx.get_raw_data(times=5) if v is not None]
            if not raw:
                continue
            weight_values.append(sum(raw) / len(raw))
            time.sleep(0.1)

        print(f"   Run {run}/{weight_runs} (with weight):")
        for i, value in enumerate(weight_values, start=1):
            print(f"     {i:2d}: {value:>14,.0f}")

        if weight_values:
            if filter_outliers:
                weight_for_dev, _ = filter_outliers(weight_values)
            else:
                weight_for_dev = weight_values
            weight_mean = sum(weight_for_dev) / len(weight_for_dev)
            weight_devs = [v - weight_mean for v in weight_for_dev]
            min_dev = min(weight_devs)
            max_dev = max(weight_devs)
            print(f"   Deviation from mean: min {min_dev:+.0f} max {max_dev:+.0f}")

        if filter_outliers:
            weight_filtered, weight_removed = filter_outliers(weight_values)
        else:
            weight_filtered, weight_removed = weight_values, []

        if weight_removed:
            print(f"   Excluded weight samples: {len(weight_removed)}")
            print("   Excluded values:")
            for value in weight_removed:
                print(f"     - {value:>14,.0f}")

        if not weight_filtered:
            print("   No valid weight samples collected. Check wiring/gain/timing.")
            return
        weight_raw = sum(weight_filtered) / len(weight_filtered)
        run_raws.append(weight_raw)
        print(f"   Raw weight average (run {run}): {weight_raw:.0f}")
        run_factors.append((weight_raw - tare_value) / known_weight)

        if run < weight_runs:
            print("   Run complete. Prepare to reposition the weight.")

    calibration_factor = sum(run_factors) / len(run_factors)
    avg_weight_raw = sum(run_raws) / len(run_raws)

    print("\n" + "=" * 50)
    print("RESULT:")
    print(f"  Tare Value:        {tare_value:.0f}")
    print(f"  Raw with Weight (avg): {avg_weight_raw:.0f}")
    print(f"  Calibration Factor: {calibration_factor:.2f}")
    print("=" * 50)
    print("\nUse this value in Mycodo:")
    print(f"  - Calibration Factor: {calibration_factor:.2f}")
    return calibration_factor


def main():
    print("=" * 50)
    print("HX711 TEST TOOL")
    print(f"GPIO pins: DT={DT_PIN}, SCK={SCK_PIN}")
    print("Backend: circuitpython")
    print("=" * 50)

    backend = 'circuitpython'
    last_tare = None
    prev_tare = None
    last_factor = None
    prev_factor = None
    try:
        hx = init_backend(backend, channel='A', gain=128)
        hx.reset()
        time.sleep(0.5)
        print("HX711 initialized ✓")
    except Exception as e:
        print(f"Initialization error (rpi): {e}")
        try:
            if GPIO is not None:
                GPIO.cleanup()
        except Exception:
            pass
        backend = 'circuitpython'
        try:
            hx = init_backend(backend, channel='A', gain=128)
            hx.reset()
            time.sleep(0.5)
            print("HX711 initialized ✓")
        except Exception as e2:
            print(f"Initialization error (circuitpython): {e2}")
            sys.exit(1)

    while True:
        print("\n" + "-" * 50)
        print("Choose an option:")
        print("  1. Stability test (10 samples)")
        print("  2. Live monitoring (wiggle test)")
        print("  3. Calibration wizard")
        print("  6. Tare calibration only")
        print("  7. Factor calibration only (5 runs)")
        print("  10. Set tare manually")
        print("  11. Set factor manually")
        print("  4. Test with gain 64")
        print("  5. Test channel B")
        print("  8. Live TUI dashboard")
        print(f"  9. Switch backend (current: {backend})")
        print("  q. Quit")
        print("\nTUI defaults:")
        print(
            f"  samples={TUI_SAMPLES}  filter={'ON' if TUI_USE_FILTER else 'OFF'}"
            f"  mad={TUI_MAD_THRESHOLD:.2f}  zero={'ON' if TUI_ZERO_TRACKING_ENABLED else 'OFF'}"
        )
        print(
            f"  zt_threshold={TUI_ZERO_TRACKING_THRESHOLD_G:.2f}g"
            f"  zt_rate={TUI_ZERO_TRACKING_RATE:.2f}"
        )

        raw_data = [v for v in hx.get_raw_data(times=5) if v is not None]
        if raw_data:
            raw_avg = sum(raw_data) / len(raw_data)
            filtered, _removed = filter_outliers(raw_data, mad_threshold=TUI_MAD_THRESHOLD) if TUI_USE_FILTER else (raw_data, [])
            filtered_avg = sum(filtered) / len(filtered)
        else:
            raw_avg = None
            filtered_avg = None

        tare_current = last_tare
        tare_diff = None
        if last_tare is not None and prev_tare is not None:
            tare_diff = last_tare - prev_tare

        factor_current = last_factor
        factor_diff = None
        if last_factor is not None and prev_factor is not None:
            factor_diff = last_factor - prev_factor

        weight_grams = None
        if filtered_avg is not None:
            tared_val = filtered_avg - (last_tare if last_tare is not None else 0.0)
            if last_factor not in (None, 0):
                weight_grams = tared_val / last_factor
            else:
                weight_grams = tared_val

        print("\nCurrent readings:")
        if raw_avg is None:
            print("  Raw avg: N/A")
        else:
            print(f"  Raw avg: {raw_avg:.0f}")
            print(f"  Filtered avg: {filtered_avg:.0f}")

        print("\nTare:")
        print(f"  Previous: {prev_tare:.0f}" if prev_tare is not None else "  Previous: N/A")
        print(f"  Current:  {tare_current:.0f}" if tare_current is not None else "  Current:  N/A")
        print(f"  Diff:     {tare_diff:+.0f}" if tare_diff is not None else "  Diff:     N/A")

        print("\nCalibration factor:")
        print(f"  Previous: {prev_factor:.4f}" if prev_factor is not None else "  Previous: N/A")
        print(f"  Current:  {factor_current:.4f}" if factor_current is not None else "  Current:  N/A")
        print(f"  Diff:     {factor_diff:+.4f}" if factor_diff is not None else "  Diff:     N/A")

        print("\nWeight on scale:")
        print(f"  {weight_grams:.2f} g" if weight_grams is not None else "  N/A")

        choice = input("\nChoice: ").strip().lower()

        if choice == '1':
            hx.reset()
            avg, spread = test_stability(hx)
            if avg is None:
                print("\n❌ No valid data - check wiring/gain/timing")
            elif spread < 50000:
                print("\n✅ Sensor is stable!")
            else:
                print("\n❌ Sensor is unstable - check wiring")

        elif choice == '2':
            hx.reset()
            live_monitor(hx)

        elif choice == '3':
            hx.reset()
            avg, spread = test_stability(hx, 5)
            if avg is None:
                print("\n⚠️  No valid data for calibration!")
                print("    Fix wiring/gain/timing first.")
            elif spread > 100000:
                print("\n⚠️  Sensor too unstable for calibration!")
                print("    Fix wiring first.")
            else:
                prev_tare = last_tare
                last_tare = tare_calibration(hx, tare_samples=20, tare_runs=1, filter_outliers=filter_outliers)
                if last_tare is not None:
                    prev_factor = last_factor
                    last_factor = factor_calibration(
                        hx,
                        tare_value=last_tare,
                        filter_outliers=filter_outliers
                    )
        elif choice == '6':
            hx.reset()
            avg, spread = test_stability(hx, 5)
            if avg is None:
                print("\n⚠️  No valid data for tare calibration!")
                print("    Fix wiring/gain/timing first.")
            elif spread > 100000:
                print("\n⚠️  Sensor too unstable for tare calibration!")
                print("    Fix wiring first.")
            else:
                prev_tare = last_tare
                last_tare = tare_calibration(hx, filter_outliers=filter_outliers)
        elif choice == '7':
            hx.reset()
            default_tare = last_tare
            prompt = "\nWhat is your current tare value (raw)?"
            if default_tare is not None:
                prompt += f" [{default_tare:.0f}]"
            prompt += " "
            tare_input = input(prompt).strip().replace(",", "")
            if not tare_input and default_tare is not None:
                tare_value = float(default_tare)
            else:
                try:
                    tare_value = float(tare_input)
                except Exception:
                    print("   Invalid input!")
                    continue
            if last_tare != tare_value:
                prev_tare = last_tare
                last_tare = tare_value
            prev_factor = last_factor
            last_factor = factor_calibration(hx, tare_value, filter_outliers=filter_outliers)

        elif choice == '10':
            prompt = "\nEnter tare value (raw)"
            if last_tare is not None:
                prompt += f" [{last_tare:.0f}]"
            prompt += ": "
            tare_input = input(prompt).strip().replace(",", "")
            if not tare_input and last_tare is not None:
                tare_value = float(last_tare)
            else:
                try:
                    tare_value = float(tare_input)
                except Exception:
                    print("   Invalid input!")
                    continue
            if last_tare != tare_value:
                prev_tare = last_tare
                last_tare = tare_value

        elif choice == '11':
            prompt = "\nEnter calibration factor"
            if last_factor is not None:
                prompt += f" [{last_factor:.4f}]"
            prompt += ": "
            factor_input = input(prompt).strip().replace(",", "")
            if not factor_input and last_factor is not None:
                factor_value = float(last_factor)
            else:
                try:
                    factor_value = float(factor_input)
                except Exception:
                    print("   Invalid input!")
                    continue
            if last_factor != factor_value:
                prev_factor = last_factor
                last_factor = factor_value

        elif choice == '4':
            print("\nTesting gain 64...")
            hx.cleanup()
            hx = init_backend(backend, channel='A', gain=64)
            hx.reset()
            test_stability(hx)
            # Restore default gain/channel after test
            hx.cleanup()
            hx = init_backend(backend, channel='A', gain=128)
            hx.reset()

        elif choice == '5':
            print("\nTesting channel B (gain 32)...")
            hx.cleanup()
            hx = init_backend(backend, channel='B', gain=32)
            hx.reset()
            test_stability(hx)
            # Restore default gain/channel after test
            hx.cleanup()
            hx = init_backend(backend, channel='A', gain=128)
            hx.reset()

        elif choice == '8':
            hx.reset()
            tui_dashboard(
                hx,
                samples=TUI_SAMPLES,
                use_filter=TUI_USE_FILTER,
                mad_threshold=TUI_MAD_THRESHOLD,
                zero_tracking_enabled=TUI_ZERO_TRACKING_ENABLED,
                zero_tracking_threshold_g=TUI_ZERO_TRACKING_THRESHOLD_G,
                zero_tracking_rate=TUI_ZERO_TRACKING_RATE
            )

        elif choice == '9':
            hx.cleanup()
            backend = 'rpi' if backend == 'circuitpython' else 'circuitpython'
            print(f"\nSwitching backend to: {backend}")
            try:
                hx = init_backend(backend, channel='A', gain=128)
                hx.reset()
                time.sleep(0.5)
                print("HX711 initialized ✓")
            except Exception as e:
                print(f"Initialization error: {e}")
                hx = init_backend('rpi', channel='A', gain=128)
                hx.reset()

        elif choice == 'q':
            break
        else:
            print("Invalid choice")

    hx.cleanup()
    print("\nTest tool closed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
HX711 Test Script
Usage: sudo python3 hx711_test.py
"""
from hx711 import HX711
import RPi.GPIO as GPIO
import time
import sys
import curses

GPIO.setwarnings(False)

# CONFIGURATION - adjust as needed
DT_PIN = 17   # Data pin (DOUT)
SCK_PIN = 21  # Clock pin (PD_SCK)


def test_stability(hx, num_samples=10):
    """Test sensor stability."""
    print(f"\nStability test ({num_samples} samples):")
    print("-" * 50)

    values = []
    for i in range(num_samples):
        raw = hx.get_raw_data(times=5)
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
            raw = hx.get_raw_data(times=3)
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


def tui_dashboard(hx, samples=5, use_filter=True, mad_threshold=3.5):
    """Interactive TUI dashboard with live stats and weight in kg."""
    def _run(screen):
        curses.curs_set(0)
        screen.nodelay(True)
        screen.timeout(200)

        tare_value = 0.0
        calibration_factor = 1.0
        last_raw_avg = 0.0

        while True:
            screen.erase()
            screen.addstr(0, 0, "HX711 Live Dashboard")
            screen.addstr(1, 0, f"Samples: {samples}  Filter: {'ON' if use_filter else 'OFF'}  MAD: {mad_threshold}")
            screen.addstr(2, 0, f"Tare: {tare_value:,.0f}  Factor: {calibration_factor:,.4f}")

            raw_data = hx.get_raw_data(times=samples)
            if not isinstance(raw_data, list) or not raw_data:
                screen.addstr(4, 0, "No data from HX711", curses.A_BOLD)
                screen.addstr(6, 0, "Keys: q=quit  t=tar e to current  f=set factor")
                screen.refresh()
                if screen.getch() == ord('q'):
                    break
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
            if calibration_factor != 0:
                grams = tared / calibration_factor
            else:
                grams = tared
            kg = grams / 1000.0

            last_raw_avg = raw_avg

            screen.addstr(4, 0, f"Raw avg:     {raw_avg:>12,.0f}")
            screen.addstr(5, 0, f"Raw min/max:{raw_min:>8,.0f} / {raw_max:>8,.0f}")
            screen.addstr(6, 0, f"Raw spread: {raw_spread:>12,.0f}")
            screen.addstr(7, 0, f"Filtered:   {filtered_avg:>12,.0f} (removed {len(removed)})")
            screen.addstr(8, 0, f"Weight:     {grams:>12,.2f} g  |  {kg:>9,.3f} kg")

            screen.addstr(10, 0, "Keys: q=quit  t=tare to current  f=set factor  g=set tare")

            key = screen.getch()
            if key == ord('q'):
                break
            if key == ord('t'):
                tare_value = last_raw_avg
            if key == ord('g'):
                curses.echo()
                screen.addstr(12, 0, "Enter tare (raw): ")
                screen.clrtoeol()
                try:
                    tare_str = screen.getstr(12, 19, 20).decode().strip()
                    tare_value = float(tare_str)
                except Exception:
                    pass
                curses.noecho()
            if key == ord('f'):
                curses.echo()
                screen.addstr(12, 0, "Enter factor: ")
                screen.clrtoeol()
                try:
                    factor_str = screen.getstr(12, 14, 20).decode().strip()
                    calibration_factor = float(factor_str)
                except Exception:
                    pass
                curses.noecho()

            screen.refresh()

    curses.wrapper(_run)


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


def calibration_wizard(hx, tare_samples=20, weight_samples=20, weight_runs=3):
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
            raw = hx.get_raw_data(times=5)
            tare_values.append(sum(raw) / len(raw))
            time.sleep(0.1)

        print("   Tare samples:")
        for i, value in enumerate(tare_values, start=1):
            print(f"     {i:2d}: {value:>14,.0f}")

        if filter_outliers:
            tare_filtered, tare_removed = filter_outliers(tare_values)
        else:
            tare_filtered, tare_removed = tare_values, []

        if tare_removed:
            print(f"   Excluded tare samples: {len(tare_removed)}")
            print("   Excluded values:")
            for value in tare_removed:
                print(f"     - {value:>14,.0f}")

        run_average = sum(tare_filtered) / len(tare_filtered)
        print(f"   Tare run average: {run_average:,.0f}")
        run_averages.append(run_average)

        if run < tare_runs:
            input("   Press Enter for the next tare run...")

    tare = sum(run_averages) / len(run_averages)

    print("\n" + "=" * 50)
    print("RESULT:")
    print(f"  Tare Value: {tare:,.0f}")
    print("=" * 50)
    print("\nUse this value in Mycodo:")
    print(f"  - Tare Value: {tare:.0f}")
    return tare


def factor_calibration(hx, tare_value, weight_samples=20, weight_runs=3, filter_outliers=None):
    """Calibration factor only (requires known tare value)."""
    if filter_outliers is None:
        filter_outliers = globals().get("filter_outliers")

    known_weight = input("\nHow many grams is your calibration weight? ")
    try:
        known_weight = float(known_weight)
    except:
        print("   Invalid input!")
        return

    input(f"   Place {known_weight}g on the scale.\n   Press Enter when ready...")

    print("   Measuring weight...")
    run_factors = []
    run_raws = []
    for run in range(1, weight_runs + 1):
        weight_values = []
        for i in range(weight_samples):
            raw = hx.get_raw_data(times=5)
            weight_values.append(sum(raw) / len(raw))
            time.sleep(0.1)

        print(f"   Run {run}/{weight_runs} (with weight):")
        for i, value in enumerate(weight_values, start=1):
            print(f"     {i:2d}: {value:>14,.0f}")

        if filter_outliers:
            weight_filtered, weight_removed = filter_outliers(weight_values)
        else:
            weight_filtered, weight_removed = weight_values, []

        if weight_removed:
            print(f"   Excluded weight samples: {len(weight_removed)}")
            print("   Excluded values:")
            for value in weight_removed:
                print(f"     - {value:>14,.0f}")

        weight_raw = sum(weight_filtered) / len(weight_filtered)
        run_raws.append(weight_raw)
        print(f"   Raw weight average (run {run}): {weight_raw:,.0f}")
        run_factors.append((weight_raw - tare_value) / known_weight)

        if run < weight_runs:
            input("   Keep the weight on and press Enter for the next run...")

    calibration_factor = sum(run_factors) / len(run_factors)
    avg_weight_raw = sum(run_raws) / len(run_raws)

    print("\n" + "=" * 50)
    print("RESULT:")
    print(f"  Tare Value:        {tare_value:,.0f}")
    print(f"  Raw with Weight (avg): {avg_weight_raw:,.0f}")
    print(f"  Calibration Factor: {calibration_factor:,.2f}")
    print("=" * 50)
    print("\nUse this value in Mycodo:")
    print(f"  - Calibration Factor: {calibration_factor:.2f}")


def main():
    print("=" * 50)
    print("HX711 TEST TOOL")
    print(f"GPIO pins: DT={DT_PIN}, SCK={SCK_PIN}")
    print("=" * 50)

    try:
        hx = HX711(dout_pin=DT_PIN, pd_sck_pin=SCK_PIN, channel='A', gain=128)
        hx.reset()
        time.sleep(0.5)
        print("HX711 initialized ✓")
    except Exception as e:
        print(f"Initialization error: {e}")
        GPIO.cleanup()
        sys.exit(1)

    while True:
        print("\n" + "-" * 50)
        print("Choose an option:")
        print("  1. Stability test (10 samples)")
        print("  2. Live monitoring (wiggle test)")
        print("  3. Calibration wizard")
        print("  6. Tare calibration only")
        print("  7. Factor calibration only")
        print("  4. Test with gain 64")
        print("  5. Test channel B")
        print("  8. Live TUI dashboard")
        print("  q. Quit")

        choice = input("\nChoice: ").strip().lower()

        if choice == '1':
            hx.reset()
            avg, spread = test_stability(hx)
            if spread < 50000:
                print("\n✅ Sensor is stable!")
            else:
                print("\n❌ Sensor is unstable - check wiring")

        elif choice == '2':
            hx.reset()
            live_monitor(hx)

        elif choice == '3':
            hx.reset()
            avg, spread = test_stability(hx, 5)
            if spread > 100000:
                print("\n⚠️  Sensor too unstable for calibration!")
                print("    Fix wiring first.")
            else:
                calibration_wizard(hx)
        elif choice == '6':
            hx.reset()
            avg, spread = test_stability(hx, 5)
            if spread > 100000:
                print("\n⚠️  Sensor too unstable for tare calibration!")
                print("    Fix wiring first.")
            else:
                tare_calibration(hx, filter_outliers=filter_outliers)
        elif choice == '7':
            hx.reset()
            tare_input = input("\nWhat is your current tare value (raw)? ").strip()
            try:
                tare_value = float(tare_input)
            except:
                print("   Invalid input!")
                continue
            factor_calibration(hx, tare_value, filter_outliers=filter_outliers)

        elif choice == '4':
            print("\nTesting gain 64...")
            GPIO.cleanup()
            hx = HX711(dout_pin=DT_PIN, pd_sck_pin=SCK_PIN, channel='A', gain=64)
            hx.reset()
            test_stability(hx)
            # Restore default gain/channel after test
            GPIO.cleanup()
            hx = HX711(dout_pin=DT_PIN, pd_sck_pin=SCK_PIN, channel='A', gain=128)
            hx.reset()

        elif choice == '5':
            print("\nTesting channel B (gain 32)...")
            GPIO.cleanup()
            hx = HX711(dout_pin=DT_PIN, pd_sck_pin=SCK_PIN, channel='B', gain=32)
            hx.reset()
            test_stability(hx)
            # Restore default gain/channel after test
            GPIO.cleanup()
            hx = HX711(dout_pin=DT_PIN, pd_sck_pin=SCK_PIN, channel='A', gain=128)
            hx.reset()

        elif choice == '8':
            hx.reset()
            tui_dashboard(hx)

        elif choice == 'q':
            break
        else:
            print("Invalid choice")

    GPIO.cleanup()
    print("\nTest tool closed.")


if __name__ == "__main__":
    main()

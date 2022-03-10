# coding=utf-8
"""Tests for influxdb."""
from mycodo.utils.influx import add_measurements_influxdb

from mycodo.utils.influx import read_influxdb_single


def test_influxdb():
    """Verify measurements can be written and read from influxdb."""
    print("\nTest: test_influxdb")
    measurements_dict = {
        0: {
            'measurement': 'duty_cycle',
            'unit': 'percent'
        }
    }
    written_measurement = 123.45
    measurements_dict[0]["value"] = written_measurement
    add_measurements_influxdb("ID_ASDF", measurements_dict)

    import time
    time.sleep(2)

    last_measurement = read_influxdb_single(
        "ID_ASDF",
        "percent",
        0,
        measure="duty_cycle",
        duration_sec=1000,
        value='LAST')

    assert last_measurement

    print(f"Returned measurement: {last_measurement}")

    returned_measurement = last_measurement[1]

    assert returned_measurement == written_measurement

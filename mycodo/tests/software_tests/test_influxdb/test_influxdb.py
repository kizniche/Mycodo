# coding=utf-8
"""Tests for influxdb."""
from mycodo.utils.influx import add_measurements_influxdb, read_influxdb_single


def test_influxdb():
    """Verify measurements can be written and read from influxdb."""
    print("\nTest: test_influxdb")
    device_id = 'ID_ASDF'
    channel = 0
    measurement = 'duty_cycle'
    unit = 'percent'
    written_measurement = 123.45

    measurements_dict = {
        channel: {
            'measurement': measurement,
            'unit': unit,
            'value': written_measurement
        }
    }

    add_measurements_influxdb(device_id, measurements_dict, block=True)

    last_measurement = read_influxdb_single(
        device_id,
        unit,
        0,
        measure=measurement,
        duration_sec=1000,
        value='LAST')

    print(f"Returned measurement: {last_measurement}")

    assert last_measurement

    returned_measurement = last_measurement[1]

    assert returned_measurement == written_measurement

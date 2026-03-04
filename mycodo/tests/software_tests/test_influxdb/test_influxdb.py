# coding=utf-8
"""Tests for influxdb."""
from mycodo.utils.influx import (add_measurements_influxdb, read_influxdb_multi,
                                 read_influxdb_single)


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


def test_influxdb_multi():
    """Verify multiple measurements can be read from influxdb in one call."""
    print("\nTest: test_influxdb_multi")
    
    # Write test data for multiple channels
    device_id = 'ID_MULTI_TEST'
    
    # Write channel 0
    measurements_dict_0 = {
        0: {
            'measurement': 'temperature',
            'unit': 'C',
            'value': 25.5
        }
    }
    add_measurements_influxdb(device_id, measurements_dict_0, block=True)
    
    # Write channel 1
    measurements_dict_1 = {
        1: {
            'measurement': 'humidity',
            'unit': 'percent',
            'value': 65.3
        }
    }
    add_measurements_influxdb(device_id, measurements_dict_1, block=True)
    
    # Query multiple channels at once
    channels_data = [
        {'unique_id': device_id, 'unit': 'C', 'channel': 0, 'measure': 'temperature'},
        {'unique_id': device_id, 'unit': 'percent', 'channel': 1, 'measure': 'humidity'}
    ]
    
    results = read_influxdb_multi(channels_data, past_seconds=1000)
    
    print(f"Multi-channel results: {results}")
    
    # Verify we got results for both channels
    assert len(results) == 2
    assert 0 in results
    assert 1 in results
    
    # Verify channel 0 temperature
    assert results[0][1] == 25.5
    
    # Verify channel 1 humidity
    assert results[1][1] == 65.3

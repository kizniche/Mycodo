# coding=utf-8
""" Tests for the TSL2591 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.tsl2591_sensor import InputModule as TSL2591Sensor


# ----------------------------
#   TSL2591 tests
# ----------------------------
def test_tsl2591_sensor_iterates_using_in():
    """ Verify that a TSL2591Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]

        tsl2591_sensor = TSL2591Sensor(None, testing=True)
        expected_result_list = [dict(lux=67.00),
                                dict(lux=52.00),
                                dict(lux=37.00),
                                dict(lux=45.00)]
        assert expected_result_list == [temp for temp in tsl2591_sensor]


def test_tsl2591_sensor__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement') as mock_measure:

        mock_measure.side_effect = [67, 52]
        tsl2591_sensor = TSL2591Sensor(None, testing=True)

        assert isinstance(tsl2591_sensor.__iter__(), Iterator)


def test_tsl2591_sensor_read_updates_temp():
    """  Verify that TSL2591Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        tsl2591_sensor = TSL2591Sensor(None, testing=True)
        assert tsl2591_sensor._lux is None
        assert not tsl2591_sensor.read()
        assert tsl2591_sensor._lux == 67.0
        assert not tsl2591_sensor.read()
        assert tsl2591_sensor._lux == 52.0


def test_tsl2591_sensor_next_returns_dict():
    """ next returns dict(lux=float) """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        tsl2591_sensor = TSL2591Sensor(None, testing=True)
        assert tsl2591_sensor.next() == dict(lux=67.00)


def test_tsl2591_sensor_condition_properties():
    """ verify lux property """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        tsl2591_sensor = TSL2591Sensor(None, testing=True)
        assert tsl2591_sensor._lux is None
        assert tsl2591_sensor.lux == 67.00
        assert tsl2591_sensor.lux == 67.00
        assert not tsl2591_sensor.read()
        assert tsl2591_sensor.lux == 52.00


def test_tsl2591_sensor_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        tsl2591_sensor = TSL2591Sensor(None, testing=True)
        tsl2591_sensor.read()
        assert "Lux: 0.00" in str(tsl2591_sensor)


def test_tsl2591_sensor_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        tsl2591_sensor = TSL2591Sensor(None, testing=True)
        tsl2591_sensor.read()
        assert "<InputModule(lux=0.00)>" in repr(tsl2591_sensor)


def test_tsl2591_sensor_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            TSL2591Sensor(None, testing=True).next()


def test_tsl2591_sensor_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement', side_effect=Exception):
        assert TSL2591Sensor(None, testing=True).read()


def test_tsl2591_sensor_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.tsl2591_sensor.InputModule.get_measurement', side_effect=Exception('msg')):
            TSL2591Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.tsl2591_sensor', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

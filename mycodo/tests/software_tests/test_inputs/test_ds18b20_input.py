# coding=utf-8
""" Tests for the DS18B20 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.ds18b20 import DS18B20Sensor


# ----------------------------
#   DS18B20 tests
# ----------------------------
def test_ds18b20_iterates_using_in():
    """ Verify that a DS18B20Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        ds18b20 = DS18B20Sensor(None, testing=True)
        expected_result_list = [dict(temperature=67.00),
                                dict(temperature=52.00),
                                dict(temperature=37.00),
                                dict(temperature=45.00)]
        assert expected_result_list == [temp for temp in ds18b20]


def test_ds18b20__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        ds18b20 = DS18B20Sensor(None, testing=True)
        # check __iter__ method return
        assert isinstance(ds18b20.__iter__(), Iterator)


def test_ds18b20_read_updates_temp():
    """  Verify that DS18B20Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        ds18b20 = DS18B20Sensor(None, testing=True)
        # test our read() function
        assert ds18b20._temperature is None  # init value
        assert not ds18b20.read()  # updating the value using our mock_measure side effect has no error
        assert ds18b20._temperature == 67.0  # first value
        assert not ds18b20.read()  # updating the value using our mock_measure side effect has no error
        assert ds18b20._temperature == 52.0  # second value


def test_ds18b20_next_returns_dict():
    """ next returns dict(temperature=float) """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        ds18b20 = DS18B20Sensor(None, testing=True)
        assert ds18b20.next() == dict(temperature=67.00)


def test_ds18b20_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        ds18b20 = DS18B20Sensor(None, testing=True)
        assert ds18b20._temperature is None  # initial value
        assert ds18b20.temperature == 67.00  # first reading with auto update
        assert ds18b20.temperature == 67.00  # same first reading, not updated yet
        assert not ds18b20.read()  # update (no errors)
        assert ds18b20.temperature == 52.00  # next reading


def test_ds18b20_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        ds18b20 = DS18B20Sensor(None, testing=True)
        ds18b20.read()  # updating the value
        assert "Temperature: 0.00" in str(ds18b20)


def test_ds18b20_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        ds18b20 = DS18B20Sensor(None, testing=True)
        ds18b20.read()  # updating the value
        assert "<DS18B20Sensor(temperature=0.00)>" in repr(ds18b20)


def test_ds18b20_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            DS18B20Sensor(None, testing=True).next()


def test_ds18b20_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement', side_effect=Exception):
        assert DS18B20Sensor(None, testing=True).read()


def test_ds18b20_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.inputs.ds18b20.DS18B20Sensor.get_measurement', side_effect=Exception('msg')):
            DS18B20Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.ds18b20', 'ERROR', 'DS18B20Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

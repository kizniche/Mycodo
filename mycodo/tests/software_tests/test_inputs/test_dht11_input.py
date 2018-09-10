# coding=utf-8
""" Tests for the DHT11 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.dht11 import InputModule as DHT11Sensor


# ----------------------------
#   DHT11 tests
# ----------------------------
def test_dht11_iterates_using_in():
    """ Verify that a DHT11Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        dht11 = DHT11Sensor(None, testing=True)
        expected_result_list = [dict(dewpoint=23.0, humidity=50.0, temperature=3000.0),
                                dict(dewpoint=25.0, humidity=55.0, temperature=3200.0),
                                dict(dewpoint=27.0, humidity=60.0, temperature=3400.0),
                                dict(dewpoint=30.0, humidity=65.0, temperature=3300.0)]
        assert expected_result_list == [temp for temp in dht11]


def test_dht11__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        dht11 = DHT11Sensor(None, testing=True)
        assert isinstance(dht11.__iter__(), Iterator)


def test_dht11_read_updates_temp():
    """  Verify that DHT11Sensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        dht11 = DHT11Sensor(None, testing=True)
        assert dht11._dew_point is None
        assert dht11._humidity is None
        assert dht11._temperature is None
        assert not dht11.read()
        assert dht11._dew_point == 23.0
        assert dht11._humidity == 50.0
        assert dht11._temperature == 3000.0
        assert not dht11.read()
        assert dht11._dew_point == 25.0
        assert dht11._humidity == 55.0
        assert dht11._temperature == 3200.0


def test_dht11_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,temperature=float) """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000)]
        dht11 = DHT11Sensor(None, testing=True)
        assert dht11.next() == dict(dewpoint=23.0,
                                  humidity=50.0,
                                  temperature=3000.0)


def test_dht11_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        dht11 = DHT11Sensor(None, testing=True)
        assert dht11._dew_point is None # initial values
        assert dht11._humidity is None
        assert dht11._temperature is None
        assert dht11.dew_point == 23.0
        assert dht11.dew_point == 23.0
        assert dht11.humidity == 50.0
        assert dht11.humidity == 50.0
        assert dht11.temperature == 3000.0
        assert dht11.temperature == 3000.0
        assert not dht11.read()
        assert dht11.dew_point == 25.0
        assert dht11.humidity == 55.0
        assert dht11.temperature == 3200.0


def test_dht11_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        dht11 = DHT11Sensor(None, testing=True)
        dht11.read()
    assert "Dew Point: 0.00" in str(dht11)
    assert "Humidity: 0.00" in str(dht11)
    assert "Temperature: 0.00" in str(dht11)


def test_dht11_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        dht11 = DHT11Sensor(None, testing=True)
        dht11.read()
        assert "<InputModule(dewpoint=0.00)(humidity=0.00)(temperature=0.00)>" in repr(dht11)


def test_dht11_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            DHT11Sensor(None, testing=True).next()


def test_dht11_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement', side_effect=Exception):
        assert DHT11Sensor(None, testing=True).read()


def test_dht11_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.dht11.InputModule.get_measurement',
                        side_effect=Exception('msg')):
            DHT11Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.dht11', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

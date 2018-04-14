# coding=utf-8
""" Tests for the TMP006 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.tmp006 import TMP006Sensor


# ----------------------------
#   TMP006 tests
# ----------------------------
def test_tmp006_iterates_using_in():
    """ Verify that a TMP006Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50),
                                    (25, 55),
                                    (27, 60),
                                    (30, 65)]
        tmp006 = TMP006Sensor(None, testing=True)
        expected_result_list = [dict(temperature_die=23.0, temperature_object=50.0),
                                dict(temperature_die=25.0, temperature_object=55.0),
                                dict(temperature_die=27.0, temperature_object=60.0),
                                dict(temperature_die=30.0, temperature_object=65.0)]
        assert expected_result_list == [temp for temp in tmp006]


def test_tmp006__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50),
                                    (25, 55),
                                    (27, 60),
                                    (30, 65)]
        tmp006 = TMP006Sensor(None, testing=True)
        assert isinstance(tmp006.__iter__(), Iterator)


def test_tmp006_read_updates_temp():
    """  Verify that TMP006Sensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50),
                                    (25, 55)]
        tmp006 = TMP006Sensor(None, testing=True)
        assert tmp006._temperature_die is None
        assert tmp006._temperature_object is None
        assert not tmp006.read()
        assert tmp006._temperature_die == 23.0
        assert tmp006._temperature_object == 50.0
        assert not tmp006.read()
        assert tmp006._temperature_die == 25.0
        assert tmp006._temperature_object == 55.0


def test_tmp006_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,temperature=float) """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50)]
        tmp006 = TMP006Sensor(None, testing=True)
        assert tmp006.next() == dict(temperature_die=23.0,
                                     temperature_object=50.0,)


def test_tmp006_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50),
                                    (25, 55)]
        tmp006 = TMP006Sensor(None, testing=True)
        assert tmp006._temperature_die is None
        assert tmp006._temperature_object is None
        assert tmp006.temperature_die == 23.0
        assert tmp006.temperature_die == 23.0
        assert tmp006.temperature_object == 50.0
        assert tmp006.temperature_object == 50.0
        assert not tmp006.read()
        assert tmp006.temperature_die == 25.0
        assert tmp006.temperature_object == 55.0


def test_tmp006_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0)]
        tmp006 = TMP006Sensor(None, testing=True)
        tmp006.read()
    assert "Temperature (Die): 0.00" in str(tmp006)
    assert "Temperature (Object): 0.00" in str(tmp006)


def test_tmp006_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0)]
        tmp006 = TMP006Sensor(None, testing=True)
        tmp006.read()
        assert "<TMP006Sensor(temperature_die=0.00)(temperature_object=0.00)>" in repr(tmp006)


def test_tmp006_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            TMP006Sensor(None, testing=True).next()


def test_tmp006_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement', side_effect=Exception):
        assert TMP006Sensor(None, testing=True).read()


def test_tmp006_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.tmp006.TMP006Sensor.get_measurement',
                        side_effect=Exception('msg')):
            TMP006Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.tmp006', 'ERROR', 'TMP006Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

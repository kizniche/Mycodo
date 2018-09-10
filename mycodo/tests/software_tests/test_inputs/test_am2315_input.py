# coding=utf-8
""" Tests for the AM2315 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.am2315 import InputModule as AM2315Sensor


# ----------------------------
#   AM2315 tests
# ----------------------------
def test_am2315_iterates_using_in():
    """ Verify that a AM2315Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(15, 23, 67),
                                    (16, 25, 52),
                                    (17, 27, 37),
                                    (18, 30, 45)]
        am2315 = AM2315Sensor(None, testing=True)
        expected_result_list = [dict(dewpoint=15, humidity=23, temperature=67.00),
                                dict(dewpoint=16, humidity=25, temperature=52.00),
                                dict(dewpoint=17, humidity=27, temperature=37.00),
                                dict(dewpoint=18, humidity=30, temperature=45.00)]
        assert expected_result_list == [temp for temp in am2315]


def test_am2315__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 67),
                                    (25, 52)]
        am2315 = AM2315Sensor(None, testing=True)
        assert isinstance(am2315.__iter__(), Iterator)


def test_am2315_read_updates_temp():
    """  Verify that AM2315Sensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(20, 33, 67),
                                    (22, 59, 52)]
        am2315 = AM2315Sensor(None, testing=True)
        assert am2315._dew_point is None
        assert am2315._humidity is None
        assert am2315._temperature is None
        assert not am2315.read()
        assert am2315._dew_point == 20.0
        assert am2315._humidity == 33.0
        assert am2315._temperature == 67.0
        assert not am2315.read()
        assert am2315._dew_point == 22.0
        assert am2315._humidity == 59.0
        assert am2315._temperature == 52.0


def test_am2315_next_returns_dict():
    """ next returns dict(temperature=float) """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(20, 44, 67),
                                    (22, 64, 52)]
        am2315 = AM2315Sensor(None, testing=True)
        assert am2315.next() == dict(dewpoint=20,
                                     humidity=44,
                                     temperature=67.00)


def test_am2315_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(20, 50, 67),
                                    (22, 55, 52)]
        am2315 = AM2315Sensor(None, testing=True)
        assert am2315._dew_point is None
        assert am2315._humidity is None
        assert am2315._temperature is None
        assert am2315.dew_point == 20.00
        assert am2315.dew_point == 20.00
        assert am2315.humidity == 50.00
        assert am2315.humidity == 50.00
        assert am2315.temperature == 67.00
        assert am2315.temperature == 67.00
        assert not am2315.read()
        assert am2315.dew_point == 22.00
        assert am2315.humidity == 55.00
        assert am2315.temperature == 52.00


def test_am2315_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        am2315 = AM2315Sensor(None, testing=True)
        am2315.read()
        assert "Dew Point: 0.00" in str(am2315)
        assert "Humidity: 0.00" in str(am2315)
        assert "Temperature: 0.00" in str(am2315)


def test_am2315_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        am2315 = AM2315Sensor(None, testing=True)
        am2315.read()
        assert "<InputModule(dewpoint=0.00)(humidity=0.00)(temperature=0.00)>" in repr(am2315)


def test_am2315_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            AM2315Sensor(None, testing=True).next()


def test_am2315_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement', side_effect=Exception):
        assert AM2315Sensor(None, testing=True).read()


def test_am2315_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.am2315.InputModule.get_measurement', side_effect=Exception('msg')):
            AM2315Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.am2315', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

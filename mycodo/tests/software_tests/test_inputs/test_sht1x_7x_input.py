# coding=utf-8
""" Tests for the SHT1x7x sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.sht1x_7x import SHT1x7xSensor


# ----------------------------
#   SHT1x7x tests
# ----------------------------
def test_sht1x_7x_iterates_using_in():
    """ Verify that a SHT1x7xSensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        sht1x_7x = SHT1x7xSensor(None, testing=True)
        expected_result_list = [dict(dewpoint=23.0, humidity=50.0, temperature=3000.0),
                                dict(dewpoint=25.0, humidity=55.0, temperature=3200.0),
                                dict(dewpoint=27.0, humidity=60.0, temperature=3400.0),
                                dict(dewpoint=30.0, humidity=65.0, temperature=3300.0)]
        assert expected_result_list == [temp for temp in sht1x_7x]


def test_sht1x_7x__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        sht1x_7x = SHT1x7xSensor(None, testing=True)
        assert isinstance(sht1x_7x.__iter__(), Iterator)


def test_sht1x_7x_read_updates_temp():
    """  Verify that SHT1x7xSensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        sht1x_7x = SHT1x7xSensor(None, testing=True)
        assert sht1x_7x._dew_point is None
        assert sht1x_7x._humidity is None
        assert sht1x_7x._temperature is None
        assert not sht1x_7x.read()
        assert sht1x_7x._dew_point == 23.0
        assert sht1x_7x._humidity == 50.0
        assert sht1x_7x._temperature == 3000.0
        assert not sht1x_7x.read()
        assert sht1x_7x._dew_point == 25.0
        assert sht1x_7x._humidity == 55.0
        assert sht1x_7x._temperature == 3200.0


def test_sht1x_7x_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,temperature=float) """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000)]
        sht1x_7x = SHT1x7xSensor(None, testing=True)
        assert sht1x_7x.next() == dict(dewpoint=23.0,
                                  humidity=50.0,
                                  temperature=3000.0)


def test_sht1x_7x_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        sht1x_7x = SHT1x7xSensor(None, testing=True)
        assert sht1x_7x._dew_point is None # initial values
        assert sht1x_7x._humidity is None
        assert sht1x_7x._temperature is None
        assert sht1x_7x.dew_point == 23.0
        assert sht1x_7x.dew_point == 23.0
        assert sht1x_7x.humidity == 50.0
        assert sht1x_7x.humidity == 50.0
        assert sht1x_7x.temperature == 3000.0
        assert sht1x_7x.temperature == 3000.0
        assert not sht1x_7x.read()
        assert sht1x_7x.dew_point == 25.0
        assert sht1x_7x.humidity == 55.0
        assert sht1x_7x.temperature == 3200.0


def test_sht1x_7x_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        sht1x_7x = SHT1x7xSensor(None, testing=True)
        sht1x_7x.read()
    assert "Dew Point: 0.00" in str(sht1x_7x)
    assert "Humidity: 0.00" in str(sht1x_7x)
    assert "Temperature: 0.00" in str(sht1x_7x)


def test_sht1x_7x_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        sht1x_7x = SHT1x7xSensor(None, testing=True)
        sht1x_7x.read()
        assert "<SHT1x7xSensor(dewpoint=0.00)(humidity=0.00)(temperature=0.00)>" in repr(sht1x_7x)


def test_sht1x_7x_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            SHT1x7xSensor(None, testing=True).next()


def test_sht1x_7x_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement', side_effect=Exception):
        assert SHT1x7xSensor(None, testing=True).read()


def test_sht1x_7x_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.sht1x_7x.SHT1x7xSensor.get_measurement',
                        side_effect=Exception('msg')):
            SHT1x7xSensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.sht1x_7x', 'ERROR', 'SHT1x7xSensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

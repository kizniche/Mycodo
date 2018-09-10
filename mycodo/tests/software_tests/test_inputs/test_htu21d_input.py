# coding=utf-8
""" Tests for the HTU21D sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.htu21d import InputModule as HTU21DSensor


# ----------------------------
#   HTU21D tests
# ----------------------------
def test_htu21d_iterates_using_in():
    """ Verify that a HTU21DSensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        htu21d = HTU21DSensor(None, testing=True)
        expected_result_list = [dict(dewpoint=23.0, humidity=50.0, temperature=3000.0),
                                dict(dewpoint=25.0, humidity=55.0, temperature=3200.0),
                                dict(dewpoint=27.0, humidity=60.0, temperature=3400.0),
                                dict(dewpoint=30.0, humidity=65.0, temperature=3300.0)]
        assert expected_result_list == [temp for temp in htu21d]


def test_htu21d__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        htu21d = HTU21DSensor(None, testing=True)
        assert isinstance(htu21d.__iter__(), Iterator)


def test_htu21d_read_updates_temp():
    """  Verify that HTU21DSensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        htu21d = HTU21DSensor(None, testing=True)
        assert htu21d._dew_point is None
        assert htu21d._humidity is None
        assert htu21d._temperature is None
        assert not htu21d.read()
        assert htu21d._dew_point == 23.0
        assert htu21d._humidity == 50.0
        assert htu21d._temperature == 3000.0
        assert not htu21d.read()
        assert htu21d._dew_point == 25.0
        assert htu21d._humidity == 55.0
        assert htu21d._temperature == 3200.0


def test_htu21d_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,temperature=float) """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000)]
        htu21d = HTU21DSensor(None, testing=True)
        assert htu21d.next() == dict(dewpoint=23.0,
                                  humidity=50.0,
                                  temperature=3000.0)


def test_htu21d_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        htu21d = HTU21DSensor(None, testing=True)
        assert htu21d._dew_point is None # initial values
        assert htu21d._humidity is None
        assert htu21d._temperature is None
        assert htu21d.dew_point == 23.0
        assert htu21d.dew_point == 23.0
        assert htu21d.humidity == 50.0
        assert htu21d.humidity == 50.0
        assert htu21d.temperature == 3000.0
        assert htu21d.temperature == 3000.0
        assert not htu21d.read()
        assert htu21d.dew_point == 25.0
        assert htu21d.humidity == 55.0
        assert htu21d.temperature == 3200.0


def test_htu21d_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        htu21d = HTU21DSensor(None, testing=True)
        htu21d.read()
    assert "Dew Point: 0.00" in str(htu21d)
    assert "Humidity: 0.00" in str(htu21d)
    assert "Temperature: 0.00" in str(htu21d)


def test_htu21d_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        htu21d = HTU21DSensor(None, testing=True)
        htu21d.read()
        assert "<InputModule(dewpoint=0.00)(humidity=0.00)(temperature=0.00)>" in repr(htu21d)


def test_htu21d_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            HTU21DSensor(None, testing=True).next()


def test_htu21d_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement', side_effect=Exception):
        assert HTU21DSensor(None, testing=True).read()


def test_htu21d_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.htu21d.InputModule.get_measurement',
                        side_effect=Exception('msg')):
            HTU21DSensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.htu21d', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

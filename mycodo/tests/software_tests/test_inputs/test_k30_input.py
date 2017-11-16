# coding=utf-8
""" Tests for the K30 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.k30 import K30Sensor


# ----------------------------
#   K30 tests
# ----------------------------
def test_k30_iterates_using_in():
    """ Verify that a K30Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]
        k30 = K30Sensor(None, testing=True)
        expected_result_list = [dict(co2=67.00),
                                dict(co2=52.00),
                                dict(co2=37.00),
                                dict(co2=45.00)]
        assert expected_result_list == [temp for temp in k30]


def test_k30__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        k30 = K30Sensor(None, testing=True)

        assert isinstance(k30.__iter__(), Iterator)


def test_k30_read_updates_temp():
    """  Verify that K30Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        k30 = K30Sensor(None, testing=True)
        assert k30._co2 is None
        assert not k30.read()
        assert k30._co2 == 67.0
        assert not k30.read()
        assert k30._co2 == 52.0


def test_k30_next_returns_dict():
    """ next returns dict(co2=float) """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        k30 = K30Sensor(None, testing=True)
        assert k30.next() == dict(co2=67.00)


def test_k30_condition_properties():
    """ verify co2 property """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        k30 = K30Sensor(None, testing=True)
        assert k30._co2 is None
        assert k30.co2 == 67.00
        assert k30.co2 == 67.00
        assert not k30.read()
        assert k30.co2 == 52.00


def test_k30_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        k30 = K30Sensor(None, testing=True)
        k30.read()
        assert "CO2: 0.00" in str(k30)


def test_k30_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        k30 = K30Sensor(None, testing=True)
        k30.read()
        assert "<K30Sensor(co2=0.00)>" in repr(k30)


def test_k30_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            K30Sensor(None, testing=True).next()


def test_k30_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement', side_effect=Exception):
        assert K30Sensor(None, testing=True).read()


def test_k30_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.k30.K30Sensor.get_measurement', side_effect=Exception('msg')):
            K30Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.k30', 'ERROR', 'K30Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

# coding=utf-8
""" Tests for the MHZ16 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.mh_z16 import MHZ16Sensor


# ----------------------------
#   MHZ16 tests
# ----------------------------
def test_mh_z16_iterates_using_in():
    """ Verify that a MHZ16Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]
        mh_z16 = MHZ16Sensor(None, testing=True)
        expected_result_list = [dict(co2=67.00),
                                dict(co2=52.00),
                                dict(co2=37.00),
                                dict(co2=45.00)]
        assert expected_result_list == [temp for temp in mh_z16]


def test_mh_z16__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mh_z16 = MHZ16Sensor(None, testing=True)
        assert isinstance(mh_z16.__iter__(), Iterator)


def test_mh_z16_read_updates_temp():
    """  Verify that MHZ16Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mh_z16 = MHZ16Sensor(None, testing=True)
        assert mh_z16._co2 is None
        assert not mh_z16.read()
        assert mh_z16._co2 == 67.0
        assert not mh_z16.read()
        assert mh_z16._co2 == 52.0


def test_mh_z16_next_returns_dict():
    """ next returns dict(co2=float) """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mh_z16 = MHZ16Sensor(None, testing=True)
        assert mh_z16.next() == dict(co2=67.00)


def test_mh_z16_condition_properties():
    """ verify co2 property """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mh_z16 = MHZ16Sensor(None, testing=True)
        assert mh_z16._co2 is None
        assert mh_z16.co2 == 67.00
        assert mh_z16.co2 == 67.00
        assert not mh_z16.read()
        assert mh_z16.co2 == 52.00


def test_mh_z16_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        mh_z16 = MHZ16Sensor(None, testing=True)
        mh_z16.read()
        assert "CO2: 0.00" in str(mh_z16)


def test_mh_z16_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        mh_z16 = MHZ16Sensor(None, testing=True)
        mh_z16.read()
        assert "<MHZ16Sensor(co2=0.00)>" in repr(mh_z16)


def test_mh_z16_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            MHZ16Sensor(None, testing=True).next()


def test_mh_z16_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement', side_effect=Exception):
        assert MHZ16Sensor(None, testing=True).read()


def test_mh_z16_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.mh_z16.MHZ16Sensor.get_measurement', side_effect=Exception('msg')):
            MHZ16Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.mh_z16', 'ERROR', 'MHZ16Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

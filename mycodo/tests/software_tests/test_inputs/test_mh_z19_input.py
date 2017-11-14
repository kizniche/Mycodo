# coding=utf-8
""" Tests for the MHZ19 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.mh_z19 import MHZ19Sensor


# ----------------------------
#   MHZ19 tests
# ----------------------------
def test_mh_z19_iterates_using_in():
    """ Verify that a MHZ19Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        mh_z19 = MHZ19Sensor(None, testing=True)
        expected_result_list = [dict(co2=67.00),
                                dict(co2=52.00),
                                dict(co2=37.00),
                                dict(co2=45.00)]
        assert expected_result_list == [temp for temp in mh_z19]


def test_mh_z19__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        mh_z19 = MHZ19Sensor(None, testing=True)
        # check __iter__ method return
        assert isinstance(mh_z19.__iter__(), Iterator)


def test_mh_z19_read_updates_temp():
    """  Verify that MHZ19Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        mh_z19 = MHZ19Sensor(None, testing=True)
        # test our read() function
        assert mh_z19._co2 is None  # init value
        assert not mh_z19.read()  # updating the value using our mock_measure side effect has no error
        assert mh_z19._co2 == 67.0  # first value
        assert not mh_z19.read()  # updating the value using our mock_measure side effect has no error
        assert mh_z19._co2 == 52.0  # second value


def test_mh_z19_next_returns_dict():
    """ next returns dict(co2=float) """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        mh_z19 = MHZ19Sensor(None, testing=True)
        assert mh_z19.next() == dict(co2=67.00)


def test_mh_z19_condition_properties():
    """ verify co2 property """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        mh_z19 = MHZ19Sensor(None, testing=True)
        assert mh_z19._co2 is None  # initial value
        assert mh_z19.co2 == 67.00  # first reading with auto update
        assert mh_z19.co2 == 67.00  # same first reading, not updated yet
        assert not mh_z19.read()  # update (no errors)
        assert mh_z19.co2 == 52.00  # next reading


def test_mh_z19_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        mh_z19 = MHZ19Sensor(None, testing=True)
        mh_z19.read()  # updating the value
        assert "CO2: 0.00" in str(mh_z19)


def test_mh_z19_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        mh_z19 = MHZ19Sensor(None, testing=True)
        mh_z19.read()  # updating the value
        assert "<MHZ19Sensor(co2=0.00)>" in repr(mh_z19)


def test_mh_z19_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            MHZ19Sensor(None, testing=True).next()


def test_mh_z19_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement', side_effect=Exception):
        assert MHZ19Sensor(None, testing=True).read()


def test_mh_z19_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.inputs.mh_z19.MHZ19Sensor.get_measurement', side_effect=Exception('msg')):
            MHZ19Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.mh_z19', 'ERROR', 'MHZ19Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

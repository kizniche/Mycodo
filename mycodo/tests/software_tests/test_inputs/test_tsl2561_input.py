# coding=utf-8
""" Tests for the TSL2561 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.tsl2561 import TSL2561Sensor


# ----------------------------
#   TSL2561 tests
# ----------------------------
def test_tsl2561_iterates_using_in():
    """ Verify that a TSL2561Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        tsl2561 = TSL2561Sensor(None, None, testing=True)
        expected_result_list = [dict(lux=67.00),
                                dict(lux=52.00),
                                dict(lux=37.00),
                                dict(lux=45.00)]
        assert expected_result_list == [temp for temp in tsl2561]


def test_tsl2561__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        tsl2561 = TSL2561Sensor(None, None, testing=True)
        # check __iter__ method return
        assert isinstance(tsl2561.__iter__(), Iterator)


def test_tsl2561_read_updates_temp():
    """  Verify that TSL2561Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        tsl2561 = TSL2561Sensor(None, None, testing=True)
        # test our read() function
        assert tsl2561._lux is None  # init value
        assert not tsl2561.read()  # updating the value using our mock_measure side effect has no error
        assert tsl2561._lux == 67.0  # first value
        assert not tsl2561.read()  # updating the value using our mock_measure side effect has no error
        assert tsl2561._lux == 52.0  # second value


def test_tsl2561_next_returns_dict():
    """ next returns dict(lux=float) """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        tsl2561 = TSL2561Sensor(None, None, testing=True)
        assert tsl2561.next() == dict(lux=67.00)


def test_tsl2561_condition_properties():
    """ verify lux property """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        tsl2561 = TSL2561Sensor(None, None, testing=True)
        assert tsl2561._lux is None  # initial value
        assert tsl2561.lux == 67.00  # first reading with auto update
        assert tsl2561.lux == 67.00  # same first reading, not updated yet
        assert not tsl2561.read()  # update (no errors)
        assert tsl2561.lux == 52.00  # next reading


def test_tsl2561_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        tsl2561 = TSL2561Sensor(None, None, testing=True)
        tsl2561.read()  # updating the value
        assert "Lux: 0.00" in str(tsl2561)


def test_tsl2561_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        tsl2561 = TSL2561Sensor(None, None, testing=True)
        tsl2561.read()  # updating the value
        assert "<TSL2561Sensor(lux=0.00)>" in repr(tsl2561)


def test_tsl2561_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            TSL2561Sensor(None, None, testing=True).next()


def test_tsl2561_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement', side_effect=Exception):
        assert TSL2561Sensor(None, None, testing=True).read()


def test_tsl2561_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.inputs.tsl2561.TSL2561Sensor.get_measurement', side_effect=Exception('msg')):
            TSL2561Sensor(None, None, testing=True).read()
    expected_logs = ('mycodo.inputs.tsl2561', 'ERROR', 'TSL2561Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

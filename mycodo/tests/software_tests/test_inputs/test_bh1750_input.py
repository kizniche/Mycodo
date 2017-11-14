# coding=utf-8
""" Tests for the BH1750 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.bh1750 import BH1750Sensor


# ----------------------------
#   BH1750 tests
# ----------------------------
def test_bh1750_iterates_using_in():
    """ Verify that a BH1750Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        bh1750 = BH1750Sensor(None, None, None, None, testing=True)
        expected_result_list = [dict(lux=67.00),
                                dict(lux=52.00),
                                dict(lux=37.00),
                                dict(lux=45.00)]
        assert expected_result_list == [temp for temp in bh1750]


def test_bh1750__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        bh1750 = BH1750Sensor(None, None, None, None, testing=True)
        # check __iter__ method return
        assert isinstance(bh1750.__iter__(), Iterator)


def test_bh1750_read_updates_temp():
    """  Verify that BH1750Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        bh1750 = BH1750Sensor(None, None, None, None, testing=True)
        # test our read() function
        assert bh1750._lux is None  # init value
        assert not bh1750.read()  # updating the value using our mock_measure side effect has no error
        assert bh1750._lux == 67.0  # first value
        assert not bh1750.read()  # updating the value using our mock_measure side effect has no error
        assert bh1750._lux == 52.0  # second value


def test_bh1750_next_returns_dict():
    """ next returns dict(lux=float) """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        bh1750 = BH1750Sensor(None, None, None, None, testing=True)
        assert bh1750.next() == dict(lux=67.00)


def test_bh1750_condition_properties():
    """ verify lux property """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        bh1750 = BH1750Sensor(None, None, None, None, testing=True)
        assert bh1750._lux is None  # initial value
        assert bh1750.lux == 67.00  # first reading with auto update
        assert bh1750.lux == 67.00  # same first reading, not updated yet
        assert not bh1750.read()  # update (no errors)
        assert bh1750.lux == 52.00  # next reading


def test_bh1750_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        bh1750 = BH1750Sensor(None, None, None, None, testing=True)
        bh1750.read()  # updating the value
        assert "Lux: 0.00" in str(bh1750)


def test_bh1750_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        bh1750 = BH1750Sensor(None, None, None, None, testing=True)
        bh1750.read()  # updating the value
        assert "<BH1750Sensor(lux=0.00)>" in repr(bh1750)


def test_bh1750_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            BH1750Sensor(None, None, None, None, testing=True).next()


def test_bh1750_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement', side_effect=Exception):
        assert BH1750Sensor(None, None, None, None, testing=True).read()


def test_bh1750_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.inputs.bh1750.BH1750Sensor.get_measurement', side_effect=Exception('msg')):
            BH1750Sensor(None, None, None, None, testing=True).read()
    expected_logs = ('mycodo.inputs.bh1750', 'ERROR', 'BH1750Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

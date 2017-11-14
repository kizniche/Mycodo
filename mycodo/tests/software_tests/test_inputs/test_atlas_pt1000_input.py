# coding=utf-8
""" Tests for the AtlasPT1000 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.atlas_pt1000 import AtlasPT1000Sensor


# ----------------------------
#   AtlasPT1000 tests
# ----------------------------
def test_atlas_pt1000_iterates_using_in():
    """ Verify that a AtlasPT1000Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        atlas_pt1000 = AtlasPT1000Sensor(None, testing=True)
        expected_result_list = [dict(temperature=67.00),
                                dict(temperature=52.00),
                                dict(temperature=37.00),
                                dict(temperature=45.00)]
        assert expected_result_list == [temp for temp in atlas_pt1000]


def test_atlas_pt1000__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_pt1000 = AtlasPT1000Sensor(None, testing=True)
        # check __iter__ method return
        assert isinstance(atlas_pt1000.__iter__(), Iterator)


def test_atlas_pt1000_read_updates_temp():
    """  Verify that AtlasPT1000Sensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_pt1000 = AtlasPT1000Sensor(None, testing=True)
        # test our read() function
        assert atlas_pt1000._temperature is None  # init value
        assert not atlas_pt1000.read()  # updating the value using our mock_measure side effect has no error
        assert atlas_pt1000._temperature == 67.0  # first value
        assert not atlas_pt1000.read()  # updating the value using our mock_measure side effect has no error
        assert atlas_pt1000._temperature == 52.0  # second value


def test_atlas_pt1000_next_returns_dict():
    """ next returns dict(temperature=float) """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_pt1000 = AtlasPT1000Sensor(None, testing=True)
        assert atlas_pt1000.next() == dict(temperature=67.00)


def test_atlas_pt1000_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_pt1000 = AtlasPT1000Sensor(None, testing=True)
        assert atlas_pt1000._temperature is None  # initial value
        assert atlas_pt1000.temperature == 67.00  # first reading with auto update
        assert atlas_pt1000.temperature == 67.00  # same first reading, not updated yet
        assert not atlas_pt1000.read()  # update (no errors)
        assert atlas_pt1000.temperature == 52.00  # next reading


def test_atlas_pt1000_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        atlas_pt1000 = AtlasPT1000Sensor(None, testing=True)
        atlas_pt1000.read()  # updating the value
        assert "Temperature: 0.00" in str(atlas_pt1000)


def test_atlas_pt1000_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        atlas_pt1000 = AtlasPT1000Sensor(None, testing=True)
        atlas_pt1000.read()  # updating the value
        assert "<AtlasPT1000Sensor(temperature=0.00)>" in repr(atlas_pt1000)


def test_atlas_pt1000_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            AtlasPT1000Sensor(None, testing=True).next()


def test_atlas_pt1000_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement', side_effect=Exception):
        assert AtlasPT1000Sensor(None, testing=True).read()


def test_atlas_pt1000_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.inputs.atlas_pt1000.AtlasPT1000Sensor.get_measurement', side_effect=Exception('msg')):
            AtlasPT1000Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.atlas_pt1000', 'ERROR', 'AtlasPT1000Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

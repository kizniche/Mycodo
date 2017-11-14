# coding=utf-8
""" Tests for the AtlaspH sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.atlas_ph import AtlaspHSensor


# ----------------------------
#   AtlaspH tests
# ----------------------------
def test_atlas_ph_iterates_using_in():
    """ Verify that a AtlaspHSensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        atlas_ph = AtlaspHSensor(None, testing=True)
        expected_result_list = [dict(ph=67.00),
                                dict(ph=52.00),
                                dict(ph=37.00),
                                dict(ph=45.00)]
        assert expected_result_list == [temp for temp in atlas_ph]


def test_atlas_ph__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_ph = AtlaspHSensor(None, testing=True)
        # check __iter__ method return
        assert isinstance(atlas_ph.__iter__(), Iterator)


def test_atlas_ph_read_updates_temp():
    """  Verify that AtlaspHSensor(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_ph = AtlaspHSensor(None, testing=True)
        # test our read() function
        assert atlas_ph._ph is None  # init value
        assert not atlas_ph.read()  # updating the value using our mock_measure side effect has no error
        assert atlas_ph._ph == 67.0  # first value
        assert not atlas_ph.read()  # updating the value using our mock_measure side effect has no error
        assert atlas_ph._ph == 52.0  # second value


def test_atlas_ph_next_returns_dict():
    """ next returns dict(ph=float) """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_ph = AtlaspHSensor(None, testing=True)
        assert atlas_ph.next() == dict(ph=67.00)


def test_atlas_ph_condition_properties():
    """ verify ph property """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        atlas_ph = AtlaspHSensor(None, testing=True)
        assert atlas_ph._ph is None  # initial value
        assert atlas_ph.ph == 67.00  # first reading with auto update
        assert atlas_ph.ph == 67.00  # same first reading, not updated yet
        assert not atlas_ph.read()  # update (no errors)
        assert atlas_ph.ph == 52.00  # next reading


def test_atlas_ph_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        atlas_ph = AtlaspHSensor(None, testing=True)
        atlas_ph.read()  # updating the value
        assert "pH: 0.00" in str(atlas_ph)


def test_atlas_ph_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        atlas_ph = AtlaspHSensor(None, testing=True)
        atlas_ph.read()  # updating the value
        assert "<AtlaspHSensor(ph=0.00)>" in repr(atlas_ph)


def test_atlas_ph_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            AtlaspHSensor(None, testing=True).next()


def test_atlas_ph_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement', side_effect=Exception):
        assert AtlaspHSensor(None, testing=True).read()


def test_atlas_ph_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.inputs.atlas_ph.AtlaspHSensor.get_measurement', side_effect=Exception('msg')):
            AtlaspHSensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.atlas_ph', 'ERROR', 'AtlaspHSensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

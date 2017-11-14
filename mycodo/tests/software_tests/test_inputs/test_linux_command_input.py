# coding=utf-8
""" Tests for the LinuxCommand sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.linux_command import LinuxCommand


# ----------------------------
#   LinuxCommand tests
# ----------------------------
def test_linux_command_iterates_using_in():
    """ Verify that a LinuxCommand object can use the 'in' operator """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading
        linux_command = LinuxCommand(None, 'measurement', testing=True)
        expected_result_list = [dict(measurement=67.00),
                                dict(measurement=52.00),
                                dict(measurement=37.00),
                                dict(measurement=45.00)]
        assert expected_result_list == [temp for temp in linux_command]


def test_linux_command__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        linux_command = LinuxCommand(None, 'measurement', testing=True)
        # check __iter__ method return
        assert isinstance(linux_command.__iter__(), Iterator)


def test_linux_command_read_updates_temp():
    """  Verify that LinuxCommand(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        linux_command = LinuxCommand(None, 'measurement', testing=True)
        # test our read() function
        assert linux_command._measurement is None  # init value
        assert not linux_command.read()  # updating the value using our mock_measure side effect has no error
        assert linux_command._measurement == 67.0  # first value
        assert not linux_command.read()  # updating the value using our mock_measure side effect has no error
        assert linux_command._measurement == 52.0  # second value


def test_linux_command_next_returns_dict():
    """ next returns dict(measurement=float) """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        linux_command = LinuxCommand(None, 'measurement', testing=True)
        assert linux_command.next() == dict(measurement=67.00)


def test_linux_command_condition_properties():
    """ verify measurement property """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        linux_command = LinuxCommand(None, 'measurement', testing=True)
        assert linux_command._measurement is None  # initial value
        assert linux_command.measurement == 67.00  # first reading with auto update
        assert linux_command.measurement == 67.00  # same first reading, not updated yet
        assert not linux_command.read()  # update (no errors)
        assert linux_command.measurement == 52.00  # next reading


def test_linux_command_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        linux_command = LinuxCommand(None, 'measurement', testing=True)
        linux_command.read()  # updating the value
        assert "Measurement: 0.00" in str(linux_command)


def test_linux_command_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [0.0]  # first reading
        linux_command = LinuxCommand(None, 'measurement', testing=True)
        linux_command.read()  # updating the value
        assert "<LinuxCommand(measurement=0.00)>" in repr(linux_command)


def test_linux_command_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            LinuxCommand(None, 'measurement', testing=True).next()


def test_linux_command_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement', side_effect=Exception):
        assert LinuxCommand(None, 'measurement', testing=True).read()


def test_linux_command_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.inputs.linux_command.LinuxCommand.get_measurement', side_effect=Exception('msg')):
            LinuxCommand(None, 'measurement', testing=True).read()
    expected_logs = ('mycodo.inputs.linux_command', 'ERROR', 'LinuxCommand raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

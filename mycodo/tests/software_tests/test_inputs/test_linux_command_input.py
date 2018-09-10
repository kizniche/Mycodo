# coding=utf-8
""" Tests for the LinuxCommand sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.linux_command import InputModule as LinuxCommand


# ----------------------------
#   LinuxCommand tests
# ----------------------------
def test_linux_command_iterates_using_in():
    """ Verify that a LinuxCommand object can use the 'in' operator """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]
        linux_command = LinuxCommand(None, testing=True)
        expected_result_list = [dict(measurement=67.00),
                                dict(measurement=52.00),
                                dict(measurement=37.00),
                                dict(measurement=45.00)]
        assert expected_result_list == [temp for temp in linux_command]


def test_linux_command__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        linux_command = LinuxCommand(None, testing=True)
        assert isinstance(linux_command.__iter__(), Iterator)


def test_linux_command_read_updates_temp():
    """  Verify that LinuxCommand(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        linux_command = LinuxCommand(None, testing=True)
        assert linux_command._measurement is None
        assert not linux_command.read()
        assert linux_command._measurement == 67.0
        assert not linux_command.read()
        assert linux_command._measurement == 52.0


def test_linux_command_next_returns_dict():
    """ next returns dict(measurement=float) """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        linux_command = LinuxCommand(None, testing=True)
        assert linux_command.next() == dict(measurement=67.00)


def test_linux_command_condition_properties():
    """ verify measurement property """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        linux_command = LinuxCommand(None, testing=True)
        assert linux_command._measurement is None
        assert linux_command.measurement == 67.00
        assert linux_command.measurement == 67.00
        assert not linux_command.read()
        assert linux_command.measurement == 52.00


def test_linux_command_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        linux_command = LinuxCommand(None, testing=True)
        linux_command.read()
        assert "Measurement: 0.00" in str(linux_command)


def test_linux_command_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        linux_command = LinuxCommand(None, testing=True)
        linux_command.read()
        assert "<InputModule(measurement=0.00)>" in repr(linux_command)


def test_linux_command_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            LinuxCommand(None, testing=True).next()


def test_linux_command_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement', side_effect=Exception):
        assert LinuxCommand(None, testing=True).read()


def test_linux_command_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.linux_command.InputModule.get_measurement', side_effect=Exception('msg')):
            LinuxCommand(None, testing=True).read()
    expected_logs = ('mycodo.inputs.linux_command', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

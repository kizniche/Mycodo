# coding=utf-8
""" Tests for the DS18B20 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.signal_revolutions import InputModule as SignalRPMInput


# ----------------------------
#   SignalRPMInput tests
# ----------------------------
def test_signal_revolutions_iterates_using_in():
    """ Verify that a SignalRPMInput object can use the 'in' operator """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]
        signal_revolutions = SignalRPMInput(None, testing=True)
        expected_result_list = [dict(revolutions=67.00),
                                dict(revolutions=52.00),
                                dict(revolutions=37.00),
                                dict(revolutions=45.00)]
        assert expected_result_list == [temp for temp in signal_revolutions]


def test_signal_revolutions__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_revolutions = SignalRPMInput(None, testing=True)
        assert isinstance(signal_revolutions.__iter__(), Iterator)


def test_signal_revolutions_read_updates_temp():
    """  Verify that SignalRPMInput(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_revolutions = SignalRPMInput(None, testing=True)
        assert signal_revolutions._revolutions is None
        assert not signal_revolutions.read()
        assert signal_revolutions._revolutions == 67.0
        assert not signal_revolutions.read()
        assert signal_revolutions._revolutions == 52.0


def test_signal_revolutions_next_returns_dict():
    """ next returns dict(revolutions=float) """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_revolutions = SignalRPMInput(None, testing=True)
        assert signal_revolutions.next() == dict(revolutions=67.00)


def test_signal_revolutions_condition_properties():
    """ verify revolutions property """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_revolutions = SignalRPMInput(None, testing=True)
        assert signal_revolutions._revolutions is None
        assert signal_revolutions.revolutions == 67.00
        assert signal_revolutions.revolutions == 67.00
        assert not signal_revolutions.read()
        assert signal_revolutions.revolutions == 52.00


def test_signal_revolutions_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        signal_revolutions = SignalRPMInput(None, testing=True)
        signal_revolutions.read()
        assert "Revolutions: 0.00" in str(signal_revolutions)


def test_signal_revolutions_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        signal_revolutions = SignalRPMInput(None, testing=True)
        signal_revolutions.read()
        assert "<SignalRPMInput(revolutions=0.00)>" in repr(signal_revolutions)


def test_signal_revolutions_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            SignalRPMInput(None, testing=True).next()


def test_signal_revolutions_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement', side_effect=Exception):
        assert SignalRPMInput(None, testing=True).read()


def test_signal_revolutions_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.signal_revolutions.SignalRPMInput.get_measurement', side_effect=Exception('msg')):
            SignalRPMInput(None, testing=True).read()
    expected_logs = ('mycodo.inputs.signal_revolutions', 'ERROR', 'SignalRPMInput raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

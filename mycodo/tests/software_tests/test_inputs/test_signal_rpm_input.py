# coding=utf-8
""" Tests for the DS18B20 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.signal_rpm import SignalRPMInput


# ----------------------------
#   SignalRPMInput tests
# ----------------------------
def test_signal_rpm_iterates_using_in():
    """ Verify that a SignalRPMInput object can use the 'in' operator """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]
        signal_rpm = SignalRPMInput(None, testing=True)
        expected_result_list = [dict(rpm=67.00),
                                dict(rpm=52.00),
                                dict(rpm=37.00),
                                dict(rpm=45.00)]
        assert expected_result_list == [temp for temp in signal_rpm]


def test_signal_rpm__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_rpm = SignalRPMInput(None, testing=True)
        assert isinstance(signal_rpm.__iter__(), Iterator)


def test_signal_rpm_read_updates_temp():
    """  Verify that SignalRPMInput(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_rpm = SignalRPMInput(None, testing=True)
        assert signal_rpm._rpm is None
        assert not signal_rpm.read()
        assert signal_rpm._rpm == 67.0
        assert not signal_rpm.read()
        assert signal_rpm._rpm == 52.0


def test_signal_rpm_next_returns_dict():
    """ next returns dict(rpm=float) """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_rpm = SignalRPMInput(None, testing=True)
        assert signal_rpm.next() == dict(rpm=67.00)


def test_signal_rpm_condition_properties():
    """ verify rpm property """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        signal_rpm = SignalRPMInput(None, testing=True)
        assert signal_rpm._rpm is None
        assert signal_rpm.rpm == 67.00
        assert signal_rpm.rpm == 67.00
        assert not signal_rpm.read()
        assert signal_rpm.rpm == 52.00


def test_signal_rpm_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        signal_rpm = SignalRPMInput(None, testing=True)
        signal_rpm.read()
        assert "RPM: 0.00" in str(signal_rpm)


def test_signal_rpm_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        signal_rpm = SignalRPMInput(None, testing=True)
        signal_rpm.read()
        assert "<SignalRPMInput(rpm=0.00)>" in repr(signal_rpm)


def test_signal_rpm_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            SignalRPMInput(None, testing=True).next()


def test_signal_rpm_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement', side_effect=Exception):
        assert SignalRPMInput(None, testing=True).read()


def test_signal_rpm_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.signal_rpm.SignalRPMInput.get_measurement', side_effect=Exception('msg')):
            SignalRPMInput(None, testing=True).read()
    expected_logs = ('mycodo.inputs.signal_rpm', 'ERROR', 'SignalRPMInput raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

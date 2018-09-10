# coding=utf-8
""" Tests for the SHT2x sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.signal_pwm import InputModule as SignalPWMInput


# ----------------------------
#   SignalPWMInput tests
# ----------------------------
def test_signal_pwm_iterates_using_in():
    """ Verify that a SignalPWMInput object can use the 'in' operator """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        signal_pwm = SignalPWMInput(None, testing=True)
        expected_result_list = [dict(frequency=23.0, pulse_width=50.0, duty_cycle=3000.0),
                                dict(frequency=25.0, pulse_width=55.0, duty_cycle=3200.0),
                                dict(frequency=27.0, pulse_width=60.0, duty_cycle=3400.0),
                                dict(frequency=30.0, pulse_width=65.0, duty_cycle=3300.0)]
        assert expected_result_list == [temp for temp in signal_pwm]


def test_signal_pwm__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        signal_pwm = SignalPWMInput(None, testing=True)
        assert isinstance(signal_pwm.__iter__(), Iterator)


def test_signal_pwm_read_updates_temp():
    """  Verify that SignalPWMInput(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        signal_pwm = SignalPWMInput(None, testing=True)
        assert signal_pwm._frequency is None
        assert signal_pwm._pulse_width is None
        assert signal_pwm._duty_cycle is None
        assert not signal_pwm.read()
        assert signal_pwm._frequency == 23.0
        assert signal_pwm._pulse_width == 50.0
        assert signal_pwm._duty_cycle == 3000.0
        assert not signal_pwm.read()
        assert signal_pwm._frequency == 25.0
        assert signal_pwm._pulse_width == 55.0
        assert signal_pwm._duty_cycle == 3200.0


def test_signal_pwm_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,duty_cycle=float) """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000)]
        signal_pwm = SignalPWMInput(None, testing=True)
        assert signal_pwm.next() == dict(frequency=23.0,
                                  pulse_width=50.0,
                                  duty_cycle=3000.0)


def test_signal_pwm_condition_properties():
    """ verify duty_cycle property """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        signal_pwm = SignalPWMInput(None, testing=True)
        assert signal_pwm._frequency is None
        assert signal_pwm._pulse_width is None
        assert signal_pwm._duty_cycle is None
        assert signal_pwm.frequency == 23.0
        assert signal_pwm.frequency == 23.0
        assert signal_pwm.pulse_width == 50.0
        assert signal_pwm.pulse_width == 50.0
        assert signal_pwm.duty_cycle == 3000.0
        assert signal_pwm.duty_cycle == 3000.0
        assert not signal_pwm.read()
        assert signal_pwm.frequency == 25.0
        assert signal_pwm.pulse_width == 55.0
        assert signal_pwm.duty_cycle == 3200.0


def test_signal_pwm_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        signal_pwm = SignalPWMInput(None, testing=True)
        signal_pwm.read()
    assert "Frequency: 0.00" in str(signal_pwm)
    assert "Pulse Width: 0.00" in str(signal_pwm)
    assert "Duty Cycle: 0.00" in str(signal_pwm)


def test_signal_pwm_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        signal_pwm = SignalPWMInput(None, testing=True)
        signal_pwm.read()
        assert "<InputModule(frequency=0.00)(pulse_width=0.00)(duty_cycle=0.00)>" in repr(signal_pwm)


def test_signal_pwm_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            SignalPWMInput(None, testing=True).next()


def test_signal_pwm_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement', side_effect=Exception):
        assert SignalPWMInput(None, testing=True).read()


def test_signal_pwm_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.signal_pwm.InputModule.get_measurement',
                        side_effect=Exception('msg')):
            SignalPWMInput(None, testing=True).read()
    expected_logs = ('mycodo.inputs.signal_pwm', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

# coding=utf-8
""" Tests for the raspberry pi CPU and GPU temp classes """
import mock
import pytest
from testfixtures import LogCapture
from subprocess import CalledProcessError

from collections import Iterator
from mycodo.sensors.base_sensor import AbstractSensor
from mycodo.sensors.raspi import (RaspberryPiCPUTemp,
                                  RaspberryPiGPUTemp)


# ----------------------------
#   AbstractSensor
# ----------------------------
def test_abstract_sensor_deprecated_stopsensor_warns_use():
    """ verify that the depreciated stopSensor() method warns it's use """
    with LogCapture() as log_cap:
        RaspberryPiGPUTemp().stopSensor()
    expected_log = ('mycodo.sensors.base_sensor', 'WARNING', ('Old style `stopSensor()` called by '
                                                              'RaspberryPiGPUTemp.  This is depreciated '
                                                              'and will be deleted in future releases.  '
                                                              'Switch to using `stop_sensor` instead.'))
    assert expected_log in log_cap.actual()


def test_abstract_sensor_read_method_logs_when_not_implemented():
    """  verify that methods that are not overwritten log as errors"""
    with LogCapture() as log_cap:
        with pytest.raises(NotImplementedError):
            AbstractSensor().read()
    expected_error = ('mycodo.sensors.base_sensor', 'ERROR', ('AbstractSensor did not overwrite the read() '
                                                              'method.  All subclasses of the AbstractSensor '
                                                              'class are required to overwrite this method'))
    assert expected_error in log_cap.actual()


def test_abstract_sensor_next_method_logs_when_not_implemented():
    """ verify that methods that are not overwritten log as errors"""
    with LogCapture() as log_cap:
        with pytest.raises(NotImplementedError):
            AbstractSensor().next()
    expected_error = ('mycodo.sensors.base_sensor', 'ERROR', ('AbstractSensor did not overwrite the next() '
                                                              'method.  All subclasses of the AbstractSensor '
                                                              'class are required to overwrite this method'))
    assert expected_error in log_cap.actual()


# ----------------------------
#   RaspberryPiCPUTemp tests
# ----------------------------
def test_raspberry_pi_cpu_temp_has_depreciated_stop_sensor():
    """ Verify that the RaspberryPICPUTemp object has the stopSensor() method """
    assert hasattr(RaspberryPiCPUTemp(), 'stopSensor')


def test_raspberry_pi_cpu_temp_is_iterator_instance():
    """ Verify that a RaspberryPiCPUTemp object is and behaves like an iterator """
    assert isinstance(RaspberryPiCPUTemp(), Iterator), "RaspberryPiGPUTemp is not and iterator instance"


def test_raspberry_pi_cpu_temp_iterates_using_in():
    """ Verify that a RaspberryPiCPUTemp object can use the 'in' operator """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        rpicpu = RaspberryPiCPUTemp()
        expected_result_list = [dict(temperature=67.00),
                                dict(temperature=52.00),
                                dict(temperature=37.00),
                                dict(temperature=45.00)]
        assert expected_result_list == [temp for temp in rpicpu]


def test_raspberry_pi_cpu_temp__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        rpi_cpu = RaspberryPiCPUTemp()
        # check __iter__ method return
        assert isinstance(rpi_cpu.__iter__(), Iterator)


def test_raspberry_pi_cpu_temp_read_updates_temp():
    """  Verify that RaspberryPiCPUTemp().read() gets the average temp """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        rpi_cpu = RaspberryPiCPUTemp()

        # test our read() function
        assert rpi_cpu._temperature == 0  # init value
        assert not rpi_cpu.read()  # updating the value using our mock_measure side effect has no error
        assert rpi_cpu._temperature == 67.0  # first value
        assert not rpi_cpu.read()  # updating the value using our mock_measure side effect has no error
        assert rpi_cpu._temperature == 52.0  # second value


def test_raspberry_pi_cpu_temp_next_returns_dict():
    """ next returns dict(temperature=float) """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        rpi_cpu = RaspberryPiCPUTemp()
        assert rpi_cpu.next() == dict(temperature=67.00)


def test_raspberry_pi_cpu_temp_temperature_property():
    """ verify temperature property """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        rpi_cpu = RaspberryPiCPUTemp()
        assert rpi_cpu._temperature == 0  # initial value
        assert rpi_cpu.temperature == 67.00  # first reading with auto update
        assert rpi_cpu.temperature == 67.00  # same first reading, not updated yet
        assert not rpi_cpu.read()  # update (no errors)
        assert rpi_cpu.temperature == 52.00  # next reading


def test_raspberry_pi_cpu_temp_special_method_str():
    """ expect a __str__ format """
    assert "temperature: 0.00" in str(RaspberryPiCPUTemp())


def test_raspberry_pi_cpu_temp_special_method_repr():
    """ expect a __repr__ format """
    assert "<RaspberryPiCPUTemp(temperature=0.00)>" in repr(RaspberryPiCPUTemp())


def test_raspberry_pi_cpu_temp_raises_stop_iteration():
    """ stops iteration on read() error """
    with pytest.raises(StopIteration):
        RaspberryPiCPUTemp().next()


def test_raspberry_pi_cpu_temp_get_measurement_divs_by_1k():
    """ verify the return value of get_measurement """
    mocked_open = mock.mock_open(read_data='45780')  # value read from sys temperature file
    with mock.patch('mycodo.sensors.raspi.open', mocked_open, create=True):
        assert RaspberryPiCPUTemp.get_measurement() == 45.78  # value read / 1000


def test_raspberry_pi_cpu_read_logs_ioerrors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.sensors.raspi.RaspberryPiCPUTemp.get_measurement', side_effect=IOError('msg')):
            RaspberryPiCPUTemp().read()
    expected_logs = ('root', 'ERROR', "CPU temperature reading returned IOError: msg")
    assert expected_logs in log_cap.actual()


def test_raspberry_pi_cpu_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        # force an Exception to be raised when get_measurement is called
        with mock.patch('mycodo.sensors.raspi.RaspberryPiCPUTemp.get_measurement', side_effect=Exception('msg')):
            RaspberryPiCPUTemp().read()
    expected_logs = ('root', 'ERROR', 'Unknown error in RaspberryPiCPUTemp.get_measurement(): msg')
    assert expected_logs in log_cap.actual()


# ----------------------------
#  RaspberryPiGPUTemp tests
# ----------------------------
def test_raspberry_pi_gpu_temp_is_iterator_instance():
    """ Verify that a RaspberryPiGPUTemp object is and behaves like an iterator """
    assert isinstance(RaspberryPiGPUTemp(), Iterator), "RaspberryPiGPUTemp is not and iterator instance"


def test_raspberry_pi_gpu_temp_iterates_using_in():
    """ Verify that a RaspberryPiGPUTemp object can use the 'in' operator """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]  # first reading, second reading

        rpigpu = RaspberryPiGPUTemp()
        expected_result_list = [dict(temperature=67.00),
                                dict(temperature=52.00),
                                dict(temperature=37.00),
                                dict(temperature=45.00)]
        assert expected_result_list == [temp for temp in rpigpu]


def test_raspberry_pi_gpu_temp__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67, 52]  # first reading, second reading
        rpi_gpu = RaspberryPiGPUTemp()
        # check __iter__ method return
        assert isinstance(rpi_gpu.__iter__(), Iterator)


def test_raspberry_pi_gpu_temp_read_updates_temp():
    """  Verify that RaspberryPiGPUTemp().read() gets the average temp """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
        # create the get_measurement values
        mock_measure.side_effect = [67, 52]  # first reading, second reading

        # create our object and test
        rpi_gpu = RaspberryPiGPUTemp()
        assert rpi_gpu._temperature == 0  # initial value
        assert not rpi_gpu.read()  # update 1
        assert rpi_gpu._temperature == 67.0  # first reading at the init
        assert not rpi_gpu.read()  # update 2
        assert rpi_gpu._temperature == 52.0  # second value


def test_raspberry_pi_gpu_temp_temperature_property():
    """ verify temperature property """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
        # create the get_measurement values
        mock_measure.side_effect = [67.2, 52.5]  # first reading, second reading

        # create our object and test
        rpi_gpu = RaspberryPiGPUTemp()
        assert rpi_gpu._temperature == 0  # initial value
        assert rpi_gpu.temperature == 67.2  # first reading with auto update
        assert rpi_gpu.temperature == 67.2  # same reading, not updated yet
        assert not rpi_gpu.read()  # update (no errors)
        assert rpi_gpu.temperature == 52.5  # second reading


def test_raspberry_pi_gpu_temp_next_returns_dict():
    """ Expect next() to return string: '{'measurement type':measurement value}' """
    with mock.patch('mycodo.sensors.raspi.subprocess') as mock_subprocess:
        mock_subprocess.check_output.side_effect = lambda n: "temp=42.8'C"

        rpi_gpu = RaspberryPiGPUTemp()
        assert rpi_gpu.next() == dict(temperature=42.80)


def test_raspberry_pi_gpu_temp_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67.2, 52.5]  # first reading, second reading
        rpi_gpu = RaspberryPiGPUTemp()
        assert "temperature: 0.00" in str(rpi_gpu)  # initial value
        assert not rpi_gpu.read()  # update 1 (no errors)
        assert "temperature: 67.20" in str(rpi_gpu)  # first reading
        assert not rpi_gpu.read()  # update 2 (no errors)
        assert "temperature: 52.50" in str(rpi_gpu)  # second reading


def test_raspberry_pi_gpu_temp_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
        # create our object
        mock_measure.side_effect = [67.2, 52.5]  # first reading, second reading
        rpi_gpu = RaspberryPiGPUTemp()
        assert "<RaspberryPiGPUTemp(temperature=0.00)>" in repr(rpi_gpu)  # initial value
        assert not rpi_gpu.read()  # update 1 (no errors)
        assert "<RaspberryPiGPUTemp(temperature=67.20)>" in repr(rpi_gpu)  # first reading
        assert not rpi_gpu.read()  # update 2 (no errors)
        assert "<RaspberryPiGPUTemp(temperature=52.50)>" in repr(rpi_gpu)  # second reading


def test_raspberry_pi_gpu_temp_raises_stop_iteration():
    """ stops iteration on read() error """
    with pytest.raises(StopIteration):
        RaspberryPiGPUTemp().next()


def test_raspberry_pi_gpu_temp_get_measurement_method_returns_float():
    """ verify get_measurement string format """
    with mock.patch('mycodo.sensors.raspi.subprocess') as mock_subprocess:
        mock_subprocess.check_output.side_effect = lambda n: "temp=42.8'C"
        assert 42.8 == RaspberryPiGPUTemp.get_measurement()


def test_raspberry_pi_gpu_temp_read_logs_called_process_error():
    """ verify get_measurement string format """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement',
                        side_effect=CalledProcessError(cmd='cmd', returncode=0)):
            RaspberryPiGPUTemp().read()
    expected_log = ('root', 'ERROR', ("RaspberryPiGPUTemp.get_measurement() subprocess call raised Command "
                                      "'cmd' returned non-zero exit status 0"))
    assert expected_log in log_cap.actual()


def test_raspberry_pi_gpu_temp_read_logs_ioerror():
    """ verify get_measurement string format """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement', side_effect=IOError('msg')):
            RaspberryPiGPUTemp().read()
    expected_log = ('root', 'ERROR', "RaspberryPiGPUTemp.get_measurement() method raised IOError: msg")
    assert expected_log in log_cap.actual()


def test_raspberry_pi_gpu_temp_read_logs_unknown_errors():
    """ verify get_measurement string format """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.sensors.raspi.RaspberryPiGPUTemp.get_measurement', side_effect=Exception('msg')):
            RaspberryPiGPUTemp().read()
    expected_log = ('root', 'ERROR', "Unknown error in RaspberryPiGPUTemp.get_measurement(): msg")
    assert expected_log in log_cap.actual()

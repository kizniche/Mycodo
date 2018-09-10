# coding=utf-8
""" Tests for the raspberry pi CPU and GPU temp classes """
import mock
import pytest
from testfixtures import LogCapture
from subprocess import CalledProcessError

from collections import Iterator
from mycodo.inputs.raspi import InputModule as RaspberryPiCPUTemp


# ----------------------------
#   RaspberryPiCPUTemp tests
# ----------------------------
def test_raspberry_pi_cpu_temp_iterates_using_in():
    """ Verify that a RaspberryPiCPUTemp object can use the 'in' operator """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]
        rpicpu = RaspberryPiCPUTemp(None, testing=True)
        expected_result_list = [dict(temperature=67.00),
                                dict(temperature=52.00),
                                dict(temperature=37.00),
                                dict(temperature=45.00)]
        assert expected_result_list == [temp for temp in rpicpu]


def test_raspberry_pi_cpu_temp__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        rpi_cpu = RaspberryPiCPUTemp(None, testing=True)
        assert isinstance(rpi_cpu.__iter__(), Iterator)


def test_raspberry_pi_cpu_temp_read_updates_temp():
    """  Verify that RaspberryPiCPUTemp().read() gets the average temp """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        rpi_cpu = RaspberryPiCPUTemp(None, testing=True)
        assert rpi_cpu._temperature is None
        assert not rpi_cpu.read()
        assert rpi_cpu._temperature == 67.0
        assert not rpi_cpu.read()
        assert rpi_cpu._temperature == 52.0


def test_raspberry_pi_cpu_temp_next_returns_dict():
    """ next returns dict(temperature=float) """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        rpi_cpu = RaspberryPiCPUTemp(None, testing=True)
        assert rpi_cpu.next() == dict(temperature=67.00)


def test_raspberry_pi_cpu_temp_temperature_property():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        rpi_cpu = RaspberryPiCPUTemp(None, testing=True)
        assert rpi_cpu._temperature is None
        assert rpi_cpu.temperature == 67.00
        assert rpi_cpu.temperature == 67.00
        assert not rpi_cpu.read()
        assert rpi_cpu.temperature == 52.00


def test_raspberry_pi_cpu_temp_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [0, 0]
        rpi_cpu = RaspberryPiCPUTemp(None, testing=True)
        rpi_cpu.read()
        assert "Temperature: 0.00" in str(rpi_cpu)


def test_raspberry_pi_cpu_temp_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement') as mock_measure:
        mock_measure.side_effect = [0, 0]
        rpi_cpu = RaspberryPiCPUTemp(None, testing=True)
        rpi_cpu.read()
        assert "<RaspberryPiCPUTemp(temperature=0.00)>" in repr(rpi_cpu)


def test_raspberry_pi_cpu_temp_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            RaspberryPiCPUTemp(None, testing=True).next()


def test_raspberry_pi_cpu_temp_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement', side_effect=Exception):
        assert RaspberryPiCPUTemp(None, testing=True).read()


# def test_raspberry_pi_cpu_temp_get_measurement_divs_by_1k():
#     """ verify the return value of get_measurement """
#     mocked_open = mock.mock_open(read_data='45780')
#     with mock.patch('mycodo.inputs.raspi.open', mocked_open, create=True):
#         assert RaspberryPiCPUTemp.get_measurement() == 45.78


def test_raspberry_pi_cpu_read_logs_ioerrors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement', side_effect=IOError('msg')):
            RaspberryPiCPUTemp(None, testing=True).read()
    expected_logs = ('mycodo.inputs.raspi', 'ERROR', "RaspberryPiCPUTemp.get_measurement() method raised IOError: msg")
    assert expected_logs in log_cap.actual()


def test_raspberry_pi_cpu_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.raspi.RaspberryPiCPUTemp.get_measurement', side_effect=Exception('msg')):
            RaspberryPiCPUTemp(None, testing=True).read()
    expected_logs = ('mycodo.inputs.raspi', 'ERROR', 'RaspberryPiCPUTemp raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()


# ----------------------------
#  RaspberryPiGPUTemp tests
# ----------------------------
# def test_raspberry_pi_gpu_temp_is_iterator_instance():
#     """ Verify that a RaspberryPiGPUTemp object is and behaves like an iterator """
#     assert isinstance(RaspberryPiGPUTemp(None, testing=True), Iterator), "RaspberryPiGPUTemp is not and iterator instance"
#
#
# def test_raspberry_pi_gpu_temp_iterates_using_in():
#     """ Verify that a RaspberryPiGPUTemp object can use the 'in' operator """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
#         mock_measure.side_effect = [67, 52, 37, 45]
#         rpigpu = RaspberryPiGPUTemp(None, testing=True)
#         expected_result_list = [dict(temperature=67.00),
#                                 dict(temperature=52.00),
#                                 dict(temperature=37.00),
#                                 dict(temperature=45.00)]
#         assert expected_result_list == [temp for temp in rpigpu]
#
#
# def test_raspberry_pi_gpu_temp__iter__returns_iterator():
#     """ The iter methods must return an iterator in order to work properly """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
#         mock_measure.side_effect = [67, 52]
#         rpi_gpu = RaspberryPiGPUTemp(None, testing=True)
#         assert isinstance(rpi_gpu.__iter__(), Iterator)
#
#
# def test_raspberry_pi_gpu_temp_read_updates_temp():
#     """  Verify that RaspberryPiGPUTemp().read() gets the average temp """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
#         mock_measure.side_effect = [67, 52]
#         rpi_gpu = RaspberryPiGPUTemp(None, testing=True)
#         assert rpi_gpu._temperature is None
#         assert not rpi_gpu.read()
#         assert rpi_gpu._temperature == 67.0
#         assert not rpi_gpu.read()
#         assert rpi_gpu._temperature == 52.0
#
#
# def test_raspberry_pi_gpu_temp_temperature_property():
#     """ verify temperature property """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
#         mock_measure.side_effect = [67.2, 52.5]
#         rpi_gpu = RaspberryPiGPUTemp(None, testing=True)
#         assert rpi_gpu._temperature is None
#         assert rpi_gpu.temperature == 67.2
#         assert rpi_gpu.temperature == 67.2  # same reading, not updated yet
#         assert not rpi_gpu.read()
#         assert rpi_gpu.temperature == 52.5
#
#
# def test_raspberry_pi_gpu_temp_next_returns_dict():
#     """ Expect next() to return string: '{'measurement type':measurement value}' """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
#         mock_measure.side_effect = [20, 22]
#         rpi_gpu = RaspberryPiGPUTemp(None, testing=True)
#         assert rpi_gpu.next() == dict(temperature=20.00)
#
#
# def test_raspberry_pi_gpu_temp_special_method_str():
#     """ expect a __str__ format """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
#         mock_measure.side_effect = [67.2, 52.5]
#         rpi_gpu = RaspberryPiGPUTemp(None, testing=True)
#         assert not rpi_gpu.read()
#         assert "Temperature: 67.20" in str(rpi_gpu)
#         assert not rpi_gpu.read()
#         assert "Temperature: 52.50" in str(rpi_gpu)
#
#
# def test_raspberry_pi_gpu_temp_special_method_repr():
#     """ expect a __repr__ format """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement') as mock_measure:
#         mock_measure.side_effect = [67.2, 52.5]
#         rpi_gpu = RaspberryPiGPUTemp(None, testing=True)
#         assert not rpi_gpu.read()
#         assert "<RaspberryPiGPUTemp(temperature=67.20)>" in repr(rpi_gpu)
#         assert not rpi_gpu.read()
#         assert "<RaspberryPiGPUTemp(temperature=52.50)>" in repr(rpi_gpu)
#
#
# def test_raspberry_pi_gpu_temp_raises_exception():
#     """ stops iteration on read() error """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement', side_effect=IOError):
#         with pytest.raises(StopIteration):
#             RaspberryPiGPUTemp(None, testing=True).next()
#
#
# def test_raspberry_pi_gpu_temp_read_returns_1_on_exception():
#     """ Verify the read() method returns true on error """
#     with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement', side_effect=Exception):
#         assert RaspberryPiGPUTemp(None, testing=True).read()
#
#
# # def test_raspberry_pi_gpu_temp_get_measurement_method_returns_float():
# #     """ verify get_measurement string format """
# #     with mock.patch('mycodo.inputs.raspi.subprocess') as mock_subprocess:
# #         mock_subprocess.check_output.side_effect = lambda n: "temp=42.8'C"
# #         assert 42.8 == RaspberryPiGPUTemp.get_measurement()
#
#
# def test_raspberry_pi_gpu_temp_read_logs_called_process_error():
#     """ verify get_measurement string format """
#     with LogCapture() as log_cap:
#         with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement',
#                         side_effect=CalledProcessError(cmd='cmd', returncode=0)):
#             RaspberryPiGPUTemp(None, testing=True).read()
#     expected_log = ('mycodo.inputs.raspi', 'ERROR', "RaspberryPiGPUTemp.get_measurement() subprocess call raised: Command 'cmd' returned non-zero exit status 0")
#     assert expected_log in log_cap.actual()
#
#
# def test_raspberry_pi_gpu_temp_read_logs_ioerror():
#     """ verify get_measurement string format """
#     with LogCapture() as log_cap:
#         with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement', side_effect=IOError('msg')):
#             RaspberryPiGPUTemp(None, testing=True).read()
#     expected_log = ('mycodo.inputs.raspi', 'ERROR', "RaspberryPiGPUTemp.get_measurement() method raised IOError: msg")
#     assert expected_log in log_cap.actual()
#
#
# def test_raspberry_pi_gpu_temp_read_logs_unknown_errors():
#     """ verify get_measurement string format """
#     with LogCapture() as log_cap:
#         with mock.patch('mycodo.inputs.raspi.RaspberryPiGPUTemp.get_measurement', side_effect=Exception('msg')):
#             RaspberryPiGPUTemp(None, testing=True).read()
#     expected_log = ('mycodo.inputs.raspi', 'ERROR', "RaspberryPiGPUTemp raised an exception when taking a reading: msg")
#     assert expected_log in log_cap.actual()

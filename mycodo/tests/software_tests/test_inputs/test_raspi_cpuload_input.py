# coding=utf-8
""" Tests for the RaspberryPiCPULoad sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.raspi_cpuload import RaspberryPiCPULoad


# ----------------------------
#   RaspberryPiCPULoad tests
# ----------------------------
def test_raspi_cpuload_iterates_using_in():
    """ Verify that a RaspberryPiCPULoad object can use the 'in' operator """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        raspi_cpuload = RaspberryPiCPULoad(testing=True)
        expected_result_list = [dict(cpu_load_1m=23.0, cpu_load_5m=50.0, cpu_load_15m=3000.0),
                                dict(cpu_load_1m=25.0, cpu_load_5m=55.0, cpu_load_15m=3200.0),
                                dict(cpu_load_1m=27.0, cpu_load_5m=60.0, cpu_load_15m=3400.0),
                                dict(cpu_load_1m=30.0, cpu_load_5m=65.0, cpu_load_15m=3300.0)]
        assert expected_result_list == [temp for temp in raspi_cpuload]


def test_raspi_cpuload__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200),
                                    (27, 60, 3400),
                                    (30, 65, 3300)]
        raspi_cpuload = RaspberryPiCPULoad(testing=True)
        assert isinstance(raspi_cpuload.__iter__(), Iterator)


def test_raspi_cpuload_read_updates_temp():
    """  Verify that RaspberryPiCPULoad(testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        raspi_cpuload = RaspberryPiCPULoad(testing=True)
        assert raspi_cpuload._cpu_load_1m is None
        assert raspi_cpuload._cpu_load_5m is None
        assert raspi_cpuload._cpu_load_15m is None
        assert not raspi_cpuload.read()
        assert raspi_cpuload._cpu_load_1m == 23.0
        assert raspi_cpuload._cpu_load_5m == 50.0
        assert raspi_cpuload._cpu_load_15m == 3000.0
        assert not raspi_cpuload.read()
        assert raspi_cpuload._cpu_load_1m == 25.0
        assert raspi_cpuload._cpu_load_5m == 55.0
        assert raspi_cpuload._cpu_load_15m == 3200.0


def test_raspi_cpuload_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,cpu_load_15m=float) """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000)]
        raspi_cpuload = RaspberryPiCPULoad(testing=True)
        assert raspi_cpuload.next() == dict(cpu_load_1m=23.0,
                                  cpu_load_5m=50.0,
                                  cpu_load_15m=3000.0)


def test_raspi_cpuload_condition_properties():
    """ verify cpu_load_15m property """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement') as mock_measure:
        mock_measure.side_effect = [(23, 50, 3000),
                                    (25, 55, 3200)]
        raspi_cpuload = RaspberryPiCPULoad(testing=True)
        assert raspi_cpuload._cpu_load_1m is None # initial values
        assert raspi_cpuload._cpu_load_5m is None
        assert raspi_cpuload._cpu_load_15m is None
        assert raspi_cpuload.cpu_load_1m == 23.0
        assert raspi_cpuload.cpu_load_1m == 23.0
        assert raspi_cpuload.cpu_load_5m == 50.0
        assert raspi_cpuload.cpu_load_5m == 50.0
        assert raspi_cpuload.cpu_load_15m == 3000.0
        assert raspi_cpuload.cpu_load_15m == 3000.0
        assert not raspi_cpuload.read()
        assert raspi_cpuload.cpu_load_1m == 25.0
        assert raspi_cpuload.cpu_load_5m == 55.0
        assert raspi_cpuload.cpu_load_15m == 3200.0


def test_raspi_cpuload_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        raspi_cpuload = RaspberryPiCPULoad(testing=True)
        raspi_cpuload.read()
    assert "CPU Load (1m): 0.00" in str(raspi_cpuload)
    assert "CPU Load (5m): 0.00" in str(raspi_cpuload)
    assert "CPU Load (15m): 0.00" in str(raspi_cpuload)


def test_raspi_cpuload_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        raspi_cpuload = RaspberryPiCPULoad(testing=True)
        raspi_cpuload.read()
        assert "<RaspberryPiCPULoad(cpu_load_1m=0.00)(cpu_load_5m=0.00)(cpu_load_15m=0.00)>" in repr(raspi_cpuload)


def test_raspi_cpuload_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            RaspberryPiCPULoad(testing=True).next()


def test_raspi_cpuload_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement', side_effect=Exception):
        assert RaspberryPiCPULoad(testing=True).read()


def test_raspi_cpuload_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.raspi_cpuload.RaspberryPiCPULoad.get_measurement',
                        side_effect=Exception('msg')):
            RaspberryPiCPULoad(testing=True).read()
    expected_logs = ('mycodo.inputs.raspi_cpuload', 'ERROR', 'RaspberryPiCPULoad raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

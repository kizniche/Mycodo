# coding=utf-8
"""Tests for input classes."""
import inspect
import os
from collections.abc import Iterator

import mock
import pytest
from testfixtures import LogCapture

from mycodo.inputs.am2315 import InputModule as AM2315Sensor
from mycodo.inputs.atlas_ph import InputModule as AtlaspHSensor
from mycodo.inputs.atlas_pt1000 import InputModule as AtlasPT1000Sensor
from mycodo.inputs.bh1750 import InputModule as BH1750Sensor
from mycodo.inputs.bme280 import InputModule as BME280Sensor
from mycodo.inputs.bmp180 import InputModule as BMP180Sensor
from mycodo.inputs.bmp280 import InputModule as BMP280Sensor
from mycodo.inputs.chirp import InputModule as ChirpSensor
from mycodo.inputs.dht11 import InputModule as DHT11Sensor
from mycodo.inputs.dht22 import InputModule as DHT22Sensor
from mycodo.inputs.ds18b20 import InputModule as DS18B20Sensor
from mycodo.inputs.htu21d import InputModule as HTU21DSensor
from mycodo.inputs.ina219x import InputModule as INA219xSensor
from mycodo.inputs.k30 import InputModule as K30Sensor
from mycodo.inputs.linux_command import InputModule as LinuxCommand
from mycodo.inputs.mh_z16 import InputModule as MHZ16Sensor
from mycodo.inputs.mh_z19 import InputModule as MHZ19Sensor
from mycodo.inputs.mycodo_ram import InputModule as MycodoRam
from mycodo.inputs.rpi_cpu_gpu_temperature import \
    InputModule as RaspberryPiCPUTemp
from mycodo.inputs.rpi_signal_pwm import InputModule as SignalPWMInput
from mycodo.inputs.rpi_signal_revolutions import InputModule as SignalRPMInput
from mycodo.inputs.sht1x_7x import InputModule as SHT1x7xSensor
from mycodo.inputs.sht2x import InputModule as SHT2xSensor
from mycodo.inputs.system_cpuload import InputModule as RaspberryPiCPULoad
from mycodo.inputs.system_freespace import InputModule as RaspberryPiFreeSpace
from mycodo.inputs.tmp006 import InputModule as TMP006Sensor
from mycodo.inputs.tsl2561 import InputModule as TSL2561Sensor
from mycodo.inputs.tsl2591_sensor import InputModule as TSL2591Sensor
from mycodo.inputs.ttn_data_storage import InputModule as TTNDataStorage

input_classes = [
    AM2315Sensor(None, testing=True),
    AtlaspHSensor(None, testing=True),
    AtlasPT1000Sensor(None, testing=True),
    BH1750Sensor(None, testing=True),
    BME280Sensor(None, testing=True),
    BMP180Sensor(None, testing=True),
    BMP280Sensor(None, testing=True),
    ChirpSensor(None, testing=True),
    DHT11Sensor(None, testing=True),
    DHT22Sensor(None, testing=True),
    DS18B20Sensor(None, testing=True),
    HTU21DSensor(None, testing=True),
    INA219xSensor(None, testing=True),
    K30Sensor(None, testing=True),
    LinuxCommand(None, testing=True),
    MHZ16Sensor(None, testing=True),
    MHZ19Sensor(None, testing=True),
    MycodoRam(None, testing=True),
    RaspberryPiCPUTemp(None, testing=True),
    RaspberryPiCPULoad(None, testing=True),
    RaspberryPiFreeSpace(None, testing=True),
    SHT1x7xSensor(None, testing=True),
    SHT2xSensor(None, testing=True),
    SignalPWMInput(None, testing=True),
    SignalRPMInput(None, testing=True),
    TMP006Sensor(None, testing=True),
    TSL2561Sensor(None, testing=True),
    TSL2591Sensor(None, testing=True),
    TTNDataStorage(None, testing=True)
]


def test_inputs_have_depreciated_stop_input():
    """Verify that the input objects have the stop_input() method."""
    print("\nTest: test_inputs_have_depreciated_stop_input")
    for index, each_class in enumerate(input_classes):
        print("test_inputs_have_depreciated_stop_input: Testing Class ({}/{}): {}".format(
            index + 1, len(input_classes), each_class))
        assert hasattr(each_class, 'stop_input')


def test__iter__returns_iterator():
    """The iter methods must return an iterator in order to work properly."""
    print("\nTest: test__iter__returns_iterator")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        print("test__iter__returns_iterator: Testing Input ({}/{}): {}".format(
            index + 1, len(input_classes), filename))
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename)) as mock_measure:
            mock_measure.side_effect = [
                {
                   0: {
                       'measurement': 'temperature',
                       'unit': 'C',
                       'value': 24,
                       'time': 1556199975
                   },
                   1: {
                       'measurement': 'humidity',
                       'unit': 'percent',
                       'value': 55,
                       'time': 1556199975
                   }
                },
                {
                   0: {
                       'measurement': 'temperature',
                       'unit': 'C',
                       'value': 25,
                       'time': 1556199975
                   },
                   1: {
                       'measurement': 'humidity',
                       'unit': 'percent',
                       'value': 76,
                       'time': 1556199975
                   }
                }
            ]
            assert isinstance(each_class.__iter__(), Iterator), "{cls} is not an iterator instance".format(cls=each_class.__class__.__name__)


def test_read_updates_measurement():
    """Verify that read() gets the average temp."""
    print("\nTest: test_read_updates_measurement")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        print("test_read_updates_measurement: Testing Input ({}/{}): {}".format(
            index + 1, len(input_classes), filename))
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename)) as mock_measure:
            mock_measure.side_effect = [
                {
                   0: {
                       'measurement': 'temperature',
                       'unit': 'C',
                       'value': 24,
                       'time': 1556199975
                   },
                   1: {
                       'measurement': 'humidity',
                       'unit': 'percent',
                       'value': 55,
                       'time': 1556199975
                   }
                },
                {
                   0: {
                       'measurement': 'temperature',
                       'unit': 'C',
                       'value': 25,
                       'time': 1556199975
                   },
                   1: {
                       'measurement': 'humidity',
                       'unit': 'percent',
                       'value': 76,
                       'time': 1556199975
                   }
                }
            ]
            assert each_class._measurements is None
            assert each_class._measurements is None
            assert not each_class.read()
            assert each_class.measurements[0]['measurement'] == 'temperature'
            assert each_class.measurements[0]['unit'] == 'C'
            assert each_class.measurements[0]['time'] == 1556199975
            assert each_class.measurements[0]['value'] == 24
            assert each_class.measurements[1]['measurement'] == 'humidity'
            assert each_class.measurements[1]['unit'] == 'percent'
            assert each_class.measurements[1]['time'] == 1556199975
            assert each_class.measurements[1]['value'] == 55
            assert not each_class.read()
            assert each_class.measurements[0]['value'] == 25
            assert each_class.measurements[1]['value'] == 76


def test_special_method_str():
    """expect a __str__ format."""
    print("\nTest: test_special_method_str")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        print("test_special_method_str: Testing Input ({}/{}): {}".format(index + 1, len(input_classes), filename))
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename)) as mock_measure:
            mock_measure.side_effect = [
                {
                   0: {
                       'measurement': 'temperature',
                       'unit': 'C',
                       'value': 24,
                       'time': 1556199975
                   },
                   1: {
                       'measurement': 'humidity',
                       'unit': 'percent',
                       'value': 55,
                       'time': 1556199975
                   }
                },
                {
                   0: {
                       'measurement': 'temperature',
                       'unit': 'C',
                       'value': 25,
                       'time': 1556199975
                   },
                   1: {
                       'measurement': 'humidity',
                       'unit': 'percent',
                       'value': 76,
                       'time': 1556199975
                   }
                }
            ]
            each_class.read()
            assert "1556199975,0,temperature,C,24" in str(each_class)
            assert "1556199975,1,humidity,percent,55" in str(each_class)


def test_special_method_repr():
    """expect a __repr__ format."""
    print("\nTest: test_special_method_repr")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename)) as mock_measure:
            mock_measure.side_effect = [
                {
                   0: {
                       'measurement': 'temperature',
                       'unit': 'C',
                       'value': 24,
                       'time': 1556199975
                   },
                   1: {
                       'measurement': 'humidity',
                       'unit': 'percent',
                       'value': 55,
                       'time': 1556199975
                   }
                }
            ]
            print("test_special_method_repr: Testing Input ({}/{}): {}".format(index + 1, len(input_classes), filename))
            each_class.read()
            assert "<InputModule" in repr(each_class)
            assert "(1556199975,0,temperature,C,24)" in repr(each_class)
            assert "(1556199975,1,humidity,percent,55)" in repr(each_class)
            assert ">" in repr(each_class)


def test_raises_exception():
    """stops iteration on read() error."""
    print("\nTest: test_raises_exception")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        print("test_raises_exception: Testing Input ({}/{}): {}".format(index + 1, len(input_classes), filename))
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename), side_effect=IOError):
            with pytest.raises(StopIteration):
                each_class.next()


def test_read_returns_1_on_exception():
    """Verify the read() method returns true on error."""
    print("\nTest: test_read_returns_1_on_exception")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        print("test_read_returns_1_on_exception: Testing Input ({}/{}): {}".format(index + 1, len(input_classes), filename))
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename), side_effect=Exception):
            assert each_class.read()


def test_read_logs_unknown_errors():
    """verify that IOErrors are logged."""
    print("\nTest: test_read_logs_unknown_errors")
    with LogCapture() as log_cap:
        for index, each_class in enumerate(input_classes):
            full_path = inspect.getfile(each_class.__class__)
            filename = os.path.splitext(os.path.basename(full_path))[0]
            print("test_read_logs_unknown_errors: Testing Input ({}/{}): {}".format(
                index + 1, len(input_classes), filename))
            with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename), side_effect=Exception('msg')):
                each_class.read()
            expected_logs = ('mycodo.inputs.{fn}'.format(fn=filename),
                             'ERROR',
                             'InputModule raised an exception when taking a reading: msg')
            assert expected_logs in log_cap.actual()

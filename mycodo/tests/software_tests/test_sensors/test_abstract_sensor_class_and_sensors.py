# coding=utf-8
""" Tests for the abstract class and sensor classes """
from collections import Iterator

import pytest
from testfixtures import LogCapture

from mycodo.sensors.am2315 import AM2315Sensor
from mycodo.sensors.atlas_pt1000 import AtlasPT1000Sensor
from mycodo.sensors.base_sensor import AbstractSensor
from mycodo.sensors.bmp import BMPSensor
from mycodo.sensors.ds18b20 import DS18B20Sensor
from mycodo.sensors.htu21d import HTU21DSensor
from mycodo.sensors.raspi import (RaspberryPiCPUTemp,
                                  RaspberryPiGPUTemp)
from mycodo.sensors.raspi_cpuload import RaspberryPiCPULoad
from mycodo.sensors.sht1x_7x import SHT1x7xSensor
from mycodo.sensors.sht2x import SHT2xSensor
from mycodo.sensors.tmp006 import TMP006Sensor
from mycodo.sensors.tsl2561 import TSL2561Sensor

# TODO: Find which errors when uncommented
# TODO: Need to mock GPIO for Travis CI
sensor_classes = [
    AtlasPT1000Sensor(0x00, 1),
    AM2315Sensor(1),
    # BME280Sensor(0x00, 1),
    BMPSensor(1),
    # DHT11Sensor(pigpio.pi(), 1),
    # DHT22Sensor(pigpio.pi(), 1),
    DS18B20Sensor('1'),
    HTU21DSensor(1),
    # K30Sensor(),
    RaspberryPiCPUTemp(),
    RaspberryPiGPUTemp(),
    RaspberryPiCPULoad(),
    TMP006Sensor(0x00, 1),
    TSL2561Sensor(0x00, 1),
    SHT1x7xSensor(1, 2, '5.0'),
    SHT2xSensor(0x00, 1)
]


# ----------------------------
#   AbstractSensor
# ----------------------------
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
#   General class tests
# ----------------------------
def test_sensors_have_depreciated_stop_sensor():
    """ Verify that the sensor objects have the stop_sensor() method """
    for each_class in sensor_classes:
        assert hasattr(each_class, 'stop_sensor')


def test_sensors_are_iterator_instance():
    """ Verify that the sensor objects are and behave like an iterator """
    for each_class in sensor_classes:
        assert isinstance(each_class, Iterator), "{cls} is not an iterator instance".format(cls=each_class.__class__.__name__)

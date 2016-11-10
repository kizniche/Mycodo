# coding=utf-8
""" Tests for the abstract class and sensor classes """
import mock
import pigpio
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.sensors.base_sensor import AbstractSensor
from mycodo.sensors.atlas_pt1000 import AtlasPT1000Sensor
from mycodo.sensors.am2315 import AM2315Sensor
from mycodo.sensors.bme280 import BME280Sensor
from mycodo.sensors.bmp import BMPSensor
from mycodo.sensors.dht11 import DHT11Sensor
from mycodo.sensors.dht22 import DHT22Sensor
from mycodo.sensors.ds18b20 import DS18B20Sensor
from mycodo.sensors.htu21d import HTU21DSensor
from mycodo.sensors.k30 import K30Sensor
from mycodo.sensors.raspi import (RaspberryPiCPUTemp,
                                  RaspberryPiGPUTemp)
from mycodo.sensors.raspi_cpuload import RaspberryPiCPULoad
from mycodo.sensors.tmp006 import TMP006Sensor
from mycodo.sensors.tsl2561 import TSL2561Sensor
from mycodo.sensors.sht1x_7x import SHT1x7xSensor
from mycodo.sensors.sht2x import SHT2xSensor

sensor_classes = [
    AtlasPT1000Sensor(0x00, 1),
    AM2315Sensor(1),
    # BME280Sensor(0x00, 1),  # TODO: Find why this errors when uncommented
    # BMPSensor(1),
    # DHT11Sensor(pigpio.pi(), 1),  # TODO: Find why this errors when uncommented
    # DHT22Sensor(pigpio.pi(), 1),  # TODO: Find why this errors when uncommented
    DS18B20Sensor('1'),
    HTU21DSensor(1),
    # K30Sensor(),  # TODO: Need to mock GPIO for Travis CI
    RaspberryPiCPUTemp(),
    RaspberryPiGPUTemp(),
    RaspberryPiCPULoad(),
    TMP006Sensor(0x00, 1),
    TSL2561Sensor(0x00, 1),
    # SHT1x7xSensor(1, 2, '5.0'),
    SHT2xSensor(0x00, 1)
]


# ----------------------------
#   AbstractSensor
# ----------------------------
def test_abstract_sensor_deprecated_stopsensor_warns_use():
    """ verify that the depreciated stopSensor() method warns it's use """
    for each_class in sensor_classes:
        with LogCapture() as log_cap:
            each_class.stopSensor()
        expected_log = ('mycodo.sensors.base_sensor', 'WARNING', ('Old style `stopSensor()` called by '
                                                                  '{cls}.  This is depreciated '
                                                                  'and will be deleted in future releases.  '
                                                                  'Switch to using `stop_sensor` instead.'.format(cls=each_class.__class__.__name__)))
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
#   General class tests
# ----------------------------
def test_sensors_have_depreciated_stop_sensor():
    """ Verify that the sensor objects have the stopSensor() method """
    for each_class in sensor_classes:
        assert hasattr(each_class, 'stopSensor')


def test_sensors_are_iterator_instance():
    """ Verify that the sensor objects are and behave like an iterator """
    for each_class in sensor_classes:
        assert isinstance(each_class, Iterator), "{cls} is not an iterator instance".format(cls=each_class.__class__.__name__)

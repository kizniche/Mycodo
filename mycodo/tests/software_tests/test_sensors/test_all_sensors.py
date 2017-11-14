# coding=utf-8
""" Tests for all sensor classes """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.sensors.am2315 import AM2315Sensor
from mycodo.sensors.atlas_pt1000 import AtlasPT1000Sensor
# from mycodo.sensors.bme280 import BME280Sensor
from mycodo.sensors.bmp180 import BMP180Sensor
# from mycodo.sensors.dht11 import DHT11Sensor
# from mycodo.sensors.dht22 import DHT22Sensor
from mycodo.sensors.ds18b20 import DS18B20Sensor
# from mycodo.sensors.htu21d import HTU21DSensor
# from mycodo.sensors.k30 import K30Sensor
# from mycodo.sensors.raspi import RaspberryPiCPUTemp
# from mycodo.sensors.raspi import RaspberryPiGPUTemp
# from mycodo.sensors.raspi_cpuload import RaspberryPiCPULoad
from mycodo.sensors.sht1x_7x import SHT1x7xSensor
from mycodo.sensors.sht2x import SHT2xSensor
from mycodo.sensors.tmp006 import TMP006Sensor
from mycodo.sensors.tsl2561 import TSL2561Sensor


# ----------------------------
#   Sensor tests
# ----------------------------
def return_classes():
    sensor_classes = [
        # AtlasPT1000Sensor('I2C', i2c_address=0x00, i2c_bus=1, testing=True),
        # AM2315Sensor(1, 1, testing=True),
        # BME280Sensor(0x00, 1),
        # BMPSensor(1),
        # DHT11Sensor(pigpio.pi(), 1),
        # DHT22Sensor(pigpio.pi(), 1),
        # DS18B20Sensor('1'),
        # HTU21DSensor(1),
        # K30Sensor(),
        # RaspberryPiCPUTemp(),
        # RaspberryPiGPUTemp(),
        # RaspberryPiCPULoad(),
        # SHT1x7xSensor(1, 2, '5.0'),
        # SHT2xSensor(0x00, 1),
        # TMP006Sensor(0x00, 1),
        # TSL2561Sensor(0x00, 1)
    ]
    return sensor_classes


def conditions_list(sensor_measurements, range_num):
    list_cond = []
    number = 20
    number_mod = 5
    for _ in range(range_num):
        tuple_conditions = []
        for _ in sensor_measurements:
            tuple_conditions.append(number)
            number += number_mod
        if len(tuple_conditions) > 1:
            tuple_conditions = tuple(tuple_conditions)
        else:
            tuple_conditions = tuple_conditions[0]
        list_cond.append(tuple_conditions)
    return list_cond


def test_sensor_class_iterates_using_in():
    """ Verify that a class object can use the 'in' operator """
    for each_class in return_classes():
        sensor_measurements = each_class.info()
        with mock.patch('{mod}.{name}.get_measurement'.format(
                mod=each_class.__module__,
                name=each_class.__class__.__name__)) as mock_measure:
            # Create mock_measure.side_effect
            list_cond = conditions_list(sensor_measurements, 4)
            mock_measure.side_effect = list_cond
            # Build expected results list
            expected_result_list = []
            for index in range(4):
                dict_build = {}
                if len(sensor_measurements) == 1:
                    if sensor_measurements[0][2] == 'float':
                        dict_build[sensor_measurements[0][1]] = float(list_cond[index])
                    else:
                        dict_build[sensor_measurements[0][1]] = list_cond[index]
                else:
                    for index_cond, each_cond in enumerate(sensor_measurements):
                        if each_cond[2] == 'float':
                            dict_build[each_cond[1]] = float(list_cond[index][index_cond])
                        else:
                            dict_build[each_cond[1]] = list_cond[index][index_cond]
                expected_result_list.append(dict_build)
            assert expected_result_list == [cond for cond in each_class]


def test_sensor_class__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    for each_class in return_classes():
        sensor_measurements = each_class.info()
        with mock.patch('{mod}.{name}.get_measurement'.format(
                mod=each_class.__module__,
                name=each_class.__class__.__name__)) as mock_measure:
            # Create mock_measure.side_effect
            mock_measure.side_effect = conditions_list(sensor_measurements, 4)
            # check __iter__ method return
            assert isinstance(each_class.__iter__(), Iterator)


def test_sensor_class_read_updates_condition():
    """  Verify that Class.read() gets the condition """
    for each_class in return_classes():
        sensor_measurements = each_class.info()
        with mock.patch('{mod}.{name}.get_measurement'.format(
                mod=each_class.__module__,
                name=each_class.__class__.__name__)) as mock_measure:
            # Create mock_measure.side_effect
            list_cond = conditions_list(sensor_measurements, 2)
            mock_measure.side_effect = list_cond
            # test read() function
            if len(sensor_measurements) == 1:
                for each_measurement in sensor_measurements:
                    assert each_measurement[4] == 0  # init value
                assert not each_class.read()  # updating the value using our mock_measure side effect has no error
                sensor_measurements = each_class.info()
                for each_measurement in sensor_measurements:
                    assert each_measurement[4] == list_cond[0]  # first value
                assert not each_class.read()  # updating the value using our mock_measure side effect has no error
                sensor_measurements = each_class.info()
                for each_measurement in sensor_measurements:
                    assert each_measurement[4] == list_cond[1]
            else:
                for each_measurement in sensor_measurements:
                    assert each_measurement[4] == 0  # init value
                assert not each_class.read()  # updating the value using our mock_measure side effect has no error
                sensor_measurements = each_class.info()
                for index, each_measurement in enumerate(sensor_measurements):
                    assert each_measurement[4] == list_cond[0][index]  # first value
                assert not each_class.read()  # updating the value using our mock_measure side effect has no error
                sensor_measurements = each_class.info()
                for index, each_measurement in enumerate(sensor_measurements):
                    assert each_measurement[4] == list_cond[1][index]  # second value


def test_sensor_class_next_returns_dict():
    """ next returns dict(condition=type) """
    for each_class in return_classes():
        sensor_measurements = each_class.info()
        with mock.patch('{mod}.{name}.get_measurement'.format(
                mod=each_class.__module__,
                name=each_class.__class__.__name__)) as mock_measure:
            # Create mock_measure.side_effect
            list_cond = conditions_list(sensor_measurements, 4)
            mock_measure.side_effect = list_cond
            # Build expected results list
            dict_build = {}
            if len(sensor_measurements) == 1:
                if sensor_measurements[0][2] == 'float':
                    dict_build[sensor_measurements[0][1]] = float(list_cond[0])
                else:
                    dict_build[sensor_measurements[0][1]] = list_cond[0]
            else:
                for index_cond, each_cond in enumerate(sensor_measurements):
                    if each_cond[2] == 'float':
                        dict_build[each_cond[1]] = float(list_cond[0][index_cond])
                    else:
                        dict_build[each_cond[1]] = list_cond[0][index_cond]
            assert each_class.next() == dict_build


def test_sensor_class_condition_properties():
    """ verify condition property """
    for each_class in return_classes():
        sensor_measurements = each_class.info()
        with mock.patch('{mod}.{name}.get_measurement'.format(
                mod=each_class.__module__,
                name=each_class.__class__.__name__)) as mock_measure:
            # Create mock_measure.side_effect
            list_cond = conditions_list(sensor_measurements, 2)
            mock_measure.side_effect = list_cond
            # test read() function
            if len(sensor_measurements) == 1:
                for each_measurement in sensor_measurements:
                    assert each_measurement[4] == 0  # init value
                sensor_measurements = each_class.info()
                for each_measurement in sensor_measurements:
                    assert each_measurement[5] == list_cond[0]  # first reading with auto update
                sensor_measurements = each_class.info()
                for each_measurement in sensor_measurements:
                    assert each_measurement[5] == list_cond[0]  # same first reading, not updated yet
                assert not each_class.read()  # update (no errors)
                sensor_measurements = each_class.info()
                for each_measurement in sensor_measurements:
                    assert each_measurement[5] == list_cond[1]  # next reading
            else:
                for each_measurement in sensor_measurements:
                    assert each_measurement[4] == 0  # init value
                sensor_measurements = each_class.info()
                for index, each_measurement in enumerate(sensor_measurements):
                    assert each_measurement[5] == list_cond[0][index]  # first reading with auto update
                sensor_measurements = each_class.info()
                for index, each_measurement in enumerate(sensor_measurements):
                    assert each_measurement[5] == list_cond[0][index]  # same first reading with auto update
                assert not each_class.read()  # update (no errors)
                sensor_measurements = each_class.info()
                for index, each_measurement in enumerate(sensor_measurements):
                    assert each_measurement[5] == list_cond[1][index]  # next reading


def test_sensor_class_special_method_str():
    """ expect a __str__ format """
    for each_class in return_classes():
        sensor_measurements = each_class.info()
        for each_cond in sensor_measurements:
            assert "{cond}: {num}".format(
                cond=each_cond[0],
                num=each_cond[3]) in str(each_class)


def test_sensor_class_special_method_repr():
    """ expect a __repr__ format """
    for each_class in return_classes():
        str_class = ''
        sensor_measurements = each_class.info()
        for each_cond in sensor_measurements:
            str_class += "({cond}={num})".format(cond=each_cond[1],
                                                 num=each_cond[3])
        assert "<{c_name}{str}>".format(
            c_name=each_class.__class__.__name__,
            str=str_class) in repr(each_class)


def test_sensor_class_raises_exception():
    """ stops iteration on read() error """
    for each_class in return_classes():
        with mock.patch('{mod}.{name}.get_measurement'.format(
                mod=each_class.__module__,
                name=each_class.__class__.__name__),
                    side_effect=IOError):
            with pytest.raises(StopIteration):
                each_class.next()


def test_sensor_class_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    for each_class in return_classes():
        with mock.patch('{mod}.{name}.get_measurement'.format(
                mod=each_class.__module__,
                name=each_class.__class__.__name__),
                    side_effect=Exception):
            assert each_class.read()


# def test_sensor_class_get_measurement_divs_by_1k():
#     """ verify the return value of get_measurement """
#     mocked_open = mock.mock_open(read_data='45780')  # value read from sys temperature file
#     with mock.patch('mycodo.sensors.sensor_class.open', mocked_open, create=True):
#         assert AtlasPT1000Sensor.get_measurement() == 45.78  # value read / 1000


def test_sensor_class_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    for each_class in return_classes():
        with LogCapture() as log_cap:
            # force an Exception to be raised when get_measurement is called
            with mock.patch('{mod}.{name}.get_measurement'.format(
                    mod=each_class.__module__,
                    name=each_class.__class__.__name__),
                        side_effect=Exception('msg')):
                each_class.read()
        expected_logs = ('{mod}'.format(mod=each_class.__module__),
                         'ERROR',
                         '{name} raised an exception when taking a reading: msg'.format(
                             name=each_class.__class__.__name__))
        assert expected_logs in log_cap.actual()

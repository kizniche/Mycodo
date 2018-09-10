# coding=utf-8
""" Tests for the BME280 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.bme280 import InputModule as BME280Sensor


# ----------------------------
#   BMP tests
# ----------------------------
def test_bme_iterates_using_in():
    """ Verify that a BME280Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 23, 50, 60, 3000),
                                    (52, 25, 55, 65, 3200),
                                    (37, 27, 60, 70, 3400),
                                    (45, 30, 65, 75, 3300)]
        bme = BME280Sensor(None, testing=True)
        expected_result_list = [dict(altitude=67.0, dewpoint=23.0, humidity=50.0, pressure=60.0, temperature=3000.0),
                                dict(altitude=52.0, dewpoint=25.0, humidity=55.0, pressure=65.0, temperature=3200.0),
                                dict(altitude=37.0, dewpoint=27.0, humidity=60.0, pressure=70.0, temperature=3400.0),
                                dict(altitude=45.0, dewpoint=30.0, humidity=65.0, pressure=75.0, temperature=3300.0)]
        assert expected_result_list == [temp for temp in bme]


def test_bme__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 23, 50, 60, 3000),
                                    (52, 25, 55, 65, 3200),
                                    (37, 27, 60, 70, 3400),
                                    (45, 30, 65, 75, 3300)]
        bme = BME280Sensor(None, testing=True)
        assert isinstance(bme.__iter__(), Iterator)


def test_bme_read_updates_temp():
    """  Verify that BME280Sensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 23, 50, 60, 3000),
                                    (52, 25, 55, 65, 3200)]
        bme = BME280Sensor(None, testing=True)
        assert bme._altitude is None
        assert bme._dew_point is None
        assert bme._humidity is None
        assert bme._pressure is None
        assert bme._temperature is None
        assert not bme.read()
        assert bme._altitude == 67.0
        assert bme._dew_point == 23.0
        assert bme._humidity == 50.0
        assert bme._pressure == 60.0
        assert bme._temperature == 3000.0
        assert not bme.read()
        assert bme._altitude == 52.0
        assert bme._dew_point == 25.0
        assert bme._humidity == 55.0
        assert bme._pressure == 65.0
        assert bme._temperature == 3200.0


def test_bme_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,temperature=float) """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 23, 50, 60, 3000)]
        bme = BME280Sensor(None, testing=True)
        assert bme.next() == dict(altitude=67.0,
                                  dewpoint=23.0,
                                  humidity=50.0,
                                  pressure=60.0,
                                  temperature=3000.0)


def test_bme_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 23, 50, 60, 3000),
                                    (52, 25, 55, 65, 3200)]
        bme = BME280Sensor(None, testing=True)
        assert bme._altitude is None
        assert bme._dew_point is None
        assert bme._humidity is None
        assert bme._pressure is None
        assert bme._temperature is None
        assert bme.altitude == 67.0
        assert bme.altitude == 67.0
        assert bme.dew_point == 23.0
        assert bme.dew_point == 23.0
        assert bme.humidity == 50.0
        assert bme.humidity == 50.0
        assert bme.pressure == 60.0
        assert bme.pressure == 60.0
        assert bme.temperature == 3000.0
        assert bme.temperature == 3000.0
        assert not bme.read()
        assert bme.altitude == 52.0
        assert bme.dew_point == 25.0
        assert bme.humidity == 55.0
        assert bme.pressure == 65.0
        assert bme.temperature == 3200.0


def test_bme_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0, 0, 0)]
        bme280 = BME280Sensor(None, testing=True)
        bme280.read()
    assert "Altitude: 0.00" in str(bme280)
    assert "Dew Point: 0.00" in str(bme280)
    assert "Humidity: 0.00" in str(bme280)
    assert "Pressure: 0.00" in str(bme280)
    assert "Temperature: 0.00" in str(bme280)


def test_bme_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0, 0, 0)]
        bme280 = BME280Sensor(None, testing=True)
        bme280.read()
        assert "<BME280Sensor(altitude=0.000000)(dewpoint=0.000000)(humidity=0.000000)(pressure=0.000000)(temperature=0.000000)>" in repr(bme280)


def test_bme_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            BME280Sensor(None, testing=True).next()


def test_bme_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement', side_effect=Exception):
        assert BME280Sensor(None, testing=True).read()


def test_bme_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:

        with mock.patch('mycodo.inputs.bme280.BME280Sensor.get_measurement', side_effect=Exception('msg')):
            BME280Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.bme280', 'ERROR', 'BME280Sensor raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

# coding=utf-8
""" Tests for the BMP180 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.bmp180 import InputModule as BMP180Sensor


# ----------------------------
#   BMP tests
# ----------------------------
def test_bmp_iterates_using_in():
    """ Verify that a BMP180Sensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 23, 3000),
                                    (52, 25, 3200),
                                    (37, 27, 3400),
                                    (45, 30, 3300)]
        bmp = BMP180Sensor(None, testing=True)
        expected_result_list = [dict(altitude=3000, pressure=23.00, temperature=67.00),
                                dict(altitude=3200, pressure=25.00, temperature=52.00),
                                dict(altitude=3400, pressure=27.00, temperature=37.00),
                                dict(altitude=3300, pressure=30.00, temperature=45.00)]
        assert expected_result_list == [temp for temp in bmp]


def test_bmp__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        bmp = BMP180Sensor(None, testing=True)
        assert isinstance(bmp.__iter__(), Iterator)


def test_bmp_read_updates_temp():
    """  Verify that BMP180Sensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 33, 2000),
                                    (52, 59, 2500)]
        bmp = BMP180Sensor(None, testing=True)
        assert bmp._altitude is None
        assert bmp._pressure is None
        assert bmp._temperature is None
        assert not bmp.read()
        assert bmp._altitude == 2000.0
        assert bmp._pressure == 33.0
        assert bmp._temperature == 67.0
        assert not bmp.read()
        assert bmp._altitude == 2500.0
        assert bmp._pressure == 59.0
        assert bmp._temperature == 52.0


def test_bmp_next_returns_dict():
    """ next returns dict(altitude=float,pressure=int,temperature=float) """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement') as mock_measure:

        mock_measure.side_effect = [(67, 44, 3000),
                                    (52, 64, 3500)]
        bmp = BMP180Sensor(None, testing=True)
        assert bmp.next() == dict(altitude=3000.00,
                                  pressure=44.00,
                                  temperature=67.00)


def test_bmp_condition_properties():
    """ verify temperature property """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 50, 3000),
                                    (52, 55, 3500)]
        bmp = BMP180Sensor(None, testing=True)
        assert bmp._altitude is None
        assert bmp._pressure is None
        assert bmp._temperature is None
        assert bmp.altitude == 3000.00
        assert bmp.altitude == 3000.00
        assert bmp.pressure == 50.00
        assert bmp.pressure == 50.00
        assert bmp.temperature == 67.00
        assert bmp.temperature == 67.00
        assert not bmp.read()
        assert bmp.altitude == 3500.00
        assert bmp.pressure == 55.00
        assert bmp.temperature == 52.00


def test_bmp_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        bmp180 = BMP180Sensor(None, testing=True)
        bmp180.read()
    assert "Altitude: 0.00" in str(bmp180)
    assert "Pressure: 0.00" in str(bmp180)
    assert "Temperature: 0.00" in str(bmp180)


def test_bmp_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        bmp180 = BMP180Sensor(None, testing=True)
        bmp180.read()
        assert "<InputModule(temperature=0.000000)(pressure=0.000000)(altitude=0.000000)>" in repr(bmp180)


def test_bmp_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            BMP180Sensor(None, testing=True).next()


def test_bmp_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement', side_effect=Exception):
        assert BMP180Sensor(None, testing=True).read()


def test_bmp_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.bmp180.InputModule.get_measurement', side_effect=Exception('msg')):
            BMP180Sensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.bmp180', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

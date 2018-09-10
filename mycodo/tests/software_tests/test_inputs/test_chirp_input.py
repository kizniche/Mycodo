# coding=utf-8
""" Tests for the BMP180 sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.chirp import InputModule as ChirpSensor


# ----------------------------
#   BMP tests
# ----------------------------
def test_bmp_iterates_using_in():
    """ Verify that a ChirpSensor object can use the 'in' operator """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 23, 3000),
                                    (52, 25, 3200),
                                    (37, 27, 3400),
                                    (45, 30, 3300)]
        bmp = ChirpSensor(None, testing=True)
        expected_result_list = [dict(temperature=3000, moisture=23.00, lux=67.00),
                                dict(temperature=3200, moisture=25.00, lux=52.00),
                                dict(temperature=3400, moisture=27.00, lux=37.00),
                                dict(temperature=3300, moisture=30.00, lux=45.00)]
        assert expected_result_list == [temp for temp in bmp]


def test_bmp__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        bmp = ChirpSensor(None, testing=True)
        assert isinstance(bmp.__iter__(), Iterator)


def test_bmp_read_updates_temp():
    """  Verify that ChirpSensor(None, testing=True).read() gets the average temp """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 33, 2000),
                                    (52, 59, 2500)]
        bmp = ChirpSensor(None, testing=True)
        assert bmp._temperature is None
        assert bmp._moisture is None
        assert bmp._lux is None
        assert not bmp.read()
        assert bmp._temperature == 2000.0
        assert bmp._moisture == 33.0
        assert bmp._lux == 67.0
        assert not bmp.read()
        assert bmp._temperature == 2500.0
        assert bmp._moisture == 59.0
        assert bmp._lux == 52.0


def test_bmp_next_returns_dict():
    """ next returns dict(temperature=float,moisture=int,lux=float) """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 44, 3000),
                                    (52, 64, 3500)]
        bmp = ChirpSensor(None, testing=True)
        assert bmp.next() == dict(temperature=3000.00,
                                  moisture=44,
                                  lux=67.00)


def test_bmp_condition_properties():
    """ verify lux property """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(67, 50, 3000),
                                    (52, 55, 3500)]
        bmp = ChirpSensor(None, testing=True)
        assert bmp._temperature is None
        assert bmp._moisture is None
        assert bmp._lux is None
        assert bmp.temperature == 3000.00
        assert bmp.temperature == 3000.00
        assert bmp.moisture == 50.00
        assert bmp.moisture == 50.00
        assert bmp.lux == 67.00
        assert bmp.lux == 67.00
        assert not bmp.read()
        assert bmp.temperature == 3500.00
        assert bmp.moisture == 55.00
        assert bmp.lux == 52.00


def test_bmp_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        chirp = ChirpSensor(None, testing=True)
        chirp.read()
    assert "Temperature: 0.00" in str(chirp)
    assert "Moisture: 0" in str(chirp)
    assert "Light: 0" in str(chirp)


def test_bmp_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement') as mock_measure:
        mock_measure.side_effect = [(0, 0, 0)]
        chirp = ChirpSensor(None, testing=True)
        chirp.read()
        assert "<InputModule(lux=0)(moisture=0)(temperature=0.00)>" in repr(chirp)


def test_bmp_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            ChirpSensor(None, testing=True).next()


def test_bmp_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement', side_effect=Exception):
        assert ChirpSensor(None, testing=True).read()


def test_bmp_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.chirp.InputModule.get_measurement', side_effect=Exception('msg')):
            ChirpSensor(None, testing=True).read()
    expected_logs = ('mycodo.inputs.chirp', 'ERROR', 'InputModule raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

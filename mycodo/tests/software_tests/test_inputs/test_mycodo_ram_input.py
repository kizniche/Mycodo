# coding=utf-8
""" Tests for the MycodoRam sensor class """
import mock
import pytest
from testfixtures import LogCapture

from collections import Iterator
from mycodo.inputs.mycodo_ram import MycodoRam


# ----------------------------
#   MycodoRam tests
# ----------------------------
def test_mycodo_ram_iterates_using_in():
    """ Verify that a MycodoRam object can use the 'in' operator """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52, 37, 45]
        mycodo_ram = MycodoRam(None, testing=True)
        expected_result_list = [dict(disk_space=67.00),
                                dict(disk_space=52.00),
                                dict(disk_space=37.00),
                                dict(disk_space=45.00)]
        assert expected_result_list == [temp for temp in mycodo_ram]


def test_mycodo_ram__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mycodo_ram = MycodoRam(None, testing=True)
        assert isinstance(mycodo_ram.__iter__(), Iterator)


def test_mycodo_ram_read_updates_temp():
    """  Verify that MycodoRam(0x99, 1).read() gets the average temp """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mycodo_ram = MycodoRam(None, testing=True)
        assert mycodo_ram._disk_space is None
        assert not mycodo_ram.read()
        assert mycodo_ram._disk_space == 67.0
        assert not mycodo_ram.read()
        assert mycodo_ram._disk_space == 52.0


def test_mycodo_ram_next_returns_dict():
    """ next returns dict(disk_space=float) """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mycodo_ram = MycodoRam(None, testing=True)
        assert mycodo_ram.next() == dict(disk_space=67.00)


def test_mycodo_ram_condition_properties():
    """ verify disk_space property """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement') as mock_measure:
        mock_measure.side_effect = [67, 52]
        mycodo_ram = MycodoRam(None, testing=True)
        assert mycodo_ram._disk_space is None
        assert mycodo_ram.disk_space == 67.00
        assert mycodo_ram.disk_space == 67.00
        assert not mycodo_ram.read()
        assert mycodo_ram.disk_space == 52.00


def test_mycodo_ram_special_method_str():
    """ expect a __str__ format """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        mycodo_ram = MycodoRam(None, testing=True)
        mycodo_ram.read()
        assert "Ram: 0.00" in str(mycodo_ram)


def test_mycodo_ram_special_method_repr():
    """ expect a __repr__ format """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement') as mock_measure:
        mock_measure.side_effect = [0.0]
        mycodo_ram = MycodoRam(None, testing=True)
        mycodo_ram.read()
        assert "<MycodoRam(disk_space=0.00)>" in repr(mycodo_ram)


def test_mycodo_ram_raises_exception():
    """ stops iteration on read() error """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement', side_effect=IOError):
        with pytest.raises(StopIteration):
            MycodoRam(None, testing=True).next()


def test_mycodo_ram_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement', side_effect=Exception):
        assert MycodoRam(None, testing=True).read()


def test_mycodo_ram_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
    with LogCapture() as log_cap:
        with mock.patch('mycodo.inputs.mycodo_ram.MycodoRam.get_measurement', side_effect=Exception('msg')):
            MycodoRam(None, testing=True).read()
    expected_logs = ('mycodo.inputs.mycodo_ram', 'ERROR', 'MycodoRam raised an exception when taking a reading: msg')
    assert expected_logs in log_cap.actual()

# coding=utf-8
""" Tests for input classes """
import inspect
import os
from collections.abc import Iterator

import mock
import pytest
from testfixtures import LogCapture

from mycodo.utils.inputs import parse_input_information
from mycodo.utils.modules import load_module_from_file

dict_inputs = parse_input_information()

input_classes = []
for each_device in dict_inputs:
    input_loaded = load_module_from_file(
        dict_inputs[each_device]['file_path'],
        'inputs')
    input_classes.append(input_loaded.InputModule(None, testing=True))


def test_inputs_have_depreciated_stop_input():
    """ Verify that the input objects have the stop_input() method """
    print("\nTest: test_inputs_have_depreciated_stop_input")
    for index, each_class in enumerate(input_classes):
        print("test_inputs_have_depreciated_stop_input: Testing Class ({}/{}): {}".format(
            index + 1, len(input_classes), each_class))
        assert hasattr(each_class, 'stop_input')


def test__iter__returns_iterator():
    """ The iter methods must return an iterator in order to work properly """
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
    """  Verify that read() gets the average temp """
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
    """ expect a __str__ format """
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
    """ expect a __repr__ format """
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
    """ stops iteration on read() error """
    print("\nTest: test_raises_exception")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        print("test_raises_exception: Testing Input ({}/{}): {}".format(index + 1, len(input_classes), filename))
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename), side_effect=IOError):
            with pytest.raises(StopIteration):
                each_class.next()


def test_read_returns_1_on_exception():
    """ Verify the read() method returns true on error """
    print("\nTest: test_read_returns_1_on_exception")
    for index, each_class in enumerate(input_classes):
        full_path = inspect.getfile(each_class.__class__)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        print("test_read_returns_1_on_exception: Testing Input ({}/{}): {}".format(index + 1, len(input_classes), filename))
        with mock.patch('mycodo.inputs.{fn}.InputModule.get_measurement'.format(fn=filename), side_effect=Exception):
            assert each_class.read()


def test_read_logs_unknown_errors():
    """ verify that IOErrors are logged """
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

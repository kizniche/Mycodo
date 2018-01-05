# # coding=utf-8
# """ Tests for the DHT22 sensor class """
# import mock
# import pytest
# from testfixtures import LogCapture
#
# from collections import Iterator
# from mycodo.inputs.dht22 import DHT22Sensor
#
#
# # ----------------------------
# #   DHT22 tests
# # ----------------------------
# def test_dht22_iterates_using_in():
#     """ Verify that a DHT22Sensor object can use the 'in' operator """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement') as mock_measure:
#         mock_measure.side_effect = [(23, 50, 3000),
#                                     (25, 55, 3200),
#                                     (27, 60, 3400),
#                                     (30, 65, 3300)]
#         dht22 = DHT22Sensor(None, None, testing=True)
#         expected_result_list = [dict(dewpoint=23.0, humidity=50.0, temperature=3000.0),
#                                 dict(dewpoint=25.0, humidity=55.0, temperature=3200.0),
#                                 dict(dewpoint=27.0, humidity=60.0, temperature=3400.0),
#                                 dict(dewpoint=30.0, humidity=65.0, temperature=3300.0)]
#         assert expected_result_list == [temp for temp in dht22]
#
#
# def test_dht22__iter__returns_iterator():
#     """ The iter methods must return an iterator in order to work properly """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement') as mock_measure:
#         mock_measure.side_effect = [(23, 50, 3000),
#                                     (25, 55, 3200),
#                                     (27, 60, 3400),
#                                     (30, 65, 3300)]
#         dht22 = DHT22Sensor(None, None, testing=True)
#         assert isinstance(dht22.__iter__(), Iterator)
#
#
# def test_dht22_read_updates_temp():
#     """  Verify that DHT22Sensor(None, None, testing=True).read() gets the average temp """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement') as mock_measure:
#         mock_measure.side_effect = [(23, 50, 3000),
#                                     (25, 55, 3200)]
#         dht22 = DHT22Sensor(None, None, testing=True)
#         assert dht22._dew_point is None
#         assert dht22._humidity is None
#         assert dht22._temperature is None
#         assert not dht22.read()
#         assert dht22._dew_point == 23.0
#         assert dht22._humidity == 50.0
#         assert dht22._temperature == 3000.0
#         assert not dht22.read()
#         assert dht22._dew_point == 25.0
#         assert dht22._humidity == 55.0
#         assert dht22._temperature == 3200.0
#
#
# def test_dht22_next_returns_dict():
#     """ next returns dict(altitude=float,pressure=int,temperature=float) """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement') as mock_measure:
#         mock_measure.side_effect = [(23, 50, 3000)]
#         dht22 = DHT22Sensor(None, None, testing=True)
#         assert dht22.next() == dict(dewpoint=23.0,
#                                   humidity=50.0,
#                                   temperature=3000.0)
#
#
# def test_dht22_condition_properties():
#     """ verify temperature property """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement') as mock_measure:
#         mock_measure.side_effect = [(23, 50, 3000),
#                                     (25, 55, 3200)]
#         dht22 = DHT22Sensor(None, None, testing=True)
#         assert dht22._dew_point is None # initial values
#         assert dht22._humidity is None
#         assert dht22._temperature is None
#         assert dht22.dew_point == 23.0
#         assert dht22.dew_point == 23.0
#         assert dht22.humidity == 50.0
#         assert dht22.humidity == 50.0
#         assert dht22.temperature == 3000.0
#         assert dht22.temperature == 3000.0
#         assert not dht22.read()
#         assert dht22.dew_point == 25.0
#         assert dht22.humidity == 55.0
#         assert dht22.temperature == 3200.0
#
#
# def test_dht22_special_method_str():
#     """ expect a __str__ format """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement') as mock_measure:
#         mock_measure.side_effect = [(0, 0, 0)]
#         dht22 = DHT22Sensor(None, None, testing=True)
#         dht22.read()
#     assert "Dew Point: 0.00" in str(dht22)
#     assert "Humidity: 0.00" in str(dht22)
#     assert "Temperature: 0.00" in str(dht22)
#
#
# def test_dht22_special_method_repr():
#     """ expect a __repr__ format """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement') as mock_measure:
#         mock_measure.side_effect = [(0, 0, 0)]
#         dht22 = DHT22Sensor(None, None, testing=True)
#         dht22.read()
#         assert "<DHT22Sensor(dewpoint=0.00)(humidity=0.00)(temperature=0.00)>" in repr(dht22)
#
#
# def test_dht22_raises_exception():
#     """ stops iteration on read() error """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement', side_effect=IOError):
#         with pytest.raises(StopIteration):
#             DHT22Sensor(None, None, testing=True).next()
#
#
# def test_dht22_read_returns_1_on_exception():
#     """ Verify the read() method returns true on error """
#     with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement', side_effect=Exception):
#         assert DHT22Sensor(None, None, testing=True).read()
#
#
# def test_dht22_read_logs_unknown_errors():
#     """ verify that IOErrors are logged """
#     with LogCapture() as log_cap:
#         with mock.patch('mycodo.inputs.dht22.DHT22Sensor.get_measurement',
#                         side_effect=Exception('msg')):
#             DHT22Sensor(None, None, testing=True).read()
#     expected_logs = ('mycodo.inputs.dht22', 'ERROR', 'DHT22Sensor raised an exception when taking a reading: msg')
#     assert expected_logs in log_cap.actual()

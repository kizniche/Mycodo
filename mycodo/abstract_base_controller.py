# coding=utf-8
"""
This module contains the AbstractBaseController Class which acts as a template
for all controllers.  It is not to be used directly. The AbstractBaseController Class
ensures that certain methods and instance variables are included in each
Controller template.

All Controller templates should inherit from this class

These base classes currently inherit this AbstractBaseController:
controllers/base_controller.py
input/base_inputs.py
"""
import logging

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import return_measurement_info


class AbstractBaseController(object):
    """
    Base Controller class that ensures certain methods and values are present
    in controllers.
    """
    def __init__(self, unique_id=None, testing=False, name=__name__):

        logger_name = "{}".format(name)
        if not testing and unique_id:
            logger_name += "_{}".format(unique_id.split('-')[0])
        self.logger = logging.getLogger(logger_name)

    def setup_custom_options(self, custom_options, custom_controller):
        for each_option_default in custom_options:
            try:
                required = False
                custom_option_set = False
                error = []
                if 'type' not in each_option_default:
                    error.append("'type' not found in custom_options")
                if 'id' not in each_option_default:
                    error.append("'id' not found in custom_options")
                if 'default_value' not in each_option_default:
                    error.append(
                        "'default_value' not found in custom_options")
                for each_error in error:
                    self.logger.error(each_error)
                if error:
                    return

                if ('required' in each_option_default and
                        each_option_default['required']):
                    required = True

                option_value = each_option_default['default_value']
                device_id = None
                measurement_id = None

                if not hasattr(custom_controller, 'custom_options'):
                    self.logger.error("custom_controller missing attribute custom_options")
                    return

                if custom_controller.custom_options:
                    for each_option in custom_controller.custom_options.split(';'):
                        option = each_option.split(',')[0]

                        if option == each_option_default['id']:
                            custom_option_set = True

                            if (each_option_default['type'] == 'select_measurement' and
                                    len(each_option.split(',')) > 2):
                                device_id = each_option.split(',')[1]
                                measurement_id = each_option.split(',')[2]
                            else:
                                option_value = each_option.split(',')[1]

                if required and not custom_option_set:
                    self.logger.error(
                        "Custom option '{}' required but was not found to be "
                        "set by the user".format(each_option_default['id']))

                if each_option_default['type'] == 'integer':
                    setattr(
                        self, each_option_default['id'], int(option_value))

                elif each_option_default['type'] == 'float':
                    setattr(
                        self, each_option_default['id'], float(option_value))

                elif each_option_default['type'] == 'bool':
                    setattr(
                        self, each_option_default['id'], bool(option_value))

                elif each_option_default['type'] == 'text':
                    setattr(
                        self, each_option_default['id'], str(option_value))

                elif each_option_default['type'] == 'select':
                    setattr(
                        self, each_option_default['id'], str(option_value))

                elif each_option_default['type'] == 'select_measurement':
                    setattr(
                        self,
                        '{}_device_id'.format(each_option_default['id']),
                        str(device_id))
                    setattr(
                        self,
                        '{}_measurement_id'.format(each_option_default['id']),
                        str(measurement_id))

                elif each_option_default['type'] == 'select_device':
                    setattr(
                        self,
                        '{}_id'.format(each_option_default['id']),
                        str(option_value))

                else:
                    self.logger.error(
                        "Unknown custom_option type '{}'".format(
                            each_option_default['type']))
            except Exception:
                self.logger.exception("Error parsing custom_options")

    @staticmethod
    def get_last_measurement(device_id, measurement_id, max_age=None):
        device_measurement = db_retrieve_table_daemon(
            DeviceMeasurements).filter(
            DeviceMeasurements.unique_id == measurement_id).first()
        if device_measurement:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        last_measurement = read_last_influxdb(
            device_id,
            unit,
            channel,
            measure=measurement,
            duration_sec=max_age)

        return last_measurement

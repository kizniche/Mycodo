# coding=utf-8
"""
This module contains the AbstractBaseController Class which acts as a template
for all controllers.  It is not to be used directly. The AbstractBaseController Class
ensures that certain methods and instance variables are included in each
Controller template.

All Controller templates should inherit from this class

These base classes currently inherit this AbstractBaseController:
controllers/base_controller.py
inputs/base_input.py
outputs/base_output.py
"""
import json
import logging
from collections import OrderedDict

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import OutputChannel
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.lockfile import LockFile
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

        self.lockfile = LockFile()

    def setup_custom_options(self, custom_options, custom_controller):
        if not hasattr(custom_controller, 'custom_options'):
            self.logger.error("custom_controller missing attribute custom_options")
            return
        elif custom_controller.custom_options.startswith("{"):
            return self.setup_custom_options_json(custom_options, custom_controller)
        else:
            return self.setup_custom_options_csv(custom_options, custom_controller)

    # TODO: Remove in place of JSON function, below, in next major version
    def setup_custom_options_csv(self, custom_options, custom_controller):
        for each_option_default in custom_options:
            try:
                required = False
                custom_option_set = False
                error = []

                if 'type' not in each_option_default:
                    error.append("'type' not found in custom_options")
                if ('id' not in each_option_default and
                        ('type' in each_option_default and
                         each_option_default['type'] not in ['new_line', 'message'])):
                    error.append("'id' not found in custom_options")
                if ('default_value' not in each_option_default and
                        ('type' in each_option_default and
                         each_option_default['type'] != 'new_line')):
                    error.append("'default_value' not found in custom_options")

                for each_error in error:
                    self.logger.error(each_error)
                if error:
                    return

                if each_option_default['type'] in ['new_line', 'message']:
                    continue

                if 'required' in each_option_default and each_option_default['required']:
                    required = True

                option_value = each_option_default['default_value']
                device_id = None
                measurement_id = None
                channel_id = None

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
                            if (each_option_default['type'] == 'select_measurement_channel' and
                                    len(each_option.split(',')) > 3):
                                device_id = each_option.split(',')[1]
                                measurement_id = each_option.split(',')[2]
                                channel_id = each_option.split(',')[3]
                            else:
                                option_value = each_option.split(',')[1]

                if required and not custom_option_set:
                    self.logger.error(
                        "Custom option '{}' required but was not found to be set by the user".format(
                            each_option_default['id']))

                elif each_option_default['type'] == 'integer':
                    setattr(self, each_option_default['id'], int(option_value))

                elif each_option_default['type'] == 'float':
                    setattr(self, each_option_default['id'], float(option_value))

                elif each_option_default['type'] == 'bool':
                    setattr(self, each_option_default['id'], bool(option_value))

                elif each_option_default['type'] in ['multiline_text',
                                                     'text']:
                    setattr(self, each_option_default['id'], str(option_value))

                elif each_option_default['type'] == 'select_multi_measurement':
                    setattr(self, each_option_default['id'], str(option_value))

                elif each_option_default['type'] == 'select':
                    option_value = str(option_value)
                    if 'cast_value' in each_option_default and each_option_default['cast_value']:
                        if each_option_default['cast_value'] == 'integer':
                            option_value = int(option_value)
                        elif each_option_default['cast_value'] == 'float':
                            option_value = float(option_value)
                    setattr(self, each_option_default['id'], option_value)

                elif each_option_default['type'] == 'select_measurement':
                    setattr(self,
                            '{}_device_id'.format(each_option_default['id']),
                            device_id)
                    setattr(self,
                            '{}_measurement_id'.format(each_option_default['id']),
                            measurement_id)

                elif each_option_default['type'] == 'select_measurement_channel':
                    setattr(self,
                            '{}_device_id'.format(each_option_default['id']),
                            device_id)
                    setattr(self,
                            '{}_measurement_id'.format(each_option_default['id']),
                            measurement_id)
                    setattr(self,
                            '{}_channel_id'.format(each_option_default['id']),
                            channel_id)

                elif each_option_default['type'] in ['select_type_measurement',
                                                     'select_type_unit']:
                    setattr(self, each_option_default['id'], str(option_value))

                elif each_option_default['type'] == 'select_device':
                    setattr(self,
                            '{}_id'.format(each_option_default['id']),
                            str(option_value))

                elif each_option_default['type'] in ['message', 'new_line']:
                    pass

                else:
                    self.logger.error(
                        "setup_custom_options_csv() Unknown custom_option type '{}'".format(each_option_default['type']))
            except Exception:
                self.logger.exception("Error parsing custom_options")

    def setup_custom_options_json(self, custom_options, custom_controller):
        for each_option_default in custom_options:
            try:
                required = False
                custom_option_set = False
                error = []

                if 'type' not in each_option_default:
                    error.append("'type' not found in custom_options")
                if ('id' not in each_option_default and
                        ('type' in each_option_default and
                         each_option_default['type'] not in ['new_line', 'message'])):
                    error.append("'id' not found in custom_options")
                if ('default_value' not in each_option_default and
                        ('type' in each_option_default and
                         each_option_default['type'] != 'new_line')):
                    error.append("'default_value' not found in custom_options")

                for each_error in error:
                    self.logger.error(each_error)
                if error:
                    return

                if each_option_default['type'] in ['new_line', 'message']:
                    continue

                if 'required' in each_option_default and each_option_default['required']:
                    required = True

                # set default value
                option_value = each_option_default['default_value']
                device_id = None
                measurement_id = None
                channel_id = None

                if not hasattr(custom_controller, 'custom_options'):
                    self.logger.error("custom_controller missing attribute custom_options")
                    return

                if getattr(custom_controller, 'custom_options'):
                    for each_option, each_value in json.loads(getattr(custom_controller, 'custom_options')).items():
                        if each_option == each_option_default['id']:
                            custom_option_set = True

                            if (each_option_default['type'] == 'select_measurement' and
                                    len(each_value.split(',')) > 1):
                                device_id = each_value.split(',')[0]
                                measurement_id = each_value.split(',')[1]
                            if (each_option_default['type'] == 'select_measurement_channel' and
                                    len(each_value.split(',')) > 2):
                                device_id = each_value.split(',')[0]
                                measurement_id = each_value.split(',')[1]
                                channel_id = each_value.split(',')[2]
                            else:
                                option_value = each_value

                if required and not custom_option_set:
                    self.logger.error(
                        "Option '{}' required but was not found to be set by the user".format(
                            each_option_default['id']))

                elif each_option_default['type'] in ['integer',
                                                     'float',
                                                     'bool',
                                                     'multiline_text',
                                                     'select_multi_measurement',
                                                     'text',
                                                     'select']:
                    setattr(self, each_option_default['id'], option_value)

                elif each_option_default['type'] == 'select_measurement':
                    setattr(self,
                            '{}_device_id'.format(each_option_default['id']),
                            device_id)
                    setattr(self,
                            '{}_measurement_id'.format(each_option_default['id']),
                            measurement_id)

                elif each_option_default['type'] == 'select_measurement_channel':
                    setattr(self,
                            '{}_device_id'.format(each_option_default['id']),
                            device_id)
                    setattr(self,
                            '{}_measurement_id'.format(each_option_default['id']),
                            measurement_id)
                    setattr(self,
                            '{}_channel_id'.format(each_option_default['id']),
                            channel_id)

                elif each_option_default['type'] == 'select_type_measurement':
                    setattr(self, each_option_default['id'], str(option_value))

                elif each_option_default['type'] == 'select_type_unit':
                    setattr(self, each_option_default['id'], str(option_value))

                elif each_option_default['type'] == 'select_device':
                    setattr(self,
                            '{}_id'.format(each_option_default['id']),
                            str(option_value))

                elif each_option_default['type'] in ['message', 'new_line']:
                    pass

                else:
                    self.logger.error(
                        "setup_custom_options_json() Unknown option type '{}'".format(each_option_default['type']))
            except Exception:
                self.logger.exception("Error parsing options")

    def setup_custom_channel_options_json(self, custom_options, custom_controller_channels):
        dict_values = {}
        for each_option_default in custom_options:
            try:
                dict_values[each_option_default['id']] = OrderedDict()
                required = False
                custom_option_set = False
                error = []
                if 'type' not in each_option_default:
                    error.append("'type' not found in custom_options")
                if 'id' not in each_option_default:
                    error.append("'id' not found in custom_options")
                if 'default_value' not in each_option_default:
                    error.append("'default_value' not found in custom_options")
                for each_error in error:
                    self.logger.error(each_error)
                if error:
                    return

                if 'required' in each_option_default and each_option_default['required']:
                    required = True

                for each_chan in custom_controller_channels:
                    # set default value
                    dict_values[each_option_default['id']][each_chan.channel] = each_option_default['default_value']

                    if each_option_default['type'] == 'select_measurement':
                        dict_values[each_option_default['id']][each_chan.channel] = {}
                        dict_values[each_option_default['id']][each_chan.channel]['device_id'] = None
                        dict_values[each_option_default['id']][each_chan.channel]['measurement_id'] = None
                        dict_values[each_option_default['id']][each_chan.channel]['channel_id'] = None

                    if not hasattr(each_chan, 'custom_options'):
                        self.logger.error("custom_controller missing attribute custom_options")
                        return

                    if getattr(each_chan, 'custom_options'):
                        for each_option, each_value in json.loads(getattr(each_chan, 'custom_options')).items():
                            if each_option == each_option_default['id']:
                                custom_option_set = True

                                if each_option_default['type'] == 'select_measurement':
                                    if len(each_value.split(',')) > 1:
                                        dict_values[each_option_default['id']][each_chan.channel]['device_id'] = each_value.split(',')[0]
                                        dict_values[each_option_default['id']][each_chan.channel]['measurement_id'] = each_value.split(',')[1]
                                    if len(each_value.split(',')) > 2:
                                        dict_values[each_option_default['id']][each_chan.channel]['channel_id'] = each_value.split(',')[2]
                                else:
                                    dict_values[each_option_default['id']][each_chan.channel] = each_value

                    if required and not custom_option_set:
                        self.logger.error(
                            "Option '{}' required but was not found to be set by the user".format(
                                each_option_default['id']))
            except Exception:
                self.logger.exception("Error parsing options")

        return dict_values

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
        channel, unit, measurement = return_measurement_info(device_measurement, conversion)

        last_measurement = read_last_influxdb(
            device_id,
            unit,
            channel,
            measure=measurement,
            duration_sec=max_age)

        return last_measurement

    @staticmethod
    def get_output_channel_from_channel_id(channel_id):
        """Return channel number from channel ID"""
        output_channel = db_retrieve_table_daemon(
            OutputChannel).filter(
            OutputChannel.unique_id == channel_id).first()
        if output_channel:
            return output_channel.channel

    def lock_acquire(self, lockfile, timeout):
        self.logger.debug("Acquiring lock")
        return self.lockfile.lock_acquire(lockfile, timeout)

    def lock_locked(self, lockfile):
        return self.lockfile.lock_locked(lockfile)

    def lock_release(self, lockfile):
        self.logger.debug("Releasing lock")
        self.lockfile.lock_release(lockfile)

# coding=utf-8
"""
This module contains the AbstractController Class which acts as a template
for all controllers.  It is not to be used directly. The AbstractController Class
ensures that certain methods and instance variables are included in each
Controller.

All Controllers should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import logging
import time
import timeit

import Pyro5

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import return_measurement_info


class AbstractController(object):
    """
    Base Controller class that ensures certain methods and values are present
    in controllers.
    """
    def __init__(self, ready, unique_id=None, name=__name__):
        self.thread_startup_timer = timeit.default_timer()
        self.running = False
        self.thread_shutdown_timer = 0
        self.sample_rate = 30
        self.ready = ready

        logger_name = "{}".format(name)
        if unique_id:
            logger_name += "_{}".format(unique_id.split('-')[0])
        self.logger = logging.getLogger(logger_name)

    #
    # Begin functions the user is expected to overwrite
    #

    def initialize_variables(self):
        self.logger.error(
            "{cls} did not overwrite the initialize_variables() method. All subclasses of the "
            "AbstractController class are required to overwrite this "
            "method".format(cls=type(self).__name__))
        raise NotImplementedError

    def loop(self):
        self.logger.error(
            "{cls} did not overwrite the loop() method. All subclasses of the "
            "AbstractController class are required to overwrite this "
            "method".format(cls=type(self).__name__))
        raise NotImplementedError

    def run_finally(self):
        """ Executed after loop() has finished """
        pass

    def pre_stop(self):
        """ Executed when the controller is instructed to stop """
        pass

    #
    # End functions the user typically overwrites
    #

    def run(self):
        try:
            try:
                self.initialize_variables()
            except Exception as except_msg:
                self.logger.exception(
                    "initialize_variables() Exception: {err}".format(
                        err=except_msg))

            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))

            self.ready.set()
            self.running = True

            while self.running:
                try:
                    self.loop()
                except Pyro5.errors.TimeoutError:
                    self.logger.exception("Pyro5 TimeoutError")
                except Exception:
                    self.logger.exception("loop() Error")
                finally:
                    time.sleep(self.sample_rate)

        except Exception:
            self.logger.exception("Run Error")
            self.thread_shutdown_timer = timeit.default_timer()
        finally:
            self.run_finally()
            self.running = False
            if self.thread_shutdown_timer:
                self.logger.info("Deactivated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
            else:
                self.logger.error("Deactivated unexpectedly")

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.pre_stop()
        self.running = False

    def set_log_level_debug(self, log_level_debug):
        if log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def attempt_execute(self, func, times=3, delay_sec=10):
        """ Attempt to execute a function several times with a delay between attempts """
        for i in range(1, times + 1):
            try:
                func()
                break
            except Exception:
                if i < times:
                    self.logger.exception(
                        "Exception executing {}() on attempt {} of {}. Waiting "
                        "{} seconds and trying again.".format(
                            func.__name__, i, times, delay_sec))
                    time.sleep(delay_sec)
                else:
                    self.logger.exception(
                        "Exception executing {}() on attempt {} of {}.".format(
                            func.__name__, i, times))

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

                            if each_option_default['type'] == 'select_measurement':
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

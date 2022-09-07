# coding=utf-8
"""
This module contains the AbstractFunction Class which acts as a template
for all functions.  It is not to be used directly. The AbstractFunction Class
ensures that certain methods and instance variables are included in each
Function.

All Functions should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import logging

from mycodo.abstract_base_controller import AbstractBaseController
from mycodo.databases.models import CustomController


class AbstractFunction(AbstractBaseController):
    """
    Base Function class that ensures certain methods and values are present
    in functions.
    """
    def __init__(self, function, testing=False, name=__name__):
        if not testing:
            super().__init__(function.unique_id, testing=testing, name=__name__)
        else:
            super().__init__(None, testing=testing, name=__name__)

        self.logger = None
        self.setup_logger(testing=testing, name=name, function=function)
        self.function = function
        self.running = True

        if not testing:
            self.unique_id = function.unique_id
            self.initialize_measurements()

    def initialize_measurements(self):
        try:
            if self.device_measurements:
                return
        except:
            pass
        self.setup_device_measurement(self.unique_id)

    def is_enabled(self, channel):
        try:
            return self.channels_measurement[channel].is_enabled
        except:
            self.setup_device_measurement(self.unique_id)
            return self.channels_measurement[channel].is_enabled

    def setup_logger(self, testing=None, name=None, function=None):
        name = name if name else __name__
        if not testing and function:
            log_name = "{}_{}".format(name, function.unique_id.split('-')[0])
        else:
            log_name = name
        self.logger = logging.getLogger(log_name)
        if not testing and function:
            if function.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def initialize(self):
        self.logger.error(
            "{cls} did not overwrite the initialize() method. All "
            "subclasses of the AbstractFunction class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def start_function(self):
        """Not used yet."""
        self.running = True

    def stop_function(self):
        """Called when Function is deactivated."""
        self.running = False

    #
    # Accessory functions
    #

    def set_custom_option(self, option, value):
        return self._set_custom_option(CustomController, self.unique_id, option, value)

    def get_custom_option(self, option):
        return self._get_custom_option(CustomController, self.unique_id, option)

    def delete_custom_option(self, option):
        return self._delete_custom_option(CustomController, self.unique_id, option)

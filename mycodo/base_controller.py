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


class AbstractController(object):
    """
    Base Controller class that ensures certain methods and values are present
    in controllers.
    """
    def __init__(self, ready, unique_id=None, name=__name__):
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0

        logger_name = "{}".format(name)
        if unique_id:
            logger_name += "_{}".format(unique_id.split('-')[0])
        self.logger = logging.getLogger(logger_name)

        self.ready = ready
        self.running = True

    def run(self):
        self.logger.error(
            "{cls} did not overwrite the run() method. All subclasses of the "
            "AbstractController class are required to overwrite this "
            "method".format(cls=type(self).__name__))
        raise NotImplementedError

    def attempt_execute(self, func, times_attempt, sleep_sec):
        for i in range(times_attempt):
            try:
                func()
                break
            except Exception:
                if i+1 < times_attempt:
                    self.logger.exception(
                        "Exception executing on attempt {} of {}. Waiting "
                        "{} seconds and trying again.".format(
                            i + 1, times_attempt, sleep_sec))
                    time.sleep(sleep_sec)
                else:
                    self.logger.exception(
                        "Exception executing on attempt {} of {}. Could not "
                        "execute {}()".format(
                            i + 1, times_attempt, func.__name__))

    def set_log_level_debug(self, log_level_debug):
        if log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

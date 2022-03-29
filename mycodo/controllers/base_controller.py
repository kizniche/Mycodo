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

from mycodo.abstract_base_controller import AbstractBaseController


class AbstractController(AbstractBaseController):
    """
    Base Controller class that ensures certain methods and values are present
    in controllers.
    """
    def __init__(self, ready, unique_id=None, name=__name__):
        super().__init__(unique_id, name=__name__)

        self.thread_startup_timer = timeit.default_timer()
        self.running = False
        self.thread_shutdown_timer = 0
        self.sample_rate = 0.25
        self.unique_id = unique_id
        self.ready = ready

        logger_name = f"{name}"
        if self.unique_id:
            logger_name += f"_{unique_id.split('-')[0]}"
            self.setup_device_measurement(unique_id)
        self.logger = logging.getLogger(logger_name)

    #
    # Begin functions the user is expected to overwrite
    #

    def initialize_variables(self):
        self.logger.error(
            f"{type(self).__name__} did not overwrite the initialize_variables() method. "
            f"All subclasses of the AbstractController class are required to overwrite this method")
        raise NotImplementedError

    def loop(self):
        self.logger.error(
            f"{type(self).__name__} did not overwrite the loop() method. "
            f"All subclasses of the AbstractController class are required to overwrite this method")
        raise NotImplementedError

    def run_finally(self):
        """Executed after loop() has finished."""
        pass

    def pre_stop(self):
        """Executed when the controller is instructed to stop."""
        pass

    #
    # End functions the user typically overwrites
    #

    def run(self):
        try:
            try:
                self.initialize_variables()
            except Exception as except_msg:
                self.logger.exception(f"initialize_variables() Exception: {except_msg}")

            dur = (timeit.default_timer() - self.thread_startup_timer) * 1000
            self.logger.info(f"Activated in {dur:.1f} ms")

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
                dur = (timeit.default_timer() - self.thread_shutdown_timer) * 1000
                self.logger.info(f"Deactivated in {dur:.1f} ms")
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
        """Attempt to execute a function several times with a delay between attempts."""
        for i in range(1, times + 1):
            try:
                func()
                break
            except Exception:
                if i < times:
                    self.logger.exception(
                        f"Exception executing {func.__name__}() on attempt {i} of {times}. "
                        f"Waiting {delay_sec} seconds and trying again.")
                    time.sleep(delay_sec)
                else:
                    self.logger.exception(
                        f"Exception executing {func.__name__}() on attempt {i} of {times}.")

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

import Pyro4


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
                except Pyro4.errors.TimeoutError:
                    self.logger.exception("Pyro4 TimeoutError")
                except Exception as except_msg:
                    self.logger.exception(
                        "loop() Error: {err}".format(err=except_msg))
                finally:
                    time.sleep(self.sample_rate)

        except Exception as except_msg:
            self.logger.exception("Run Error: {err}".format(
                err=except_msg))
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

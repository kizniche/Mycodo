# coding=utf-8
"""
This module contains the AbstractOutput Class which acts as a template
for all outputs. It is not to be used directly. The AbstractOutput Class
ensures that certain methods and instance variables are included in each
Output.

All Outputs should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import logging
import timeit

from mycodo.abstract_base_controller import AbstractBaseController


class AbstractOutput(AbstractBaseController):
    """
    Base Output class that ensures certain methods and values are present
    in outputs.
    """
    def __init__(self, output, testing=False, name=__name__):
        if not testing:
            super(AbstractOutput, self).__init__(output.unique_id, testing=testing, name=__name__)
        else:
            super(AbstractOutput, self).__init__(None, testing=testing, name=__name__)

        self.startup_timer = timeit.default_timer()

        self.logger = None
        self.setup_logger(testing=testing, name=name, output_dev=output)
        self.output = output
        self.running = True

        if not testing:
            self.unique_id = output.unique_id

    def __iter__(self):
        """ Support the iterator protocol """
        return self

    def __repr__(self):
        """  Representation of object """
        return_str = '<{cls}'.format(cls=type(self).__name__)
        return_str += '>'
        return return_str

    def __str__(self):
        """ Return measurement information """
        return_str = ''
        return return_str

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None):
        self.logger.error(
            "{cls} did not overwrite the output_switch() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def is_on(self):
        self.logger.error(
            "{cls} did not overwrite the is_on() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def is_setup(self):
        self.logger.error(
            "{cls} did not overwrite the is_setup() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def setup_output(self):
        self.logger.error(
            "{cls} did not overwrite the setup_output() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def stop_output(self):
        """ Called when Output is stopped """
        self.running = False
        try:
            # Release all locks
            for lockfile, lock_state in self.lockfile.locked.items():
                if lock_state:
                    self.lock_release(lockfile)
        except:
            pass

    #
    # Do not overwrite the function below
    #

    def init_post(self):
        self.logger.info("Initialized in {:.1f} ms".format(
            (timeit.default_timer() - self.startup_timer) * 1000))

    def setup_logger(self, testing=None, name=None, output_dev=None):
        name = name if name else __name__
        if not testing and output_dev:
            log_name = "{}_{}".format(name, output_dev.unique_id.split('-')[0])
        else:
            log_name = name
        self.logger = logging.getLogger(log_name)
        if not testing and output_dev:
            if output_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def shutdown(self, shutdown_timer):
        self.stop_output()
        self.logger.info("Stopped in {:.1f} ms".format(
            (timeit.default_timer() - shutdown_timer) * 1000))

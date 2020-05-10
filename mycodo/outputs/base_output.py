# coding=utf-8
"""
This module contains the AbstractOutput Class which acts as a template
for all outputs. It is not to be used directly. The AbstractOutput Class
ensures that certain methods and instance variables are included in each
Output.

All Outputs should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import datetime
import logging
import time

import filelock
import os

from mycodo.abstract_base_controller import AbstractBaseController
from mycodo.utils.database import db_retrieve_table_daemon


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

        self.logger = None
        self.setup_logger(testing=testing, name=name, output_dev=output)
        self.output = output
        self.lock = {}
        self.lock_file = None
        self.locked = {}
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

    def output_switch(self, state, amount=None, duty_cycle=None):
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

    def _is_setup(self):
        self.logger.error(
            "{cls} did not overwrite the _is_setup() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def setup_output(self):
        self.logger.error(
            "{cls} did not overwrite the setup_output() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

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

    def start_output(self):
        """ Not used yet """
        self.running = True

    def stop_output(self):
        """ Called when Output is deactivated """
        self.running = False
        try:
            if self.lock_file:
                self.lock_release(self.lock_file)
        except:
            pass

    def lock_acquire(self, lockfile, timeout):
        """ Non-blocking locking method """
        self.lock[lockfile] = filelock.FileLock(lockfile, timeout=1)
        self.locked[lockfile] = False
        timer = time.time() + timeout
        self.logger.debug("Acquiring lock for {} ({} sec timeout)".format(
            lockfile, timeout))
        while self.running and time.time() < timer:
            try:
                self.lock[lockfile].acquire()
                seconds = time.time() - (timer - timeout)
                self.logger.debug(
                    "Lock acquired for {} in {:.3f} seconds".format(
                        lockfile, seconds))
                self.locked[lockfile] = True
                break
            except:
                pass
            time.sleep(0.05)
        if not self.locked[lockfile]:
            self.logger.debug(
                "Lock unable to be acquired after {:.3f} seconds. "
                "Breaking for future lock.".format(timeout))
            self.lock_release(self.lock_file)

    def lock_release(self, lockfile):
        """ Release lock and force deletion of lock file """
        try:
            self.logger.debug("Releasing lock for {}".format(lockfile))
            self.lock[lockfile].release(force=True)
            os.remove(lockfile)
        except Exception:
            pass
        finally:
            self.locked[lockfile] = False

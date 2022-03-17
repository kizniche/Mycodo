# coding=utf-8
"""
This module contains the AbstractWidget Class which acts as a template
for all widgets. It is not to be used directly. The AbstractWidget Class
ensures that certain methods and instance variables are included in each
Widget.

All Widgets should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import logging
import timeit

from mycodo.abstract_base_controller import AbstractBaseController


class AbstractWidget(AbstractBaseController):
    """
    Base Widget class that ensures certain methods and values are present
    in widgets.
    """
    def __init__(self, widget, testing=False, name=__name__):
        if not testing:
            super().__init__(widget.unique_id, testing=testing, name=__name__)
        else:
            super().__init__(None, testing=testing, name=__name__)

        self.startup_timer = timeit.default_timer()

        self.logger = None
        self.setup_logger(testing=testing, name=name, widget=widget)
        self.widget = widget
        self.running = True

        if not testing:
            self.unique_id = widget.unique_id

    def __iter__(self):
        """Support the iterator protocol."""
        return self

    def __repr__(self):
        """Representation of object."""
        return_str = '<{cls}'.format(cls=type(self).__name__)
        return_str += '>'
        return return_str

    def __str__(self):
        """Return measurement information."""
        return_str = ''
        return return_str

    def execute_refresh(self):
        self.logger.error(
            "{cls} did not overwrite the setup_widget() method. All "
            "subclasses of the AbstractWidget class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def stop_widget(self):
        """Called when Widget is stopped."""
        self.running = False

    #
    # Do not overwrite the function below
    #

    def init_post(self):
        self.logger.info("Initialized in {:.1f} ms".format(
            (timeit.default_timer() - self.startup_timer) * 1000))

    def setup_logger(self, testing=None, name=None, widget=None):
        name = name if name else __name__
        if not testing and widget:
            log_name = "{}_{}".format(name, widget.unique_id.split('-')[0])
        else:
            log_name = name
        self.logger = logging.getLogger(log_name)
        if not testing and widget:
            if widget.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def shutdown(self, shutdown_timer):
        self.stop_widget()
        self.logger.info("Stopped in {:.1f} ms".format(
            (timeit.default_timer() - shutdown_timer) * 1000))

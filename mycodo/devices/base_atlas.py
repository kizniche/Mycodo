# coding=utf-8
"""
This module contains the AbstractBaseAtlasScientific Class which acts as a template
for all Atlas Scientific devices.  It is not to be used directly. The
AbstractBaseAtlasScientific Class ensures that certain methods and instance variables
are included in each Atlas Scientific class template.

All Atlas Scientific templates should inherit from this class
"""
import logging


class AbstractBaseAtlasScientific(object):
    """
    Base Atlas Scientific class that ensures certain methods and values are present
    in controllers.
    """
    def __init__(self, interface, name):
        self.interface = interface
        self.atlas_sensor = None
        self.logger = None

        self.board = None
        self.revision = None
        self.firmware = None

        self.logger = logging.getLogger(
            "{}{}".format(__name__, name))

    def get_board_version(self):
        """Return the board version of the Atlas Scientific device"""
        if self.board and self.revision and self.firmware:
            return self.board, self.revision, self.firmware

        try:
            if self.interface == 'FTDI':
                info = self.query('i')
            elif self.interface == 'UART':
                info = self.query('i')
            elif self.interface == 'I2C':
                info = self.query('i')
            else:
                return None, 0, None

            # Find relevant string in response
            response_str = None
            if isinstance(info[1], list):
                for each_line in info[1]:
                    if "," in each_line:
                        response_str = each_line
                        break
            elif isinstance(info[1], str):
                if "," in info[1]:
                    response_str = info[1]

            if not response_str or info[0] == "error":
                return None, 0, None

            # Check first letter of info response; "P" indicates a legacy board version
            if response_str.startswith("P"):
                self.board = "NA"
                self.revision = 1  # Older board version (1)
                self.firmware = response_str
            elif len(response_str.split(',')) == 3:
                info_split = response_str.split(',')
                measurement = info_split[1]
                firmware = info_split[2]
                self.board = measurement
                self.revision = 2  # Newer board version (2)
                self.firmware = firmware
            else:
                return None, 0, None

            return self.board, self.revision, self.firmware

        except TypeError:
            self.logger.exception("Unable to determine board version of Atlas sensor")
            return None, 0, None

    def query(self, query_str):
        self.logger.error(
            "{cls} did not overwrite the query() method. All subclasses of "
            "the AbstractBaseAtlasScientific class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

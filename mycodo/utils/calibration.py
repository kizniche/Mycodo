# coding=utf-8
import logging
import time

logger = logging.getLogger("mycodo.atlas_scientific")


class AtlasScientificCommand:
    """
    Class to handle issuing commands to the Atlas Scientific sensor boards
    """

    def __init__(self, input_dev):
        self.cmd_send = None
        self.ph_sensor_uart = None
        self.ph_sensor_i2c = None
        self.interface = input_dev.interface

        if self.interface == 'FTDI':
            from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
            self.ph_sensor_ftdi = AtlasScientificFTDI(
                input_dev.ftdi_location)
        elif self.interface == 'UART':
            from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
            self.ph_sensor_uart = AtlasScientificUART(
                input_dev.uart_location,
                baudrate=input_dev.baud_rate)
        elif self.interface == 'I2C':
            from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
            self.ph_sensor_i2c = AtlasScientificI2C(
                i2c_address=int(str(input_dev.i2c_location), 16),
                i2c_bus=input_dev.i2c_bus)

        self.board_version, self.board_info = self.get_board_version()

        if self.board_version == 0:
            logger.error("Unable to retrieve device info (this indicates the "
                         "device was not properly initialized or connected)")
        else:
            logger.debug("Device Info: {info}".format(info=self.board_info))
            logger.debug("Detected Version: {ver}".format(ver=self.board_version))

    def get_board_version(self):
        """Return the board version of the Atlas Scientific pH sensor"""
        info = None

        try:
            if self.interface == 'FTDI':
                self.ph_sensor_ftdi.send_cmd('i')
                info = self.ph_sensor_ftdi.read_lines()
            elif self.interface == 'UART':
                info = self.ph_sensor_uart.query('i')
            elif self.interface == 'I2C':
                info = self.ph_sensor_i2c.query('i')
        except TypeError:
            logger.exception("Unable to determine board version of Atlas sensor")

        # Check first letter of info response
        # "P" indicates a legacy board version
        if info is None:
            return 0, None
        elif info is list:
            for each_line in info:
                if each_line == 'P':
                    return 1, each_line  # Older board version
                elif ',' in each_line and len(each_line.split(',')) == 3:
                    return 2, each_line  # Newer board version

    def calibrate(self, command, temperature=None, custom_cmd=None):
        """
        Determine and send the correct command to an Atlas Scientific sensor,
        based on the board version
        """
        # Formulate command based on calibration step and board version.
        # Legacy boards requires a different command than recent boards.
        # Some commands are not necessary for recent boards and will not
        # generate a response.
        err = 1
        msg = "Default message"
        if command == 'temperature' and temperature is not None:
            if self.board_version == 1:
                err, msg = self.send_command(temperature)
            elif self.board_version == 2:
                err, msg = self.send_command('T,{temp}'.format(temp=temperature))
        elif command == 'clear_calibration':
            if self.board_version == 1:
                err, msg = self.send_command('X')
                self.send_command('L0')
            elif self.board_version == 2:
                err, msg = self.send_command('Cal,clear')
        elif command == 'continuous':
            if self.board_version == 1:
                err, msg = self.send_command('C')
            elif self.board_version == 2:
                err, msg = self.send_command('C,1')
        elif command == 'low':
            if self.board_version == 1:
                err, msg = self.send_command('F')
            elif self.board_version == 2:
                err, msg = self.send_command('Cal,low,4.00')
        elif command == 'mid':
            if self.board_version == 1:
                err, msg = self.send_command('S')
            elif self.board_version == 2:
                err, msg = self.send_command('Cal,mid,7.00')
        elif command == 'high':
            if self.board_version == 1:
                err, msg = self.send_command('T')
            elif self.board_version == 2:
                err, msg = self.send_command('Cal,high,10.00')
        elif command == 'end':
            if self.board_version == 1:
                err, msg = self.send_command('E')
            elif self.board_version == 2:
                err, msg = self.send_command('C,0')
        elif custom_cmd:
            err, msg = self.send_command(custom_cmd)
        return err, msg

    def send_command(self, cmd_send):
        """ Send the command (if not None) and return the response """
        try:
            return_value = "No message"
            if cmd_send is not None:
                if self.interface == 'FTDI':
                    self.ph_sensor_ftdi.send_cmd(cmd_send)
                    return_value = self.ph_sensor_ftdi.read_lines()
                elif self.interface == 'UART':
                    return_value = self.ph_sensor_uart.query(cmd_send)
                elif self.interface == 'I2C':
                    return_value = self.ph_sensor_i2c.query(cmd_send)
                time.sleep(0.1)
                return 0, return_value
            else:
                return 1, "No command given"
        except Exception as err:
            logger.error("{cls} raised an exception while communicating with "
                         "the board: {err}".format(cls=type(self).__name__,
                                                   err=err))
            return 1, err

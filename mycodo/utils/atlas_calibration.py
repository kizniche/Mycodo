# coding=utf-8
import logging

logger = logging.getLogger("mycodo.atlas_scientific")


def setup_atlas_device(atlas_device):
    if atlas_device.interface == 'FTDI':
        from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
        atlas_device = AtlasScientificFTDI(
            atlas_device.ftdi_location)
    elif atlas_device.interface == 'UART':
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        atlas_device = AtlasScientificUART(
            atlas_device.uart_location,
            baudrate=atlas_device.baud_rate)
    elif atlas_device.interface == 'I2C':
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        atlas_device = AtlasScientificI2C(
            i2c_address=int(str(atlas_device.i2c_location), 16),
            i2c_bus=atlas_device.i2c_bus)
    else:
        logger.error("Unrecognized interface: {}".format(atlas_device.interface))
        return
    return atlas_device


class AtlasScientificCommand:
    """Class to handle issuing commands to the Atlas Scientific sensor boards."""

    def __init__(self, input_dev, sensor=None):
        self.cmd_send = None
        self.atlas_device = None
        self.interface = input_dev.interface
        self.init_error = None

        if sensor:
            self.atlas_device = sensor
        else:
            self.atlas_device = setup_atlas_device(input_dev)

        (self.measurement,
         self.board_version,
         self.firmware_version) = self.atlas_device.get_board_version()

        if self.board_version == 0:
            error_msg = "Atlas Scientific board initialization unsuccessful. " \
                        "Unable to retrieve device info (this indicates the " \
                        "device was not properly initialized or connected). " \
                        "Returned: {}, {}, {}".format(
                 self.measurement,
                 self.board_version,
                 self.firmware_version)
            logger.error(error_msg)
            self.init_error = error_msg
        else:
            logger.debug(
                "Atlas Scientific board initialization success. "
                "Measurement: {meas}, Board: {brd}, Firmware: {fw}".format(
                    meas=self.measurement,
                    brd=self.board_version,
                    fw=self.firmware_version))

    def get_sensor_measurement(self):
        return self.measurement

    def calibrate(self, command, set_amount=None, custom_cmd=None):
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

        if self.init_error:
            msg = self.init_error

        # Atlas EC
        if command == 'ec_dry':
            if self.board_version >= 2:
                err, msg = self.send_command('cal,dry')
        elif command == 'ec_low':
            if self.board_version >= 2:
                err, msg = self.send_command(f'cal,low,{set_amount}')
        elif command == 'ec_high':
            if self.board_version >= 2:
                err, msg = self.send_command(f'cal,high,{set_amount}')

        # Atlas pH
        elif command == 'temperature' and set_amount is not None:
            if self.board_version == 1:
                err, msg = self.send_command(set_amount)
            elif self.board_version >= 2:
                err, msg = self.send_command(f'T,{set_amount:.2f}')
        elif command == 'clear_calibration':
            if self.board_version == 1:
                err, msg = self.send_command('X')
                self.send_command('L0')
            elif self.board_version >= 2:
                err, msg = self.send_command('Cal,clear')
        elif command == 'continuous':
            if self.board_version == 1:
                err, msg = self.send_command('C')
            elif self.board_version >= 2:
                err, msg = self.send_command('C,1')
        elif command == 'low':
            if self.board_version == 1:
                err, msg = self.send_command('F')
            elif self.board_version >= 2:
                err, msg = self.send_command('Cal,low,4.00')
        elif command == 'mid':
            if self.board_version == 1:
                err, msg = self.send_command('S')
            elif self.board_version >= 2:
                err, msg = self.send_command('Cal,mid,7.00')
        elif command == 'high':
            if self.board_version == 1:
                err, msg = self.send_command('T')
            elif self.board_version >= 2:
                err, msg = self.send_command('Cal,high,10.00')
        elif command == 'calibrated':  # Not implemented. This queries whether there is a stored calibration
            if self.board_version == 1:
                err = 'success'
                msg = 'Calibrated query not implemented on board version 1 (assume it was successfully calibrated)'
            elif self.board_version >= 2:
                err, msg = self.send_command('Cal,?')
        elif command == 'end':
            if self.board_version == 1:
                err, msg = self.send_command('E')
            elif self.board_version >= 2:
                err, msg = self.send_command('C,0')
        elif custom_cmd:
            err, msg = self.send_command(custom_cmd)

        return err, msg

    def send_command(self, cmd_send):
        """Send the command (if not None) and return the response."""
        try:
            if not cmd_send:
                return 1, "No command given"

            if self.interface == 'FTDI':
                return_status, return_value = self.atlas_device.query(cmd_send)
            elif self.interface == 'UART':
                return_status, return_value = self.atlas_device.query(cmd_send)
            elif self.interface == 'I2C':
                return_status, return_value = self.atlas_device.query(cmd_send)
            else:
                return 1, f"Interface not recognized: {self.interface}"

            if return_status == 'success':
                return 0, return_value
            else:
                return 1, return_value
        except Exception as err:
            logger.error(f"{type(self).__name__} raised an exception while communicating with the board: {err}")
            return 1, err

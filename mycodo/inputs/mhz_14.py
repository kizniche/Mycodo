# coding=utf-8
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device


def constraints_pass_measure_range(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    if value not in ["2000", "5000", "10000"]:
        all_passed = False
        errors.append("Invalid range")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {0: {"measurement": "co2", "unit": "ppm"}}

# Input information
INPUT_INFORMATION = {
    "input_name_unique": "MH_Z14A",
    "input_manufacturer": "Winsen",
    "input_name": "MH-Z14A",
    "input_library": "serial",
    "measurements_name": "CO2",
    "measurements_dict": measurements_dict,
    "url_manufacturer": "https://www.winsen-sensor.com/sensors/co2-sensor/mh-z14a.html",
    "url_datasheet": "https://www.winsen-sensor.com/d/files/mh-z14a-co2-manual-v1_4.pdf",
    "options_enabled": ["interface", "uart_location", "period", "pre_output"],
    "dependencies_module": [("pip-pypi", "RPi.GPIO", "RPi.GPIO")],
    "interfaces": ["UART"],
    "gpio_location": "27",
    "uart_location": "/dev/ttyAMA0",
    "custom_options": [
        {
            "id": "self_calibration_enable",
            "type": "bool",
            "default_value": True,
            "name": "Automatic Self-calibration",
            "phrase": "Enable automatic self-calibration",
        },
        {
            "id": "measure_range",
            "type": "select",
            "default_value": "2000",
            "options_select": [
                ("2000", "400 - 2000 ppmv"),
                ("5000", "400 - 5000 ppmv"),
                ("10000", "400 - 10000 ppmv"),
            ],
            "required": True,
            "constraints_pass": constraints_pass_measure_range,
            "name": "Measurement Range",
            "phrase": "Set the measuring range of the sensor",
        },
        {
            "id": "gpio_fallback",
            "type": "integer",
            "default_value": 27,
            "name": "GPIO Fallback",
            "phrase": "Fall back to obtaining readings using PWM on this pin",
        },
    ],
    "custom_commands_message": "Self-calibration: The module can gauge the zero point "
    "intelligently based on the lowest reading observed in the past 24 hours. This value "
    "is automatically set as the new zero point (400 ppmv). This method is suitable for "
    "office and home environments that circulate fresh outside air, but not suitable for "
    "closed environments or ones that produce CO2 (e.g. agriculture greenhouse, refrigerator, "
    "etc.). If the module is used in such environments then please turn off this function."
    "<br>Zero point calibration: activate the sensor in a 400 ppmv CO2 environment (outside "
    "air), allow to run for 20 minutes, then press the Calibrate Zero Point button.<br>Span "
    "point calibration: activate the sensor in an environment with a stable CO2 concentration "
    "between 1000 and 2000 ppmv (2000 recommended), allow to run for 20 minutes, enter the "
    "ppmv value in the Span Point (ppmv) input field, then press the Calibrate Span Point "
    "button. If running a span point calibration, run a zero point calibration first. A span "
    "point calibration is not necessary and should only be performed if you know what you "
    "are doing and can accurately produce a 2000 ppmv environment.",
    "custom_commands": [
        {
            "id": "calibrate_zero_point",
            "type": "button",
            "name": "Calibrate Zero Point",
        },
        {
            "id": "span_point_value_ppmv",
            "type": "integer",
            "default_value": 2000,
            "name": "Span Point (ppmv)",
            "phrase": "The ppmv concentration for a span point calibration",
        },
        {
            "id": "calibrate_span_point",
            "type": "button",
            "name": "Calibrate Span Point",
        },
    ],
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the MH-Z14's CO2 concentration"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.ser = None
        self.gpio = None
        self.self_calibration_enable = True

        self.measuring = None
        self.calibrating = None

        self.measure_range = 2000
        self.gpio_fallback = None

        if not testing:
            self.setup_custom_options(INPUT_INFORMATION["custom_options"], input_dev)
            self.initialize_input()

    def initialize_input(self):

        if self.input_dev.interface == "UART":
            import serial

            # Use serial interface
            if is_device(self.input_dev.uart_location):
                try:
                    self.ser = serial.Serial(
                        port=self.input_dev.uart_location,
                        baudrate=9600,
                        # dsrdtr=True,
                        timeout=1,
                        writeTimeout=5,
                    )
                except serial.SerialException:
                    self.logger.exception("Opening serial")
            else:
                self.logger.error(
                    'Could not open "{dev}". Check the device location is correct.'.format(
                        dev=self.input_dev.uart_location
                    )
                )
        if self.gpio_fallback:
            # Fall back to reading measurements on PWM interface
            import RPi.GPIO as GPIO

            self.gpio = GPIO

            self.location = int(self.input_dev.gpio_location)
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.location, self.gpio.IN)

        self.set_self_calibration()

        if self.measure_range:
            self.set_measure_range(self.measure_range)

        time.sleep(0.1)

    def get_measurement(self):
        """Gets the MH-Z14's CO2 concentration in ppmv"""
        while self.calibrating:
            time.sleep(0.1)
        self.measuring = True

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            if not self.ser:
                self.logger.error("Input not set up")
                return

            self._get_co2_uart()
        except:
            if self.gpio_fallback:
                self.logger.warn(
                    "Could not obtain sensor reading via UART! Falling back to using GPIO..."
                )
                if not self.gpio:
                    self.logger.error("Fallback input not set up")
                    return

                self._get_co2_gpio()
            else:
                self.logger.exception("get_measurement()")
        finally:
            self.measuring = False

        return self.return_dict

    def set_self_calibration(self):
        if self.self_calibration_enable:
            self.ser.write(
                bytearray([0xFF, 0x01, 0x79, 0xA0, 0x00, 0x00, 0x00, 0x00, 0xE6])
            )
        else:
            self.ser.write(
                bytearray([0xFF, 0x01, 0x79, 0x00, 0x00, 0x00, 0x00, 0x00, 0x86])
            )

    def set_measure_range(self, measure_range):
        """
        Sets the measurement range. Options are: '2000', '5000' or '10000' (ppmv)
        :param measure_range: string
        :return: None
        """
        if measure_range == "2000":
            self.ser.write(
                bytearray([0xFF, 0x01, 0x99, 0x00, 0x00, 0x00, 0x07, 0xD0, 0x8F])
            )
        elif measure_range == "5000":
            self.ser.write(
                bytearray([0xFF, 0x01, 0x99, 0x00, 0x00, 0x00, 0x13, 0x88, 0xCB])
            )
        elif measure_range == "10000":
            self.ser.write(
                bytearray([0xFF, 0x01, 0x99, 0x00, 0x00, 0x00, 0x27, 0x10, 0x2F])
            )
        else:
            return "out of range"

    def calibrate_span_point(self, args_dict):
        """
        Span Point Calibration
        from https://github.com/UedaTakeyuki/mh-z19
        """
        if "span_point_value_ppmv" not in args_dict:
            self.logger.error(
                "Cannot conduct span point calibration without a ppmv value"
            )
            return
        if not isinstance(args_dict["span_point_value_ppmv"], int):
            self.logger.error(
                "ppmv value does not represent an integer: '{}', type: {}".format(
                    args_dict["span_point_value_ppmv"],
                    type(args_dict["span_point_value_ppmv"]),
                )
            )
            return

        while self.measuring:
            time.sleep(0.1)
        self.calibrating = True

        try:
            self.logger.info(
                "Conducting span point calibration with a value of {} ppmv".format(
                    args_dict["span_point_value_ppmv"]
                )
            )
            b3 = args_dict["span_point_value_ppmv"] // 256
            b4 = args_dict["span_point_value_ppmv"] % 256
            c = self.checksum([0x01, 0x88, b3, b4])
            self.ser.write(bytearray([0xFF, 0x01, 0x88, b3, b4, 0x00, 0x0B, 0xB8, c]))
            time.sleep(0.1)
        except:
            self.logger.exception()
        finally:
            self.calibrating = False

    def calibrate_zero_point(self, args_dict):
        """
        Zero Point Calibration
        from https://github.com/UedaTakeyuki/mh-z19
        """
        while self.measuring:
            time.sleep(0.1)
        self.calibrating = True

        try:
            self.logger.info("Conducting zero point calibration")
            self.ser.write(
                bytearray([0xFF, 0x01, 0x87, 0x00, 0x00, 0x00, 0x00, 0x00, 0x78])
            )
            time.sleep(0.1)
        except:
            self.logger.exception()
        finally:
            self.calibrating = False

    @staticmethod
    def checksum(array):
        return (
            0xFF - (sum(array[i] for i in range(1, 7)) & 0xFF) + 1
        )  # formula from datasheet

    def _get_co2_uart(self):
        self.ser.flushInput()
        self.ser.write(
            bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])
        )
        time.sleep(0.01)
        resp = self.ser.read(9)

        if not resp:
            self.logger.debug("No response")
        elif len(resp) != 9:
            self.logger.debug("Response has incorrect length '{}'".format(resp))
        elif self.checksum(resp) != resp[8]:
            self.logger.error("Bad checksum")
        else:
            high = resp[2]
            low = resp[3]
            co2 = (high * 256) + low
            self.value_set(0, co2)

    def _get_co2_gpio(self):
        start_ts = 0
        duration = 0

        while self.gpio.input(self.location) == 0:
            # Wait for next cycle
            start_ts = time.time_ns()

        while self.gpio.input(self.location) == 1:
            duration = time.time_ns() - start_ts
        # from datasheet
        # CO2 ppm = 5000 * (Th - 2ms) / (Th + Tl - 4ms)
        #   given Tl + Th = 1004
        #   Tl = 1004 - Th
        #   = 5000 * (Th - 2ms) / (Th + 1004 - Th - 4ms)
        #   = 5000 * (Th - 2ms) / 1000 = 2 * (Th - 2ms)
        if duration:
            co2 = 5 * ((duration / 1_000_000) - 2)
            self.value_set(0, co2)

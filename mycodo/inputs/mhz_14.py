# coding=utf-8
import copy
import time

import serial

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device


def constraints_pass_measure_range(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    if value not in ["2000", "5000", "10000"]:
        all_passed = False
        errors.append(f"Invalid measurement range '{value}'")

    return all_passed, errors, mod_input


def constraints_pass_gpio(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: string
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    if value:
        try:
            int(value)
        except:
            all_passed = False
            errors.append(f"Invalid GPIO pin number '{value}'")

    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        "measurement": "co2",
        "unit": "ppm"
    }
}

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

    "options_enabled": [
        "interface",
        "uart_location",
        "period",
        "pre_output"
    ],

    "dependencies_module": [
        ("pip-pypi", "RPi.GPIO", "RPi.GPIO")
    ],

    "interfaces": ["UART"],
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
            "type": "message",
            "default_value": """The CO2 measurement can also be obtained using PWM via a GPIO pin. Enter the pin number below or leave blank to disable this option. This also makes it possible to obtain measurements even if the UART interface is not available (note that the sensor can't be configured / calibrated without a working UART interface).""",
        },
        {
            "id": "gpio_location",
            "type": "text",
            "default_value": None,
            "constraints_pass": constraints_pass_gpio,
            "name": "GPIO Override",
            "phrase": "Obtain readings using PWM on this GPIO pin instead of via UART",
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
        super().__init__(input_dev, testing=testing, name=__name__)

        self._gpio_location = ""

        self.ser = None
        self.gpio = None

        self.is_measuring = False
        self.is_calibrating = False
        self.bad_checksum = 0

        if not testing:
            self.setup_custom_options(INPUT_INFORMATION["custom_options"], input_dev)
            self.try_initialize()

    def initialize(self):
        # Check if device is valid
        if is_device(self.input_dev.uart_location):
            self.ser = serial.Serial(
                port=self.input_dev.uart_location,
                baudrate=9600,
                timeout=1,
                writeTimeout=5)

            self.set_measure_range()
            self.set_self_calibration()
        else:
            self.logger.error(
                f"Could not open '{self.input_dev.uart_location}'. "
                f"Check the device location is correct.")

        if self.gpio_location:
            # Prefer reading measurements using PWM via GPIO
            import RPi.GPIO as GPIO

            self.gpio = GPIO

            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.gpio_location, self.gpio.IN)

    @property
    def gpio_location(self):
        if self._gpio_location != "":
            return self._gpio_location
        else:
            # GPIO location not initialized, do so now
            gpio_location = self.get_custom_option("gpio_location")

            if gpio_location:
                try:
                    # Convert to integer
                    self._gpio_location = int(gpio_location)
                except (TypeError, ValueError) as e:
                    self.logger.error(f"Invalid GPIO pin number '{gpio_location}': {e}")
                    self._gpio_location = None
            else:
                # No override specified, continue...
                self._gpio_location = None

        return self._gpio_location

    def stop_input(self):
        if self.gpio:
            self.logger.debug(f"Cleaning up GPIO channel '{self.gpio_location}'...")
            self.gpio.cleanup(self.gpio_location)

    def set_measure_range(self):
        """
        Sets the measurement range. Options are: '2000', '5000' or '10000' (ppmv)
        :return: None
        """
        if not self.ser:
            self.logger.error("Input not set up - cannot set measurement range")
            return

        measure_range = self.get_custom_option("measure_range")

        if measure_range == "2000":
            cmd = bytearray([0xFF, 0x01, 0x99, 0x00, 0x00, 0x00, 0x07, 0xD0, 0x8F])
        elif measure_range == "5000":
            cmd = bytearray([0xFF, 0x01, 0x99, 0x00, 0x00, 0x00, 0x13, 0x88, 0xCB])
        elif measure_range == "10000":
            cmd = bytearray([0xFF, 0x01, 0x99, 0x00, 0x00, 0x00, 0x27, 0x10, 0x2F])
        else:
            self.logger.error(f"Invalid measurement range '{measure_range}'")
            return

        self.logger.info(f"Setting measurement range to '{measure_range}'...")
        self.ser.write(cmd)
        time.sleep(0.1)
        self.logger.info("Measurement range set!")

    def set_self_calibration(self):
        if not self.ser:
            self.logger.error("Input not set up - cannot be calibrated")
            return

        if self.get_custom_option("self_calibration_enable"):
            self.logger.info("Enabling self-calibration...")
            self.ser.write(
                bytearray([0xFF, 0x01, 0x79, 0xA0, 0x00, 0x00, 0x00, 0x00, 0xE6]))
        else:
            self.logger.info("Disabling self-calibration...")
            self.ser.write(
                bytearray([0xFF, 0x01, 0x79, 0x00, 0x00, 0x00, 0x00, 0x00, 0x86]))
        time.sleep(0.1)
        self.logger.info("Self-calibration settings updated!")

    def get_measurement(self):
        """Gets the measurement in units by reading the MH-Z14A."""
        if not self.ser and not self.gpio:
            self.logger.error(
                "Error 101: Device not set up. "
                "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        co2 = self.read_co2()
        if co2 is not None:
            self.value_set(0, co2)

        return self.return_dict

    def read_co2(self):
        """Gets the MH-Z14's CO2 concentration in ppmv"""
        while self.is_calibrating:
            time.sleep(0.1)

        self.is_measuring = True

        try:
            if self.gpio:
                # Obtain reading via GPIO
                self.logger.debug(
                    f"Obtaining reading via GPIO channel {self.gpio_location}...")
                return self._read_co2_gpio()

            elif self.ser:
                # Obtain reading via UART
                self.logger.debug("Obtaining reading via UART...")
                return self._read_co2_uart()
            else:
                self.logger.error(
                    "Error 101: Device not set up. "
                    "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
                return None
        except:
            self.logger.exception("read_co2()")
        finally:
            self.is_measuring = False

    def calibrate_span_point(self, args_dict):
        """
        Span Point Calibration
        from https://github.com/UedaTakeyuki/mh-z19
        """
        if not self.ser:
            self.logger.error("Input not set up - cannot calibrate span point")
            return

        try:
            span_point_value_ppmv = int(args_dict["span_point_value_ppmv"])
        except KeyError:
            self.logger.error(
                "Cannot conduct span point calibration without a valid integer ppmv value")
            return

        while self.is_measuring:
            time.sleep(0.1)

        self.is_calibrating = True

        try:
            self.logger.info(
                f"Conducting span point calibration with a value of {span_point_value_ppmv} ppmv...")
            b3 = span_point_value_ppmv // 256
            b4 = span_point_value_ppmv % 256
            c = self.checksum([0x01, 0x88, b3, b4])
            self.ser.write(bytearray([0xFF, 0x01, 0x88, b3, b4, 0x00, 0x0B, 0xB8, c]))
            time.sleep(0.1)
            self.logger.info("Span point calibration completed!")
        except:
            self.logger.exception("calibrate_span_point()")
        finally:
            self.is_calibrating = False

    def calibrate_zero_point(self, args_dict):
        """
        Zero Point Calibration
        from https://github.com/UedaTakeyuki/mh-z19
        """
        if not self.ser:
            self.logger.error("Input not set up - cannot calibrate zero point")
            return

        while self.is_measuring:
            time.sleep(0.1)

        self.is_calibrating = True

        try:
            self.logger.info("Conducting zero point calibration...")
            self.ser.write(
                bytearray([0xFF, 0x01, 0x87, 0x00, 0x00, 0x00, 0x00, 0x00, 0x78])
            )
            time.sleep(0.1)
            self.logger.info("Zero point calibrated!")
        except:
            self.logger.exception("calibrate_zero_point()")
        finally:
            self.is_calibrating = False

    @staticmethod
    def checksum(array):
        return (
            0xFF - (sum(array[i] for i in range(1, 7)) & 0xFF) + 1
        )  # formula from datasheet

    def _read_co2_uart(self):
        if not self.ser:
            self.logger.error("Input not set up - cannot read CO2 measurement")
            return

        self.ser.flushInput()
        self.ser.write(
            bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])
        )
        time.sleep(0.1)
        resp = self.ser.read(9)

        if not resp:
            self.logger.error("No response")
        elif len(resp) != 9:
            self.logger.error(f"Response has incorrect length '{resp}'")
        elif self.checksum(resp) != resp[8]:
            self.logger.error("Bad checksum")
            self.bad_checksum += 1
            if self.bad_checksum >= 2:
                self.bad_checksum = 0
                self.initialize()
        else:
            high = resp[2]
            low = resp[3]
            co2 = (high * 256) + low
            self.logger.debug(f"Read measurement via UART: {co2}")
            self.bad_checksum = 0
            return co2

        return None

    def _read_co2_gpio(self):
        # From datasheet:
        # cycle length = 1004ms ± 5%
        # CO2 ppm = 2000 * (Th - 2ms) / (Th + Tl - 4ms)
        try:
            # Wait for edge changes to calculate CO2 values. According to the
            # data sheet the theoretical cycle length is 1004ms ± 5% = 1054ms,
            # so twice that duration (i.e. 2108ms) should be safe to use as a
            # timeout threshold. NOTE: the code below is intentionally
            # duplicated inline to reduce method calls and ensure the most
            # accurate readings can be made.
            if (
                self.gpio.wait_for_edge(
                    self.gpio_location, self.gpio.RISING, timeout=2_2108
                )
                is None
            ):
                raise RuntimeError("Timeout waiting for rising edge!")
            else:
                th_start = time.time_ns() / 1_000

            if (
                self.gpio.wait_for_edge(
                    self.gpio_location, self.gpio.FALLING, timeout=2_2108
                )
                is None
            ):
                raise RuntimeError("Timeout waiting for falling edge!")
            else:
                th_end = time.time_ns() / 1_000

            if (
                self.gpio.wait_for_edge(
                    self.gpio_location, self.gpio.RISING, timeout=2_2108
                )
                is None
            ):
                raise RuntimeError("Timeout waiting for rising edge!")
            else:
                tl_end = time.time_ns() / 1_000

        except RuntimeError as e:
            self.logger.error(f"No response: {e}")
            return None

        th = th_end - th_start
        tl = tl_end - th_end

        co2 = 2_000 * (th - 2) / (th + tl - 4)
        self.logger.debug(f"Read measurement via GPIO: {co2}")
        return co2

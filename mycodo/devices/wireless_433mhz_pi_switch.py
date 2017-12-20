# coding=utf-8
import logging
import sys

from rpi_rf import RFDevice

logger = logging.getLogger("mycodo.device.433mhz_pi_switch")


class Transmit433MHz:
    """Transmit 433MHz commands"""

    def __init__(self, pin, protocol=1, pulse_length=189, bit_length=24):
        self.device = None
        self.pin = pin
        self.protocol = protocol
        self.pulse_length = pulse_length
        self.num = 0
        self.timestamp = None

    def enable_receive(self):
        try:
            self.device = RFDevice(self.pin)
            self.device.enable_rx()
            self.num = 0
        except Exception as err:
            logger.exception(
                "{cls} raised an exception when enabling receiving: "
                "{err}".format(cls=type(self).__name__, err=err))

    def receive_available(self):
        try:
            if self.device.rx_code_timestamp != self.timestamp:
                self.timestamp = self.device.rx_code_timestamp
                command = self.device.rx_code
                pulse_length = self.device.rx_pulselength
                protocol = self.device.rx_proto
                return self.num, command, pulse_length, protocol
            return 0, 0, 0, 0
        except Exception as err:
            logger.exception(
                "{cls} raised an exception when receiving: "
                "{err}".format(cls=type(self).__name__, err=err))

    def transmit(self, cmd):
        try:
            self.device = RCSwitchSender()
            self.device = RFDevice(self.pin)
            self.device.enable_tx()
            self.device.tx_code(cmd, self.protocol, self.pulse_length)
            self.cleanup()
        except Exception as err:
            logger.exception(
                "{cls} raised an exception when transmitting: "
                "{err}".format(cls=type(self).__name__, err=err))

    def cleanup(self):
        self.device.cleanup()


def is_int(test_var, check_range=None):
    """
    Test if var is integer (and also between range)
    check_range should be a list of minimum and maximum values
    e.g. check_range=[0, 100]
    """
    try:
        value = int(test_var)
    except ValueError:
        return False

    if check_range:
        if not (check_range[0] <= int(test_var) <= check_range[1]):
            return False

    return True


def main():
    print(">> pi_switch 433MHz sample code")
    print(">> Send or receive 433MHz commands:")
    print(">>   1. Send command.")
    print(">>   2. Listen for commands.")
    print(">> Pressing ctrl-c to stop")

    cmd_str = input("Select 1 or 2: ")
    if not is_int(cmd_str, check_range=[1, 2]):
        print("Invalid option")
        sys.exit(1)

    if int(cmd_str) == 1:
        pin = input("Pin connected to transmitter: ")
        if not is_int(pin):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        protocol = input("Protocol (Default: 1): ")
        if not is_int(protocol):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        pulse_length = input("Pulse Length (Default: 189): ")
        if not is_int(pulse_length):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        send_str = input("What numerical command to send: ")
        if not is_int(send_str):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        device = Transmit433MHz(int(pin),
                                protocol=int(protocol),
                                pulse_length=int(pulse_length))
        device.transmit(int(send_str))
        print("Command sent: {}".format(int(send_str)))

    elif int(cmd_str) == 2:
        pin = input("Pin connected to receiver: ")
        if not is_int(pin):
            print("Invalid option. Must be integer.")
            sys.exit(1)

        device = Transmit433MHz(int(pin))
        device.enable_receive()
        print("Receiver listening. Press a button on your remote or use your "
              "transmitter near the receiver.")

        try:
            while True:
                num, rec_value, pulse_length, protocol = device.receive_available()
                if rec_value:
                    print("Received[{}]: {}".format(num, rec_value))
                    print("Pulse Length: {}".format(pulse_length))
                    print("Protocol: {}\n".format(protocol))
        except KeyboardInterrupt:
            device.cleanup()

if __name__ == "__main__":
    main()

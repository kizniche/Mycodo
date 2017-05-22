# coding=utf-8
import logging
import sys
from pi_switch import RCSwitchReceiver
from pi_switch import RCSwitchSender

logger = logging.getLogger("mycodo.device.433mhz_pi_switch")


class Transmit433MHz:
    """Transmit 433MHz commands"""

    def __init__(self, pin, protocol=1, pulse_length=189, bit_length=24):
        self.device = None
        self.pin = pin
        self.protocol = protocol
        self.pulse_length = pulse_length
        self.bit_length = bit_length

        self.num = 0

    def enable_receive(self):
        self.device = RCSwitchReceiver()
        self.device.enableReceive(self.pin)
        self.num = 0

    def receive_available(self):
        if self.device.available():
            received_value = self.device.getReceivedValue()
            if received_value:
                self.num += 1
                bit_length = self.device.getReceivedBitlength()
                delay = self.device.getReceivedDelay()
                protocol = self.device.getReceivedProtocol()
                return self.num, received_value, bit_length, delay, protocol
        return 0, 0, 0, 0, 0

    def reset_available(self):
        self.device.resetAvailable()

    def transmit(self, cmd):
        self.device = RCSwitchSender()
        self.device.setProtocol(self.protocol)
        self.device.setPulseLength(self.pulse_length)
        self.device.enableTransmit(self.pin)
        self.device.sendDecimal(cmd, self.bit_length)  # switch on


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

    cmd_str = raw_input("Select 1 or 2: ")
    if not is_int(cmd_str, check_range=[1, 2]):
        print("Invalid option")
        sys.exit(1)

    if int(cmd_str) == 1:
        pin = raw_input("Pin connected to transmitter: ")
        if not is_int(pin):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        protocol = raw_input("Protocol (Default: 1): ")
        if not is_int(protocol):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        pulse_length = raw_input("Pulse Length (Default: 189): ")
        if not is_int(pulse_length):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        bit_length = raw_input("Bit Length (Default: 24): ")
        if not is_int(bit_length):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        send_str = raw_input("What numerical command to send: ")
        if not is_int(send_str):
            print("Invalid option. Must be integer.")
            sys.exit(1)
        device = Transmit433MHz(int(pin),
                                protocol=int(protocol),
                                pulse_length=int(pulse_length),
                                bit_length=int(bit_length))
        device.transmit(int(send_str))
        print("Command sent: {}".format(int(send_str)))

    elif int(cmd_str) == 2:
        pin = raw_input("Pin connected to receiver: ")
        if not is_int(pin):
            print("Invalid option. Must be integer.")
            sys.exit(1)

        device = Transmit433MHz(int(pin))
        device.enable_receive()
        print("Receiver listening. Press a button on your remote or use your "
              "transmitter near the receiver.")

        while True:
            num, rec_value, bit_length, delay, protocol = device.receive_available()
            if rec_value:
                print("Received[{}]: {}".format(num, rec_value))
                print("Bit Length: {} bit".format(bit_length))
                print("Delay: {}".format(delay))
                print("Protocol: {}\n".format(protocol))
            device.reset_available()

if __name__ == "__main__":
    main()

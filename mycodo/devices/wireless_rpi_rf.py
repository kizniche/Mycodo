# coding=utf-8
import argparse
import logging
import time

from rpi_rf import RFDevice

logger = logging.getLogger("mycodo.device.wireless_rpi_rf")


class Transmit433MHz:
    """Transmit/Receive 433MHz commands."""

    def __init__(self, pin, protocol=1, pulse_length=189):
        self.device = None
        self.pin = pin
        self.protocol = protocol
        self.pulse_length = pulse_length
        self.num = 0
        self.timestamp = None
        self.device = RFDevice(self.pin)

    def enable_receive(self):
        try:
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
            self.device.enable_tx()
            self.device.tx_code(cmd, self.protocol, self.pulse_length)
        except Exception as err:
            logger.exception(
                "{cls} raised an exception when transmitting: "
                "{err}".format(cls=type(self).__name__, err=err))

    def cleanup(self):
        self.device.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Sends/Receives a decimal code via a 433/315MHz GPIO device')
    parser.add_argument('-d', dest='direction', type=int, default=2,
                        help="Send (1) or Receive (2) (Default: 2)")
    parser.add_argument('-g', dest='gpio', type=int, default=17,
                        help="GPIO pin (Default: 17)")

    # Send-specific commands
    parser.add_argument('-c', dest='code', type=int, required=False,
                        help="Decimal code to send")
    parser.add_argument('-p', dest='pulselength', type=int, default=None,
                        help="Pulselength (Default: 350)")
    parser.add_argument('-t', dest='protocol', type=int, default=None,
                        help="Protocol (Default: 1)")
    args = parser.parse_args()

    if args.direction == 1:
        rfdevice = RFDevice(args.gpio)
        rfdevice.enable_tx()

        if args.protocol:
            protocol = args.protocol
        else:
            protocol = "default"
        if args.pulselength:
            pulselength = args.pulselength
        else:
            pulselength = "default"

        print(str(args.code) +
              " [protocol: " + str(protocol) +
              ", pulselength: " + str(pulselength) + "]")

        rfdevice.tx_code(args.code, args.protocol, args.pulselength)
        rfdevice.cleanup()

    elif args.direction == 2:
        rfdevice = RFDevice(args.gpio)
        rfdevice.enable_rx()
        timestamp = None
        print("Listening for codes on GPIO " + str(args.gpio))
        try:
            while True:
                if rfdevice.rx_code_timestamp != timestamp:
                    timestamp = rfdevice.rx_code_timestamp
                    print(str(rfdevice.rx_code) +
                          " [pulselength " + str(rfdevice.rx_pulselength) +
                          ", protocol " + str(rfdevice.rx_proto) + "]")
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("Keyboard Interupt")
        finally:
            rfdevice.cleanup()

    else:
        print("Invalid option: '{opt}'. "
              "You may either Send (1) or Receive (2). ".format(
            opt=args.direction))


if __name__ == "__main__":
    main()

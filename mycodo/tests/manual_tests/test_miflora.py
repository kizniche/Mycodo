# coding=utf-8
import argparse
import logging
import sys

import re
from btlewrap import BluepyBackend
from miflora import miflora_scanner
from miflora.miflora_poller import MI_BATTERY
from miflora.miflora_poller import MI_CONDUCTIVITY
from miflora.miflora_poller import MI_LIGHT
from miflora.miflora_poller import MI_MOISTURE
from miflora.miflora_poller import MI_TEMPERATURE
from miflora.miflora_poller import MiFloraPoller

logger = logging.getLogger("mycodo.inputs.miflora")


def poll(args):
    """Poll data from the sensor."""
    poller = MiFloraPoller(args.mac, BluepyBackend)
    print("Getting data from Mi Flora")
    print("FW: {}".format(poller.firmware_version()))
    print("Name: {}".format(poller.name()))
    print("Temperature: {}".format(poller.parameter_value(MI_TEMPERATURE)))
    print("Moisture: {}".format(poller.parameter_value(MI_MOISTURE)))
    print("Light: {}".format(poller.parameter_value(MI_LIGHT)))
    print("Conductivity: {}".format(poller.parameter_value(MI_CONDUCTIVITY)))
    print("Battery: {}".format(poller.parameter_value(MI_BATTERY)))

def scan(args):
    """Scan for sensors."""
    print('Scanning for 10 seconds...')
    devices = miflora_scanner.scan(BluepyBackend, 10)
    print('Found {} devices:'.format(len(devices)))
    for device in devices:
        print('  {}'.format(device))

def valid_miflora_mac(mac, pat=re.compile(r"C4:7C:8D:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
    """Check for valid mac addresses."""
    if not pat.match(mac.upper()):
        raise argparse.ArgumentTypeError('The MAC address "{}" seems to be in the wrong format'.format(mac))
    return mac

def main():
    """Main function. Mostly parsing the command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_const', const=True)
    subparsers = parser.add_subparsers(help='sub-command help', )

    parser_poll = subparsers.add_parser('poll', help='poll data from a sensor')
    parser_poll.add_argument('mac', type=valid_miflora_mac)
    parser_poll.set_defaults(func=poll)

    parser_scan = subparsers.add_parser('scan', help='scan for devices')
    parser_scan.set_defaults(func=scan)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == '__main__':
    main()

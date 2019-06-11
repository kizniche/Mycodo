# coding=utf-8
import argparse
import logging
from ruuvitag_sensor.ruuvitag import RuuviTag

logging.getLogger('ruuvitag_sensor').setLevel(logging.CRITICAL)


def parseargs(parser):
    parser.add_argument('--mac_address', nargs=1,
                        metavar='ID', type=str,
                        help='MAC address of RuuviTag',
                        required=True)
    parser.add_argument('--bt_adapter', nargs=1,
                        metavar='ID', type=str,
                        help='Bluetooth adapter to use (/dev/hci[x], where x is the adapter number)',
                        required=True)
    return parser.parse_args()


if __name__ == "__main__":
    parse = argparse.ArgumentParser(description="Receive latest measurement from RuuviTag")
    args = parseargs(parse)
    try:
        bt_device = 'hci{}'.format(args.bt_adapter[0])
        sensor = RuuviTag(args.mac_address[0], bt_device=bt_device)
        state = sensor.update()
        state = sensor.state

        if state:
            result = "{temp},{hum},{press},{bat},{accel},{accel_x},{accel_y},{accel_z}".format(
                temp=state['temperature'],
                hum=state['humidity'],
                press=state['pressure'],
                bat=state['battery'],
                accel=state['acceleration'],
                accel_x=state['acceleration_x'],
                accel_y=state['acceleration_y'],
                accel_z=state['acceleration_z'])
            print(result, end='')
    except:
        pass

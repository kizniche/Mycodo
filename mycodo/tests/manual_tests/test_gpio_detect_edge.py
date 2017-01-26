#!/usr/bin/python
# coding=utf-8

import argparse
import RPi.GPIO as GPIO
import os
import sys
import time


class EdgeDetect(object):
    def __init__(self, pin, rising):
        self.count = 0
        self.pin = pin
        self.running = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        if rising:
            self.gpio_detect = GPIO.RISING
            self.detect_dir = 'Rising'
        else:
            self.gpio_detect = GPIO.FALLING
            self.detect_dir = 'Falling'
        self.active_timer = time.time()

    def run(self):
        try:
            GPIO.add_event_detect(self.pin, self.gpio_detect, callback=self.edge)
            while self.running:
                # GPIO.wait_for_edge(self.pin, GPIO.FALLING)
                time.sleep(1)
        except KeyboardInterrupt:
            print("Quit")
            GPIO.cleanup()

    def edge(self):
        if time.time() > self.active_timer:
            self.active_timer = time.time() + 10
            self.count += 1
            print("{dir} Edge Detected, {count}".format(dir=self.detect_dir, count=self.count))


def menu():
    parser = argparse.ArgumentParser(
        description='Watch GPIO pin to detect edge (falling edge). This can '
                    'be a switch, hall effect sensor, float sensor, motion '
                    'sensor, or anything that merely completes a circuit. Be '
                    'sure to add a pull up or down resistor (depending on the '
                    'device), because internal resistors are not enabled.')
    parser.add_argument('-g', '--gpio', metavar='GPIO', type=int,
                        help='The GPIO (BCM numbering) connected to the device.',
                        required=True)
    parser.add_argument('-r', '--rising', metavar='RISING', action='store_true',
                        help='Detect rising edge instead of falling edge. If '
                             'not set, a falling edge will be used.')

    args = parser.parse_args()

    if not 0 < args.gpio < 40:
        print('Error: Invalid GPIO pin.\n')
        sys.exit(1)

    print("Use CTRL+C to Quit.")
    time.sleep(2)
    print("Ready")
    ed = EdgeDetect(args.gpio, args.rising)
    ed.run()


if __name__ == "__main__":
    # Check for root privileges
    if not os.geteuid() == 0:
        sys.exit("Script must be executed as root")
    menu()

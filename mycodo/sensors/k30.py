# coding=utf-8

import os
import serial
import time
from lockfile import LockFile
import RPi.GPIO as GPIO

K30_LOCK_FILE = "/var/lock/sensor-k30"


class K30(object):
    def __init__(self):
        self._co2 = None
        self.running = True
        if GPIO.RPI_INFO['P1_REVISION'] == 3:
            self.serial_device = "/dev/ttyS0"
        else:
            self.serial_device = "/dev/ttyAMA0"

    def read(self):
        lock = LockFile(K30_LOCK_FILE)
        try:
            # Acquire lock on K30 to ensure more than one read isn't
            # being attempted at once.
            while not lock.i_am_locking():
                try:
                    lock.acquire(timeout=60)  # wait up to 60 seconds before breaking lock
                except:
                    lock.break_lock()
                    lock.acquire()
            self._co2 = self.get_measurement()
            lock.release()
        except:
            lock.release()
            return 1

    def get_measurement(self):
        ser = serial.Serial(self.serial_device, timeout=1)  # Wait 1 second for reply
        ser.flushInput()
        time.sleep(1)
        ser.write("\xFE\x44\x00\x08\x02\x9F\x25")
        time.sleep(.01)
        resp = ser.read(7)
        if len(resp) == 0:
            co2 = None
        else:
            high = ord(resp[3])
            low = ord(resp[4])
            co2 = (high * 256) + low
        return co2

    @property
    def co2(self):
        return self._co2

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return co2 information.
        """
        if self.read():
            return None
        response = {
            'co2': self.co2
        }
        return response

    def stopSensor(self):
        self.running = False



if __name__ == "__main__":
    k30 = K30()

    for measurement in k30:
        print("CO2: {} ppmv".format(measurement['co2']))
        time.sleep(2)

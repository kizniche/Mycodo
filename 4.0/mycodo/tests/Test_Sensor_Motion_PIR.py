# coding=utf-8

import RPi.GPIO as GPIO
import time


class Motion(object):
    def __init__(self, pin):
        self.count = 0
        self.pin = pin
        self.running = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        self.active_timer = time.time()

    def run(self):
        try:
            GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.motion)
            while self.running:
                # GPIO.wait_for_edge(self.pin, GPIO.FALLING)
                time.sleep(1)
        except KeyboardInterrupt:
            print("Quit")
            GPIO.cleanup()

    def motion(self, pin):
        if time.time() > self.active_timer:
            self.active_timer = time.time() + 10
            self.count += 1
            print("Motion Detected {}".format(self.count))

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    print("Use CTRL+C to Quit.")
    time.sleep(2)
    print("Ready")
    # Be sure to add a pull up or down resistor (depending on the device)
    # Change '19' to the GPIO connected to your motion signal pin
    motion = Motion(19)
    motion.run()

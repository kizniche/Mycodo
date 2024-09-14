# coding=utf-8
import datetime
import threading
import time

from mycodo.databases.models import Trigger
from mycodo.inputs.base_input import AbstractInput
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import write_influxdb_value

# Measurements
measurements_dict = {
    0: {
        'measurement': 'edge',
        'unit': 'bool'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'EDGE',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'Edge Detection',
    'input_library': 'RPi.GPIO',
    'measurements_name': 'Rising/Falling Edge',
    'measurements_dict': measurements_dict,

    'edge_input': True,  # Treat as an Edge Detection Input

    'options_enabled': [
        'gpio_location',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'pin_mode',
            'type': 'select',
            'default_value': 'floating',
            'options_select': [
                ('floating', 'Floating'),
                ('pull_down', 'Pull Down'),
                ('pull_up', 'Pull Up')
            ],
            'name': 'Pin Mode',
            'phrase': 'Enables or disables the pull-up or pull-down resistor'
        }
    ]

}

class InputModule(AbstractInput):
    """A sensor support class that listens for rising or falling pin edge events."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.GPIO = None
        self.gpio_location = None
        self.switch_bouncetime = None
        self.switch_edge = None
        self.switch_reset_period = None
        self.control = None
        self.switch_edge_gpio = None
        self.edge_reset_timer = time.time()
        self.pin_mode = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        try:
            import RPi.GPIO as GPIO

            self.GPIO = GPIO

            self.gpio_location = self.input_dev.gpio_location
            self.switch_bouncetime = self.input_dev.switch_bouncetime
            self.switch_edge = self.input_dev.switch_edge
            self.switch_reset_period = self.input_dev.switch_reset_period
            self.control = DaemonControl()

            if self.switch_edge == 'rising':
                self.switch_edge_gpio = GPIO.RISING
            elif self.switch_edge == 'falling':
                self.switch_edge_gpio = GPIO.FALLING
            else:
                self.switch_edge_gpio = GPIO.BOTH

            self.GPIO.setmode(GPIO.BCM)

            if self.pin_mode == "pull_down":
                self.logger.debug("Pull-DOWN enabled for pin {ch}".format(ch=self.gpio_location))
                self.GPIO.setup(int(self.gpio_location), self.GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            elif self.pin_mode == "pull_up":
                self.logger.debug("Pull-UP enabled for pin {ch}".format(ch=self.gpio_location))
                self.GPIO.setup(int(self.gpio_location), self.GPIO.IN, pull_up_down=GPIO.PUD_UP)
            else:
                self.GPIO.setup(int(self.gpio_location), self.GPIO.IN)

        except:
            self.logger.exception("Setting up Input")

    def listener(self):
        self.GPIO.add_event_detect(
            int(self.gpio_location),
            self.switch_edge_gpio,
            callback=self.edge_detected,
            bouncetime=self.switch_bouncetime)

    def edge_detected(self, bcm_pin):
        """
        Callback function from GPIO.add_event_detect() for when an edge is detected

        Write rising (1) or falling (-1) edge to influxdb database
        Trigger any conditionals that match the rising/falling/both edge

        :param bcm_pin: BMC pin of rising/falling edge (required parameter)
        :return: None
        """
        try:
            gpio_state = self.GPIO.input(int(self.gpio_location))
        except:
            self.logger.exception("RPi.GPIO and Raspberry Pi required")
            gpio_state = None

        self.logger.debug("Edge detected on pin {ch}: {state}".format(ch=self.gpio_location, state=gpio_state))

        if gpio_state is not None and time.time() > self.edge_reset_timer:
            self.edge_reset_timer = time.time() + self.switch_reset_period

            if (self.switch_edge == 'rising' or
                    (self.switch_edge == 'both' and gpio_state)):
                rising_or_falling = 1  # Rising edge detected
                state_str = 'Rising'
            else:
                rising_or_falling = -1  # Falling edge detected
                state_str = 'Falling'

            write_db = threading.Thread(
                target=write_influxdb_value,
                args=(self.unique_id, measurements_dict[0]['unit'], rising_or_falling,),
                kwargs={'channel': 0,
                        'measure': measurements_dict[0]['measurement'],
                        'timestamp': datetime.datetime.utcnow()})
            write_db.start()

            trigger = db_retrieve_table_daemon(Trigger)
            trigger = trigger.filter(Trigger.trigger_type == 'trigger_edge')
            trigger = trigger.filter(Trigger.measurement == self.unique_id)
            trigger = trigger.filter(Trigger.is_activated.is_(True))

            for each_trigger in trigger.all():
                if each_trigger.edge_detected in ['both', state_str.lower()]:
                    now = time.time()
                    timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H-%M-%S')
                    message = "{ts}\n[Trigger {cid} ({cname})] " \
                              "Input {oid} ({name}) {state} edge detected " \
                              "on pin {pin} (BCM)".format(
                                    ts=timestamp,
                                    cid=each_trigger.id,
                                    cname=each_trigger.name,
                                    oid=self.unique_id,
                                    name=self.input_dev.name,
                                    state=state_str,
                                    pin=bcm_pin)
                    self.logger.debug("Edge: {}".format(message))

                    self.control.trigger_all_actions(
                        each_trigger.unique_id, message=message)

    def stop_input(self):
        """Called when Input is deactivated."""
        self.running = False
        try:
            self.logger.debug("Cleaning up GPIO")
            self.GPIO.remove_event_detect(int(self.gpio_location))
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.cleanup(int(self.gpio_location))
        except:
            self.logger.exception("RPi.GPIO and Raspberry Pi required")

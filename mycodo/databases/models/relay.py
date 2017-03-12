# coding=utf-8
from RPi import GPIO

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Relay(CRUDMixin, db.Model):
    __tablename__ = "relay"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default='Relay')
    pin = db.Column(db.Integer, default=0)
    amps = db.Column(db.Float, default=0.0)  # The current drawn by the device connected to the relay
    trigger = db.Column(db.Boolean, default=True)  # GPIO output to turn relay on (True=HIGH, False=LOW)
    on_at_start = db.Column(db.Boolean, default=False)  # Turn relay on when daemon starts?
    on_until = db.Column(db.DateTime, default=None)  # Stores time to turn off relay (if on for a duration)
    last_duration = db.Column(db.Float, default=None)  # Stores the last on duration (seconds)
    on_duration = db.Column(db.Boolean, default=None)  # Stores if the relay is currently on for a duration

    def __reper__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

    @staticmethod
    def _is_setup():
        """
        This function checks to see if the GPIO pin is setup and ready to use.  This is for safety
        and to make sure we don't blow anything.

        # TODO Make it do that.

        :return: Is it safe to manipulate this relay?
        :rtype: bool
        """
        return True

    def setup_pin(self):
        """
        Setup pin for this relay

        :rtype: None
        """
        # TODO add some extra checks here.  Maybe verify BCM?
        GPIO.setup(self.pin, GPIO.OUT)

    def turn_off(self):
        """
        Turn this relay off

        :rtype: None
        """
        if self._is_setup():
            self.on_duration = False
            self.on_until = datetime.datetime.now()
            GPIO.output(self.pin, not self.trigger)

    def turn_on(self):
        """
        Turn this relay on

        :rtype: None
        """
        if self._is_setup():
            GPIO.output(self.pin, self.trigger)

    def is_on(self):
        """
        :return: Whether the relay is currently "ON"
        :rtype: bool
        """
        return self.trigger == GPIO.input(self.pin)


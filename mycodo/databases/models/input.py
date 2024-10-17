# -*- coding: utf-8 -*-
from sqlalchemy.dialects.mysql import LONGTEXT

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma


class Input(CRUDMixin, db.Model):
    __tablename__ = "input"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    device = db.Column(db.Text, default='')  # Device name, such as DHT11, DHT22, DS18B20
    is_activated = db.Column(db.Boolean, default=False)

    name = db.Column(db.Text, default='Input Name')
    position_y = db.Column(db.Integer, default=0)
    log_level_debug = db.Column(db.Boolean, default=False)
    is_preset = db.Column(db.Boolean, default=False)  # Is config saved as a preset?
    preset_name = db.Column(db.Text, default=None)  # Name for preset
    interface = db.Column(db.Text, default=None)  # Communication interface (I2C, UART, etc.)
    period = db.Column(db.Float, default=15.0)  # Duration between readings
    start_offset = db.Column(db.Float, default=0.0)
    power_output_id = db.Column(db.String(36), default=None)
    resolution = db.Column(db.Integer, default=0)
    resolution_2 = db.Column(db.Integer, default=0)
    sensitivity = db.Column(db.Integer, default=0)
    thermocouple_type = db.Column(db.Text, default=None)
    ref_ohm = db.Column(db.Integer, default=None)
    calibrate_sensor_measure = db.Column(db.Text, default=None)  # sensor ID and measurement (CSV)

    location = db.Column(db.Text, default='')  # GPIO pin or i2c address to communicate with sensor
    gpio_location = db.Column(db.Integer, default=0)  # Pin location for GPIO communication

    # I2C
    i2c_location = db.Column(db.Text, default=None)  # Address location for I2C communication
    i2c_bus = db.Column(db.Integer, default=1)  # I2C bus the sensor is connected to

    # FTDI
    ftdi_location = db.Column(db.Text, default=None)  # Device location for FTDI communication

    # Communication (SPI)
    uart_location = db.Column(db.Text, default=None)  # Device location for UART communication
    baud_rate = db.Column(db.Integer, default=None)  # Baud rate for UART communication
    pin_clock = db.Column(db.Integer, default=None)
    pin_cs = db.Column(db.Integer, default=None)
    pin_mosi = db.Column(db.Integer, default=None)
    pin_miso = db.Column(db.Integer, default=None)

    # Communication (Bluetooth)
    bt_adapter = db.Column(db.Text, default='hci0')

    # Switch options
    switch_edge = db.Column(db.Text, default='rising')
    switch_bouncetime = db.Column(db.Integer, default=50)
    switch_reset_period = db.Column(db.Integer, default=10)

    # Pre-measurement output options
    pre_output_id = db.Column(db.String(36), default=None)  # Output to turn on before sensor read
    pre_output_duration = db.Column(db.Float, default=10.0)  # Duration to turn output on before sensor read
    pre_output_during_measure = db.Column(db.Boolean, default=True)

    # SHT sensor options
    sht_voltage = db.Column(db.Text, default='3.5')

    # Analog to digital converter options
    adc_gain = db.Column(db.Integer, default=1)
    adc_resolution = db.Column(db.Integer, default=18)
    adc_sample_speed = db.Column(db.Text, default='')

    # Command options
    cmd_command = db.Column(db.Text, default=None)

    # PWM and RPM options
    weighting = db.Column(db.Float, default=0.0)
    rpm_pulses_per_rev = db.Column(db.Float, default=1.0)
    sample_time = db.Column(db.Float, default=2.0)

    # Server options
    port = db.Column(db.Integer, default=80)
    times_check = db.Column(db.Integer, default=1)
    deadline = db.Column(db.Integer, default=2)

    # The Things Network: Data Storage
    datetime = db.Column(db.DateTime, default=None)

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')

    def is_active(self):
        """
        :return: Whether the sensor is currently activated
        :rtype: bool
        """
        return self.is_activated

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class InputSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Input


class InputChannel(CRUDMixin, db.Model):
    __tablename__ = "input_channel"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    input_id = db.Column(db.String(36), default=None)
    channel = db.Column(db.Integer, default=None)
    name = db.Column(db.Text, default='')

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class InputChannelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = InputChannel

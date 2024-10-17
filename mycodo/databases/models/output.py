# coding=utf-8
from sqlalchemy.dialects.mysql import LONGTEXT

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma


class Output(CRUDMixin, db.Model):
    __tablename__ = "output"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    output_type = db.Column(db.Text, default='wired')  # Options: 'command', 'wired', 'wireless_rpi_rf', 'pwm'
    name = db.Column(db.Text, default='Output')
    position_y = db.Column(db.Integer, default=0)
    size_y = db.Column(db.Integer, default=2)
    log_level_debug = db.Column(db.Boolean, default=False)

    # Interface options
    interface = db.Column(db.Text, default='')
    location = db.Column(db.Text, default='')

    # I2C
    i2c_location = db.Column(db.Text, default=None)  # Address location for I2C communication
    i2c_bus = db.Column(db.Integer, default='')  # I2C bus the sensor is connected to

    # FTDI
    ftdi_location = db.Column(db.Text, default=None)  # Device location for FTDI communication

    # SPI
    uart_location = db.Column(db.Text, default=None)  # Device location for UART communication
    baud_rate = db.Column(db.Integer, default=None)  # Baud rate for UART communication

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')

    # TODO; Delete at next major version
    # No longer used
    pin = db.Column(db.Integer, default=None)
    on_state = db.Column(db.Boolean, default=True)
    amps = db.Column(db.Float, default=0.0)
    on_until = db.Column(db.DateTime, default=None)
    off_until = db.Column(db.DateTime, default=None)
    last_duration = db.Column(db.Float, default=None)
    on_duration = db.Column(db.Boolean, default=None)
    protocol = db.Column(db.Integer, default=None)
    pulse_length = db.Column(db.Integer, default=None)
    linux_command_user = db.Column(db.Text, default=None)
    on_command = db.Column(db.Text, default=None)
    off_command = db.Column(db.Text, default=None)
    pwm_command = db.Column(db.Text, default=None)
    force_command = db.Column(db.Boolean, default=False)
    trigger_functions_at_start = db.Column(db.Boolean, default=True)
    state_startup = db.Column(db.Text, default=None)
    startup_value = db.Column(db.Float, default=0)
    state_shutdown = db.Column(db.Text, default=None)
    shutdown_value = db.Column(db.Float, default=0)
    pwm_hertz = db.Column(db.Integer, default=None)
    pwm_library = db.Column(db.Text, default=None)
    pwm_invert_signal = db.Column(db.Boolean, default=False)
    flow_rate = db.Column(db.Float, default=None)
    output_mode = db.Column(db.Text, default=None)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class OutputSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Output


class OutputChannel(CRUDMixin, db.Model):
    __tablename__ = "output_channel"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    output_id = db.Column(db.Text, default=None)
    channel = db.Column(db.Integer, default=None)
    name = db.Column(db.Text, default='')

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class OutputChannelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OutputChannel

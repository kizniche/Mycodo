# coding=utf-8
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class Conditional(CRUDMixin, db.Model):
    __tablename__ = "conditional"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Conditional Name')
    conditional_type = db.Column(db.Text, default=None)
    is_activated = db.Column(db.Boolean, default=False)

    # TODO: Make one variable 'unique_id' instead of non-unique ID, in next major version
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), default=None)  # Which sensor does this belong?
    math_id = db.Column(db.Integer, db.ForeignKey('math.id'), default=None)  # Which sensor does this belong?

    # Relay options
    if_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Watch this relay for action
    if_relay_state = db.Column(db.Text, default='')  # What action to watch relay for
    if_relay_duration = db.Column(db.Float, default=0.0)

    # Sunrise/sunset
    rise_or_set = db.Column(db.Text, default='sunrise')
    latitude = db.Column(db.Float, default=33.749249)
    longitude = db.Column(db.Float, default=-84.387314)
    zenith = db.Column(db.Float, default=90.8)
    date_offset_days = db.Column(db.Integer, default=0)
    time_offset_minutes = db.Column(db.Integer, default=0)

    # Sensor/Math options
    # TODO: Make variable names more generic in next major version change sensor->measurement
    if_sensor_period = db.Column(db.Float, default=60.0)
    if_sensor_refractory_period = db.Column(db.Float, default=0.0)
    if_sensor_measurement = db.Column(db.Text, default='')  # which measurement to monitor
    if_sensor_max_age = db.Column(db.Integer, default=120.0)  # max age of the measurement
    if_sensor_edge_detected = db.Column(db.Text, default='')
    if_sensor_direction = db.Column(db.Text, default='')  # 'above' or 'below' setpoint
    if_sensor_setpoint = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class ConditionalActions(CRUDMixin, db.Model):
    __tablename__ = "conditional_data"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    conditional_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)

    # Actions
    do_action = db.Column(db.Text, default='')  # what action, such as 'email', 'execute command', 'flash LCD'
    do_action_string = db.Column(db.Text, default='')  # string, such as the email address or command
    do_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)
    do_relay_state = db.Column(db.Text, default='')  # 'on' or 'off'
    do_relay_duration = db.Column(db.Float, default=0.0)
    do_relay_pwm = db.Column(db.Float, default=0.0)

    do_camera_id = db.Column(db.Integer, db.ForeignKey('lcd.id'), default=None)
    do_camera_duration = db.Column(db.Float, default=0.0)
    do_lcd_id = db.Column(db.Integer, db.ForeignKey('lcd.id'), default=None)
    do_pid_id = db.Column(db.Integer, db.ForeignKey('pid.id'), default=None)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


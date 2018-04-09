# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Conditional(CRUDMixin, db.Model):
    __tablename__ = "conditional"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Conditional Name')
    conditional_type = db.Column(db.Text, default=None)
    is_activated = db.Column(db.Boolean, default=False)

    unique_id_1 = db.Column(db.String, default=None)

    # Relay options
    output_state = db.Column(db.Text, default='')  # What action to watch output for
    output_duration = db.Column(db.Float, default=0.0)

    # Sunrise/sunset
    rise_or_set = db.Column(db.Text, default='sunrise')
    latitude = db.Column(db.Float, default=33.749249)
    longitude = db.Column(db.Float, default=-84.387314)
    zenith = db.Column(db.Float, default=90.8)
    date_offset_days = db.Column(db.Integer, default=0)
    time_offset_minutes = db.Column(db.Integer, default=0)

    # Sensor/Math options
    period = db.Column(db.Float, default=60.0)
    refractory_period = db.Column(db.Float, default=0.0)
    measurement = db.Column(db.Text, default='')  # which measurement to monitor
    max_age = db.Column(db.Integer, default=120.0)  # max age of the measurement
    edge_detected = db.Column(db.Text, default='')
    direction = db.Column(db.Text, default='')  # 'above' or 'below' setpoint
    setpoint = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

class ConditionalActions(CRUDMixin, db.Model):
    __tablename__ = "conditional_data"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    conditional_id = db.Column(db.String, db.ForeignKey('output.unique_id'), default=None)

    # Actions
    do_unique_id = db.Column(db.Text, default='')
    do_action = db.Column(db.Text, default='')  # what action, such as 'email', 'execute command', 'flash LCD'
    do_action_string = db.Column(db.Text, default='')  # string, such as the email address or command
    do_output_state = db.Column(db.Text, default='')  # 'on' or 'off'
    do_output_duration = db.Column(db.Float, default=0.0)
    do_output_pwm = db.Column(db.Float, default=0.0)
    do_camera_duration = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


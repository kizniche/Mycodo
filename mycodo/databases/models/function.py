# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Function(CRUDMixin, db.Model):
    __tablename__ = "function"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    function_type = db.Column(db.Text, default='')
    name = db.Column(db.Text, default='Function Name')


class Conditional(CRUDMixin, db.Model):
    __tablename__ = "conditional"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Conditional')

    is_activated = db.Column(db.Boolean, default=False)
    conditional_statement = db.Column(db.Text, default='')
    period = db.Column(db.Float, default=60.0)
    refractory_period = db.Column(db.Float, default=0.0)
    start_offset = db.Column(db.Float, default=10.0)


class ConditionalConditions(CRUDMixin, db.Model):
    __tablename__ = "conditional_data"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    conditional_id = db.Column(db.String, db.ForeignKey('conditional.unique_id'), default=None)
    condition_type = db.Column(db.Text, default=None)

    # Sensor/Math
    measurement = db.Column(db.Text, default='')  # which measurement to monitor
    max_age = db.Column(db.Integer, default=120)  # max age of the measurement

    # GPIO State
    gpio_pin = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class Trigger(CRUDMixin, db.Model):
    __tablename__ = "trigger"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    trigger_type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default='Trigger Name')
    is_activated = db.Column(db.Boolean, default=False)

    # Used to hold unique IDs
    unique_id_1 = db.Column(db.String, default=None)
    unique_id_2 = db.Column(db.String, default=None)

    # Output
    output_state = db.Column(db.Text, default='')  # What action to watch output for
    output_duration = db.Column(db.Float, default=0.0)
    output_duty_cycle = db.Column(db.Float, default=0.0)

    # Sunrise/sunset
    rise_or_set = db.Column(db.Text, default='sunrise')
    latitude = db.Column(db.Float, default=33.749249)
    longitude = db.Column(db.Float, default=-84.387314)
    zenith = db.Column(db.Float, default=90.8)
    date_offset_days = db.Column(db.Integer, default=0)
    time_offset_minutes = db.Column(db.Integer, default=0)

    # Timer
    period = db.Column(db.Float, default=60.0)
    timer_start_offset = db.Column(db.Integer, default=0)
    timer_start_time = db.Column(db.Text, default='16:30')
    timer_end_time = db.Column(db.Text, default='19:00')

    # Receive infrared from remote
    program = db.Column(db.Text, default='mycodo')
    word = db.Column(db.Text, default='button_a')

    # Method
    method_start_time = db.Column(db.Text, default=None)
    method_end_time = db.Column(db.Text, default=None)
    trigger_actions_at_period = db.Column(db.Boolean, default=True)
    trigger_actions_at_start = db.Column(db.Boolean, default=True)

    # Edge
    measurement = db.Column(db.Text, default='')
    edge_detected = db.Column(db.Text, default='')


class Actions(CRUDMixin, db.Model):
    __tablename__ = "function_actions"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    function_id = db.Column(db.String, default=None)
    function_type = db.Column(db.Text, default='')
    action_type = db.Column(db.Text, default='')  # what action, such as 'email', 'execute command', 'flash LCD'

    # Actions
    pause_duration = db.Column(db.Float, default=5.0)
    do_unique_id = db.Column(db.Text, default='')
    do_action_string = db.Column(db.Text, default='')  # string, such as the email address or command
    do_output_state = db.Column(db.Text, default='')  # 'on' or 'off'
    do_output_duration = db.Column(db.Float, default=0.0)
    do_output_pwm = db.Column(db.Float, default=0.0)
    do_camera_duration = db.Column(db.Float, default=5.0)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

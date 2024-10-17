# coding=utf-8
from sqlalchemy.dialects.mysql import LONGTEXT

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma


class Function(CRUDMixin, db.Model):
    __tablename__ = "function"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    function_type = db.Column(db.Text, default='')
    name = db.Column(db.Text, default='Function Name')
    position_y = db.Column(db.Integer, default=0)
    log_level_debug = db.Column(db.Boolean, default=False)


class Conditional(CRUDMixin, db.Model):
    __tablename__ = "conditional"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Conditional')
    position_y = db.Column(db.Integer, default=0)

    is_activated = db.Column(db.Boolean, default=False)
    log_level_debug = db.Column(db.Boolean, default=False)
    conditional_statement = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')
    conditional_import = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')
    conditional_initialize = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')
    conditional_status = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')
    period = db.Column(db.Float, default=60.0)
    start_offset = db.Column(db.Float, default=10.0)
    pyro_timeout = db.Column(db.Float, default=30.0)
    use_pylint = db.Column(db.Boolean, default=True)
    message_include_code = db.Column(db.Boolean, default=False)

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')


class ConditionalConditions(CRUDMixin, db.Model):
    __tablename__ = "conditional_data"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    conditional_id = db.Column(db.String(36), default=None)
    condition_type = db.Column(db.Text, default=None)

    # Sensor
    measurement = db.Column(db.Text, default='')  # which measurement to monitor
    max_age = db.Column(db.Integer, default=120)  # max age of the measurement

    # GPIO State
    gpio_pin = db.Column(db.Integer, default=0)

    # Output State
    output_id = db.Column(db.String(36), default='')

    # Controller
    controller_id = db.Column(db.String(36), default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class Trigger(CRUDMixin, db.Model):
    __tablename__ = "trigger"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    trigger_type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default='Trigger Name')
    position_y = db.Column(db.Integer, default=0)
    is_activated = db.Column(db.Boolean, default=False)
    log_level_debug = db.Column(db.Boolean, default=False)

    # Used to hold unique IDs
    unique_id_1 = db.Column(db.String(36), default=None)
    unique_id_2 = db.Column(db.String(36), default=None)
    unique_id_3 = db.Column(db.String(36), default=None)

    # Output
    output_state = db.Column(db.Text, default='')  # What action to watch output for
    output_duration = db.Column(db.Float, default=0.0)
    output_duty_cycle = db.Column(db.Float, default=0.0)

    # Sunrise/sunset
    rise_or_set = db.Column(db.Text, default='sunrise')
    latitude = db.Column(db.Float, default=33.749249)
    longitude = db.Column(db.Float, default=-84.387314)
    date_offset_days = db.Column(db.Integer, default=0)
    time_offset_minutes = db.Column(db.Integer, default=0)

    # Timer
    period = db.Column(db.Float, default=60.0)
    timer_start_offset = db.Column(db.Integer, default=0)
    timer_start_time = db.Column(db.Text, default='16:30')
    timer_end_time = db.Column(db.Text, default='19:00')

    # Receive infrared from remote (deprecated, TODO: remove)
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

    # Unused  TODO: remove
    zenith = db.Column(db.Float, default=90.8)


class TriggerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Trigger


class Actions(CRUDMixin, db.Model):
    __tablename__ = "function_actions"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    function_id = db.Column(db.String(36), default=None)
    function_type = db.Column(db.Text, default='')
    action_type = db.Column(db.Text, default='')  # what action, such as 'email', 'execute command', 'flash LCD'

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='{}')

    # Actions
    pause_duration = db.Column(db.Float, default=5.0)
    do_unique_id = db.Column(db.String(36), default='')
    do_action_string = db.Column(db.Text, default='')  # string, such as the email address or command
    do_output_state = db.Column(db.Text, default='')  # 'on' or 'off'
    do_output_amount = db.Column(db.Float, default=0.0)
    do_output_duration = db.Column(db.Float, default=0.0)
    do_output_pwm = db.Column(db.Float, default=0.0)
    do_output_pwm2 = db.Column(db.Float, default=0.0)
    do_camera_duration = db.Column(db.Float, default=5.0)

    # Infrared remote send (deprecated, TODO: remove)
    remote = db.Column(db.Text, default='my_remote')
    code = db.Column(db.Text, default='KEY_A')
    send_times = db.Column(db.Integer, default=1)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

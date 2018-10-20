# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


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

    # Method
    method_start_time = db.Column(db.Text, default=None)
    method_end_time = db.Column(db.Text, default=None)
    trigger_actions_at_period = db.Column(db.Boolean, default=True)
    trigger_actions_at_start = db.Column(db.Boolean, default=True)

    # Edge
    edge_detected = db.Column(db.Text, default='')
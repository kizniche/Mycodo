# coding=utf-8
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid


class PID(CRUDMixin, db.Model):
    __tablename__ = "pid"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default='PID')
    is_activated = db.Column(db.Boolean, default=False)
    is_held = db.Column(db.Boolean, default=False)
    is_paused = db.Column(db.Boolean, default=False)
    is_preset = db.Column(db.Boolean, default=False)  # Is config saved as a preset?
    preset_name = db.Column(db.Text, default='')  # Name for preset
    period = db.Column(db.Float, default=30.0)
    max_measure_age = db.Column(db.Float, default=120.0)
    measurement = db.Column(db.Text, default='')  # What condition is the controller regulating?
    direction = db.Column(db.Text, default='Raise')  # Direction of regulation (raise, lower, both)
    setpoint = db.Column(db.Float, default=30.0)  # PID setpoint
    method_id = db.Column(db.Integer, db.ForeignKey('method.id'), default=None)
    method_start_time = db.Column(db.Text, default=None)
    method_end_time = db.Column(db.Text, default=None)
    p = db.Column(db.Float, default=1.0)  # Kp gain
    i = db.Column(db.Float, default=0.0)  # Ki gain
    d = db.Column(db.Float, default=0.0)  # Kd gain
    integrator_min = db.Column(db.Float, default=-100.0)
    integrator_max = db.Column(db.Float, default=100.0)
    raise_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Relay to raise the condition
    raise_min_duration = db.Column(db.Float, default=0.0)
    raise_max_duration = db.Column(db.Float, default=0.0)
    raise_min_off_duration = db.Column(db.Float, default=0.0)
    lower_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Relay to lower the condition
    lower_min_duration = db.Column(db.Float, default=0.0)
    lower_max_duration = db.Column(db.Float, default=0.0)
    lower_min_off_duration = db.Column(db.Float, default=0.0)

    def __reper__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

# -*- coding: utf-8 -*-
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class SensorConditional(CRUDMixin, db.Model):
    __tablename__ = "sensorconditional"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Sensor Cond')
    is_activated = db.Column(db.Integer, default=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), default=None)
    period = db.Column(db.Float, default=60.0)
    measurement = db.Column(db.Text, default='')  # which measurement to monitor
    edge_select = db.Column(db.Text, default='edge')  # monitor Rising, Falling, or Both switch edges
    edge_detected = db.Column(db.Text, default='rising')
    gpio_state = db.Column(db.Boolean, default=True)
    direction = db.Column(db.Text, default='')  # 'above' or 'below' setpoint
    setpoint = db.Column(db.Float, default=0.0)
    relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)
    relay_state = db.Column(db.Text, default='')  # 'on' or 'off'
    relay_on_duration = db.Column(db.Float, default=0.0)
    execute_command = db.Column(db.Text, default='')
    email_notify = db.Column(db.Text, default='')
    flash_lcd = db.Column(db.Text, default='')
    camera_record = db.Column(db.Text, default='')

    def __reper__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

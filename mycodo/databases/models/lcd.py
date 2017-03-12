# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.mycodo_flask.extensions import db


class LCD(CRUDMixin, db.Model):
    __tablename__ = "lcd"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='LCD')
    is_activated = db.Column(db.Boolean, default=False)
    period = db.Column(db.Integer, default=30)
    location = db.Column(db.Text, default='27')
    multiplexer_address = db.Column(db.Text, default='')
    multiplexer_channel = db.Column(db.Integer, default=0)
    x_characters = db.Column(db.Integer, default=16)
    y_lines = db.Column(db.Integer, default=2)
    line_1_sensor_id = db.Column(db.Text, default='')
    line_1_measurement = db.Column(db.Text, default='')
    line_2_sensor_id = db.Column(db.Text, default='')
    line_2_measurement = db.Column(db.Text, default='')
    line_3_sensor_id = db.Column(db.Text, default='')
    line_3_measurement = db.Column(db.Text, default='')
    line_4_sensor_id = db.Column(db.Text, default='')
    line_4_measurement = db.Column(db.Text, default='')

    def __reper__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

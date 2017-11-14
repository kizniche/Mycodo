# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.mycodo_flask.extensions import db


class LCD(CRUDMixin, db.Model):
    __tablename__ = "lcd"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='LCD')
    is_activated = db.Column(db.Boolean, default=False)
    period = db.Column(db.Float, default=30.0)
    location = db.Column(db.Text, default='27')
    i2c_bus = db.Column(db.Integer, default=1)
    multiplexer_address = db.Column(db.Text, default='')
    multiplexer_channel = db.Column(db.Integer, default=0)
    x_characters = db.Column(db.Integer, default=16)
    y_lines = db.Column(db.Integer, default=2)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class LCDData(CRUDMixin, db.Model):
    __tablename__ = "lcd_data"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    lcd_id = db.Column(db.Integer, db.ForeignKey('lcd.id'), default=None)
    line_1_id = db.Column(db.Text, default='')
    line_1_type = db.Column(db.Text, default='')
    line_1_measurement = db.Column(db.Text, default='')
    line_2_id = db.Column(db.Text, default='')
    line_2_type = db.Column(db.Text, default='')
    line_2_measurement = db.Column(db.Text, default='')
    line_3_id = db.Column(db.Text, default='')
    line_3_type = db.Column(db.Text, default='')
    line_3_measurement = db.Column(db.Text, default='')
    line_4_id = db.Column(db.Text, default='')
    line_4_type = db.Column(db.Text, default='')
    line_4_measurement = db.Column(db.Text, default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

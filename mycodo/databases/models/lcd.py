# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class LCD(CRUDMixin, db.Model):
    __tablename__ = "lcd"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    lcd_type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default='LCD')
    is_activated = db.Column(db.Boolean, default=False)
    period = db.Column(db.Float, default=30.0)
    location = db.Column(db.Text, default=None)
    i2c_bus = db.Column(db.Integer, default=1)
    x_characters = db.Column(db.Integer, default=16)
    y_lines = db.Column(db.Integer, default=2)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class LCDData(CRUDMixin, db.Model):
    __tablename__ = "lcd_data"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    lcd_id = db.Column(db.String, db.ForeignKey('lcd.unique_id'), default=None)
    line_1_id = db.Column(db.Text, default='')
    line_1_type = db.Column(db.Text, default='')
    line_1_measurement = db.Column(db.Text, default='')
    line_1_max_age = db.Column(db.Integer, default=360)
    line_1_decimal_places = db.Column(db.Integer, default=2)
    line_2_id = db.Column(db.Text, default='')
    line_2_type = db.Column(db.Text, default='')
    line_2_measurement = db.Column(db.Text, default='')
    line_2_max_age = db.Column(db.Integer, default=360)
    line_2_decimal_places = db.Column(db.Integer, default=2)
    line_3_id = db.Column(db.Text, default='')
    line_3_type = db.Column(db.Text, default='')
    line_3_measurement = db.Column(db.Text, default='')
    line_3_max_age = db.Column(db.Integer, default=360)
    line_3_decimal_places = db.Column(db.Integer, default=2)
    line_4_id = db.Column(db.Text, default='')
    line_4_type = db.Column(db.Text, default='')
    line_4_measurement = db.Column(db.Text, default='')
    line_4_max_age = db.Column(db.Integer, default=360)
    line_4_decimal_places = db.Column(db.Integer, default=2)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

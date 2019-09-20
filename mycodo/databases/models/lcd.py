# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class LCD(CRUDMixin, db.Model):
    __tablename__ = "lcd"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    pin_reset = db.Column(db.Integer, default=None)
    lcd_type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default='LCD')
    is_activated = db.Column(db.Boolean, default=False)
    log_level_debug = db.Column(db.Boolean, default=False)
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
    line_1_text = db.Column(db.Text, default='Text to display')
    line_1_measurement = db.Column(db.Text, default='')
    line_1_max_age = db.Column(db.Integer, default=360)
    line_1_decimal_places = db.Column(db.Integer, default=2)

    line_2_id = db.Column(db.Text, default='')
    line_2_text = db.Column(db.Text, default='Text to display')
    line_2_measurement = db.Column(db.Text, default='')
    line_2_max_age = db.Column(db.Integer, default=360)
    line_2_decimal_places = db.Column(db.Integer, default=2)

    line_3_id = db.Column(db.Text, default='')
    line_3_text = db.Column(db.Text, default='Text to display')
    line_3_measurement = db.Column(db.Text, default='')
    line_3_max_age = db.Column(db.Integer, default=360)
    line_3_decimal_places = db.Column(db.Integer, default=2)

    line_4_id = db.Column(db.Text, default='')
    line_4_text = db.Column(db.Text, default='Text to display')
    line_4_measurement = db.Column(db.Text, default='')
    line_4_max_age = db.Column(db.Integer, default=360)
    line_4_decimal_places = db.Column(db.Integer, default=2)

    line_5_id = db.Column(db.Text, default='')
    line_5_text = db.Column(db.Text, default='Text to display')
    line_5_measurement = db.Column(db.Text, default='')
    line_5_max_age = db.Column(db.Integer, default=360)
    line_5_decimal_places = db.Column(db.Integer, default=2)

    line_6_id = db.Column(db.Text, default='')
    line_6_text = db.Column(db.Text, default='Text to display')
    line_6_measurement = db.Column(db.Text, default='')
    line_6_max_age = db.Column(db.Integer, default=360)
    line_6_decimal_places = db.Column(db.Integer, default=2)

    line_7_id = db.Column(db.Text, default='')
    line_7_text = db.Column(db.Text, default='Text to display')
    line_7_measurement = db.Column(db.Text, default='')
    line_7_max_age = db.Column(db.Integer, default=360)
    line_7_decimal_places = db.Column(db.Integer, default=2)

    line_8_id = db.Column(db.Text, default='')
    line_8_text = db.Column(db.Text, default='Text to display')
    line_8_measurement = db.Column(db.Text, default='')
    line_8_max_age = db.Column(db.Integer, default=360)
    line_8_decimal_places = db.Column(db.Integer, default=2)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

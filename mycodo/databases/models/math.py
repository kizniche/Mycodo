# -*- coding: utf-8 -*-
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Math(CRUDMixin, db.Model):
    __tablename__ = "math"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Input Name')
    math_type = db.Column(db.Text, default=None)
    is_activated = db.Column(db.Boolean, default=False)
    period = db.Column(db.Float, default=15.0)  # Duration between readings
    max_measure_age = db.Column(db.Integer, default=60)

    # Difference options
    difference_reverse_order = db.Column(db.Boolean, default=False)  # False: var1 - var2 or True: var2 - var1
    difference_absolute = db.Column(db.Boolean, default=False)

    # Equation
    equation_input = db.Column(db.Text, default='')
    equation = db.Column(db.Text, default='x*1')

    # Verification options
    max_difference = db.Column(db.Float, default=10.0)  # Maximum difference between any measurements

    # Multi-input options
    inputs = db.Column(db.Text, default='')

    # Humidity calculation
    dry_bulb_t_id = db.Column(db.Text, default=None)
    dry_bulb_t_measure = db.Column(db.Text, default=None)
    wet_bulb_t_id = db.Column(db.Text, default=None)
    wet_bulb_t_measure = db.Column(db.Text, default=None)
    pressure_pa_id = db.Column(db.Text, default=None)
    pressure_pa_measure = db.Column(db.Text, default=None)

    def is_active(self):
        """
        :return: Whether the sensor is currently activated
        :rtype: bool
        """
        return self.is_activated

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class MathMeasurements(CRUDMixin, db.Model):
    __tablename__ = "math_measurements"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)

    name = db.Column(db.Text, default='')
    math_id = db.Column(db.Text, db.ForeignKey('math.unique_id'), default=None)

    # Default measurement/unit
    is_enabled = db.Column(db.Boolean, default=True)
    measurement = db.Column(db.Text, default='')
    unit = db.Column(db.Text, default='')
    channel = db.Column(db.Integer, default=None)
    single_channel = db.Column(db.Boolean, default=None)

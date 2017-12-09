# -*- coding: utf-8 -*-
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid


class Math(CRUDMixin, db.Model):
    __tablename__ = "math"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default='Input Name')
    math_type = db.Column(db.Text, default=None)
    is_activated = db.Column(db.Boolean, default=False)
    period = db.Column(db.Float, default=15.0)  # Duration between readings
    inputs = db.Column(db.Text, default='')
    max_measure_age = db.Column(db.Integer, default=60.0)
    measure = db.Column(db.Text, default='Measurement')
    measure_units = db.Column(db.Text, default='unit')
    max_difference = db.Column(db.Float, default=10.0)  # Maximum difference between any measurements
    
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
        return is_activated

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=__class__.__name__)

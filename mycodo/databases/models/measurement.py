# coding=utf-8
from marshmallow_sqlalchemy.fields import Nested

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma


class Measurement(CRUDMixin, db.Model):
    __tablename__ = "measurements"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name_safe = db.Column(db.Text)
    name = db.Column(db.Text)
    units = db.Column(db.Text)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class MeasurementSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Measurement


class Unit(CRUDMixin, db.Model):
    __tablename__ = "units"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name_safe = db.Column(db.Text)
    name = db.Column(db.Text)
    unit = db.Column(db.Text)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class UnitSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Unit


class Conversion(CRUDMixin, db.Model):
    __tablename__ = "conversion"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    convert_unit_from = db.Column(db.Text)
    convert_unit_to = db.Column(db.Text)
    equation = db.Column(db.Text)
    protected = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class ConversionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Conversion


class DeviceMeasurements(CRUDMixin, db.Model):
    __tablename__ = "device_measurements"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)

    name = db.Column(db.Text, default='')
    device_type = db.Column(db.Text, default=None)
    device_id = db.Column(db.String(36), default=None)

    # Default measurement/unit
    is_enabled = db.Column(db.Boolean, default=True)
    measurement = db.Column(db.Text, default='')
    measurement_type = db.Column(db.Text, default='')
    unit = db.Column(db.Text, default='')
    channel = db.Column(db.Integer, default=None)

    # Rescale measurement
    rescale_method = db.Column(db.Text, default='linear')
    rescale_equation = db.Column(db.Text, default='(x+2)*3')
    invert_scale = db.Column(db.Boolean, default=False)
    rescaled_measurement = db.Column(db.Text, default='')
    rescaled_unit = db.Column(db.Text, default='')
    scale_from_min = db.Column(db.Float, default=0)
    scale_from_max = db.Column(db.Float, default=10)
    scale_to_min = db.Column(db.Float, default=0)
    scale_to_max = db.Column(db.Float, default=20)

    conversion_id = db.Column(db.String(36), default='')


class DeviceMeasurementsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DeviceMeasurements

    conversion = Nested(ConversionSchema)

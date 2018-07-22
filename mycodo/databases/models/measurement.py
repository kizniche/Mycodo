# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Measurement(CRUDMixin, db.Model):
    __tablename__ = "measurements"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name_safe = db.Column(db.Text)
    name = db.Column(db.Text)
    units = db.Column(db.Text)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class Unit(CRUDMixin, db.Model):
    __tablename__ = "units"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name_safe = db.Column(db.Text)
    name = db.Column(db.Text)
    unit = db.Column(db.Text)


    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

class Conversion(CRUDMixin, db.Model):
    __tablename__ = "conversion"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    convert_unit_from = db.Column(db.Text)
    convert_unit_to = db.Column(db.Text)
    equation = db.Column(db.Text)


    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Conditional(CRUDMixin, db.Model):
    __tablename__ = "conditional"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Conditional')

    is_activated = db.Column(db.Boolean, default=False)
    conditional_statement = db.Column(db.Text, default='')
    period = db.Column(db.Float, default=60.0)
    refractory_period = db.Column(db.Float, default=0.0)


class ConditionalConditions(CRUDMixin, db.Model):
    __tablename__ = "conditional"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    conditional_id = db.Column(db.String, db.ForeignKey('conditional.unique_id'), default=None)
    condition_type = db.Column(db.Text, default=None)

    # Used to hold unique IDs
    unique_id_1 = db.Column(db.String, default=None)
    unique_id_2 = db.Column(db.String, default=None)

    # Sensor/Math
    measurement = db.Column(db.Text, default='')  # which measurement to monitor
    max_age = db.Column(db.Integer, default=120)  # max age of the measurement

    # GPIO State
    gpio_pin = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


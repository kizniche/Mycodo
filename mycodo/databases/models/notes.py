# coding=utf-8
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid


class Notes(CRUDMixin, db.Model):
    __tablename__ = "notes"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default=None)
    tags = db.Column(db.Text, default=None)
    files = db.Column(db.Text, default=None)
    note = db.Column(db.Text, default=None)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class NoteTags(CRUDMixin, db.Model):
    __tablename__ = "note_tags"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default=None)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

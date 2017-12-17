# coding=utf-8
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class DisplayOrder(CRUDMixin, db.Model):
    __tablename__ = "displayorder"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    graph = db.Column(db.Text, default='')
    lcd = db.Column(db.Text, default='')
    math = db.Column(db.Text, default='')
    method = db.Column(db.Text, default='')
    pid = db.Column(db.Text, default='')
    relay = db.Column(db.Text, default='')
    remote_host = db.Column(db.Text, default='')
    sensor = db.Column(db.Text, default='')
    timer = db.Column(db.Text, default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

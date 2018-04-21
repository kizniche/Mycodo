# coding=utf-8
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class DisplayOrder(CRUDMixin, db.Model):
    __tablename__ = "displayorder"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    conditional = db.Column(db.Text, default='')
    dashboard = db.Column(db.Text, default='')
    lcd = db.Column(db.Text, default='')
    math = db.Column(db.Text, default='')
    method = db.Column(db.Text, default='')
    pid = db.Column(db.Text, default='')
    output = db.Column(db.Text, default='')
    remote_host = db.Column(db.Text, default='')
    inputs = db.Column(db.Text, default='')
    timer = db.Column(db.Text, default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

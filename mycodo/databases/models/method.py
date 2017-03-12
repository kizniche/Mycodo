# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.mycodo_flask.extensions import db


class Method(CRUDMixin, db.Model):
    __tablename__ = "method"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Method')
    method_type = db.Column(db.Text, default='')
    method_order = db.Column(db.Text, default='')
    start_time = db.Column(db.Text, default=None)

    def __reper__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

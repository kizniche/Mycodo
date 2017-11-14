# -*- coding: utf-8 -*-
from mycodo.databases import CRUDMixin
from mycodo.mycodo_flask.extensions import db


class Remote(CRUDMixin, db.Model):
    __tablename__ = "remote"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    is_activated = db.Column(db.Boolean, default=False)
    host = db.Column(db.Text, default='')
    username = db.Column(db.Text, default='')
    password_hash = db.Column(db.Text, default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

# -*- coding: utf-8 -*-
from mycodo.databases import CRUDMixin
from mycodo.mycodo_flask.extensions import db


class SMTP(CRUDMixin, db.Model):
    __tablename__ = "smtp"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    host = db.Column(db.Text, default='smtp.gmail.com')
    protocol = db.Column(db.Text, default='ssl')
    port = db.Column(db.Integer, default=None)
    user = db.Column(db.Text, default='email@gmail.com')
    passw = db.Column(db.Text, default='password')
    email_from = db.Column(db.Text, default='email@gmail.com')
    hourly_max = db.Column(db.Integer, default=5)
    email_count = db.Column(db.Integer, default=0)
    smtp_wait_timer = db.Column(db.Integer, default=0)

    # TODO: Remove unused columns, below
    ssl = db.Column(db.Boolean, default=None)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

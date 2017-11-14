# -*- coding: utf-8 -*-
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class Timer(CRUDMixin, db.Model):
    __tablename__ = "timer"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Timer')
    is_activated = db.Column(db.Boolean, default=False)
    timer_type = db.Column(db.Text, default=None)
    method_id = db.Column(db.Integer, default=None)  # TODO: Add ForeignKey in next major release
    method_start_time = db.Column(db.Text, default=None)
    method_end_time = db.Column(db.Text, default=None)
    method_period = db.Column(db.Float, default=None)
    relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)
    state = db.Column(db.Text, default=None)  # 'on' or 'off'
    time_start = db.Column(db.Text, default=None)
    time_end = db.Column(db.Text, default=None)
    duration_on = db.Column(db.Float, default=None)
    duration_off = db.Column(db.Float, default=None)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

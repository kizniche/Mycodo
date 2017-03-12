# -*- coding: utf-8 -*-
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class RelayConditional(CRUDMixin, db.Model):
    __tablename__ = "relayconditional"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Relay Cond')
    is_activated = db.Column(db.Boolean, default=False)
    if_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Watch this relay for action
    if_action = db.Column(db.Text, default='')  # What action to watch relay for
    if_duration = db.Column(db.Float, default=0.0)
    do_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'),
                            default=None)  # Actuate relay if conditional triggered
    do_action = db.Column(db.Text, default='')  # what action, such as email, execute command, flash LCD
    do_action_data = db.Column(db.Text, default='')  # string, such as email address, command, or duration

    def __reper__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

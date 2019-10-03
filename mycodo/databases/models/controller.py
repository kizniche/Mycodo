# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class CustomController(CRUDMixin, db.Model):
    __tablename__ = "custom_controller"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Conditional')
    device = db.Column(db.Text, default='')

    is_activated = db.Column(db.Boolean, default=False)
    log_level_debug = db.Column(db.Boolean, default=False)

    custom_options = db.Column(db.Text, default='')

    def is_active(self):
        """
        :return: Whether the sensor is currently activated
        :rtype: bool
        """
        return self.is_activated

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

# coding=utf-8
from sqlalchemy.dialects.mysql import LONGTEXT

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma


class CustomController(CRUDMixin, db.Model):
    __tablename__ = "custom_controller"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Custom Function')
    position_y = db.Column(db.Integer, default=0)
    device = db.Column(db.Text, default='')

    is_activated = db.Column(db.Boolean, default=False)
    log_level_debug = db.Column(db.Boolean, default=False)

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')

    def is_active(self):
        """
        :return: Whether the Controller is currently activated
        :rtype: bool
        """
        return self.is_activated

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class FunctionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CustomController


class FunctionChannel(CRUDMixin, db.Model):
    __tablename__ = "function_channel"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    function_id = db.Column(db.String(36), default=None)
    channel = db.Column(db.Integer, default=None)
    name = db.Column(db.Text, default='')

    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class FunctionChannelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FunctionChannel

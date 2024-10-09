# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Role(CRUDMixin, db.Model):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}
    # __abstract__ = True

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.String(36), nullable=False, unique=True)
    edit_settings = db.Column(db.Boolean, nullable=False, default=False)
    edit_controllers = db.Column(db.Boolean, nullable=False, default=False)
    edit_users = db.Column(db.Boolean, nullable=False, default=False)
    view_settings = db.Column(db.Boolean, nullable=False, default=False)
    view_camera = db.Column(db.Boolean, nullable=False, default=False)
    view_stats = db.Column(db.Boolean, nullable=False, default=False)
    view_logs = db.Column(db.Boolean, nullable=False, default=False)
    reset_password = db.Column(db.Boolean, nullable=False, default=False)

    # user = db.relationship("User", back_populates="roles")

    def __repr__(self):
        return "<{cls}(id={s.id}, name='{s.name}')>".format(s=self, cls=self.__class__.__name__)

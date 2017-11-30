# coding=utf-8
import bcrypt

from flask_login import UserMixin
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class User(UserMixin, CRUDMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(64), unique=True, index=True)
    password_hash = db.Column(db.VARCHAR(255))
    email = db.Column(db.VARCHAR(64), unique=True, index=True)
    role = db.Column(db.Integer, db.ForeignKey('roles.id'), default=None)
    theme = db.Column(db.VARCHAR(64))
    language = db.Column(db.Text, default=None)  # Force the web interface to use a specific language

    roles = db.relationship("Role", back_populates="user")

    def __repr__(self):
        output = "<User: <name='{name}', email='{email}' is_admin='{isadmin}'>"
        return output.format(name=self.name, email=self.email, isadmin=bool(self.role == 1))

    def set_password(self, new_password):
        """ saves a password hash  """
        self.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def check_password(password, hashed_password):
        """ validates a password """
        hashes_match = bcrypt.hashpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        return hashes_match

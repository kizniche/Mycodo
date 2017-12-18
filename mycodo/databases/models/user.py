# coding=utf-8
import bcrypt

from flask_login import UserMixin
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin


class User(UserMixin, CRUDMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    # __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(64), unique=True, index=True)
    password_hash = db.Column(db.VARCHAR(255))
    email = db.Column(db.VARCHAR(64), unique=True, index=True)
    role = db.Column(db.Integer, db.ForeignKey('roles.id'), default=None)
    theme = db.Column(db.VARCHAR(64))
    language = db.Column(db.Text, default=None)  # Force the web interface to use a specific language

    # roles = db.relationship("Role", back_populates="user")

    def __repr__(self):
        output = "<User: <name='{name}', email='{email}' is_admin='{isadmin}'>"
        return output.format(name=self.name, email=self.email, isadmin=bool(self.role == 1))

    def set_password(self, new_password):
        """ saves a password hash  """
        self.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def check_password(password, hashed_password):
        """ validates a password """
        # Check type of password hashed_password to determine if it should be encoded or decoded
        if isinstance(password, str):
            password = password.encode('utf-8')
        # elif isinstance(password, bytes):
        #     password = password.decode('utf-8')
            
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        # elif isinstance(hashed_password, bytes):
        #     hashed_password = hashed_password.decode('utf-8')
        hashes_match = bcrypt.hashpw(password, hashed_password)
        return hashes_match

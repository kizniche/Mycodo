# coding=utf-8
import bcrypt
from flask_login import UserMixin

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma


class User(UserMixin, CRUDMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.VARCHAR(64), unique=True, index=True)
    password_hash = db.Column(db.VARCHAR(255))
    code = db.Column(db.Integer, default=None)
    api_key = db.Column(db.BLOB, unique=True)
    email = db.Column(db.VARCHAR(64), unique=True, index=True)
    role_id = db.Column(db.Integer, default=None)
    theme = db.Column(db.VARCHAR(64))
    landing_page = db.Column(db.Text, default='live')
    index_page = db.Column(db.Text, default='landing')
    language = db.Column(db.Text, default=None)  # Force the web interface to use a specific language
    password_reset_code = db.Column(db.Text, default=None)
    password_reset_code_expiration = db.Column(db.DateTime, default=None)
    password_reset_last_request = db.Column(db.DateTime, default=None)

    def __repr__(self):
        output = "<User: <name='{name}', email='{email}' is_admin='{isadmin}'>"
        return output.format(name=self.name, email=self.email, isadmin=bool(self.role_id == 1))

    def set_password(self, new_password):
        """saves a password hash  """
        if isinstance(new_password, str):
            new_password = new_password.encode('utf-8')
        self.password_hash = bcrypt.hashpw(new_password, bcrypt.gensalt())

    @staticmethod
    def check_password(password, hashed_password):
        """validates a password."""
        # Check type of password hashed_password to determine if it is a str
        # and should be encoded
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')

        hashes_match = bcrypt.hashpw(password, hashed_password)
        return hashes_match


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        exclude = ('api_key', 'password_hash',)

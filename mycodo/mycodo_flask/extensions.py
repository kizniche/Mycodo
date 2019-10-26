# coding=utf-8
"""
The Flask extensions module contains extensions like Flask SQLAlchemy
which requires a flask context in order to operate.

These extensions are instantiated here and imported into the modules
that require them.  The extensions themselves are configured at run
time when the application factory in mycodo_flask initializes them
and adds it's configuration to them.
"""
from flask import app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow  # must be imported after SQLAlchemy

db = SQLAlchemy()
ma = Marshmallow(app)

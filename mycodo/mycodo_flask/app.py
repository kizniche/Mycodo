# coding=utf-8
#
#  app.py - Flask web server for Mycodo, for visualizing data,
#           configuring the system, and controlling the daemon.
#

import logging

import base64
import flask_login
from flask import Flask
from flask import flash
from flask import redirect
from flask import request
from flask import url_for
from flask_babel import Babel
from flask_babel import gettext
from flask_compress import Compress
from flask_limiter import Limiter
from flask_restful import Api
from flask_sslify import SSLify

from mycodo.config import LANGUAGES
from mycodo.config import ProdConfig
from mycodo.databases.models import Misc
from mycodo.databases.models import User
from mycodo.databases.models import populate_db
from mycodo.databases.utils import session_scope
from mycodo.mycodo_flask import routes_admin
from mycodo.mycodo_flask import routes_authentication
from mycodo.mycodo_flask import routes_calibration
from mycodo.mycodo_flask import routes_general
from mycodo.mycodo_flask import routes_method
from mycodo.mycodo_flask import routes_page
from mycodo.mycodo_flask import routes_remote_admin
from mycodo.mycodo_flask import routes_settings
from mycodo.mycodo_flask import routes_static
from mycodo.mycodo_flask.api import Inputs
from mycodo.mycodo_flask.api import Users
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma
from mycodo.mycodo_flask.utils.utils_general import get_ip_address

logger = logging.getLogger(__name__)


def create_app(config=ProdConfig):
    """
    Application factory:
        http://flask.pocoo.org/docs/0.11/patterns/appfactories/

    :param config: configuration object that holds config constants
    :returns: Flask
    """
    app = Flask(__name__)
    app.config.from_object(config)

    register_extensions(app)
    register_blueprints(app)

    return app


def register_extensions(app):
    """ register extensions to the app """
    app.jinja_env.add_extension('jinja2.ext.do')  # Global values in jinja

    db.init_app(app)  # Influx db time-series database
    ma.init_app(app)

    app = extension_api(app)  # API
    app = extension_babal(app)  # Language translations
    app = extension_compress(app)  # Compress app responses with gzip
    app = extension_limiter(app)  # Limit authentication blueprint requests to 200 per minute
    app = extension_login_manager(app)  # User login management

    # Create and populate database if it doesn't exist
    with app.app_context():
        db.create_all()
        populate_db()

        # This is disabled because there's a bug that messes up user databases
        # The upgrade script will execute alembic to upgrade the database
        # alembic_upgrade_db()

    # Check user option to force all web connections to use SSL
    # Fail if the URI is empty (pytest is running)
    if app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
        with session_scope(app.config['SQLALCHEMY_DATABASE_URI']) as new_session:
            misc = new_session.query(Misc).first()
            if misc and misc.force_https:
                SSLify(app)


def register_blueprints(app):
    """ register blueprints to the app """
    app.register_blueprint(routes_admin.blueprint)  # register admin views
    app.register_blueprint(routes_authentication.blueprint)  # register login/logout views
    app.register_blueprint(routes_calibration.blueprint)  # register calibration views
    app.register_blueprint(routes_general.blueprint)  # register general routes
    app.register_blueprint(routes_method.blueprint)  # register method views
    app.register_blueprint(routes_page.blueprint)  # register page views
    app.register_blueprint(routes_remote_admin.blueprint)  # register remote admin views
    app.register_blueprint(routes_settings.blueprint)  # register settings views
    app.register_blueprint(routes_static.blueprint)  # register static routes


def extension_babal(app):
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        try:
            user = User.query.filter(
                User.id == flask_login.current_user.id).first()
            if user and user.language != '':
                for key in LANGUAGES:
                    if key == user.language:
                        return key
        # Bypass endpoint test error "'AnonymousUserMixin' object has no attribute 'id'"
        except AttributeError:
            pass
        return request.accept_languages.best_match(LANGUAGES.keys())

    return app


def extension_api(app):
    api = Api(app)
    api.add_resource(Inputs, '/get_inputs')
    api.add_resource(Users, '/get_users')
    return app


def extension_compress(app):
    compress = Compress()
    compress.init_app(app)
    return app


def extension_limiter(app):
    limiter = Limiter(app, key_func=get_ip_address)
    limiter.limit("200/minute")(routes_authentication.blueprint)
    return app


def extension_login_manager(app):
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def user_loader(user_id):
        user = User.query.filter(User.id == user_id).first()
        if not user:
            return
        return user

    @login_manager.request_loader
    def load_user_from_request(req):
        try:  # first, try to login using the api_key url arg
            api_key = req.args.get('api_key')
            api_key = base64.b64decode(api_key)
            if api_key:
                user = User.query.filter_by(api_key=api_key).first()
                if user:
                    return user
        except:
            pass

        try:  # next, try to login using Basic Auth
            api_key = req.headers.get('Authorization')
            api_key = api_key.replace('Basic ', '', 1)
            api_key = base64.b64decode(api_key)
            user = User.query.filter_by(api_key=api_key).first()
            if user:
                return user
        except:
            pass

        # return None if both methods did not login the user
        return None

    @login_manager.unauthorized_handler
    def unauthorized():
        flash(gettext('Please log in to access this page'), "error")
        return redirect(url_for('routes_authentication.do_login'))

    return app

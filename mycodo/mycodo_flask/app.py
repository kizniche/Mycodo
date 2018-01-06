# coding=utf-8
#
#  app.py - Flask web server for Mycodo, for visualizing data,
#           configuring the system, and controlling the daemon.
#

import datetime
import sys

import flask_login
import os
from flask import Flask
from flask import flash
from flask import redirect
from flask import request
from flask import url_for
from flask_babel import Babel
from flask_babel import gettext
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sslify import SSLify
from werkzeug.contrib.profiler import MergeStream
from werkzeug.contrib.profiler import ProfilerMiddleware

from mycodo.config import INSTALL_DIRECTORY
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
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.routes_general import influx_db
from mycodo.utils.system_pi import assure_path_exists


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

    # Uncomment to enable profiler
    # See scripts/profile_analyzer.py to analyze output
    # app = setup_profiler(app)

    # Check user option to force all web connections to use SSL
    # If URI is empty, pytest is running, don't query database
    if app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
        with session_scope(app.config['SQLALCHEMY_DATABASE_URI']) as new_session:
            misc = new_session.query(Misc).first()
            if misc and misc.force_https:
                SSLify(app)

    compress = Compress()
    compress.init_app(app)

    db.init_app(app)
    influx_db.init_app(app)  # attach influx db

    # Limit authentication blueprint requests to 60 per minute
    limiter = Limiter(app, key_func=get_remote_address)
    limiter.limit("60/minute")(routes_authentication.blueprint)

    # Translations
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

    # Login Manager
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def user_loader(user_id):
        user = User.query.filter(User.id == user_id).first()
        if not user:
            return
        return user

    @login_manager.unauthorized_handler
    def unauthorized():
        flash(gettext('Please log in to access this page'), "error")
        return redirect(url_for('routes_authentication.do_login'))

    with app.app_context():
        db.create_all()
        populate_db()

        # This is disabled because there's a bug that messes up user databases
        # The upgrade script will execute alembic to upgrade the database
        # alembic_upgrade_db()


def register_blueprints(_app):
    """ register blueprints to the app """
    _app.register_blueprint(routes_admin.blueprint)  # register admin views
    _app.register_blueprint(routes_authentication.blueprint)  # register login/logout views
    _app.register_blueprint(routes_calibration.blueprint)  # register calibration views
    _app.register_blueprint(routes_general.blueprint)  # register general routes
    _app.register_blueprint(routes_method.blueprint)  # register method views
    _app.register_blueprint(routes_page.blueprint)  # register page views
    _app.register_blueprint(routes_remote_admin.blueprint)  # register remote admin views
    _app.register_blueprint(routes_settings.blueprint)  # register settings views
    _app.register_blueprint(routes_static.blueprint)  # register static routes


def setup_profiler(app):
    """
    Set up a profiler
    Outputs to file and stream
    See profile_analyzer.py in Mycodo/mycodo/scripts/
    """
    app.config['PROFILE'] = True
    new = 'profile-{dt:%Y-%m-%d_%H:%M:%S}'.format(
        dt=datetime.datetime.now())
    profile_path = assure_path_exists(os.path.join(INSTALL_DIRECTORY, new))
    profile_log = os.path.join(profile_path, 'profile.log')
    profile_log_file = open(profile_log, 'w')
    stream = MergeStream(sys.stdout, profile_log_file)
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, stream, restrictions=[30])
    return app

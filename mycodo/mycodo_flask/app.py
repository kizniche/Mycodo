# coding=utf-8
#
#  app.py - Flask web server for Mycodo
#
import base64
import logging
import os

import flask_login
from flask import Flask, flash, redirect, request, url_for
from flask_babel import Babel, gettext
from flask_compress import Compress
from flask_limiter import Limiter
from flask_login import current_user
from flask_session import Session
from flask_talisman import Talisman

from mycodo.config import INSTALL_DIRECTORY, LANGUAGES, ProdConfig
from mycodo.databases.models import Misc, User, Widget, populate_db
from mycodo.databases.utils import session_scope
from mycodo.mycodo_flask import (routes_admin, routes_authentication,
                                 routes_dashboard, routes_function,
                                 routes_general, routes_input, routes_method,
                                 routes_output, routes_page,
                                 routes_password_reset, routes_remote_admin,
                                 routes_settings, routes_static)
from mycodo.mycodo_flask.api import api_blueprint, init_api
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import get_ip_address
from mycodo.utils.layouts import update_layout
from mycodo.utils.widgets import parse_widget_information

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
    register_widget_endpoints(app)

    return app


def register_extensions(app):
    """register extensions to the app."""
    app.jinja_env.add_extension('jinja2.ext.do')  # Global values in jinja

    db.init_app(app)  # Influx db time-series database

    init_api(app)

    app = extension_babel(app)  # Language translations
    app = extension_compress(app)  # Compress app responses with gzip
    app = extension_limiter(app)  # Limit authentication blueprint requests to 200 per minute
    app = extension_login_manager(app)  # User login management
    app = extension_session(app)  # Server side session

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
            if misc:
                # Ensure layout.html is present, by generating it at startup
                update_layout(misc.custom_layout)

                if misc.force_https:
                    csp = {'default-src': ['*', '\'unsafe-inline\'', '\'unsafe-eval\'']}
                    Talisman(app, content_security_policy=csp)


def register_blueprints(app):
    """register blueprints to the app."""
    app.register_blueprint(routes_admin.blueprint)  # register admin views
    app.register_blueprint(routes_authentication.blueprint)  # register login/logout views
    app.register_blueprint(routes_password_reset.blueprint)  # register password reset views
    app.register_blueprint(routes_dashboard.blueprint)  # register dashboard views
    app.register_blueprint(routes_function.blueprint)  # register function views
    app.register_blueprint(routes_general.blueprint)  # register general routes
    app.register_blueprint(routes_input.blueprint)  # register input routes
    app.register_blueprint(routes_method.blueprint)  # register method views
    app.register_blueprint(routes_output.blueprint)  # register output views
    app.register_blueprint(routes_page.blueprint)  # register page views
    app.register_blueprint(routes_remote_admin.blueprint)  # register remote admin views
    app.register_blueprint(routes_settings.blueprint)  # register settings views
    app.register_blueprint(routes_static.blueprint)  # register static routes


def register_widget_endpoints(app):
    try:
        if app.config['TESTING']:  # TODO: Add pytest endpoint test and remove this
            return

        dict_widgets = parse_widget_information()

        with session_scope(app.config['SQLALCHEMY_DATABASE_URI']) as new_session:
            widget = new_session.query(Widget).all()
            widget_types = []
            for each_widget in widget:
                if each_widget.graph_type not in widget_types:
                    widget_types.append(each_widget.graph_type)

            for each_widget_type in widget_types:
                if each_widget_type in dict_widgets and 'endpoints' in dict_widgets[each_widget_type]:
                    for rule, endpoint, view_func, methods in dict_widgets[each_widget_type]['endpoints']:
                        if endpoint in app.view_functions:
                            logger.info(
                                "Endpoint {} ({}) already exists. Not adding.".format(
                                    endpoint, rule))
                        else:
                            logger.info(
                                "Adding endpoint {} ({}).".format(endpoint, rule))
                            app.add_url_rule(rule, endpoint, view_func, methods=methods)
    except:
        logger.exception("Adding Widget Endpoints")


def extension_babel(app):
    def get_locale():
        # Check if a user is logged in and a language is set
        try:
            user = User.query.filter(
                User.id == flask_login.current_user.id).first()
            if user and user.language != '':
                for key in LANGUAGES:
                    if key == user.language:
                        return key
        except AttributeError:  # Bypass endpoint test error "'AnonymousUserMixin' object has no attribute 'id'"
            pass

        # Check the session for a language
        try:
            from flask import session
            if session.get("language") and session['language'] in LANGUAGES:
                return session['language']
        except:
            pass

        # Check for the presence of Mycodo/.language with a language
        try:
            lang_path = os.path.join(INSTALL_DIRECTORY, ".language")
            if os.path.exists(lang_path):
                with open(lang_path) as f:
                    language = f.read().split(":")[0]
                    if language and language in LANGUAGES:
                        return language
        except:
            pass

        return request.accept_languages.best_match(LANGUAGES.keys())
    
    babel = Babel(app, locale_selector=get_locale)
    return app


def extension_compress(app):
    compress = Compress()
    compress.init_app(app)
    return app


def extension_limiter(app):
    def get_key_func():
        """Custom key_func for flask-limiter to handle both logged-in and logged-out requests."""
        if get_ip_address():
            str_return = get_ip_address()
        else:
            str_return = '0.0.0.0'
        if current_user and hasattr(current_user, 'name'):
            str_return += f'/{current_user.name}'
        return str_return

    limiter = Limiter(app=app, key_func=get_key_func, headers_enabled=True)
    limiter.limit("300/hour")(routes_authentication.blueprint)
    limiter.limit("20/hour")(routes_password_reset.blueprint)
    limiter.limit("200/minute")(api_blueprint)
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
            api_key = req.args.get('api_key').replace(' ', '+')
            api_key = base64.b64decode(api_key)
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

        try:  # next, try to login using X-API-KEY
            api_key = req.headers.get('X-API-KEY')
            api_key = base64.b64decode(api_key)
            user = User.query.filter_by(api_key=api_key).first()
            if user:
                return user
        except:
            pass

        # User unable to be logged in
        return

    @login_manager.unauthorized_handler
    def unauthorized():
        try:
            if str(request.url_rule).startswith('/api/'):
                return None, 401
        except:
            pass
        flash(gettext('Please log in to access this page'), "error")
        return redirect(url_for('routes_authentication.login_check'))

    return app


def extension_session(app):
    # TODO: Remove this code if Mycodo doesn't produce this issue anymore
    # If "EOFError: Ran out of input" returns, consider removing flask-session using filesystem
    # https://github.com/pallets/cachelib/issues/21
    # https://github.com/fengsp/flask-session/issues/132
    # try:
    #     # Remove flask_session directory every time flask starts
    #     import shutil
    #     shutil.rmtree('/opt/Mycodo/mycodo/flask_session')
    # except:
    #     pass

    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)

    return app

# coding=utf-8
#
#  mycodo_flask.py - Flask web server for Mycodo, for visualizing data,
#                    configuring the system, and controlling the daemon.
#
#  Copyright (C) 2016  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

# Debug messages to debug console
from __future__ import print_function  # In python 2.7
import os

from flask import (
    Flask,
    request
)
from flask_babel import Babel
# from flask_sqlalchemy import SQLAlchemy
from flask_sslify import SSLify

# Classes
from mycodo.databases.mycodo_db.models_5 import (
    db,
    Misc
)

# Functions
from init_databases import create_dbs
from mycodo.mycodo_flask import (
    admin_routes,
    authentication_routes,
    general_routes,
    method_routes,
    page_routes,
    settings_routes
)
from mycodo.mycodo_flask.general_routes import influx_db

# Config
from mycodo.config import (
    ProdConfig,
    LANGUAGES
)


def create_app(config=ProdConfig):
    """
    Applicaiton factory:
        http://flask.pocoo.org/docs/0.11/patterns/appfactories/

    :param config: configuration object that holds config constants
    :returns: Flask
    """
    app = Flask(__name__)

    app.config.from_object(config)
    app.secret_key = os.urandom(24)

    db.init_app(app)

    register_extensions(app, config)
    register_blueprints(app)

    # Translations
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        misc = Misc.query.first()
        if misc.language != '':
            for key, _ in LANGUAGES.iteritems():
                if key == misc.language:
                    return key
        return request.accept_languages.best_match(LANGUAGES.keys())

    return app


def register_extensions(_app, config):
    """ register extensions to the app """
    _app.jinja_env.add_extension('jinja2.ext.do')  # Global values in jinja

    # create the databases if needed
    create_dbs(None, create_all=True, config=config, exit_when_done=False)

    # attach influx db
    influx_db.init_app(_app)

    # Check user option to force all web connections to use SSL
    force_https = True
    from databases.utils import session_scope
    with session_scope(_app.config['SQLALCHEMY_DATABASE_URI']) as new_session:
        try:
            misc = new_session.query(Misc).first()
            force_https = misc.force_https
        except:
            pass

    if force_https:
        SSLify(_app)


def register_blueprints(_app):
    """ register blueprints to the app """
    _app.register_blueprint(admin_routes.blueprint)  # register admin views
    _app.register_blueprint(authentication_routes.blueprint)  # register login/logout views
    _app.register_blueprint(general_routes.blueprint)  # register general routes
    _app.register_blueprint(method_routes.blueprint)  # register method views
    _app.register_blueprint(page_routes.blueprint)  # register page views
    _app.register_blueprint(settings_routes.blueprint)  # register settings views

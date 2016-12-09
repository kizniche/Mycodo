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

from flask import Flask
from flask_sslify import SSLify

import flaskutils
from init_databases import create_dbs
from databases.mycodo_db.models import Misc
from config import ProdConfig

from mycodo.mycodo_flask import admin_routes
from mycodo.mycodo_flask import authentication_routes
from mycodo.mycodo_flask import general_routes
from mycodo.mycodo_flask import method_routes
from mycodo.mycodo_flask import page_routes
from mycodo.mycodo_flask import settings_routes
from mycodo.mycodo_flask.general_routes import influx_db


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

    register_extensions(app, config)
    register_blueprints(app)

    return app


def register_extensions(_app, config):
    """ register extensions to the app """
    _app.jinja_env.add_extension('jinja2.ext.do')  # Global values in jinja

    # create the databases if needed
    create_dbs(None, create_all=True, config=config, exit_when_done=False)

    # attach influx db
    influx_db.init_app(_app)

    # Check user option to force all web connections to use SSL
    misc = flaskutils.db_retrieve_table(_app.config['MYCODO_DB_PATH'], Misc, first=True)
    if misc.force_https:
        SSLify(_app)


def register_blueprints(_app):
    """ register blueprints to the app """
    _app.register_blueprint(admin_routes.blueprint)  # register admin views
    _app.register_blueprint(authentication_routes.blueprint)  # register our login/logout views
    _app.register_blueprint(general_routes.blueprint)  # register general routes
    _app.register_blueprint(method_routes.blueprint)  # register method views
    _app.register_blueprint(page_routes.blueprint)  # register page views
    _app.register_blueprint(settings_routes.blueprint)  # register settings views

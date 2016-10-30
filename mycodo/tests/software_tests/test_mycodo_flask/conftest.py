# coding=utf-8
""" conftest holds pytest fixtures and functions """
#  Hardware specific libs are found through out the flask app pages
#  and the following mock work will patch them so that we can pretend
#  that we have them installed:
from mock import patch, MagicMock
patch.dict("sys.modules", RPi=MagicMock(), picamera=MagicMock()).start()

import pytest
from webtest import TestApp

from mycodo.config import TestConfig
from mycodo.mycodo_flask.app import create_app
from mycodo.databases.utils import session_scope
from mycodo.tests.software_tests.conftest import create_admin_user


def build_single_use_config(db_config):
    """
    Creates a TestConfig instance with database fixtures
    that get deleted when test ends
    """
    config = TestConfig
    config.SQL_DATABASE_USER = db_config.SQL_DATABASE_USER
    config.SQL_DATABASE_MYCODO = db_config.SQL_DATABASE_MYCODO
    config.SQL_DATABASE_NOTE = db_config.SQL_DATABASE_NOTE
    config.MYCODO_DB_PATH = db_config.MYCODO_DB_PATH
    config.NOTES_DB_PATH = db_config.NOTES_DB_PATH
    config.USER_DB_PATH = db_config.USER_DB_PATH
    return config


@pytest.yield_fixture()
def app(db_config):
    """
    Create a flask app test fixture

    :param db_config: database config object
    """
    config = build_single_use_config(db_config=db_config)
    _app = create_app(config=config)

    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture()
def testapp(app):
    """ A basic web app

    :param app: flask app
    :return: webtest.TestApp
    """
    create_admin_user(app.config['USER_DB_PATH'])
    return TestApp(app)


@pytest.fixture()
def testapp_no_admin_user(app):
    """ A basic web app

    :param app: flask app
    :return: webtest.TestApp
    """
    return TestApp(app)


def login_user(app, username, password):
    """
    returns a test context with a modified
    session for the user login status

    :returns: None
    """

    res = app.get('/login')
    form = res.forms['login_form']

    form['username'] = username
    form['password'] = password
    form.submit().maybe_follow()

    return None


@pytest.yield_fixture()
def user_db(app):
    """ creates a session to the user db """
    with session_scope(app.config['USER_DB_PATH']) as session:
        yield session

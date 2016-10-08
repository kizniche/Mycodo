# coding=utf-8
""" conftest holds pytest fixtures and functions """
#  Hardware specific libs are found through out the flask app pages
#  and the following mock work will patch them so that we can pretend
#  that we have them installed:
from mock import patch, MagicMock
patch.dict("sys.modules", RPi=MagicMock(), picamera=MagicMock()).start()

import pytest
from webtest import TestApp

# See docstring of this fuction for details on use
from mycodo.tests.software_tests.conftest import setup_databases_if_missing
setup_databases_if_missing()
from mycodo.mycodo_flask import app as _app


@pytest.yield_fixture()
def app():
    """ Create a python-eve test fixture """

    # this change of settings part can be removed when we switch to using
    # an application factory: http://flask.pocoo.org/docs/0.11/patterns/appfactories/
    _app.config['TESTING'] = True
    _app.config['DEBUG'] = True

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


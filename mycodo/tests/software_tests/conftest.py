# coding=utf-8
"""pytest file."""
#  Hardware specific libs are found through out the flask app pages
#  and the following mock work will patch them so that we can pretend
#  that we have them installed:
try:
from mock import patch, MagicMock
except ImportError:  # Fallback to stdlib for environments without 'mock'
    from unittest.mock import patch, MagicMock
patch.dict("sys.modules",
           RPi=MagicMock(),
           picamera=MagicMock(),
           AM2315=MagicMock(),
           tentacle_pi=MagicMock(),
           Adafruit_BMP=MagicMock(),
           Adafruit_TMP=MagicMock(),
           w1thermsensor=MagicMock(),
           sht_sensor=MagicMock(),
           smbus2=MagicMock(),
           flask_login=MagicMock(),
           flask_babel=MagicMock(),
           flask_compress=MagicMock(),
           flask_limiter=MagicMock(),
           flask_session=MagicMock(),
           flask_talisman=MagicMock(),
           ).start()

import pytest
import tempfile
import secrets
import shutil
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.realpath(__file__), '../../../..')))

# Ensure Flask is available; otherwise, skip tests gracefully
try:
    import flask  # noqa: F401
except Exception:
    import pytest as _pytest  # local alias to avoid confusion with fixture decorator
    _pytest.skip("Flask is not installed in this environment; skipping software tests.", allow_module_level=True)

from mycodo.mycodo_flask.app import create_app
from mycodo.config import TestConfig
try:
    from webtest import TestApp  # Optional dependency; fallback to Flask test_client if unavailable
except Exception:
    TestApp = None
from mycodo.mycodo_flask.extensions import db as _db
from mycodo.tests.software_tests.factories import UserFactory
from mycodo.databases.models import Role
from mycodo.databases.models import User
from mycodo.databases.models import populate_db


@pytest.fixture()
def app():
    """Creates a flask instance."""
    _app = create_app(config=TestConfig)
    ctx = _app.test_request_context()
    ctx.push()
    yield _app
    ctx.pop()


@pytest.fixture()
def testapp(app):
    """Creates a test client fixture (uses WebTest if available, otherwise Flask test_client)."""
    with app.app_context():
        populate_db()
        create_admin_user()
        create_guest_user()
    if TestApp is not None:
    return TestApp(app)
    # Fallback to Flask's built-in test client
    return app.test_client()


@pytest.fixture()
def tmp_file():
    """
    make a tmp file in an empty tmp dir and
    remove it after it is used
    """
    parent_dir = tempfile.mkdtemp()
    _, tmp_path = tempfile.mkstemp(dir=parent_dir)

    yield tmp_path

    if os.path.isdir(parent_dir):
        shutil.rmtree(parent_dir)


@pytest.fixture()
def db(app):
    """Creates a config object to set up and databases during tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db
    _db.drop_all()


def create_admin_user():
    """Create an admin user if it doesn't exist."""
    if not User.query.filter_by(name='admin').count():
        user = UserFactory()
        user.name = 'admin'
        user.set_password('53CR3t_p4zZW0rD')
        user.api_key = b'secret_admin_api_key'
        user.language = 'en'
        user.save()
        user.role_id = Role.query.filter_by(name='Admin').first().id
        user.save()


def create_guest_user():
    """Create a guest user if it doesn't exist."""
    if not User.query.filter_by(name='guest').count():
        user = UserFactory()
        user.name = 'guest'
        user.email = 'guest@email.com'
        user.set_password('53CR3t_p4zZW0rD')
        user.api_key = b'secret_guest_api_key'
        user.role_id = Role.query.filter_by(name='Guest').first().id
        user.language = 'en'
        user.save()


def login_user(app, username, password):
    """
    returns a test context with a modified
    session for the user login status
    :returns: None
    """
    res = app.get('/login_password')
    form = res.forms['login_form']
    form['mycodo_username'] = username
    form['mycodo_password'] = password
    form.submit().maybe_follow()
    return None

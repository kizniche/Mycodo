# coding=utf-8
""" pytest file """
#  Hardware specific libs are found through out the flask app pages
#  and the following mock work will patch them so that we can pretend
#  that we have them installed:
from mock import patch, MagicMock
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
           ).start()

import pytest
import tempfile
import secrets
import shutil
import os
from mycodo.mycodo_flask.app import create_app
from mycodo.config import TestConfig
from webtest import TestApp
from mycodo.mycodo_flask.extensions import db as _db
from mycodo.tests.software_tests.factories import UserFactory
from mycodo.databases.models import Role
from mycodo.databases.models import User
from mycodo.databases.models import populate_db


@pytest.fixture()
def app():
    """ creates a flask instance """
    _app = create_app(config=TestConfig)
    ctx = _app.test_request_context()
    ctx.push()
    yield _app
    ctx.pop()


@pytest.fixture()
def testapp(app):
    """ creates a webtest fixture """
    with app.app_context():
        populate_db()
        create_admin_user()
        create_guest_user()
    return TestApp(app)


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
    """ Creates a config object to setup and databases during tests """
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db
    _db.drop_all()


def create_admin_user():
    """ Create an admin user if it doesn't exist """
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
    """ Create a guest user if it doesn't exist """
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
    form['username'] = username
    form['password'] = password
    form.submit().maybe_follow()
    return None

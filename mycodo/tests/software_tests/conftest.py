# coding=utf-8
""" pytest file """
#  Hardware specific libs are found through out the flask app pages
#  and the following mock work will patch them so that we can pretend
#  that we have them installed:
from mock import patch, MagicMock
patch.dict("sys.modules",
           RPi=MagicMock(),
           imutils=MagicMock(),
           picamera=MagicMock(),
           AM2315=MagicMock(),
           tentacle_pi=MagicMock(),
           Adafruit_BMP=MagicMock(),
           Adafruit_TMP=MagicMock(),
           w1thermsensor=MagicMock(),
           sht_sensor=MagicMock(),
           smbus=MagicMock(),
           ).start()

import pytest
import tempfile
import shutil
import os
from mycodo.mycodo_flask.app import create_app
from mycodo.config import TestConfig
from webtest import TestApp
from mycodo.mycodo_flask.extensions import db as _db
from mycodo.tests.software_tests.factories import UserFactory
from mycodo.databases.models import Role
from mycodo.databases.models import populate_db


@pytest.yield_fixture()
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
    create_admin_user(app=app)
    return TestApp(app)


@pytest.yield_fixture()
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


def create_admin_user(app):
    """ mycodo_flask exits if there is no user called admin. So we create one """
    with app.app_context():
        populate_db()

        user = UserFactory()
        user.set_password('53CR3t p4zZW0rD')
        user.save()

        role = Role.query.filter_by(name='Admin').first()
        user.user_role = role.id
        user.save()

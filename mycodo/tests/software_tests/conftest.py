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
           smbus=MagicMock(),
           ).start()

import pytest
import logging
import tempfile
import shutil
import os
from mycodo.databases.utils import session_scope
from mycodo.databases.mycodo_db.models import User


def uri_to_path(uri):
    """ splits a URI back into a path """
    return str(uri).split('sqlite:///')[1]


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
def db_config(mycodo_db_uri):
    """ Creates a config object to setup and databases during tests """

    class Config(object):
        SQL_DATABASE_MYCODO = uri_to_path(mycodo_db_uri)
        MYCODO_DB_PATH = mycodo_db_uri

    return Config


@pytest.fixture()
def mycodo_db_uri(tmp_file):
    """ returns the sqlalchemy URI as the MYCODO_DB_PATH """
    return ''.join(['sqlite:///', tmp_file, '_mycodo_db'])


def create_admin_user(mycodo_db_uri):
    """ mycodo_flask exits if there is no user called admin. So we create one """

    with session_scope(mycodo_db_uri) as db_session:
        if not db_session.query(User).filter_by(role=1).count():
            logging.info("--> Creating new 'test' user as an admin")
            db_session.add(User(name='test',
                                role=1))
            db_session.commit()
        else:
            logging.warning("--> Dirty User DB: Admin user was already setup in: '{uri}'".format(uri=mycodo_db_uri))

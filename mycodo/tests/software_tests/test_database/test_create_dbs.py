# coding=utf-8
""" evaluates the create_dbs function """
#  Hardware specific libs are found through out the flask app pages
#  and the following mock work will patch them so that we can pretend
#  that we have them installed:
from mock import patch, MagicMock
patch.dict("sys.modules", RPi=MagicMock(), picamera=MagicMock()).start()

import os
from mycodo.tests.software_tests.conftest import uri_to_path
from init_databases import create_dbs


def test_can_create_dbs_from_config_object(db_config):
    """ creates a database with test object and sees that it has data """
    create_dbs(None, create_all=True, config=db_config, exit_when_done=False)
    for db in [db_config.MYCODO_DB_PATH, db_config.NOTES_DB_PATH, db_config.USER_DB_PATH]:
        db_path = uri_to_path(db)
        assert os.path.isfile(db_path), "Database File does not exist"
        assert os.path.getsize(db_path) > 0, "Database File was not set up (It is empty)"


def test_create_dbs_mycodo_db(db_config):
    """ only create the mycodo_db """
    # Expect DB to exist
    create_dbs('mycodo', config=db_config, exit_when_done=False)
    assert os.path.isfile(uri_to_path(db_config.MYCODO_DB_PATH)), "Mycodo Database File does not exist"
    assert os.path.getsize(uri_to_path(db_config.MYCODO_DB_PATH)) > 0, "Mycodo Database File was not set up (It is empty)"


def test_create_dbs_notes_db(db_config):
    """ only create the notes_db """
    # Expect DB to exist
    create_dbs('notes', config=db_config, exit_when_done=False)
    assert os.path.isfile(uri_to_path(db_config.NOTES_DB_PATH)), "Database File does not exist"
    assert os.path.getsize(uri_to_path(db_config.NOTES_DB_PATH)) > 0, "Database File was not set up (It is empty)"


def test_create_dbs_users_db(db_config):
    """ only create the mycodo_db """
    # Expect DB to exist
    create_dbs('users', config=db_config, exit_when_done=False)
    assert os.path.isfile(uri_to_path(db_config.USER_DB_PATH)), "Users Database File does not exist"
    assert os.path.getsize(uri_to_path(db_config.USER_DB_PATH)) > 0, "Users Database File was not set up (It is empty)"

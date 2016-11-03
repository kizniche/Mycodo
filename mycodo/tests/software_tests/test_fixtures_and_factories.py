# coding=utf-8
""" make sure the fixtures are behaving as expected """
from mycodo.tests.software_tests.factories_user import AdminFactory, GuestFactory, UserFactory


def test_db_config_creates_unique_uris(db_config):
    """ Each db has a unique uri """
    assert db_config.SQL_DATABASE_USER not in [db_config.MYCODO_DB_PATH, db_config.NOTES_DB_PATH,
                                               db_config.USER_DB_PATH], "Database URIs are not Unique"
    assert db_config.MYCODO_DB_PATH not in [db_config.SQL_DATABASE_USER, db_config.NOTES_DB_PATH,
                                            db_config.USER_DB_PATH], "Database URIs are not Unique"
    assert db_config.NOTES_DB_PATH not in [db_config.SQL_DATABASE_USER, db_config.MYCODO_DB_PATH,
                                           db_config.USER_DB_PATH], "Database URIs are not Unique"
    assert db_config.USER_DB_PATH not in [db_config.SQL_DATABASE_USER, db_config.MYCODO_DB_PATH,
                                          db_config.NOTES_DB_PATH], "Database URIs are not Unique"


# --------------------------
#   Factory Tests
# --------------------------
def create_user_from_factory(factory, user_restriction=None):
    """ Uses a factory to create a user and attempts to save it """
    new_user = factory()
    assert new_user.user_name, "Failed to create a 'user_name' using {factory}".format(factory=factory)
    assert new_user.user_email, "Failed to create a 'user_email' using {factory}".format(factory=factory)
    assert new_user.user_restriction == user_restriction


def test_user_factories_creates_valid_user():
    """ Use UserFactory to create new user"""
    create_user_from_factory(UserFactory)


def test_admin_factories_creates_valid_user():
    """ Use AdminFactory to create new user"""
    create_user_from_factory(AdminFactory, user_restriction='admin')


def test_guest_factories_creates_valid_user():
    """ Use GuestFactory to create new user"""
    create_user_from_factory(GuestFactory, user_restriction='guest')

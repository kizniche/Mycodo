# coding=utf-8
""" make sure the fixtures are behaving as expected """


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

# coding=utf-8
""" pytest file """
import pytest
import logging
from os.path import isfile
from mycodo.config import SQL_DATABASE_MYCODO, SQL_DATABASE_NOTE, SQL_DATABASE_USER
from init_databases import create_dbs
from mycodo.databases.utils import session_scope
from mycodo.databases.users_db.models import Users


@pytest.yield_fixture()
def user_db():
    """ yields a session to the user db """
    with session_scope("sqlite:///" + SQL_DATABASE_USER) as db_session:
        yield db_session

        db_session.commit()


def setup_databases_if_missing():
    """
    Creates the databases if they are not present.

    Why?  Various parts of this codebase interact with the databases as soon
    as they are imported.  An example is the mycodo_flask file.  In order to
    run tests, we need to have something for these database calls to
    interact with.

    Normally we would spin up a disposable in-memory sqlite database, but
    only a single in-memory can be supported at any time.  This code base
    requires all three databases to be loaded.

    This function will eventually go away because there are much better
    ways to do this.  It requires a major refactoring of the database
    structure which will be finished shortly

    :return: None
    """

    if not all([isfile(SQL_DATABASE_USER), isfile(SQL_DATABASE_NOTE), isfile(SQL_DATABASE_MYCODO)]):
        logging.warning("--> Tests Delayed: Databases were missing and need to be installed."
                        "  You will need to run your tests again")
        create_dbs('', create_all=True)

    # mycodo_flask exits if there is no user called admin. So we create one
    with session_scope("sqlite:///" + SQL_DATABASE_USER) as db_session:
        if not db_session.query(Users).filter_by(user_restriction='admin').count():
            logging.warning("--> Creating new 'test' user as an admin")
            db_session.add(Users(user_name='test', user_restriction='admin'))
            db_session.commit()


@pytest.yield_fixture()
def mycodo_db_sess():
    """ yields mycodo_db sqlalchemy session """
    with session_scope("""sqlite://""" + SQL_DATABASE_USER) as session:
        yield session

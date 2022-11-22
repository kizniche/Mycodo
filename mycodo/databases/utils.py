# coding=utf-8
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


@contextmanager
def session_scope(db_uri):
    """Provide a transactional scope around a series of operations."""

    # configure Session class with desired options
    Session = sessionmaker()

    # later, we create the engine
    engine = create_engine(f"{db_uri}?check_same_thread=False")

    # associate it with our custom Session class
    Session.configure(bind=engine)

    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.exception("Error raised in session_scope.  Session will be rolled back: "
                         "db_uri='{uri}', error='{err}'".format(uri=db_uri, err=e))
        session.rollback()
        raise
    finally:
        session.close()

# coding=utf-8
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@contextmanager
def session_scope(db_path):
    """Provide a transactional scope around a series of operations."""

    # configure Session class with desired options
    Session = sessionmaker()

    # later, we create the engine
    engine = create_engine(db_path)

    # associate it with our custom Session class
    Session.configure(bind=engine)

    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

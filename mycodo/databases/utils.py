# coding=utf-8
import logging
import threading
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level engine cache — one engine per database URI, protected by lock.
# ---------------------------------------------------------------------------
_engine_cache = {}
_engine_cache_lock = threading.Lock()


def _get_engine(db_uri):
    """Return a cached SQLAlchemy engine for *db_uri*, creating one if needed."""
    with _engine_cache_lock:
        if db_uri not in _engine_cache:
            _engine_cache[db_uri] = create_engine(
                db_uri, connect_args={"check_same_thread": False}
            )
        return _engine_cache[db_uri]


@contextmanager
def session_scope(db_uri):
    """Provide a transactional scope around a series of operations."""
    try:
        # Custom URI overrides the supplied one (e.g. PostgreSQL in production)
        from mycodo.config_override import SQLALCHEMY_DATABASE_URI
        engine_url = SQLALCHEMY_DATABASE_URI
    except ImportError:
        # Standard SQLite path — append thread-safety flag
        engine_url = f"{db_uri}?check_same_thread=False"

    engine = _get_engine(engine_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.exception(
            "Error in session_scope — rolling back: db_uri='%s', error='%s'",
            db_uri, e
        )
        session.rollback()
        raise
    finally:
        session.close()

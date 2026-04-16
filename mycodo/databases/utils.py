# coding=utf-8
import logging
import threading
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level engine + sessionmaker cache — one pair per database URI.
# Both are cheap to reuse and expensive to recreate on every call.
# ---------------------------------------------------------------------------
_engine_cache = {}           # uri -> engine
_session_factory_cache = {}  # uri -> sessionmaker
_engine_cache_lock = threading.Lock()


def _get_engine_and_factory(db_uri):
    """Return a cached (engine, SessionFactory) pair for *db_uri*."""
    with _engine_cache_lock:
        if db_uri not in _engine_cache:
            engine = create_engine(
                db_uri, connect_args={"check_same_thread": False}
            )
            _engine_cache[db_uri] = engine
            _session_factory_cache[db_uri] = sessionmaker(bind=engine)
        return _engine_cache[db_uri], _session_factory_cache[db_uri]


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

    _, Session = _get_engine_and_factory(engine_url)
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

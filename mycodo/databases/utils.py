# coding=utf-8
"""
databases/utils.py — Low-level SQLAlchemy session management.

PUBLIC API CONTRACT
===================
The following symbols are part of Mycodo's **permanent public API** and MUST
NOT be renamed, moved, or have their call signatures changed:

  • ``session_scope(db_uri)``  — importable from ``mycodo.databases.utils``

This function is imported directly by:
  - The Mycodo daemon (mycodo_daemon.py)
  - All built-in and user-supplied controllers, inputs, outputs, functions
  - User-authored code entered via the conditional controller, Python Input,
    Python Output, and custom module textarea fields in the web UI.
    That code is stored in the database and executed at runtime; we cannot
    inspect or regenerate it on behalf of existing users.

!! DO NOT CHANGE THE SIGNATURE OR IMPORT PATH OF session_scope !!

Architecture — why two session systems exist
============================================
Flask-SQLAlchemy (``db.session``, from mycodo_flask.extensions) manages a
per-request scoped session that is only available while a Flask application
context is active.  The Mycodo daemon and all background controllers run
WITHOUT a Flask context, so ``db.session`` is unavailable to them.

``session_scope`` provides a self-contained transactional context that works
in *any* Python environment — Flask, daemon, scripts, tests — without
requiring a running Flask application.  It is the single source of truth for
all non-Flask DB access.

The engine + sessionmaker cache below ensures that expensive engine creation
happens only once per unique database URI, even across many concurrent threads.
"""
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
            engine_kwargs = {}
            if db_uri.startswith("sqlite"):
                engine_kwargs["connect_args"] = {"check_same_thread": False}
            engine = create_engine(db_uri, **engine_kwargs)
            _engine_cache[db_uri] = engine
            _session_factory_cache[db_uri] = sessionmaker(bind=engine)
        return _engine_cache[db_uri], _session_factory_cache[db_uri]


@contextmanager
def session_scope(db_uri):
    """
    Provide a transactional scope around a series of database operations.

    Usage::

        with session_scope(MYCODO_DB_PATH) as session:
            row = session.query(MyModel).filter_by(id=1).first()
            session.expunge_all()   # detach objects before leaving scope

    The session is committed on clean exit and rolled back on any exception.

    .. note::
        This is part of Mycodo's permanent public API — see module docstring.
    """
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

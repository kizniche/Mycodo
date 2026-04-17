# coding=utf-8
"""
utils/database.py — Database retrieval helpers.

PUBLIC API CONTRACT — DO NOT BREAK
====================================
The following symbols are part of Mycodo's **permanent public API**.  Their
names, import paths, and call signatures MUST NOT change:

  • ``db_retrieve_table(table, entry=None, unique_id=None)``
      Importable from ``mycodo.utils.database``
      Used by Flask routes and utilities inside a Flask application context.

  • ``db_retrieve_table_daemon(table, entry=None, device_id=None,
                               unique_id=None, custom_name=None,
                               custom_value=None)``
      Importable from ``mycodo.utils.database``
      Used by the daemon, controllers, built-in inputs/outputs/functions, AND
      user-authored code that cannot be inspected or regenerated:

        - ``mycodo/inputs/python_code.py`` injects the following line verbatim
          into every generated Python Input script file:
              from mycodo.utils.database import db_retrieve_table_daemon
          Those script files persist on disk and are NOT regenerated unless the
          user re-saves the Input.

        - ``mycodo/actions/input_action_execute_python_code.py`` injects the
          same import into every generated action script.

        - Users may write ``from mycodo.utils.database import db_retrieve_table_daemon``
          (or ``from mycodo.databases.utils import session_scope``) in the
          textarea fields of conditional controllers, Python Inputs, Python
          Outputs, and custom modules.  That code is stored in the database;
          we cannot inspect or update it on their behalf.

!! DO NOT RENAME, MOVE, OR CHANGE THE SIGNATURES OF THESE FUNCTIONS !!

Why two functions?
==================
``db_retrieve_table`` was written for Flask and historically relied on
Flask-SQLAlchemy's ``Model.query`` proxy, which only works inside a Flask app
context.  ``db_retrieve_table_daemon`` was written for the daemon and uses a
standalone ``session_scope``.

As of this refactor, ``db_retrieve_table`` now falls back to ``session_scope``
when called outside a Flask context (e.g. from tests or shared utilities),
making it safe to call from either environment.  The two function names are
kept as permanent stable exports.
"""
import logging
import time
from sqlite3 import OperationalError

import sqlalchemy

from mycodo.config import MYCODO_DB_PATH
from mycodo.databases.utils import session_scope

logger = logging.getLogger("mycodo.database")


def db_retrieve_table(table, entry=None, unique_id=None):
    """
    Return a query result with optional filtering.

    Preferred for Flask route handlers and Flask utility functions because it
    delegates to Flask-SQLAlchemy's request-scoped session when inside a Flask
    application context, giving automatic connection pooling and lazy loading.

    When called *outside* a Flask context (e.g. from shared utilities or
    tests), it falls back to ``session_scope`` so it remains safe to use.

    :param table:     SQLAlchemy model class.
    :param entry:     ``'first'`` to return the first row, ``'all'`` for all
                      rows, or ``None`` to return the raw Query object.
    :param unique_id: Filter by ``table.unique_id == unique_id``; implies
                      ``entry='first'``.
    """
    try:
        from flask import has_app_context
        if has_app_context():
            # --- Flask context: use the managed per-request session ---
            if unique_id:
                return_table = table.query.filter(table.unique_id == unique_id)
            else:
                return_table = table.query

            if entry == 'first' or unique_id:
                return_table = return_table.first()
            elif entry == 'all':
                return_table = return_table.all()

            return return_table
    except Exception:
        pass

    # --- Outside-Flask fallback (tests, shared utilities) ---
    # Delegate to db_retrieve_table_daemon which is always safe outside Flask.
    return db_retrieve_table_daemon(table, entry=entry, unique_id=unique_id)


def db_retrieve_table_daemon(
        table,
        entry=None,
        device_id=None,
        unique_id=None,
        custom_name=None,
        custom_value=None):
    """
    Return a query result with optional filtering using a standalone session.

    Designed for the Mycodo daemon, controllers, inputs, outputs, functions,
    and user-authored code running outside a Flask application context.
    Automatically retries up to 5 times on SQLite lock errors.

    .. warning::
        This function is part of Mycodo's permanent public API — see module
        docstring.  Its name, import path, and signature must never change.

    :param table:        SQLAlchemy model class.
    :param entry:        ``'first'`` / ``'all'`` / ``None`` (raw Query).
    :param device_id:    Filter by ``table.id == int(device_id)``; implies first.
    :param unique_id:    Filter by ``table.unique_id == unique_id``; implies first.
    :param custom_name:  Column name for a custom filter (used with custom_value).
    :param custom_value: Value to match for the custom filter column.
    """
    tries = 5
    while tries > 0:
        try:
            with session_scope(MYCODO_DB_PATH) as new_session:
                if device_id:
                    return_table = new_session.query(table).filter(
                        table.id == int(device_id))
                elif unique_id:
                    return_table = new_session.query(table).filter(
                        table.unique_id == unique_id)
                elif custom_name and custom_value:
                    return_table = new_session.query(table).filter(
                        getattr(table, custom_name) == custom_value)
                else:
                    return_table = new_session.query(table)

                if entry == 'first' or device_id or unique_id:
                    return_table = return_table.first()
                elif entry == 'all':
                    return_table = return_table.all()

                new_session.expunge_all()
                new_session.close()
            return return_table
        except OperationalError:
            pass
        except sqlalchemy.exc.OperationalError:
            pass

        if tries == 1:
            logger.exception(
                "Could not read the Mycodo database. "
                "Please submit a New Issue at "
                "https://github.com/kizniche/Mycodo/issues/new")
        else:
            logger.error(
                "The Mycodo database is locked. "
                "Trying to access again in 1 second...")

        time.sleep(1)
        tries -= 1

    raise RuntimeError(
        "Could not read the Mycodo database after 5 attempts — "
        "the database may be locked or corrupted. "
        "Please submit a New Issue at "
        "https://github.com/kizniche/Mycodo/issues/new"
    )

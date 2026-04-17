# coding=utf-8
"""
databases/__init__.py — Base model mixins and helpers.

Architecture note — TWO-WORLD DATABASE ACCESS
==============================================
Mycodo runs in two distinct runtime contexts that cannot share a session object:

  1. Flask request context  – Flask-SQLAlchemy manages a per-request session
     accessible via ``db.session`` (from mycodo_flask.extensions).  Using
     db.session here is correct and efficient.

  2. Daemon / outside-Flask context – The background daemon, all controllers,
     all inputs/outputs/functions, and user-authored code (conditional
     controllers, Python Inputs, Python Outputs, custom modules) run WITHOUT a
     Flask application context.  db.session is unavailable; raw SQLAlchemy
     sessions obtained via ``session_scope`` must be used instead.

The helpers below detect the active context at call-time with
``flask.has_app_context()`` and route to the appropriate session.

!! DO NOT REMOVE THE has_app_context() BRANCHES !!
User-authored code stored in the database (conditional controller statements,
Python Input/Output code typed into the UI textarea) may call model.save() or
clone_model() directly.  Those calls happen in the daemon context where no
Flask app context exists.  Removing the fallback path would silently break
user code we cannot inspect or regenerate.
"""
import logging
import secrets
import uuid

logger = logging.getLogger(__name__)


def _get_db_session():
    """
    Return the active SQLAlchemy session appropriate for the current context.

    - Inside a Flask request:  returns Flask-SQLAlchemy's ``db.session``.
    - Outside Flask (daemon):  raises RuntimeError — callers that need a
      session outside Flask should use ``session_scope`` directly.

    This helper is intentionally *not* used by CRUDMixin.save/delete because
    those methods need to manage commit/rollback themselves.
    """
    try:
        from flask import has_app_context
        if has_app_context():
            from mycodo.mycodo_flask.extensions import db
            return db.session
    except Exception:
        pass
    return None


class CRUDMixin(object):
    """
    Basic Create, Read, Update and Delete methods.
    Models that inherit from this class automatically get these CRUD methods.

    Both Flask routes (via db.session) and daemon code (via session_scope) can
    safely call .save() and .delete() — the correct session is chosen at
    runtime based on whether a Flask application context is active.
    """

    def save(self):
        """Create or update the model in the database."""
        try:
            from flask import has_app_context
            if has_app_context():
                # --- Flask context: use the managed per-request session ---
                from mycodo.mycodo_flask.extensions import db
                db.session.add(self)
                db.session.commit()
                return self
            else:
                # --- Daemon / outside-Flask context ---
                # This branch is reached by controllers, custom inputs/outputs,
                # conditional controllers, and user textarea code stored in the
                # database.  DO NOT REMOVE.
                from mycodo.config import MYCODO_DB_PATH
                from mycodo.databases.utils import session_scope
                with session_scope(MYCODO_DB_PATH) as session:
                    session.merge(self)
                return self
        except Exception as error:
            try:
                from flask import has_app_context
                if has_app_context():
                    from mycodo.mycodo_flask.extensions import db
                    db.session.rollback()
            except Exception:
                pass
            logger.error(
                "Failed to save %s due to error: %s", self, error, exc_info=True
            )
            # Re-raise so callers know the save failed
            raise

    def delete(self):
        """Delete the record from the database."""
        try:
            from flask import has_app_context
            if has_app_context():
                # --- Flask context ---
                from mycodo.mycodo_flask.extensions import db
                db.session.delete(self)
                db.session.commit()
            else:
                # --- Daemon / outside-Flask context --- DO NOT REMOVE.
                from mycodo.config import MYCODO_DB_PATH
                from mycodo.databases.utils import session_scope
                with session_scope(MYCODO_DB_PATH) as session:
                    # Re-attach the object to this session before deleting
                    obj = session.merge(self)
                    session.delete(obj)
        except Exception as error:
            try:
                from flask import has_app_context
                if has_app_context():
                    from mycodo.mycodo_flask.extensions import db
                    db.session.rollback()
            except Exception:
                pass
            logger.error(
                "Failed to delete '%s': '%s'", self, error, exc_info=True
            )
            raise


def set_api_key(length):
    """Generates an API key of specific length."""
    return secrets.token_bytes(length)


def set_uuid():
    """Returns a uuid string."""
    return str(uuid.uuid4())


def clone_model(model, **kwargs):
    """
    Clone an arbitrary SQLAlchemy model object without its primary key values.

    Works in both Flask and daemon contexts — see module docstring for why.
    """
    # Ensure the model's data is loaded before copying.
    try:
        model.id
    except Exception:
        return

    table = model.__table__
    non_pk_columns = [k for k in table.columns.keys() if k not in table.primary_key]
    data = {c: getattr(model, c) for c in non_pk_columns}
    data.update(kwargs)

    clone = model.__class__(**data)

    try:
        from flask import has_app_context
        if has_app_context():
            # --- Flask context ---
            from mycodo.mycodo_flask.extensions import db
            db.session.add(clone)
            db.session.commit()
        else:
            # --- Daemon / outside-Flask context --- DO NOT REMOVE.
            from mycodo.config import MYCODO_DB_PATH
            from mycodo.databases.utils import session_scope
            with session_scope(MYCODO_DB_PATH) as session:
                session.add(clone)
    except Exception as error:
        logger.error(
            "Failed to clone %s: %s", model, error, exc_info=True
        )
        raise

    return clone

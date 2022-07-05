# coding=utf-8
import logging
import time
from sqlite3 import OperationalError

import sqlalchemy

from mycodo.config import MYCODO_DB_PATH
from mycodo.databases.utils import session_scope
from mycodo.utils.logging_utils import set_log_level

logger = logging.getLogger("mycodo.database")
logger.setLevel(set_log_level(logging))


def db_retrieve_table(table, entry=None, unique_id=None):
    """
    Return SQL database query object with optional filtering
    Used in Flask (For daemon, see db_retrieve_table_daemon() below)

    If entry='first', only the first table entry is returned.
    If entry='all', all table entries are returned.
    If device_id is set, the first entry with that device ID is returned.
    Otherwise, the table object is returned.
    """
    if unique_id:
        return_table = table.query.filter(table.unique_id == unique_id)
    else:
        return_table = table.query

    if entry == 'first' or unique_id:
        return_table = return_table.first()
    elif entry == 'all':
        return_table = return_table.all()

    return return_table


def db_retrieve_table_daemon(
        table,
        entry=None,
        device_id=None,
        unique_id=None,
        custom_name=None,
        custom_value=None):
    """
    Return SQL database query object with optional filtering
    Used in daemon (For Flask, see db_retrieve_table() above)

    If entry='first', only the first table entry is returned.
    If entry='all', all table entries are returned.
    If device_id is set, the first entry with that device ID is returned.
    Otherwise, the table object is returned.
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

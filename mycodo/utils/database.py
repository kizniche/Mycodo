# coding=utf-8

import logging

from databases.utils import session_scope

logger = logging.getLogger("mycodo.database")


def db_retrieve_table(database, table, entry=None, device_id=None):
    """
    Return SQL database query object with optional filtering

    If entry='first', only the first table entry is returned.
    If entry='all', all table entries are returned.
    If device_id is set, the first entry with that device ID is returned.
    Otherwise, the table object is returned.
    """
    with session_scope(database) as new_session:
        if device_id:
            return_table = new_session.query(table).filter(
                table.id == device_id)
        else:
            return_table = new_session.query(table)

        if entry == 'first' or device_id:
            return_table = return_table.first()
        elif entry == 'all':
            return_table = return_table.all()

        new_session.expunge_all()
        new_session.close()
    return return_table

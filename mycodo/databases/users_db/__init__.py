#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  update-database.py - Create and update Mycodo SQLite databases
#
#  Copyright (C) 2015  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

import logging
import sqlalchemy
from sqlalchemy import create_engine

from .models import Base

logger = logging.getLogger(__name__)


def insert_or_ignore(an_object, a_session):
    """
    Duplicates INSERT OR IGNORE in SQLite.   This mostly illustrative and may not be production ready
    """

    a_session.add(an_object)

    try:
        a_session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        # Ignore duplicate primary key
        # This is the same as the 'INSERT OR IGNORE'
        logger.debug("An error occurred when committing changes to a database: "
                     "{err}".format(err=e))
        a_session.rollback()
    except Exception as e:
        logger.error("Exception in 'insert_or_ignore'' call.  Error: '{err}'".format(err=e))
        # Something else went wrong!!
        a_session.rollback()
        raise


def init_db(db_uri):
    """
    Binds the database to the specific class tables
    and creates them if needed

    :param db_uri:  URI to the database
    :return: None
    """
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)


def drop_db(db_uri):
    """
    Remove all entries in the database
    :param db_uri: URI to the database
    :return: None
    """
    engine = create_engine(db_uri)
    Base.metadata.drop_all(engine)

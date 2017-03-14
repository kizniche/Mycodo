#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  init_databases.py - Create and update Mycodo SQLite databases
#
#  Copyright (C) 2017  Kyle T. Gabriel
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

import argparse
import getpass
import logging
import os
import sys
import errno

import sqlalchemy

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import User
from mycodo.databases.utils import session_scope
from mycodo.utils.utils import (
    test_username,
    test_password,
    is_email,
    query_yes_no
)

if sys.version[0] == "3":
    raw_input = input  # Make sure this works in PY3

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


def add_user(admin=False):
    new_user = User()

    print('\nAdd user to database')

    while True:
        user_name = raw_input('User (a-z, A-Z, 2-64 chars): ').lower()
        if test_username(user_name):
            new_user.name = user_name
            break

    while True:
        user_password = getpass.getpass('Password: ')
        user_password_again = getpass.getpass('Password (again): ')
        if user_password != user_password_again:
            print("Passwords don't match")
        else:
            if test_password(user_password):
                new_user.set_password(user_password)
                break

    while True:
        email = raw_input('Email: ')
        if is_email(email):
            new_user.email = email
            break

    if admin:
        new_user.role = 1
    else:
        new_user.role = 4

    new_user.theme = 'slate'
    try:
        with session_scope(MYCODO_DB_PATH) as db_session:
            db_session.add(new_user)
        sys.exit(0)
    except sqlalchemy.exc.OperationalError:
        print("Failed to create user.  You most likely need to "
              "create the DB before trying to create users.")
        sys.exit(1)
    except sqlalchemy.exc.IntegrityError:
        print("Username already exists.")
        sys.exit(1)


def delete_user(username):
    if query_yes_no("Confirm delete user '{}' from user "
                    "database.".format(username.lower())):
        try:
            with session_scope(MYCODO_DB_PATH) as db_session:
                user = db_session.query(User).filter(
                    User.name == username.lower()).first()
                db_session.delete(user)
                print("User deleted.")
                sys.exit(0)
        except sqlalchemy.orm.exc.NoResultFound:
            print("No user found with this name.")
            sys.exit(1)


def change_password(username):
    print('Changing password for {}'.format(username.lower()))

    with session_scope(MYCODO_DB_PATH) as db_session:
        user = db_session.query(User).filter(
            User.name == username.lower()).first()

        while True:
            user_password = getpass.getpass('Password: ')
            user_password_again = getpass.getpass('Password (again): ')
            if user_password != user_password_again:
                print("Passwords don't match")
            else:
                try:
                    if test_password(user_password):
                        user.set_password(user_password)
                        sys.exit(0)
                except sqlalchemy.orm.exc.NoResultFound:
                    print("No user found with this name.")
                    sys.exit(1)


def create_dbs(config=None, exit_when_done=True):
    """
    Creates the individual databases using a database URI or
    a configuration object (like 'ProdConfig', or 'TestConfig' in
    mycodo.config

    :param db_name:  SQLAlchemy URI
    :param create_all: Bool to create all DBs
    :param config: Configuration Object to use custom URIs
    :param exit_when_done: Normally this code exits after setup is complete

    :return: None
    """
    db_path = config.SQL_DATABASE_MYCODO if config and hasattr(config, 'SQL_DATABASE_MYCODO') else SQL_DATABASE_MYCODO
    mycodo_db_uri = config.MYCODO_DB_PATH if config and hasattr(config, 'MYCODO_DB_PATH') else MYCODO_DB_PATH

    if not os.path.exists(os.path.dirname(db_path)):
        try:
            os.makedirs(os.path.dirname(db_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    logging.debug("Creating/verifying mycodo.db at {} ...".format(mycodo_db_uri))
    from mycodo.databases.models import init_db
    from mycodo.databases.models import populate_db
    init_db(mycodo_db_uri)
    populate_db(mycodo_db_uri)

    if exit_when_done:
        sys.exit(0)


def menu():
    parser = argparse.ArgumentParser(description="Initialize Mycodo Database "
                                                 "structure and manage users")

    parser.add_argument('-i', '--install_db', action='store_true',
                        help="Create new mycodo.db")

    parser.add_argument('-A', '--addadmin', action='store_true',
                        help="Add admin user to users database")

    parser.add_argument('-a', '--adduser', action='store_true',
                        help="Add user to users database")

    parser.add_argument('-d', '--deleteuser',
                        help="Remove user from users database")

    parser.add_argument('-p', '--pwchange',
                        help="Create a new password for user")

    args = parser.parse_args()

    if args.adduser:
        add_user()

    elif args.addadmin:
        add_user(admin=True)

    elif args.install_db:
        create_dbs()

    elif args.deleteuser:
        delete_user(args.deleteuser)

    elif args.pwchange:
        change_password(args.pwchange)


if __name__ == "__main__":
    menu()

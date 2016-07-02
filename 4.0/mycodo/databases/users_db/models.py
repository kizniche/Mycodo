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

# import subprocess

import bcrypt
from sqlalchemy import Column, INTEGER, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"

    user_id = Column(INTEGER, primary_key=True)
    user_name = Column(VARCHAR(64), unique=True, index=True)
    user_password_hash = Column(VARCHAR(255))
    user_email = Column(VARCHAR(64), unique=True, index=True)
    user_restriction = Column(VARCHAR(64))
    user_theme = Column(VARCHAR(64))

    def set_password(self, new_password):
        self.user_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password, hashed_password):
        hashes_match = bcrypt.hashpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        return hashes_match

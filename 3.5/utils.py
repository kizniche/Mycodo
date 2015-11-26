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

import re
import sys


def is_email(email):
    """
    Minimal Email validation

    :param email: Submitted email address
    :type email: str
    :return: Whether the string matches an Email address
    :rtype: Bool
    """

    pattern = '[^@]+@[^@]+\.[^@]+'

    if re.match(pattern, email) is None:
        print("This doesn't appear to be an email address")
        return False
    else:
        return True


def pass_length_min(pw, min_len=6):
    """
    Validate password length

    :param pw: Password
    :type pw: str
    :param min_len: Minimum length
    :type min_len: int
    :return: Whether the password is long enough
    :rtype: bool

    """
    if not len(pw) >= min_len:
        print("The password provided is too short.")
        return False
    else:
        return True


def characters(un):
    """
    Validate Username/Password is only letters and/or numbers

    :param un: Username or Password
    :type un: str
    :return: Whether the string only has numbers and letters
    :rtype: bool
    """

    if not un.isalnum():
        print("A special character was detected.  Please use only Letters and Numbers.")
        return False
    else:
        return True


def user_length_min(un, min_len=2):
    """
    Validate Username length

    :param un: Username
    :type un: str
    :param min_len: Minimum length
    :type min_len: int
    :return: Whether the Username length is long enough
    :rtype: bool
    """

    if not len(un) >= min_len:
        print("This username is too short.")
        return False
    else:
        return True


def user_length_max(un, max_len=64):
    """
    Validate Username length

    :param un:
    :type un:
    :param max_len:
    :type max_len:
    :return:
    :rtype:
    """
    if not len(un) <= max_len:
        print("This username is too long.")
        return False
    else:
        return True


def test_username(un, addl_tests=None, test_defaults=True):
    """
    Run tests on the supplied username and validate that it passes.

    :param un: Username
    :type un: str
    :param addl_tests: A list of functions that will be called on the username
    :type addl_tests: iterator
    :param test_defaults: Run the default test on the username.
    :type test_defaults: bool
    :return: Does the username pass the tests?
    :rtype: bool
    """
    tests = []

    if test_defaults:
        tests += [characters, user_length_min, user_length_max]

    if addl_tests:
        tests += addl_tests

    return validate_string(un, tests)


def test_password(pw, addl_tests=None, test_defaults=True):
    """
    Run tests on the supplied password and validate that it passes.

    :param pw:
    :type pw:
    :param addl_tests:
    :type addl_tests:
    :param test_defaults:
    :type test_defaults:
    :return:
    :rtype:
    """
    tests = []

    if test_defaults:
        tests += [characters, pass_length_min]

    if addl_tests:
        tests += addl_tests

    return validate_string(pw, tests)


def validate_string(a_str, tests):
    """
    Run tests on a string and make sure that they pass.

    :type a_str: str
    :param tests: A iterable of functions to apply to the string.  Should be boolean tests.
    :type tests: iter
    :rtype: bool
    """

    for test in tests:
        if not test(a_str):
            return False
    return True


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'y' or 'n').\n")

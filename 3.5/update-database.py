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

db_version_mycodo = 21
db_version_user = 2
db_version_note = 3

import getopt
import getpass
import os.path
import re
import sqlite3
import subprocess
import sys
import time

install_directory = os.path.dirname(os.path.abspath(__file__))

sql_database_mycodo = '%s/config/mycodo.db' % install_directory
sql_database_user = '%s/config/users.db' % install_directory
sql_database_note = '%s/config/notes.db' % install_directory

start_time = time.time()

def menu():
    if len(sys.argv) == 1:
        usage()
        return 1

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'adhip',
            ["adduser", "deleteuser", "help", "install-db", "pwchange"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        return 2
    for opt, arg in opts:
        if opt in ("-a", "--adduser"):
            try:
                sys.argv[2]
            except:
                add_user(sql_database_user)
            else:
                if db_exists_user(sys.argv[2]):
                    add_user(sys.argv[2])
            return 1
        elif opt in ("-d", "--deleteuser"):
            try:
                sys.argv[2]
            except:
                delete_user(sql_database_user)
            else:
                if db_exists_user(sys.argv[2]):
                    delete_user(sys.argv[2])
            return 1
        elif opt in ("-h", "--help"):
            usage()
            return 1
        elif opt in ("-i", "--install-db"):
            try:
                sys.argv[2]
            except:
                setup_db(0)
            else:
                if sys.argv[2] == 'update':
                    setup_db('update')
            return 1
        elif opt in ("-p", "--pwchange"):
            try:
                sys.argv[2]
            except:
                password_change(sql_database_user)
            else:
                if db_exists_user(sys.argv[2]):
                    password_change(sys.argv[2])
            return 1
        else:
            assert False, "Fail"


def usage():
    print 'Usage: update-database.py [OPTION] [FILE]...'
    print 'Create and manage Mycodo databases (if no database is specified, the'
    print 'default users.db and mycodo.db in config/ will be used)\n'
    print 'Options:'
    print '    -a, --adduser [file]'
    print '           Add user to existing users.db database'
    print '    -d, --deleteuser [file]'
    print '           Delete user from existing users.db database'
    print '    -h, --help'
    print '           Display this help and exit'
    print "    -i, --install-db [update]"
    print '           Create new users.db, mycodo.db. or both'
    print '    -p, --pwchange [file]'
    print '           Create a new password for user\n'
    print 'Examples: update-database.py -i'
    print '          update-database.py -p /home/user/Mycodo/3.5/config/users.db'


def add_user(db):
    print 'Add user to %s' % db
    pass_checks = True
    while pass_checks:
        user_name = raw_input('User (a-z, A-Z, 2-64 chars): ')
        if test_username(user_name):
            pass_checks = False

    pass_checks = True
    while pass_checks:
        user_password = getpass.getpass('Password: ')
        user_password_again = getpass.getpass('Password (again): ')
        if user_password != user_password_again:
            print "Passwords don't match"
        else:
            if test_password(user_password):
                user_password_hash = subprocess.check_output(["php", install_directory + "/public_html/includes/hash.php", "hash", user_password])
                pass_checks = False

    pass_checks = True
    while pass_checks:
        user_email = raw_input('Email: ')
        if is_email(user_email):
            pass_checks = False
        else:
            print 'Not a properly-formatted email\n'

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_name, user_password_hash, user_email, user_restriction, user_theme) VALUES ('{user_name}', '{user_password_hash}', '{user_email}', 'guest', 'light')".\
        format(user_name=user_name, user_password_hash=user_password_hash, user_email=user_email))
    conn.commit()
    cur.close()


def delete_user(db):
    print 'Delete user from %s' % db
    while 1:
        user_name = raw_input('User: ')
        if test_username(user_name):
            if query_yes_no("Confirm delete user '%s' from %s/config/users.db" % user_name, install_directory):
                conn = sqlite3.connect(sql_database_user)
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE user_name = '%s' " % user_name)
                conn.commit()
                cur.close()
                return 1
            else:
                return 0


def password_change(db):
    print 'Change password of user from %s' % db
    pass_checks = True
    while pass_checks:
        user_name = raw_input('User: ')
        if test_username(user_name):
            pass_checks = False

    while 1:
        user_password = getpass.getpass('New password: ')
        user_password_again = getpass.getpass('New password (again): ')
        if user_password != user_password_again:
            print "Passwords don't match"
        elif test_password(user_password):
            user_password_hash = subprocess.check_output(["php", install_directory + "/public_html/includes/hash.php", "hash", user_password])
            conn = sqlite3.connect(sql_database_user)
            cur = conn.cursor()
            cur.execute("UPDATE users SET user_password_hash='%s' WHERE user_name='%s'" % (user_password_hash, user_name))
            conn.commit()
            cur.close()
            return 1


def setup_db(update):
    global current_db_version_mycodo
    global current_db_version_user
    global current_db_version_note

    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("PRAGMA user_version;")
    for row in cur:
        current_db_version_mycodo = row[0]

    conn = sqlite3.connect(sql_database_user)
    cur = conn.cursor()
    cur.execute("PRAGMA user_version;")
    for row in cur:
        current_db_version_user = row[0]

    conn = sqlite3.connect(sql_database_note)
    cur = conn.cursor()
    cur.execute("PRAGMA user_version;")
    for row in cur:
        current_db_version_note = row[0]

    if update == 'update':
        mycodo_database_pre_update() # Any commands that need to be ran before the update
        mycodo_database_create()
        mycodo_database_update()
        user_database_update()
        note_database_create()
        note_database_update()
    else:
        target = raw_input("Generate which database? 'user', 'mycodo', 'notes', or 'all'? ")
    
        if target == 'all' or target == 'mycodo':
            print "Mycodo database creation/integrity check"
            mycodo_database_create()
            mycodo_database_update()
        
        if target == 'all' or target == 'user':
            delete_all_tables_user()
            create_all_tables_user()
            create_rows_columns_user()
            user_database_update()

        if target == 'all' or target == 'notes':
            note_database_create()
            note_database_update()


def mycodo_database_pre_update():
    print "Running pre-update checks..."

    # Version 10 updates: add more conditionals (exec and notify)
    # Need to remove column, but SQLite doesn't support DROP COLUMN
    if current_db_version_mycodo < 10:
        DelTable(sql_database_mycodo, 'SMTP')

    # Version 14 updates: Add ability to customize combined graphs
    # Need to remove column, but SQLite doesn't support DROP COLUMN
    if current_db_version_mycodo < 14:
        DelTable(sql_database_mycodo, 'CustomGraph')

def mycodo_database_update():
    print "Current Mycodo database version: %d" % current_db_version_mycodo
    print "Latest Mycodo database version: %d" % db_version_mycodo

    if db_version_mycodo == current_db_version_mycodo:
        print "Mycodo database is already up to date."
    else:
        print "Updating Mycodo database..."
        conn = sqlite3.connect(sql_database_mycodo)
        cur = conn.cursor()
        cur.execute("PRAGMA user_version = %s;" % db_version_mycodo)
        conn.commit()
        cur.close()

        # Version 1 - Create version number
        if current_db_version_mycodo < 1:
            print "Note database is not versioned. Updating."
    
        # Version 2 row updates
        if current_db_version_mycodo < 2:
            ModNullValue(sql_database_mycodo, 'TSensor', 'Temp_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'TSensor', 'Temp_Outmax_Low', 0)
            ModNullValue(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmax_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Temp_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Temp_Outmax_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Hum_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Hum_Outmax_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmax_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmax_Low', 0)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmax_Low', 0)
            ModNullValue(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmax_High', 0)
            ModNullValue(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmax_Low', 0)

        # Version 3 updates: add pre/post camera commands

        # Version 4 updates: add pressure sensor

        # Version 5 updates: add sensor conditional statements

        # Version 6 row updates
        if current_db_version_mycodo < 6:
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Relay_Min', -100)
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Relay_Max', 100)
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Relay_Tics', 25)
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Relay_MTics', 5)
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Temp_Min', 0)
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Temp_Max', 35)
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Temp_Tics', 5)
            ModNullValue(sql_database_mycodo, 'TSensor', 'YAxis_Temp_MTics', 5)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_Min', -100)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_Max', 100)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_Tics', 25)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_MTics', 5)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_Min', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_Max', 35)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_Tics', 5)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_MTics', 5)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_Min', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_Max', 100)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_Tics', 10)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_MTics', 5)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_Min', -100)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_Max', 100)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_Tics', 25)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_MTics', 5)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_Min', 0)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_Max', 5000)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_Tics', 500)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_MTics', 5)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_Min', -100)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_Max', 100)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_Tics', 25)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_MTics', 5)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_Min', 0)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_Max', 35)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_Tics', 5)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_MTics', 5)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Press_Min', 97000)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Press_Max', 99000)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Press_Tics', 250)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'YAxis_Press_MTics', 5)

        # Version 7 row updates
        if current_db_version_mycodo < 7:
            ModNullValue(sql_database_mycodo, 'TSensor', 'Temp_Relays_Up', '0')
            ModNullValue(sql_database_mycodo, 'TSensor', 'Temp_Relays_Down', '0')
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Temp_Relays_Up', '0')
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Temp_Relays_Down', '0')
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Hum_Relays_Up', '0')
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Hum_Relays_Down', '0')
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'CO2_Relays_Up', '0')
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'CO2_Relays_Down', '0')
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Temp_Relays_Up', '0')
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Temp_Relays_Down', '0')
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Press_Relays_Up', '0')
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Press_Relays_Down', '0')

        # Version 8 updates: add relay conditional statements

        # Version 9 updates: add table relay: Amps
        if current_db_version_mycodo < 9:
            ModNullValue(sql_database_mycodo, 'Relays', 'Amps', 0)
            ModNullValue(sql_database_mycodo, 'Misc', 'Enable_Max_Amps', 1)
            ModNullValue(sql_database_mycodo, 'Misc', 'Max_Amps', 15)

        # Version 10 updates: add more conditionals (exec and notify)
        if current_db_version_mycodo < 10:
            ModNullValue(sql_database_mycodo, 'RelayConditional', 'Sel_Relay', 1)
            ModNullValue(sql_database_mycodo, 'TSensorConditional', 'Sel_Relay', 1)
            ModNullValue(sql_database_mycodo, 'HTSensorConditional', 'Sel_Relay', 1)
            ModNullValue(sql_database_mycodo, 'CO2SensorConditional', 'Sel_Relay', 1)
            ModNullValue(sql_database_mycodo, 'PressSensorConditional', 'Sel_Relay', 1)

        # Version 11 updates: add min relay duration to PID
        if current_db_version_mycodo < 11:
            ModNullValue(sql_database_mycodo, 'TSensor', 'Temp_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'TSensor', 'Temp_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Temp_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Temp_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Hum_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Hum_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Temp_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Temp_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Press_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'PressSensor', 'Press_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'PressSensorPreset', 'Temp_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'PressSensorPreset', 'Temp_Outmin_Low', 0)
            ModNullValue(sql_database_mycodo, 'PressSensorPreset', 'Press_Outmin_High', 0)
            ModNullValue(sql_database_mycodo, 'PressSensorPreset', 'Press_Outmin_Low', 0)

        # Version 12 update: add custom message to login page

        # Version 13 updates: Add ability to verify HT sensor measurement
        if current_db_version_mycodo < 13:
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Pin', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Temp', 5)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Temp_Notify', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Temp_Stop', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Hum', 10)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Hum_Notify', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Hum_Stop', 0)
            ModNullValue(sql_database_mycodo, 'HTSensor', 'Verify_Notify_Email', '')
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Pin', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Temp', 5)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Temp_Notify', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Temp_Stop', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Hum', 10)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Hum_Notify', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Hum_Stop', 0)
            ModNullValue(sql_database_mycodo, 'HTSensorPreset', 'Verify_Notify_Email', '')

        # Version 14 updates: Add ability to customize combined graphs

        # Version 15 updates: Update log timestamp format, add relay duration and power usage stats/options
        if current_db_version_mycodo < 15:
            ModNullValue(sql_database_mycodo, 'Misc', 'Relay_Stats_Volts', 120)
            ModNullValue(sql_database_mycodo, 'Misc', 'Relay_Stats_DayofMonth', 15)

        # Version 16 updates: New graphing method, need to update log file format (remove multiple spaces)

        # Version 17 updates: Add "cost per kWh" and "currency unit" options
        if current_db_version_mycodo < 17:
            ModNullValue(sql_database_mycodo, 'Misc', 'Relay_Stats_Cost', 0.05)
            ModNullValue(sql_database_mycodo, 'Misc', 'Relay_Stats_Currency', '$')

        # Version 18 updates: no database changes, update log format

        # Version 19 updates: no database changes, initialize submodule mycodo_python

        # Version 20 updates: Add daily timers

        # Version 21 updates: move files/folders to public_html directory, symlink update happens in update-post.sh

        # any extra commands for version X
        #if current_db_version_mycodo < X:
        #    pass


def user_database_update():
    print "Current User database version: %d" % current_db_version_user
    print "Latest User database version: %d" % db_version_user

    if db_version_user == current_db_version_user:
        print "User database is already up to date."
    else:
        print "Updating User database..."
        conn = sqlite3.connect(sql_database_user)
        cur = conn.cursor()
        cur.execute("PRAGMA user_version = %s;" % db_version_user)
        conn.commit()
        cur.close()
    
    # Version 1 - Create version number
    if current_db_version_user < 1:
        print "User database is not versioned. Updating."

    # Version 2 - Add theme option and ability to restrict access
    if current_db_version_user < 2:
        AddColumn(sql_database_user, 'users', 'user_restriction', 'TEXT')
        AddColumn(sql_database_user, 'users', 'user_theme', 'TEXT')
        ModNullValue(sql_database_user, 'users', 'user_restriction', 'admin')
        ModNullValue(sql_database_user, 'users', 'user_theme', 'light')
        conn = sqlite3.connect(sql_database_user)
        cur = conn.cursor()
        cur.execute("UPDATE users SET user_restriction='guest' WHERE user_name='guest'")
        conn.commit()
        cur.close()


def note_database_update():
    print "Current Note database version: %d" % current_db_version_note
    print "Latest Note database version: %d" % db_version_note

    if db_version_note == current_db_version_note:
        print "Note database is already up to date."
    else:
        print "Updating Note database..."
        conn = sqlite3.connect(sql_database_note)
        cur = conn.cursor()
        cur.execute("PRAGMA user_version = %s;" % db_version_note)
        conn.commit()
        cur.close()

    # Version 1 - Create version number
    if current_db_version_note < 1:
        print "Note database is not versioned. Updating."

    # Version 2
    if current_db_version_note < 2:
        conn = sqlite3.connect(sql_database_note)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS Uploads (Id TEXT)")
        cur.close()
        AddColumn(sql_database_note, 'Uploads', 'Name', 'TEXT')
        AddColumn(sql_database_note, 'Uploads', 'File_Name', 'TEXT')
        AddColumn(sql_database_note, 'Uploads', 'Location', 'TEXT')

    # Version 3
    if current_db_version_note < 3:
        AddColumn(sql_database_note, 'Notes', 'Title', 'TEXT')
        ModNullValue(sql_database_note, 'Notes', 'Title', '')


def mycodo_database_create():
    AddTable(sql_database_mycodo, 'Relays')
    AddColumn(sql_database_mycodo, 'Relays', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'Relays', 'Pin', 'INT')
    AddColumn(sql_database_mycodo, 'Relays', 'Amps', 'REAL')
    AddColumn(sql_database_mycodo, 'Relays', 'Trigger', 'INT')
    AddColumn(sql_database_mycodo, 'Relays', 'Start_State', 'INT')

    AddTable(sql_database_mycodo, 'RelayConditional')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'If_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'If_Action', 'TEXT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'If_Duration', 'REAL')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Sel_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Do_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Do_Action', 'TEXT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Do_Duration', 'REAL')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Sel_Command', 'INT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Do_Command', 'TEXT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Sel_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'RelayConditional', 'Do_Notify', 'TEXT')

    AddTable(sql_database_mycodo, 'TSensor')
    AddColumn(sql_database_mycodo, 'TSensor', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Pin', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Temp_Min', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Temp_Max', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Temp_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'YAxis_Temp_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_OR', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_Period', 'INT')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_P', 'REAL')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_I', 'REAL')
    AddColumn(sql_database_mycodo, 'TSensor', 'Temp_D', 'REAL')

    AddTable(sql_database_mycodo, 'TSensorPreset')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Pin', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Temp_Min', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Temp_Max', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Temp_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'YAxis_Temp_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_Period', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_P', 'REAL')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_I', 'REAL')
    AddColumn(sql_database_mycodo, 'TSensorPreset', 'Temp_D', 'REAL')

    AddTable(sql_database_mycodo, 'TSensorConditional')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'State', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Sensor', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Direction', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Setpoint', 'REAL')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Sel_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Relay_State', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Relay_Seconds_On', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Sel_Command', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Do_Command', 'TEXT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Sel_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'TSensorConditional', 'Do_Notify', 'TEXT')

    AddTable(sql_database_mycodo, 'HTSensor')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Pin', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Clock_Pin', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Sensor_Voltage', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Pin', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Temp', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Temp_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Temp_Stop', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Hum', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Hum_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Hum_Stop', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Verify_Notify_Email', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_Min', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_Max', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Temp_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_Min', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_Max', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'YAxis_Hum_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_OR', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_Period', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_P', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_I', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Temp_D', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_OR', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_Period', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_P', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_I', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensor', 'Hum_D', 'REAL')

    AddTable(sql_database_mycodo, 'HTSensorPreset')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Pin', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Clock_Pin', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Sensor_Voltage', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Pin', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Temp', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Temp_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Temp_Stop', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Hum', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Hum_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Hum_Stop', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Verify_Notify_Email', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Temp_Min', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Temp_Max', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Temp_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Temp_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Hum_Min', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Hum_Max', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Hum_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'YAxis_Hum_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_Period', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_P', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_I', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Temp_D', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_Period', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_P', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_I', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorPreset', 'Hum_D', 'REAL')

    AddTable(sql_database_mycodo, 'HTSensorConditional')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'State', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Sensor', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Condition', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Direction', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Setpoint', 'REAL')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Sel_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Relay_State', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Relay_Seconds_On', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Sel_Command', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Do_Command', 'TEXT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Sel_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'HTSensorConditional', 'Do_Notify', 'TEXT')

    AddTable(sql_database_mycodo, 'CO2Sensor')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Pin', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'YAxis_CO2_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_OR', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_Period', 'INT')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_P', 'REAL')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_I', 'REAL')
    AddColumn(sql_database_mycodo, 'CO2Sensor', 'CO2_D', 'REAL')

    AddTable(sql_database_mycodo, 'CO2SensorPreset')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Pin', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_CO2_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_CO2_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_CO2_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'YAxis_CO2_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_Period', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_P', 'REAL')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_I', 'REAL')
    AddColumn(sql_database_mycodo, 'CO2SensorPreset', 'CO2_D', 'REAL')

    AddTable(sql_database_mycodo, 'CO2SensorConditional')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'State', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Sensor', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Direction', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Setpoint', 'REAL')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Sel_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Relay_State', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Relay_Seconds_On', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Sel_Command', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Do_Command', 'TEXT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Sel_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'CO2SensorConditional', 'Do_Notify', 'TEXT')

    AddTable(sql_database_mycodo, 'PressSensor')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Pin', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_Min', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_Max', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Temp_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Press_Min', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Press_Max', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Press_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'YAxis_Press_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_OR', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_Period', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_P', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_I', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Temp_D', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_OR', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_Period', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_P', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_I', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensor', 'Press_D', 'REAL')

    AddTable(sql_database_mycodo, 'PressSensorPreset')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Pin', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Device', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Pre_Measure_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Pre_Measure_Dur', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Activated', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Graph', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Relay_Min', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Relay_Max', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Relay_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Relay_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Temp_Min', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Temp_Max', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Temp_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Temp_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Press_Min', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Press_Max', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Press_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'YAxis_Press_MTics', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_Period', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_P', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_I', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Temp_D', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Relay_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Outmin_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Outmax_High', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Relay_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Outmin_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Outmax_Low', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Set', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Set_Direction', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_Period', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_P', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_I', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorPreset', 'Press_D', 'REAL')

    AddTable(sql_database_mycodo, 'PressSensorConditional')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'State', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Sensor', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Condition', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Direction', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Setpoint', 'REAL')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Period', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Sel_Relay', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Relay_State', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Relay_Seconds_On', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Sel_Command', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Do_Command', 'TEXT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Sel_Notify', 'INT')
    AddColumn(sql_database_mycodo, 'PressSensorConditional', 'Do_Notify', 'TEXT')

    AddTable(sql_database_mycodo, 'Timers')
    AddColumn(sql_database_mycodo, 'Timers', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'Timers', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'Timers', 'State', 'INT')
    AddColumn(sql_database_mycodo, 'Timers', 'DurationOn', 'INT')
    AddColumn(sql_database_mycodo, 'Timers', 'DurationOff', 'INT')

    AddTable(sql_database_mycodo, 'Timers_daily')
    AddColumn(sql_database_mycodo, 'Timers_daily', 'Name', 'TEXT')
    AddColumn(sql_database_mycodo, 'Timers_daily', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'Timers_daily', 'State', 'INT')
    AddColumn(sql_database_mycodo, 'Timers_daily', 'HourOn', 'INT')
    AddColumn(sql_database_mycodo, 'Timers_daily', 'MinuteOn', 'INT')
    AddColumn(sql_database_mycodo, 'Timers_daily', 'DurationOn', 'INT')

    AddTable(sql_database_mycodo, 'CustomGraph')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Mtics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Relays_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Relays_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Relays_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Temp_Relays_Mtics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Mtics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Relays_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Relays_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Relays_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Hum_Relays_Mtics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Mtics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Relays_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Relays_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Relays_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Co2_Relays_Mtics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Mtics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Relays_Up', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Relays_Down', 'TEXT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Relays_Min', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Relays_Max', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Relays_Tics', 'INT')
    AddColumn(sql_database_mycodo, 'CustomGraph', 'Combined_Press_Relays_Mtics', 'INT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO CustomGraph (id, combined_temp_min, combined_temp_max, combined_temp_tics, combined_temp_mtics, combined_temp_relays_up, combined_temp_relays_down, combined_temp_relays_min, combined_temp_relays_max, combined_temp_relays_tics, combined_temp_relays_mtics, combined_hum_min, combined_hum_max, combined_hum_tics, combined_hum_mtics, combined_hum_relays_up, combined_hum_relays_down, combined_hum_relays_min, combined_hum_relays_max, combined_hum_relays_tics, combined_hum_relays_mtics, combined_co2_min, combined_co2_max, combined_co2_tics, combined_co2_mtics, combined_co2_relays_up, combined_co2_relays_down, combined_co2_relays_min, combined_co2_relays_max, combined_co2_relays_tics, combined_co2_relays_mtics, combined_press_min, combined_press_max, combined_press_tics, combined_press_mtics, combined_press_relays_up, combined_press_relays_down, combined_press_relays_min, combined_press_relays_max, combined_press_relays_tics, combined_press_relays_mtics) VALUES ('0', 0, 35, 5, 5, '0', '0', -100, 100, 25, 5, 0, 100, 10, 5, '0', '0', -100, 100, 25, 5, 0, 5000, 500, 5, '0', '0', -100, 100, 25, 5, 96000, 100000, 500, 5, '0', '0', -100, 100, 25, 5)")
    conn.commit()
    cur.close()
       
    AddTable(sql_database_mycodo, 'SMTP')
    AddColumn(sql_database_mycodo, 'SMTP', 'Host', 'TEXT')
    AddColumn(sql_database_mycodo, 'SMTP', 'SSL', 'INT')
    AddColumn(sql_database_mycodo, 'SMTP', 'Port', 'INT')
    AddColumn(sql_database_mycodo, 'SMTP', 'User', 'TEXT')
    AddColumn(sql_database_mycodo, 'SMTP', 'Pass', 'TEXT')
    AddColumn(sql_database_mycodo, 'SMTP', 'Email_From', 'TEXT')
    AddColumn(sql_database_mycodo, 'SMTP', 'Daily_Max', 'INT')
    AddColumn(sql_database_mycodo, 'SMTP', 'Wait_Time', 'INT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO SMTP (id, host, ssl, port, user, pass, email_from, daily_max, wait_time) VALUES ('0', 'smtp.gmail.com', 1, 465, 'email@gmail.com', 'password', 'email@gmail.com', 48, 3600)")
    conn.commit()
    cur.close()
    ModNullValue(sql_database_mycodo, 'SMTP', 'Host', 'smtp.gmail.com')
    ModNullValue(sql_database_mycodo, 'SMTP', 'SSL', 1)
    ModNullValue(sql_database_mycodo, 'SMTP', 'Port', 465)
    ModNullValue(sql_database_mycodo, 'SMTP', 'User', 'email@gmail.com')
    ModNullValue(sql_database_mycodo, 'SMTP', 'Pass', 'password')
    ModNullValue(sql_database_mycodo, 'SMTP', 'Email_From', 'email@gmail.com')
    ModNullValue(sql_database_mycodo, 'SMTP', 'Daily_Max', 48)
    ModNullValue(sql_database_mycodo, 'SMTP', 'Wait_Time', 3600)

    AddTable(sql_database_mycodo, 'CameraStill')
    AddColumn(sql_database_mycodo, 'CameraStill', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'CameraStill', 'Timestamp', 'INT')
    AddColumn(sql_database_mycodo, 'CameraStill', 'Display_Last', 'INT')
    AddColumn(sql_database_mycodo, 'CameraStill', 'Cmd_Pre', 'TEXT')
    AddColumn(sql_database_mycodo, 'CameraStill', 'Cmd_Post', 'TEXT')
    AddColumn(sql_database_mycodo, 'CameraStill', 'Extra_Parameters', 'TEXT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO CameraStill (id, relay, timestamp, display_last, cmd_pre, cmd_post, extra_parameters) VALUES ('0', 0, 1, 1, '', '', '--vflip --hflip --width 800 --height 600')")
    conn.commit()
    cur.close()
    ModNullValue(sql_database_mycodo, 'CameraStill', 'Relay', 0)
    ModNullValue(sql_database_mycodo, 'CameraStill', 'Timestamp', 1)
    ModNullValue(sql_database_mycodo, 'CameraStill', 'Display_Last', 1)
    ModNullValue(sql_database_mycodo, 'CameraStill', 'Cmd_Pre', '')
    ModNullValue(sql_database_mycodo, 'CameraStill', 'Cmd_Post', '')
    ModNullValue(sql_database_mycodo, 'CameraStill', 'Extra_Parameters', '')

    AddTable(sql_database_mycodo, 'CameraStream')
    AddColumn(sql_database_mycodo, 'CameraStream', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'CameraStream', 'Cmd_Pre', 'TEXT')
    AddColumn(sql_database_mycodo, 'CameraStream', 'Cmd_Post', 'TEXT') 
    AddColumn(sql_database_mycodo, 'CameraStream', 'Extra_Parameters', 'TEXT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO CameraStream (id, relay, cmd_pre, cmd_post, extra_parameters) VALUES ('0', 0, '', '', '--contrast 20 --sharpness 60 --awb auto --quality 20 --vflip --hflip --nopreview --width 800 --height 600')")
    conn.commit()
    cur.close()
    ModNullValue(sql_database_mycodo, 'CameraStream', 'Relay', 0)
    ModNullValue(sql_database_mycodo, 'CameraStream', 'Cmd_Pre', '')
    ModNullValue(sql_database_mycodo, 'CameraStream', 'Cmd_Post', '') 
    ModNullValue(sql_database_mycodo, 'CameraStream', 'Extra_Parameters', '')

    AddTable(sql_database_mycodo, 'CameraTimelapse')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'Relay', 'INT')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'Path', 'TEXT')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'Prefix', 'TEXT')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'File_Timestamp', 'INT')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'Display_Last', 'INT')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'Cmd_Pre', 'TEXT')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'Cmd_Post', 'TEXT')
    AddColumn(sql_database_mycodo, 'CameraTimelapse', 'Extra_Parameters', 'TEXT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO CameraTimelapse (id, relay, path, prefix, file_timestamp, display_last, cmd_pre, cmd_post, extra_parameters) VALUES ('0', 0, '/var/www/mycodo/camera-timelapse', 'Timelapse', 1, 1, '', '', '--nopreview --contrast 20 --sharpness 60 --awb auto --quality 20 --vflip --hflip --width 800 --height 600')")
    conn.commit()
    cur.close()
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'Relay', 0)
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'Path', '/var/www/mycodo/camera-timelapse')
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'Prefix', 'Timelapse-')
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'File_Timestamp', 1)
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'Display_Last', 1)
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'Cmd_Pre', '')
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'Cmd_Post', '')
    ModNullValue(sql_database_mycodo, 'CameraTimelapse', 'Extra_Parameters', '')

    AddTable(sql_database_mycodo, 'Misc')
    AddColumn(sql_database_mycodo, 'Misc', 'Dismiss_Notification', 'INT')
    AddColumn(sql_database_mycodo, 'Misc', 'Login_Message', 'TEXT')
    AddColumn(sql_database_mycodo, 'Misc', 'Refresh_Time', 'INT')
    AddColumn(sql_database_mycodo, 'Misc', 'Enable_Max_Amps', 'INT')
    AddColumn(sql_database_mycodo, 'Misc', 'Max_Amps', 'REAL')
    AddColumn(sql_database_mycodo, 'Misc', 'Relay_Stats_Volts', 'INT')
    AddColumn(sql_database_mycodo, 'Misc', 'Relay_Stats_Cost', 'REAL')
    AddColumn(sql_database_mycodo, 'Misc', 'Relay_Stats_Currency', 'TEXT')
    AddColumn(sql_database_mycodo, 'Misc', 'Relay_Stats_DayofMonth', 'INT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO Misc (id, dismiss_notification, login_message, refresh_time, enable_max_amps, max_amps, relay_stats_volts, relay_stats_cost, relay_stats_currency, relay_stats_dayofmonth) VALUES ('0', 0, '', 300, 1, 15, 120, 0.05, '$', 15)")
    conn.commit()
    cur.close()
    ModNullValue(sql_database_mycodo, 'Misc', 'Dismiss_Notification', 0)
    ModNullValue(sql_database_mycodo, 'Misc', 'Login_Message', '')
    ModNullValue(sql_database_mycodo, 'Misc', 'Refresh_Time', 300)


def note_database_create():
    AddTable(sql_database_note, 'Notes')
    AddColumn(sql_database_note, 'Notes', 'Time', 'TEXT')
    AddColumn(sql_database_note, 'Notes', 'User', 'TEXT')
    AddColumn(sql_database_note, 'Notes', 'Note', 'TEXT')


def AddTable(sql_database, table):
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS %s (Id TEXT UNIQUE)" % table)
    cur.close()


def DelTable(sql_database, table):
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS %s" % table)
    conn.close()


def AddColumn(sql_database, table, column, type):
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor() 
    try:
        cur.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, column, type))
    except:
        pass # Table does exist
    else:
        pass # Table doesn't exist
    cur.close()


def ModNullValue(sql_database, table, name, value):
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    if isinstance(value, basestring):
        cur.execute("UPDATE %s SET %s='%s' WHERE %s IS NULL" % (table, name, value, name))
    else:
        cur.execute("UPDATE %s SET %s=%s WHERE %s IS NULL" % (table, name, value, name))
    conn.commit()
    cur.close()


def delete_all_tables_user():
    print "user.db: Delete all tables"
    conn = sqlite3.connect(sql_database_user)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS `users` ')
    conn.close()


def create_all_tables_user():
    print "user.db: Create all tables"
    conn = sqlite3.connect(sql_database_user)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS `users` (`user_id` INTEGER PRIMARY KEY, `user_name` varchar(64), `user_password_hash` varchar(255), `user_email` varchar(64), 'user_restriction' varchar(64), 'user_theme' varchar(64))")
    cur.execute("CREATE UNIQUE INDEX `user_name_UNIQUE` ON `users` (`user_name` ASC)")
    cur.execute("CREATE UNIQUE INDEX `user_email_UNIQUE` ON `users` (`user_email` ASC)")
    conn.close()


def create_rows_columns_user():
    print "user.db: Create all rows and columns"
    conn = sqlite3.connect(sql_database_user)
    cur = conn.cursor()

    pass_checks = True
    print "\nPassword for user 'admin' (minimum 6 charachters in length)"
    while pass_checks:
        admin_password = getpass.getpass('Password: ')
        admin_password_again = getpass.getpass('Password (again): ')
        if admin_password != admin_password_again:
            print "Passwords don't match"
        elif test_password(admin_password):
            admin_password_hash = subprocess.check_output(["php", install_directory + "/public_html/includes/hash.php", "hash", admin_password])
            pass_checks = False

    pass_checks = True
    print "\nEmail for user 'admin'"
    while pass_checks:
        admin_email = raw_input('email: ')
        if is_email(admin_email):
            pass_checks = False
        else:
            print 'Not a properly-formatted email\n'

    cur.execute("INSERT INTO users (user_name, user_password_hash, user_email, user_restriction, user_theme) VALUES ('{user_name}', '{user_password_hash}', '{user_email}', 'admin', 'light')".\
        format(user_name='admin', user_password_hash=admin_password_hash, user_email=admin_email))

    if query_yes_no('\nCreate additional admin account?'):
        pass_checks = True
        print "\nCreate user (a-z, A-Z, 2-64 characters)"
        while pass_checks:
            user_name = raw_input('username: ')
            if test_username(user_name):
                pass_checks = False

        pass_checks = True
        print "\nPassword for user '" + user_name + "'"
        while pass_checks:
            user_password = getpass.getpass('password: ')
            user_password_again = getpass.getpass('password (again): ')
            if user_password != user_password_again:
                print "Passwords don't match"
            elif test_password(user_password):
                user_password_hash = subprocess.check_output(["php", install_directory + "/public_html/includes/hash.php", "hash", user_password])
                pass_checks = False

        pass_checks = True
        print "\nEmail for user '" + user_name + "'"
        while pass_checks:
            user_email = raw_input('email: ')
            if is_email(user_email):
                pass_checks = False
            else:
                print 'Not a properly-formatted email\n'

        cur.execute("INSERT INTO users (user_name, user_password_hash, user_email, user_restriction, user_theme) VALUES ('{user_name}', '{user_password_hash}', '{user_email}', 'admin', 'light')".\
            format(user_name=user_name, user_password_hash=user_password_hash, user_email=user_email))

    if query_yes_no("\nAllow 'guest' access (view but not modify)?"):

        pass_checks = True
        print "\nPassword for user 'guest'"
        while pass_checks:
            user_password = getpass.getpass('password: ')
            user_password_again = getpass.getpass('password (again): ')
            if user_password != user_password_again:
                print "Passwords don't match"
            elif test_password(user_password):
                user_password_hash = subprocess.check_output(["php", install_directory + "/public_html/includes/hash.php", "hash", user_password])
                pass_checks = False

        cur.execute("INSERT INTO users (user_name, user_password_hash, user_email, user_restriction, user_theme) VALUES ('{user_name}', '{user_password_hash}', '{user_email}', 'guest', 'light')".\
            format(user_name='guest', user_password_hash=user_password_hash, user_email='guest@guest.com'))

    conn.commit()
    cur.close()


def is_email(email):
    pattern = '[^@]+@[^@]+\.[^@]+'
    if re.match(pattern, email):
        return True
    else:
        return False


def pass_length_min(pw):
    'Password must be at least 6 characters\n'
    return len(pw) >= 6


def test_password(pw, tests=[pass_length_min]):
    for test in tests:
        if not test(pw):
            print(test.__doc__)
            return False
    return True


def characters(un):
    'User name must be only letters and numbers\n'
    return re.match("^[A-Za-z0-9_-]+$", un)


def user_length_min(un):
    'Password must be at least 2 characters\n'
    return len(un) >= 2


def user_length_max(un):
    'Password cannot be more than 64 characters\n'
    return len(un) <= 64


def test_username(un, tests=[characters, user_length_min, user_length_max]):
    for test in tests:
        if not test(un):
            print(test.__doc__)
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


def db_exists_user(db):
    if os.path.isfile(db):
        return 1
    else:
        print 'database %s not found' % db
        sys.exit(0)


def db_exists_mycodo(db):
    if os.path.isfile(db):
        return 1
    else:
        print 'database %s not found' % db
        sys.exit(0)


menu()

elapsed_time = time.time() - start_time
print 'Completed database creation/update in %.2f seconds' % elapsed_time

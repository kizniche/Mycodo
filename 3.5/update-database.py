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


sql_database_mycodo = '/var/www/mycodo/config/mycodo.db'
sql_database_user = '/var/www/mycodo/config/users.db'

db_version_mycodo = 2
db_version_user = 1

import getopt
import getpass
import os.path
import re
import sqlite3
import subprocess
import sys
import time

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
            if database != None:
                if db_exists_user(database):
                    add_user(database)
            else:
                add_user(sql_database_user)
            return 1
        elif opt in ("-d", "--deleteuser"):
            if database != None:
                if db_exists_user(database):
                    delete_user(database)
            else:
                delete_user(sql_database_user)
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
            if database != None:
                if db_exists_user(database):
                    password_change(database)
            else:
                password_change(sql_database_user)
            return 1
        else:
            assert False, "Fail"


def usage():
    print 'Usage: setup-database.py [OPTION] [FILE]...'
    print 'Create and manage Mycodo databases (if no database is specified, the'
    print 'default users.db and mycodo.db in /var/www/mycodo/config will be used)\n'
    print 'Options:'
    print '    -a, --adduser'
    print '           Add user to existing users.db database'
    print '    -d, --deleteuser'
    print '           Delete user from existing users.db database'
    print '    -h, --help'
    print '           Display this help and exit'
    print "    -i, --install-db"
    print '           Create new users.db, mycodo.db. or both'
    print '    -p, --pwchange'
    print '           Create a new password for user\n'
    print 'Examples: setup-database.py -i'
    print '          setup-database.py -p /var/www/mycodo/config/users.db'


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
                user_password_hash = subprocess.check_output(["php", "includes/hash.php", "hash", user_password])
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
    cur.execute("INSERT INTO users (user_name, user_password_hash, user_email) VALUES ('{user_name}', '{user_password_hash}', '{user_email}')".\
        format(user_name=user_name, user_password_hash=user_password_hash, user_email=user_email))
    conn.commit()
    cur.close()


def delete_user(db):
    print 'Delete user from %s' % db
    while 1:
        user_name = raw_input('User: ')
        if test_username(user_name):
            if query_yes_no("Confirm delete user '%s' from /var/www/mycodo/config/users.db" % user_name):
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
            user_password_hash = subprocess.check_output(["php", "includes/hash.php", "hash", user_password])
            conn = sqlite3.connect(sql_database_user)
            cur = conn.cursor()
            cur.execute("UPDATE users SET user_password_hash='%s' WHERE user_name='%s'" % (user_password_hash, user_name))
            conn.commit()
            cur.close()
            return 1


def setup_db(update):
    if update == 'update':
        target = 'mycodo'
    else:
        target = raw_input("Generate which database? 'user', 'mycodo', or 'all'? ")
    
    if target == 'all' or target == 'mycodo':
        MycodoDatabase()
        UpgradeDatabase()
    
    if target == 'all' or target == 'user':
        delete_all_tables_user()
        create_all_tables_user()
        create_rows_columns_user()

        # Update User database version
        conn = sqlite3.connect(sql_database_user)
        cur = conn.cursor()
        cur.execute("PRAGMA user_version = %s;" % db_version_user)
        conn.commit()
        cur.close()


def UpgradeDatabase():
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("PRAGMA user_version;")
    for row in cur:
        current_db_version_mycodo = row[0]
    
    # Version 2 updates
    if current_db_version_mycodo < 2:
        ModNullValue('TSensor', 'Temp_Outmax_High', 0)
        ModNullValue('TSensor', 'Temp_Outmax_Low', 0)
        ModNullValue('TSensorPreset', 'Temp_Outmax_High', 0)
        ModNullValue('TSensorPreset', 'Temp_Outmax_Low', 0)
        ModNullValue('HTSensor', 'Temp_Outmax_High', 0)
        ModNullValue('HTSensor', 'Temp_Outmax_Low', 0)
        ModNullValue('HTSensor', 'Hum_Outmax_High', 0)
        ModNullValue('HTSensor', 'Hum_Outmax_Low', 0)
        ModNullValue('HTSensorPreset', 'Temp_Outmax_High', 0)
        ModNullValue('HTSensorPreset', 'Temp_Outmax_Low', 0)
        ModNullValue('HTSensorPreset', 'Hum_Outmax_High', 0)
        ModNullValue('HTSensorPreset', 'Hum_Outmax_Low', 0)
        ModNullValue('CO2Sensor', 'CO2_Outmax_High', 0)
        ModNullValue('CO2Sensor', 'CO2_Outmax_Low', 0)
        ModNullValue('CO2SensorPreset', 'CO2_Outmax_High', 0)
        ModNullValue('CO2SensorPreset', 'CO2_Outmax_Low', 0)

    # Version 3 updates (for example)
    if current_db_version_mycodo < 3:
        pass

    # Update Mycodo database version
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("PRAGMA user_version = %s;" % db_version_mycodo)
    conn.commit()
    cur.close()


def MycodoDatabase():
    AddTable('Relays')
    AddColumn('Relays', 'Name', 'TEXT')
    AddColumn('Relays', 'Pin', 'INT')
    AddColumn('Relays', 'Trigger', 'INT')
    AddColumn('Relays', 'Start_State', 'INT')

    AddTable('TSensor')
    AddColumn('TSensor', 'Name', 'TEXT')
    AddColumn('TSensor', 'Pin', 'INT')
    AddColumn('TSensor', 'Device', 'TEXT')
    AddColumn('TSensor', 'Period', 'INT')
    AddColumn('TSensor', 'Pre_Measure_Relay', 'INT')
    AddColumn('TSensor', 'Pre_Measure_Dur', 'INT')
    AddColumn('TSensor', 'Activated', 'INT')
    AddColumn('TSensor', 'Graph', 'INT')
    AddColumn('TSensor', 'Temp_Relay_High', 'INT')
    AddColumn('TSensor', 'Temp_Outmax_High', 'INT')
    AddColumn('TSensor', 'Temp_Relay_Low', 'INT')
    AddColumn('TSensor', 'Temp_Outmax_Low', 'INT')
    AddColumn('TSensor', 'Temp_OR', 'INT')
    AddColumn('TSensor', 'Temp_Set', 'REAL')
    AddColumn('TSensor', 'Temp_Set_Direction', 'INT')
    AddColumn('TSensor', 'Temp_Period', 'INT')
    AddColumn('TSensor', 'Temp_P', 'REAL')
    AddColumn('TSensor', 'Temp_I', 'REAL')
    AddColumn('TSensor', 'Temp_D', 'REAL')

    AddTable('TSensorPreset')
    AddColumn('TSensorPreset', 'Name', 'TEXT')
    AddColumn('TSensorPreset', 'Pin', 'INT')
    AddColumn('TSensorPreset', 'Device', 'TEXT')
    AddColumn('TSensorPreset', 'Period', 'INT')
    AddColumn('TSensorPreset', 'Pre_Measure_Relay', 'INT')
    AddColumn('TSensorPreset', 'Pre_Measure_Dur', 'INT')
    AddColumn('TSensorPreset', 'Activated', 'INT')
    AddColumn('TSensorPreset', 'Graph', 'INT')
    AddColumn('TSensorPreset', 'Temp_Relay_High', 'INT')
    AddColumn('TSensorPreset', 'Temp_Outmax_High', 'INT')
    AddColumn('TSensorPreset', 'Temp_Relay_Low', 'INT')
    AddColumn('TSensorPreset', 'Temp_Outmax_Low', 'INT')
    AddColumn('TSensorPreset', 'Temp_Set', 'REAL')
    AddColumn('TSensorPreset', 'Temp_Set_Direction', 'INT')
    AddColumn('TSensorPreset', 'Temp_Period', 'INT')
    AddColumn('TSensorPreset', 'Temp_P', 'REAL')
    AddColumn('TSensorPreset', 'Temp_I', 'REAL')
    AddColumn('TSensorPreset', 'Temp_D', 'REAL')

    AddTable('HTSensor')
    AddColumn('HTSensor', 'Name', 'TEXT')
    AddColumn('HTSensor', 'Pin', 'INT')
    AddColumn('HTSensor', 'Device', 'TEXT')
    AddColumn('HTSensor', 'Period', 'INT')
    AddColumn('HTSensor', 'Pre_Measure_Relay', 'INT')
    AddColumn('HTSensor', 'Pre_Measure_Dur', 'INT')
    AddColumn('HTSensor', 'Activated', 'INT')
    AddColumn('HTSensor', 'Graph', 'INT')
    AddColumn('HTSensor', 'Temp_Relay_High', 'INT')
    AddColumn('HTSensor', 'Temp_Outmax_High', 'INT')
    AddColumn('HTSensor', 'Temp_Relay_Low', 'INT')
    AddColumn('HTSensor', 'Temp_Outmax_Low', 'INT')
    AddColumn('HTSensor', 'Temp_OR', 'INT')
    AddColumn('HTSensor', 'Temp_Set', 'REAL')
    AddColumn('HTSensor', 'Temp_Set_Direction', 'INT')
    AddColumn('HTSensor', 'Temp_Period', 'INT')
    AddColumn('HTSensor', 'Temp_P', 'REAL')
    AddColumn('HTSensor', 'Temp_I', 'REAL')
    AddColumn('HTSensor', 'Temp_D', 'REAL')
    AddColumn('HTSensor', 'Hum_Relay_High', 'INT')
    AddColumn('HTSensor', 'Hum_Outmax_High', 'INT')
    AddColumn('HTSensor', 'Hum_Relay_Low', 'INT')
    AddColumn('HTSensor', 'Hum_Outmax_Low', 'INT')
    AddColumn('HTSensor', 'Hum_OR', 'INT')
    AddColumn('HTSensor', 'Hum_Set', 'REAL')
    AddColumn('HTSensor', 'Hum_Set_Direction', 'INT')
    AddColumn('HTSensor', 'Hum_Period', 'INT')
    AddColumn('HTSensor', 'Hum_P', 'REAL')
    AddColumn('HTSensor', 'Hum_I', 'REAL')
    AddColumn('HTSensor', 'Hum_D', 'REAL')

    AddTable('HTSensorPreset')
    AddColumn('HTSensorPreset', 'Name', 'TEXT')
    AddColumn('HTSensorPreset', 'Pin', 'INT')
    AddColumn('HTSensorPreset', 'Device', 'TEXT')
    AddColumn('HTSensorPreset', 'Period', 'INT')
    AddColumn('HTSensorPreset', 'Pre_Measure_Relay', 'INT')
    AddColumn('HTSensorPreset', 'Pre_Measure_Dur', 'INT')
    AddColumn('HTSensorPreset', 'Activated', 'INT')
    AddColumn('HTSensorPreset', 'Graph', 'INT')
    AddColumn('HTSensorPreset', 'Temp_Relay_High', 'INT')
    AddColumn('HTSensorPreset', 'Temp_Outmax_High', 'INT')
    AddColumn('HTSensorPreset', 'Temp_Relay_Low', 'INT')
    AddColumn('HTSensorPreset', 'Temp_Outmax_Low', 'INT')
    AddColumn('HTSensorPreset', 'Temp_Set', 'REAL')
    AddColumn('HTSensorPreset', 'Temp_Set_Direction', 'INT')
    AddColumn('HTSensorPreset', 'Temp_Period', 'INT')
    AddColumn('HTSensorPreset', 'Temp_P', 'REAL')
    AddColumn('HTSensorPreset', 'Temp_I', 'REAL')
    AddColumn('HTSensorPreset', 'Temp_D', 'REAL')
    AddColumn('HTSensorPreset', 'Hum_Relay_High', 'INT')
    AddColumn('HTSensorPreset', 'Hum_Outmax_High', 'INT')
    AddColumn('HTSensorPreset', 'Hum_Relay_Low', 'INT')
    AddColumn('HTSensorPreset', 'Hum_Outmax_Low', 'INT')
    AddColumn('HTSensorPreset', 'Hum_Set', 'REAL')
    AddColumn('HTSensorPreset', 'Hum_Set_Direction', 'INT')
    AddColumn('HTSensorPreset', 'Hum_Period', 'INT')
    AddColumn('HTSensorPreset', 'Hum_P', 'REAL')
    AddColumn('HTSensorPreset', 'Hum_I', 'REAL')
    AddColumn('HTSensorPreset', 'Hum_D', 'REAL')

    AddTable('CO2Sensor')
    AddColumn('CO2Sensor', 'Name', 'TEXT')
    AddColumn('CO2Sensor', 'Pin', 'INT')
    AddColumn('CO2Sensor', 'Device', 'TEXT')
    AddColumn('CO2Sensor', 'Period', 'INT')
    AddColumn('CO2Sensor', 'Pre_Measure_Relay', 'INT')
    AddColumn('CO2Sensor', 'Pre_Measure_Dur', 'INT')
    AddColumn('CO2Sensor', 'Activated', 'INT')
    AddColumn('CO2Sensor', 'Graph', 'INT')
    AddColumn('CO2Sensor', 'CO2_Relay_High', 'INT')
    AddColumn('CO2Sensor', 'CO2_Outmax_High', 'INT')
    AddColumn('CO2Sensor', 'CO2_Relay_Low', 'INT')
    AddColumn('CO2Sensor', 'CO2_Outmax_Low', 'INT')
    AddColumn('CO2Sensor', 'CO2_OR', 'INT')
    AddColumn('CO2Sensor', 'CO2_Set', 'REAL')
    AddColumn('CO2Sensor', 'CO2_Set_Direction', 'INT')
    AddColumn('CO2Sensor', 'CO2_Period', 'INT')
    AddColumn('CO2Sensor', 'CO2_P', 'REAL')
    AddColumn('CO2Sensor', 'CO2_I', 'REAL')
    AddColumn('CO2Sensor', 'CO2_D', 'REAL')

    AddTable('CO2SensorPreset')
    AddColumn('CO2SensorPreset', 'Name', 'TEXT')
    AddColumn('CO2SensorPreset', 'Pin', 'INT')
    AddColumn('CO2SensorPreset', 'Device', 'TEXT')
    AddColumn('CO2SensorPreset', 'Period', 'INT')
    AddColumn('CO2SensorPreset', 'Pre_Measure_Relay', 'INT')
    AddColumn('CO2SensorPreset', 'Pre_Measure_Dur', 'INT')
    AddColumn('CO2SensorPreset', 'Activated', 'INT')
    AddColumn('CO2SensorPreset', 'Graph', 'INT')
    AddColumn('CO2SensorPreset', 'CO2_Relay_High', 'INT')
    AddColumn('CO2SensorPreset', 'CO2_Outmax_High', 'INT')
    AddColumn('CO2SensorPreset', 'CO2_Relay_Low', 'INT')
    AddColumn('CO2SensorPreset', 'CO2_Outmax_Low', 'INT')
    AddColumn('CO2SensorPreset', 'CO2_Set', 'REAL')
    AddColumn('CO2SensorPreset', 'CO2_Set_Direction', 'INT')
    AddColumn('CO2SensorPreset', 'CO2_Period', 'INT')
    AddColumn('CO2SensorPreset', 'CO2_P', 'REAL')
    AddColumn('CO2SensorPreset', 'CO2_I', 'REAL')
    AddColumn('CO2SensorPreset', 'CO2_D', 'REAL')

    AddTable('Timers')
    AddColumn('Timers', 'Name', 'TEXT')
    AddColumn('Timers', 'Relay', 'INT')
    AddColumn('Timers', 'State', 'INT')
    AddColumn('Timers', 'DurationOn', 'INT')
    AddColumn('Timers', 'DurationOff', 'INT')
       
    AddTable('SMTP')
    AddColumn('SMTP', 'Host', 'TEXT')
    AddColumn('SMTP', 'SSL', 'INT')
    AddColumn('SMTP', 'Port', 'INT')
    AddColumn('SMTP', 'User', 'TEXT')
    AddColumn('SMTP', 'Pass', 'TEXT')
    AddColumn('SMTP', 'Email_From', 'TEXT')
    AddColumn('SMTP', 'Email_To', 'TEXT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO SMTP VALUES('0', 'smtp.gmail.com', 1, 587, 'email@gmail.com', 'password', 'me@gmail.com', 'you@gmail.com')")
    conn.commit()
    cur.close()
    ModNullValue('SMTP', 'Host', 'smtp.gmail.com')
    ModNullValue('SMTP', 'SSL', 1)
    ModNullValue('SMTP', 'Port', 587)
    ModNullValue('SMTP', 'User', 'email@gmail.com')
    ModNullValue('SMTP', 'Pass', 'password')
    ModNullValue('SMTP', 'Email_From', 'me@gmail.com')
    ModNullValue('SMTP', 'Email_To', 'you@gmail.com')

    AddTable('CameraStill')
    AddColumn('CameraStill', 'Relay', 'INT')
    AddColumn('CameraStill', 'Timestamp', 'INT')
    AddColumn('CameraStill', 'Display_Last', 'INT')
    AddColumn('CameraStill', 'Extra_Parameters', 'TEXT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO CameraStill VALUES('0', 0, 1, 1, '')")
    conn.commit()
    cur.close()
    ModNullValue('CameraStill', 'Relay', 0)
    ModNullValue('CameraStill', 'Timestamp', 1)
    ModNullValue('CameraStill', 'Display_Last', 1)
    ModNullValue('CameraStill', 'Extra_Parameters', '')

    AddTable('CameraStream')
    AddColumn('CameraStream', 'Relay', 'INT')
    AddColumn('CameraStream', 'Extra_Parameters', 'TEXT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO CameraStream VALUES('0', 0, '')")
    conn.commit()
    cur.close()
    ModNullValue('CameraStream', 'Relay', 0)
    ModNullValue('CameraStream', 'Extra_Parameters', '')

    AddTable('CameraTimelapse')
    AddColumn('CameraTimelapse', 'Relay', 'INT')
    AddColumn('CameraTimelapse', 'Path', 'TEXT')
    AddColumn('CameraTimelapse', 'Prefix', 'TEXT')
    AddColumn('CameraTimelapse', 'File_Timestamp', 'INT')
    AddColumn('CameraTimelapse', 'Display_Last', 'INT')
    AddColumn('CameraTimelapse', 'Extra_Parameters', 'TEXT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO CameraTimelapse VALUES('0', 0, '/var/www/mycodo/camera-timelapse', 'Timelapse-', 1, 1, '')")
    conn.commit()
    cur.close()
    ModNullValue('CameraTimelapse', 'Relay', 0)
    ModNullValue('CameraTimelapse', 'Path', '/var/www/mycodo/camera-timelapse')
    ModNullValue('CameraTimelapse', 'Prefix', 'Timelapse-')
    ModNullValue('CameraTimelapse', 'File_Timestamp', 1)
    ModNullValue('CameraTimelapse', 'Display_Last', 1)
    ModNullValue('CameraTimelapse', 'Extra_Parameters', '')

    AddTable('Misc')
    AddColumn('Misc', 'Dismiss_Notification', 'INT')
    AddColumn('Misc', 'Refresh_Time', 'INT')
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO Misc VALUES('0', 0, 300)")
    conn.commit()
    cur.close()
    ModNullValue('Misc', 'Dismiss_Notification', 0)
    ModNullValue('Misc', 'Refresh_Time', 300)


def AddTable(table):
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS %s (Id TEXT UNIQUE)" % table)
    cur.close()


def AddColumn(table, column, type):
    conn = sqlite3.connect(sql_database_mycodo)
    cur = conn.cursor() 
    try:
        cur.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, column, type))
    except:
        pass # Table does exist
    else:
        pass # Table doesn't exist
    cur.close()


def ModNullValue(table, name, value):
    conn = sqlite3.connect(sql_database_mycodo)
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

    cur.execute("CREATE TABLE IF NOT EXISTS `users` (`user_id` INTEGER PRIMARY KEY, `user_name` varchar(64), `user_password_hash` varchar(255), `user_email` varchar(64))")
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
                admin_password_hash = subprocess.check_output(["php", "includes/hash.php", "hash", admin_password])
                pass_checks = False

    pass_checks = True
    print "\nEmail for user 'admin'"
    while pass_checks:
        admin_email = raw_input('email: ')
        if is_email(admin_email):
            pass_checks = False
        else:
            print 'Not a properly-formatted email\n'

    cur.execute("INSERT INTO users (user_name, user_password_hash, user_email) VALUES ('{user_name}', '{user_password_hash}', '{user_email}')".\
        format(user_name='admin', user_password_hash=admin_password_hash, user_email=admin_email))

    if query_yes_no('\nCreate additional user account?'):
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
                    user_password_hash = subprocess.check_output(["php", "includes/hash.php", "hash", user_password])
                    pass_checks = False

        pass_checks = True
        print "\nEmail for user '" + user_name + "'"
        while pass_checks:
            user_email = raw_input('email: ')
            if is_email(user_email):
                pass_checks = False
            else:
                print 'Not a properly-formatted email\n'

        cur.execute("INSERT INTO users (user_name, user_password_hash, user_email) VALUES ('{user_name}', '{user_password_hash}', '{user_email}')".\
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
                    user_password_hash = subprocess.check_output(["php", "/var/www/mycodo/includes/hash.php", "hash", user_password])
                    pass_checks = False

        cur.execute("INSERT INTO users (user_name, user_password_hash, user_email) VALUES ('{user_name}', '{user_password_hash}', '{user_email}')".\
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

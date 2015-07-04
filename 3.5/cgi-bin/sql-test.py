#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  sql-test.py - Development code for Mycodo SQL database use
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

import getopt
import sqlite3
import sys

sql_database = '/var/www/mycodo/config/mycodo.sqlite3'

def menu():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:druv',
            ["add", "delete", "db-create", "db-delete", "db-recreate", "db-setup", "row", "update", "view"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        return 2
    for opt, arg in opts:
        if opt in ("-a", "--add"):
            add_columns(sys.argv[2], sys.argv[3], sys.argv[4])
            return 1
        elif opt == "--db-create":
            create_db()
            return 1
        elif opt == "--db-delete":
            delete_db()
            return 1
        elif opt == "--db-recreate":
            print "Recreate Database"
            delete_db()
            create_db()
            return 1
        elif opt == "--db-setup":
            setup_db()
            return 1
        elif opt in ("-d", "--delete"):
            delete_all()
            return 1
        elif opt in ("-r", "--row"):
            delete_row(sys.argv[2])
            return 1
        elif opt in ("-u", "--update"):
            update_column(sys.argv[2], sys.argv[3], sys.argv[4])
            return 1
        elif opt in ("-v", "--view"):
            print "View Values"
            view_columns()
            return 1
        else:
            assert False, "Fail"

def create_db():
    print "Create Database"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('CREATE TABLE Names (row TEXT, column TEXT)')
    cur.execute('CREATE TABLE Configuration (row TEXT, column INTEGER)')
    cur.execute('CREATE TABLE PID (row TEXT, column REAL)')
    conn.close()
    
def delete_db():
    print "Delete Database"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS Names ')
    cur.execute('DROP TABLE IF EXISTS Configuration ')
    cur.execute('DROP TABLE IF EXISTS PID ')
    conn.close()
    
def setup_db():
    delete_db()
    create_db()
    
    for i in range(1, 9):
        add_columns('Names', 'relay%dname' % i, 'Relay_%dName' % i)
        add_columns('Configuration', 'relay%dpin' % i, 0)
        add_columns('Configuration', 'relay%dtrigger' % i, 0)
        
    for i in range(1, 9):
        add_columns('Configuration', 'timer%dstate' % i, 0)
        add_columns('Configuration', 'timer%drelay' % i, 0)
        add_columns('Configuration', 'timer%ddurationon' % i, 0)
        add_columns('Configuration', 'timer%ddurationoff' % i, 0)
        
    for i in range(1, 5):
        add_columns('Names', 'sensorht%dname' % i, 'HT_%dName' % i)
        add_columns('Configuration', 'sensorht%ddevice' % i, 0)
        add_columns('Configuration', 'sensorht%dpin' % i, 0)
        add_columns('Configuration', 'sensorht%dperiod' % i, 0)
        add_columns('Configuration', 'sensorht%dactivated' % i, 0)
        add_columns('Configuration', 'sensorht%dgraph' % i, 0)
        add_columns('Configuration', 'temp%dperiod' % i, 0)
        add_columns('Configuration', 'temp%drelay' % i, 0)
        add_columns('Configuration', 'temp%dor' % i, 0)
        add_columns('Configuration', 'hum%dperiod' % i, 0)
        add_columns('Configuration', 'hum%drelay' % i, 0)
        add_columns('Configuration', 'hum%dor' % i, 0)
        add_columns('PID', 'temp%dset' % i, 0)
        add_columns('PID', 'temp%dp' % i, 0)
        add_columns('PID', 'temp%di' % i, 0)
        add_columns('PID', 'temp%dd' % i, 0)
        add_columns('PID', 'hum%dset' % i, 0)
        add_columns('PID', 'hum%dp' % i, 0)
        add_columns('PID', 'hum%di' % i, 0)
        add_columns('PID', 'hum%dd' % i, 0)
    
    for i in range(1, 5):
        add_columns('Names', 'sensorco2%dname' % i, 'CO2_%dName' % i)
        add_columns('Configuration', 'sensorco2%ddevice' % i, 0)
        add_columns('Configuration', 'sensorco2%dpin' % i, 0)
        add_columns('Configuration', 'sensorco2%dperiod' % i, 0)
        add_columns('Configuration', 'sensorco2%dactivated' % i, 0)
        add_columns('Configuration', 'sensorco2%dgraph' % i, 0)
        add_columns('Configuration', 'co2%dperiod' % i, 0)
        add_columns('Configuration', 'co2%drelay' % i, 0)
        add_columns('Configuration', 'co2%dor' % i, 0)
        add_columns('PID', 'co2%dset' % i, 0)
        add_columns('PID', 'co2%dp' % i, 0)
        add_columns('PID', 'co2%di' % i, 0)
        add_columns('PID', 'co2%dd' % i, 0)
        
    add_columns('Names', 'smtp_host', 'smtp_host')
    add_columns('Names', 'smtp_port', 'smtp_port')
    add_columns('Names', 'smtp_user', 'smtp_user')
    add_columns('Names', 'smtp_pass', 'smtp_pass')
    add_columns('Names', 'smtp_email_from', 'smtp_email_from')
    add_columns('Names', 'smtp_email_to', 'smtp_email_to')
    
    add_columns('Configuration', 'numrelays', 0)
    add_columns('Configuration', 'numco2sensors', 0)
    add_columns('Configuration', 'numhtsensors', 0)
    add_columns('Configuration', 'numtimers', 0)
    add_columns('Configuration', 'cameralight', 0)
    
def add_columns(table, row, column):
    print "Add to Table: %s Variable: %s Value: %s" % (table, row, column)
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    if table == 'Names' or represents_int(column) or represents_float(column):
        if table == 'Names':
            query = "INSERT INTO %s (row, column) VALUES ( '%s', '%s' )" % (table, row, column)
        else:
            query = "INSERT INTO %s (row, column) VALUES ( '%s', %s )" % (table, row, column)
        cur.execute(query)
    conn.commit()
    cur.close()

def view_columns():
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    
    cur.execute('SELECT row, column FROM Names')
    print "Table: Names"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])

    cur.execute('SELECT row, column FROM Configuration')
    print "Table: Configuration"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])
    
    cur.execute('SELECT row, column FROM PID')
    print "Table: PID"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])
    
    cur.close()
    
def load_global_db(verbose):
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('SELECT row, column FROM Names')
    for row in cur :
        if verbose:
            print "Load Global Variable: %s Value: %s" % (row[0], row[1])
        globals()[row[0]] = row[1]
    cur.execute('SELECT row, column FROM Configuration')
    for row in cur :
        if verbose:
            print "Load Global Variable: %s Value: %s" % (row[0], row[1])
        globals()[row[0]] = row[1]
    cur.execute('SELECT row, column FROM PID')
    for row in cur :
        if verbose:
            print "Load Global Variable: %s Value: %s" % (row[0], row[1])
        globals()[row[0]] = row[1]
    cur.close()
    
def delete_all():
    print "Delete All Rows"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DELETE FROM Names')
    cur.execute('DELETE FROM Configuration')
    cur.execute('DELETE FROM PID')
    conn.commit()
    cur.close()
    
def delete_row(row):
    print "Delete Row: %s" % row
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    query = "DELETE FROM Configuration WHERE row = '%s' " % row
    cur.execute(query)
    conn.commit()
    cur.close()
    
def update_column(table, row, column):
    print "Update Table: %s Variable: %s Value: %s" % (table, row, column)
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    query = "UPDATE %s SET column = %s WHERE row = '%s' " % (table, column, row)
    cur.execute(query)
    conn.commit()
    cur.close()
    load_global_db(0)
    

# Check if string represents an integer column
def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
        
# Check if string represents a float column
def represents_float(s):
    try: 
        float(s)
        return True
    except ValueError:
        return False
    
load_global_db(0)
menu()
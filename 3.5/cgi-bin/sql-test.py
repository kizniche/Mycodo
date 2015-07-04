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
import time

sql_database = '/var/www/mycodo/config/mycodo.sqlite3'

def menu():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:ruv',
            ["add", "delete-rows", "delete-tables", "create-tables", "db-recreate", "db-setup", "row", "update", "view"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        return 2
    for opt, arg in opts:
        if opt in ("-a", "--add"):
            add_columns(sys.argv[2], sys.argv[3], sys.argv[4])
            return 1
        elif opt == "--create-tables":
            create_all_tables()
            return 1
        elif opt == "--db-recreate":
            print "Recreate Database"
            delete_all_tables()
            create_all_tables()
            return 1
        elif opt == "--db-setup":
            setup_db()
            return 1
        elif opt == "--delete-rows":
            delete_all_rows()
            return 1
        elif opt == "--delete-tables":
            delete_all_tables()
            return 1
        elif opt in ("-r", "--row"):
            delete_row(sys.argv[2], sys.argv[3])
            return 1
        elif opt in ("-u", "--update"):
            update_value(sys.argv[2], sys.argv[3], sys.argv[4])
            return 1
        elif opt in ("-v", "--view"):
            print "View Values"
            view_columns()
            return 1
        else:
            assert False, "Fail"

def create_all_tables():
    print "Create Tables"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('CREATE TABLE Strings (row TEXT, column TEXT)')
    cur.execute('CREATE TABLE Integers (row TEXT, column INTEGER)')
    cur.execute('CREATE TABLE Floats (row TEXT, column REAL)')
    conn.close()
    
def delete_all_tables():
    print "Delete Tables"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS Relays ')
    cur.execute('DROP TABLE IF EXISTS HTSensor ')
    cur.execute('DROP TABLE IF EXISTS CO2Sensor ')
    cur.execute('DROP TABLE IF EXISTS Timers ')
    cur.execute('DROP TABLE IF EXISTS Numbers ')
    
    cur.execute('DROP TABLE IF EXISTS Strings ')
    cur.execute('DROP TABLE IF EXISTS Integers ')
    cur.execute('DROP TABLE IF EXISTS Floats ')
    conn.close()
    
def setup_db():
    delete_all_tables()
    create_all_tables()
    print "Create Rows and Columns"
    
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    
    cur.execute("CREATE TABLE Relays (Id INT, Name TEXT, Pin INT, Trigger INT)")
    for i in range(1, 9):
        cur.execute("INSERT INTO Relays VALUES(%d, 'Relay%d', 0, 0)" % (i, i))
        
    cur.execute("CREATE TABLE HTSensor (Id INT, Name TEXT, Pin INT, Device TEXT, Relay INT, Period INT, Activated INT, Graph INT, Temp_OR INT, Temp_Set REAL, Temp_P REAL, Temp_I REAL, Temp_D, Hum_OR INT, Hum_Set REAL, Hum_P REAL, Hum_I REAL, Hum_D REAL)")
    for i in range(1, 5):
        cur.execute("INSERT INTO HTSensor VALUES(%d, 'HTSensor%d', 0, 'DHT22', 0, 10, 0, 0, 1, 25.0, 1.1, 1.2, 1.3, 1, 50.0, 1.1, 1.2, 1.3)" % (i, i))
    
    cur.execute("CREATE TABLE CO2Sensor (Id INT, Name TEXT, Pin INT, Device TEXT, Relay INT, Period INT, Activated INT, Graph INT, CO2_OR INT, CO2_Set INT, CO2_P REAL, CO2_I REAL, CO2_D REAL)")
    for i in range(1, 5):
        cur.execute("INSERT INTO CO2Sensor VALUES(%d, 'CO2Sensor%d', 0, 'K30', 0, 10, 0, 0, 1, 1000, 1.1, 1.2, 1.3)" % (i, i))

    cur.execute("CREATE TABLE Timers (Id INT, Name TEXT, State INT, Relay INT, DurationOn INT, DurationOff INT)")
    for i in range(1, 9):
        cur.execute("INSERT INTO Timers VALUES(%d, 'Timer%d', 0, 0, 60, 360)" % (i, i))
    
    cur.execute("CREATE TABLE Numbers (Relays INT, HTSensors INT, CO2Sensors INT, Timers INT)")
    cur.execute("INSERT INTO Numbers VALUES(8, 3, 1, 4)")
    
    conn.commit()
    cur.close()
    
    '''
    add_columns('Integers', 'numrelays', 0)
    add_columns('Integers', 'numco2sensors', 0)
    add_columns('Integers', 'numhtsensors', 0)
    add_columns('Integers', 'numtimers', 0)
    add_columns('Integers', 'cameralight', 0)
    
    for i in range(1, 9):
        add_columns('Strings', 'relay%dname' % i, 'Relay_%dName' % i)
        add_columns('Integers', 'relay%dpin' % i, 0)
        add_columns('Integers', 'relay%dtrigger' % i, 0)
        
    for i in range(1, 9):
        add_columns('Integers', 'timer%dstate' % i, 0)
        add_columns('Integers', 'timer%drelay' % i, 0)
        add_columns('Integers', 'timer%ddurationon' % i, 0)
        add_columns('Integers', 'timer%ddurationoff' % i, 0)
        
    for i in range(1, 5):
        add_columns('Strings', 'sensorht%dname' % i, 'HT_%dName' % i)
        add_columns('Integers', 'sensorht%ddevice' % i, 0)
        add_columns('Integers', 'sensorht%dpin' % i, 0)
        add_columns('Integers', 'sensorht%dperiod' % i, 0)
        add_columns('Integers', 'sensorht%dactivated' % i, 0)
        add_columns('Integers', 'sensorht%dgraph' % i, 0)
        add_columns('Integers', 'temp%dperiod' % i, 0)
        add_columns('Integers', 'temp%drelay' % i, 0)
        add_columns('Integers', 'temp%dor' % i, 0)
        add_columns('Integers', 'hum%dperiod' % i, 0)
        add_columns('Integers', 'hum%drelay' % i, 0)
        add_columns('Integers', 'hum%dor' % i, 0)
        add_columns('Floats', 'temp%dset' % i, 0)
        add_columns('Floats', 'temp%dp' % i, 0)
        add_columns('Floats', 'temp%di' % i, 0)
        add_columns('Floats', 'temp%dd' % i, 0)
        add_columns('Floats', 'hum%dset' % i, 0)
        add_columns('Floats', 'hum%dp' % i, 0)
        add_columns('Floats', 'hum%di' % i, 0)
        add_columns('Floats', 'hum%dd' % i, 0)
    
    for i in range(1, 5):
        add_columns('Strings', 'sensorco2%dname' % i, 'CO2_%dName' % i)
        add_columns('Integers', 'sensorco2%ddevice' % i, 0)
        add_columns('Integers', 'sensorco2%dpin' % i, 0)
        add_columns('Integers', 'sensorco2%dperiod' % i, 0)
        add_columns('Integers', 'sensorco2%dactivated' % i, 0)
        add_columns('Integers', 'sensorco2%dgraph' % i, 0)
        add_columns('Integers', 'co2%dperiod' % i, 0)
        add_columns('Integers', 'co2%drelay' % i, 0)
        add_columns('Integers', 'co2%dor' % i, 0)
        add_columns('Floats', 'co2%dset' % i, 0)
        add_columns('Floats', 'co2%dp' % i, 0)
        add_columns('Floats', 'co2%di' % i, 0)
        add_columns('Floats', 'co2%dd' % i, 0)
        
    add_columns('SMTP', 'smtp_host', 'smtp_host')
    add_columns('SMTP', 'smtp_port', 'smtp_port')
    add_columns('SMTP', 'smtp_user', 'smtp_user')
    add_columns('SMTP', 'smtp_pass', 'smtp_pass')
    add_columns('SMTP', 'smtp_email_from', 'smtp_email_from')
    add_columns('SMTP', 'smtp_email_to', 'smtp_email_to')
    
    add_columns('Integers', 'numrelays', 0)
    add_columns('Integers', 'numco2sensors', 0)
    add_columns('Integers', 'numhtsensors', 0)
    add_columns('Integers', 'numtimers', 0)
    add_columns('Integers', 'cameralight', 0)
    '''
    
def add_columns(table, row, column):
    #print "Add to Table: %s Variable: %s Value: %s" % (table, row, column)
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    if table == 'Strings' or represents_int(column) or represents_float(column):
        if table == 'Strings':
            query = "INSERT INTO %s (row, column) VALUES ( '%s', '%s' )" % (table, row, column)
        else:
            query = "INSERT INTO %s (row, column) VALUES ( '%s', %s )" % (table, row, column)
        cur.execute(query)
    conn.commit()
    cur.close()

def view_columns():
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    
    cur.execute('SELECT row, column FROM Strings')
    print "Table: Strings"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])

    cur.execute('SELECT row, column FROM Integers')
    print "Table: Integers"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])
    
    cur.execute('SELECT row, column FROM Floats')
    print "Table: Floats"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])
    
    cur.close()
    
def db_value(table, row):
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    
    cur.execute('SELECT row, column FROM Strings')
    print "Table: Strings"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])

    cur.execute('SELECT row, column FROM Integers')
    print "Table: Integers"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])
    
    cur.execute('SELECT row, column FROM Floats')
    print "Table: Floats"
    for row in cur :
        print "Variable: %s Value: %s" % (row[0], row[1])
    
    cur.close()
    
def load_global_db(verbose):
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    
    # Check if tables exist in database
    cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    for table in cur:
        print table
        if table[0] != 'Strings' and table[0] != 'Integers' and table[0] != 'Floats':
            print "Missing table(s): Cannot load database to global variables."
            return 0
  
    cur.execute('SELECT row, column FROM Strings')
    for row in cur :
        if verbose:
            print "Load Global Variable: %s Value: %s" % (row[0], row[1])
        globals()[row[0]] = row[1]
    cur.execute('SELECT row, column FROM Integers')
    for row in cur :
        if verbose:
            print "Load Global Variable: %s Value: %s" % (row[0], row[1])
        globals()[row[0]] = row[1]
    cur.execute('SELECT row, column FROM Floats')
    for row in cur :
        if verbose:
            print "Load Global Variable: %s Value: %s" % (row[0], row[1])
        globals()[row[0]] = row[1]
    cur.close()
    
def delete_all_rows():
    print "Delete All Rows"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DELETE FROM Strings')
    cur.execute('DELETE FROM Integers')
    cur.execute('DELETE FROM Floats')
    conn.commit()
    cur.close()
    
def delete_row(table, row):
    print "Delete Row: %s" % row
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    query = "DELETE FROM %s WHERE row = '%s' " % (table, row)
    cur.execute(query)
    conn.commit()
    cur.close()
    
def update_value(table, row, column):
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
    
#load_global_db(0)
start_time = time.time()
menu()
elapsed_time = time.time() - start_time
print 'Completed in %.2f seconds' % elapsed_time
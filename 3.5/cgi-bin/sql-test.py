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

# GPIO pins (BCM numbering) and name of devices attached to relay
relay_num = None
relay_pin = [0] * 9
relay_name = [0] * 9
relay_trigger = [0] * 9

# Temperature & Humidity Sensors
sensor_ht_num = 0
sensor_ht_name = [0] * 5
sensor_ht_device = [0] * 5
sensor_ht_pin = [0] * 5
sensor_ht_period = [0] * 5
sensor_ht_log = [0] * 5
sensor_ht_graph = [0] * 5
sensor_ht_read_temp_c = [0] * 5
sensor_ht_read_hum = [0] * 5
sensor_ht_dewpt_c = [0] * 5

# Temperature PID
pid_temp_relay = [0] * 5
pid_temp_set = [0] * 5
pid_temp_period = [0] * 5
pid_temp_p = [0] * 5
pid_temp_i = [0] * 5
pid_temp_d = [0] * 5
pid_temp_or = [0] * 5
pid_temp_alive = [1] * 5
pid_temp_down = 0
pid_temp_up = 0
pid_temp_number = None

# Humidity PID
pid_hum_relay = [0] * 5
pid_hum_set = [0] * 5
pid_hum_period = [0] * 5
pid_hum_p = [0] * 5
pid_hum_i = [0] * 5
pid_hum_d = [0] * 5
pid_hum_or = [0] * 5
pid_hum_alive = [1] * 5
pid_hum_down = 0
pid_hum_up = 0
pid_hum_number = None

# CO2 Sensors
sensor_co2_num = 0
sensor_co2_name = [0] * 5
sensor_co2_device = [0] * 5
sensor_co2_pin = [0] * 5
sensor_co2_period = [0] * 5
sensor_co2_log = [0] * 5
sensor_co2_graph = [0] * 5
sensor_co2_read_co2 = [0] * 5

# CO2 PID
pid_co2_relay = [0] * 5
pid_co2_set = [0] * 5
pid_co2_period = [0] * 5
pid_co2_p = [0] * 5
pid_co2_i = [0] * 5
pid_co2_d = [0] * 5
pid_co2_or = [0] * 5
pid_co2_alive = [1] * 5
pid_co2_down = 0
pid_co2_up = 0
pid_co2_number = None

# Timers
timer_num = None
timer_name = [0] * 9
timer_relay = [0] * 9
timer_state = [0] * 9
timer_duration_on = [0] * 9
timer_duration_off = [0] * 9
timer_change = 0

# SMTP notify
smtp_host = None
smtp_ssl = None
smtp_port = None
smtp_user = None
smtp_pass = None
smtp_email_from = None
smtp_email_to = None

# Miscellaneous
camera_light = None
server = None
client_que = '0'
client_var = None
terminate = False

def menu():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:ruv',
            ["add", "delete-rows", "delete-tables", "create-tables", "db-recreate", "db-setup", "load", "row", "update", "view"])
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
        elif opt == "--load":
            load_global_db(0)
            return 1
        elif opt in ("-r", "--row"):
            delete_row(sys.argv[2], sys.argv[3])
            return 1
        elif opt in ("-u", "--update"):
            update_value(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
            return 1
        elif opt in ("-v", "--view"):
            print "View Values"
            view_columns()
            return 1
        else:
            assert False, "Fail"

def setup_db():
    delete_all_tables()
    create_all_tables()
    create_rows_columns()
    
def delete_all_tables():
    print "Delete Tables"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS Relays ')
    cur.execute('DROP TABLE IF EXISTS HTSensor ')
    cur.execute('DROP TABLE IF EXISTS CO2Sensor ')
    cur.execute('DROP TABLE IF EXISTS Timers ')
    cur.execute('DROP TABLE IF EXISTS Numbers ')
    cur.execute('DROP TABLE IF EXISTS SMTP ')
    #cur.execute('DROP TABLE IF EXISTS Strings ')
    #cur.execute('DROP TABLE IF EXISTS Integers ')
    #cur.execute('DROP TABLE IF EXISTS Floats ')
    conn.close()
    
def create_all_tables():
    print "Create Tables"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute("CREATE TABLE Relays (Id INT, Name TEXT, Pin INT, Trigger INT)")
    cur.execute("CREATE TABLE HTSensor (Id INT, Name TEXT, Pin INT, Device TEXT, Period INT, Activated INT, Graph INT, Temp_Relay INT, Temp_OR INT, Temp_Set REAL, Temp_P REAL, Temp_I REAL, Temp_D, Hum_Relay INT, Hum_OR INT, Hum_Set REAL, Hum_P REAL, Hum_I REAL, Hum_D REAL)")
    cur.execute("CREATE TABLE CO2Sensor (Id INT, Name TEXT, Pin INT, Device TEXT, Period INT, Activated INT, Graph INT, CO2_Relay INT, CO2_OR INT, CO2_Set INT, CO2_P REAL, CO2_I REAL, CO2_D REAL)")
    cur.execute("CREATE TABLE Timers (Id INT, Name TEXT, Relay INT, State INT, DurationOn INT, DurationOff INT)")
    cur.execute("CREATE TABLE Numbers (Relays INT, HTSensors INT, CO2Sensors INT, Timers INT)")
    cur.execute("CREATE TABLE SMTP (Host TEXT, SSL INT, Port INT, User TEXT, Pass TEXT, Email_From TEXT, Email_To TEXT)")
    #cur.execute('CREATE TABLE Strings (row TEXT, column TEXT)')
    #cur.execute('CREATE TABLE Integers (row TEXT, column INTEGER)')
    #cur.execute('CREATE TABLE Floats (row TEXT, column REAL)')
    conn.close()
    
def create_rows_columns():
    print "Create Rows and Columns"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    for i in range(1, 9):
        cur.execute("INSERT INTO Relays VALUES(%d, 'Relay%d', 0, 0)" % (i, i))
    for i in range(1, 5):
        cur.execute("INSERT INTO HTSensor VALUES(%d, 'HTSensor%d', 0, 'DHT22', 10, 0, 0, 0, 1, 25.0, 1.1, 1.2, 1.3, 0, 1, 50.0, 1.1, 1.2, 1.3)" % (i, i))
    for i in range(1, 5):
        cur.execute("INSERT INTO CO2Sensor VALUES(%d, 'CO2Sensor%d', 0, 'K30', 10, 0, 0, 0, 1, 1000, 1.1, 1.2, 1.3)" % (i, i))
    for i in range(1, 9):
        cur.execute("INSERT INTO Timers VALUES(%d, 'Timer%d', 0, 0, 60, 360)" % (i, i))
    cur.execute("INSERT INTO Numbers VALUES(8, 3, 1, 4)")
    cur.execute("INSERT INTO SMTP VALUES('smtp.gmail.com', 1, 587, 'email@gmail.com', 'password', 'me@gmail.com', 'you@gmail.com')")
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
    
def add_columns(table, variable, value):
    #print "Add to Table: %s Variable: %s Value: %s" % (table, row, column)
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    if represents_int(column) or represents_float(column):
        query = "INSERT INTO %s (row) VALUES ( '%s' )" % (table, variable, value)
    else:
        query = "INSERT INTO %s (row) VALUES ( %s )" % (table, variable, value)
    cur.execute(query)
    conn.commit()
    cur.close()

def view_columns():
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    
    cur.execute('SELECT Id, Name, Pin, Trigger FROM Relays')
    print "Table: Relays"
    for row in cur :
        print "%s %s %s %s" % (row[0], row[1], row[2], row[3])

    cur.execute('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_P, Hum_I, Hum_D FROM HTSensor')
    print "Table: HTSensor"
    for row in cur :
        print "%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18])
    
    cur.execute('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay, CO2_OR, CO2_Set, CO2_P, CO2_I, CO2_D FROM CO2Sensor ')
    print "Table: CO2Sensor "
    for row in cur :
        print "%s %s %s %s %s %s %s %s %s %s %s %s %s" % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12])
    
    cur.execute('SELECT Id, Name, State, Relay, DurationOn, DurationOff FROM Timers ')
    print "Table: Timers "
    for row in cur :
        print "%s %s %s %s %s %s" % (row[0], row[1], row[2], row[3], row[4], row[5])
        
    cur.execute('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers ')
    print "Table: Numbers "
    for row in cur :
        print "%s %s %s %s" % (row[0], row[1], row[2], row[3])
        
    cur.execute('SELECT Host, SSL, Port, User, Pass, Email_From, Email_To FROM SMTP ')
    print "Table: SMTP "
    for row in cur :
        print "%s %s %s %s %s %s %s" % (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
    
    cur.close()
    
def load_global_db(verbose):
    global relay_name
    global relay_pin
    global relay_trigger
    
    global sensor_ht_name
    global sensor_ht_device
    global sensor_ht_pin
    global sensor_ht_period
    global sensor_ht_log
    global sensor_ht_graph
    
    global pid_temp_relay
    global pid_temp_set
    global pid_temp_or
    global pid_temp_p
    global pid_temp_i
    global pid_temp_d
    
    global pid_hum_relay
    global pid_hum_set
    global pid_hum_or
    global pid_hum_p
    global pid_hum_i
    global pid_hum_d
    
    global sensor_co2_name
    global sensor_co2_device
    global sensor_co2_pin
    global sensor_co2_period
    global sensor_co2_log
    global sensor_co2_graph
    
    global pid_co2_period
    global pid_co2_relay
    global pid_co2_set
    global pid_co2_or
    global pid_co2_p
    global pid_co2_i
    global pid_co2_d
    
    global relay_num
    global sensor_ht_num
    global sensor_co2_num
    global timer_num
    
    global timer_relay
    global timer_state
    global timer_duration_on
    global timer_duration_off
    
    global smtp_host
    global smtp_ssl
    global smtp_port
    global smtp_user
    global smtp_pass
    global smtp_email_from
    global smtp_email_to
    
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    
    # Check if tables exist in database
    cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    for table in cur:
        if verbose:
            print table
        if table[0] != 'Relays' and table[0] != 'HTSensor' and table[0] != 'CO2Sensor' and table[0] != 'Timers' and table[0] != 'Numbers' and table[0] != 'SMTP':
            print "Missing table(s): Cannot load database to global variables."
            return 0
  
    cur.execute('SELECT Id, Name, Pin, Trigger FROM Relays')
    if verbose:
            print "Table: Relays"
    for row in cur :
        if verbose:
            print "%s %s %s %s" % (row[0], row[1], row[2], row[3])
        relay_name[row[0]] = row[1]
        relay_pin[row[0]] = row[2]
        relay_trigger[row[0]] = row[3]

    cur.execute('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_P, Hum_I, Hum_D FROM HTSensor')
    if verbose:
            print "Table: HTSensor"
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s%s " % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18])
        sensor_ht_name[row[0]] = row[1]
        sensor_ht_pin[row[0]] = row[2]
        sensor_ht_device[row[0]] = row[3]
        sensor_ht_period[row[0]] = row[4]
        sensor_ht_log[row[0]] = row[5]
        sensor_ht_graph[row[0]] = row[6]
        pid_temp_relay[row[0]] = row[7]
        pid_temp_or[row[0]] = row[8]
        pid_temp_set[row[0]] = row[9]
        pid_temp_p[row[0]] = row[10]
        pid_temp_i[row[0]] = row[11]
        pid_temp_d[row[0]] = row[12]
        pid_hum_relay[row[0]] = row[13]
        pid_hum_or[row[0]] = row[14]
        pid_hum_set[row[0]] = row[15]
        pid_hum_p[row[0]] = row[16]
        pid_hum_i[row[0]] = row[17]
        pid_hum_d[row[0]] = row[18]
    
    cur.execute('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay, CO2_OR, CO2_Set, CO2_P, CO2_I, CO2_D FROM CO2Sensor ')
    if verbose:
            print "Table: CO2Sensor "
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s %s %s %s %s %s %s %s" % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12])
        sensor_co2_name[row[0]] = row[1]
        sensor_co2_pin[row[0]] = row[2]
        sensor_co2_device[row[0]] = row[3]
        sensor_co2_period[row[0]] = row[4]
        sensor_co2_log[row[0]] = row[5]
        sensor_co2_graph[row[0]] = row[6]
        pid_co2_relay[row[0]] = row[7]
        pid_co2_or[row[0]] = row[8]
        pid_co2_set[row[0]] = row[9]
        pid_co2_p[row[0]] = row[10]
        pid_co2_i[row[0]] = row[11]
        pid_co2_d[row[0]] = row[12]
    
    cur.execute('SELECT Id, Name, Relay, State, DurationOn, DurationOff FROM Timers ')
    if verbose:
            print "Table: Timers "
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s" % (row[0], row[1], row[2], row[3], row[4], row[5])
        timer_name[row[0]] = row[1]
        timer_relay[row[0]] = row[2]
        timer_state[row[0]] = row[3]
        timer_duration_on[row[0]] = row[4]
        timer_duration_off[row[0]] = row[5]
        
    cur.execute('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers ')
    if verbose:
            print "Table: Numbers "
    for row in cur :
        if verbose:
            print "%s %s %s %s" % (row[0], row[1], row[2], row[3])
        relay_num = row[0]
        sensor_ht_num = row[1]
        sensor_co2_num = row[2]
        timer_num = row[3]
        
    cur.execute('SELECT Host, SSL, Port, User, Pass, Email_From, Email_To FROM SMTP ')
    if verbose:
            print "Table: SMTP "
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s %s" % (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        smtp_host = row[0]
        smtp_ssl = row[1]
        smtp_port = row[2]
        smtp_user = row[3]
        smtp_pass = row[4]
        smtp_email_from = row[5]
        smtp_email_to = row[6]
  
    #cur.execute('SELECT row, column FROM Strings')
    #for row in cur :
    #    if verbose:
    #        print "Load Global Variable: %s Value: %s" % (row[0], row[1])
    #    globals()[row[0]] = row[1]

    cur.close()
    
def delete_all_rows():
    print "Delete All Rows"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DELETE FROM Relays ')
    cur.execute('DELETE FROM HTSensor ')
    cur.execute('DELETE FROM CO2Sensor ')
    cur.execute('DELETE FROM Timers ')
    cur.execute('DELETE FROM Numbers ')
    cur.execute('DELETE FROM SMTP ')
    #cur.execute('DELETE FROM Strings')
    #cur.execute('DELETE FROM Integers')
    #cur.execute('DELETE FROM Floats')
    conn.commit()
    cur.close()
    
def delete_row(table, Id):
    print "Delete Row: %s" % row
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    query = "DELETE FROM %s WHERE Id = '%s' " % (table, Id)
    cur.execute(query)
    conn.commit()
    cur.close()
    
def update_value(table, Id, variable, value):
    print "Update Table: %s Id: %s Variable: %s Value: %s" % (table, Id, variable, value)
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    if represents_int(value) or represents_float(value):
        query = "UPDATE %s SET %s=%s WHERE Id=%s" % (table, variable, value, Id)
    else:
        query = "UPDATE %s SET %s='%s' WHERE Id=%s" % (table, variable, value, Id)
    cur.execute(query)
    conn.commit()
    cur.close() 

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
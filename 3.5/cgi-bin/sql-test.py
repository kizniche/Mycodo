#!/usr/bin/python

import getopt
import sqlite3
import sys

sql_database = '/var/www/mycodo/config/mycodo.sqlite3'

def menu():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:cdruv',
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
#!/usr/bin/python

import getopt
import sqlite3
import sys

sql_database = '/var/www/mycodo/config/mycodo.sqlite3'

def menu():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:cdruv',
            ["add", "db-create", "db-delete", "db-recreate", "db-setup", "row", "update", "view"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        return 2
    for opt, arg in opts:
        if opt in ("-a", "--add"):
            add_columns(sys.argv[2], sys.argv[3], sys.argv[4])
            return 1
        elif opt in ("--db-create"):
            create_db()
            return 1
        elif opt in ("--db-delete"):
            delete_db()
            return 1
        elif opt in ("--db-recreate"):
            print "Recreate Database"
            delete_db()
            create_db()
            return 1
        elif opt in ("--db-setup"):
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
    cur.execute('CREATE TABLE Configuration (row TEXT, column INTEGER)')
    cur.execute('CREATE TABLE PID (row TEXT, column REAL)')
    conn.close()
    
def setup_db():
    delete_db()
    create_db()
    add_columns('Configuration', 'HUM1Set', 0)
    add_columns('Configuration', 'HUM2Set', 0)
    add_columns('Configuration', 'HUM3Set', 0)
    add_columns('Configuration', 'HUM4Set', 0)
    add_columns('Configuration', 'TEMP1Set', 0)
    add_columns('Configuration', 'TEMP2Set', 0)
    add_columns('Configuration', 'TEMP3Set', 0)
    add_columns('Configuration', 'TEMP4Set', 0)
    add_columns('Configuration', 'CO21Set', 0)
    add_columns('Configuration', 'CO22Set', 0)
    add_columns('Configuration', 'CO23Set', 0)
    add_columns('Configuration', 'CO24Set', 0)
    add_columns('PID', 'HUM1P', 0.0)
    add_columns('PID', 'HUM1I', 0.0)
    add_columns('PID', 'HUM1D', 0.0)
    add_columns('PID', 'TEMP1P', 0.0)
    add_columns('PID', 'TEMP1I', 0.0)
    add_columns('PID', 'TEMP1D', 0.0)
    add_columns('PID', 'CO21P', 0.0)
    add_columns('PID', 'CO21I', 0.0)
    add_columns('PID', 'CO21D', 0.0)

def delete_db():
    print "Delete Database"
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS Configuration ')
    cur.execute('DROP TABLE IF EXISTS PID ')
    conn.close()
    
def add_columns(table, row, column):
    print "Add to Table: %s Variable: %s Value: %s" % (table, row, column)
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    if represents_int(column) or represents_float(column):
        query = "INSERT INTO %s (row, column) VALUES ( '%s', %s )" % (table, row, column)
        cur.execute(query)
    conn.commit()
    cur.close()

def view_columns():
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
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
    cur.execute('DELETE FROM Configuration WHERE column != 0')
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
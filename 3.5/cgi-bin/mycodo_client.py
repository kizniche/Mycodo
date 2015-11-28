#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo-client.py - Client for mycodo.py. Communicates with daemonized
#                     mycodo.py to execute commands and receive status.
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

import argparse
import datetime
import socket
import sys

import rpyc

# TODO: Move to logging printing to STDOUT (for line prefix)
# TODO: Run it and see if it works

VALID_PID_TYPES = ["TTemp", "HTTemp", "HTHum", "CO2", "PressTemp", "PressPress"]
now = datetime.datetime.now


def menu2():
    parser = argparse.ArgumentParser(
            description="Client for mycodo.py daemon (daemon must be running).",
            formatter_class=argparse.RawTextHelpFormatter)

    graph_options = parser.add_argument_group('Graph options')
    graph_options.add_argument('--graph', nargs=7, metavar=(
        'THEME', 'GRAPH_TYPE', 'GRAPH_ID', 'GRAPH_SPAN', 'TIME_FROM', 'TIME_TO', 'WIDTH'),
                               help="Generate graph, where time_from and time_to are the number of seconds since epoch")

    pid_options = parser.add_argument_group('PID controls')
    pid_options.add_argument('--pidstart', nargs=2, metavar=("PID_TYPE", "PID_NUMBER"),
                             help="Start PID Controller. Valid options are: {{{}}}".format(
                                     ", ".join(VALID_PID_TYPES)))
    pid_options.add_argument('--pidstop', nargs=2, metavar=("PID_TYPE", "PID_NUMBER"),
                             help="Stop PID Controller. Valid options are: {{{}}}".format(
                                     ", ".join(VALID_PID_TYPES)))
    pid_options.add_argument('--pidrestart', nargs=2, metavar=("PID_TYPE", "PID_NUMBER"),
                             help="Restart PID Controller. Valid options are: {{{}}}".format(
                                     ", ".join(VALID_PID_TYPES)))
    pid_options.add_argument('--pidallrestart', choices=['T', 'HT', 'CO2'],
                             help="Restart all PIDs of a particular type.")

    relay_option = parser.add_argument_group('Relay Controls')
    relay_option.add_argument('-r', '--relay', nargs=2, metavar=("RELAY", "STATE"),
                              help="Turn a relay on or off. \nState can be 0, 1, or X; 0=OFF, 1=ON, or X number of seconds on")
    relay_option.add_argument('--sqlreload', nargs=1, metavar='RELAY',
                              help="Reload the SQLite database, initialize GPIO of relay if relay != -1")

    sensor_options = parser.add_argument_group('Sensor controls')
    sensor_options.add_argument('--sensort', nargs=2, metavar=("DEVICE", "SENSOR_NUMBER"),
                                help="Returns a reading from the temperature on given GPIO pin\n"
                                     "Device options: DS18B20")
    sensor_options.add_argument('--sensorht', nargs=2, metavar=("DEVICE", "SENSOR_NUMBER"),
                                help="Returns a reading from the temperature and humidity sensor on given GPIO pin\n"
                                     "Device options: DHT22, DHT11, or AM2302")
    sensor_options.add_argument('--sensorco2', nargs=2, metavar=("DEVICE", "SENSOR_NUMBER"),
                                help="Returns a reading from the CO2 sensor on given GPIO pin\n Device options: K30")
    sensor_options.add_argument('--sensorpress', nargs=2, metavar=("DEVICE", "SENSOR_NUMBER"),
                                help="Returns a reading from the pressure sensor on given GPIO pin\n"
                                     "Device options: BMP085-180")

    misc_options = parser.add_argument_group('Misc.')
    misc_options.add_argument('-s', '--status', action='store_true',
                              help="Return the status of the daemon and all global variables")
    misc_options.add_argument('-t', '--terminate', action='store_true',
                              help="Terminate the communication service and daemon")
    misc_options.add_argument('--test_email', nargs=1, metavar='RECIPIENT',
                              help="Send a test email")

    args = parser.parse_args()

    ########################################
    #                                      #
    #       Connect to RPyC server         #
    #                                      #
    ########################################

    try:
        c = rpyc.connect("localhost", 18812)
    except socket.error:
        print("Connection refused.")
        sys.exit(1)

    ########################################
    #                                      #
    #            Graph Options             #
    #                                      #
    ########################################

    if args.graph:
        print(
            "{}, [Remote command] Graph: {} {} {} {} {} {} {}".format(now(), *args.graph))

        print("{} [Remote command] Server returned:".format(now()))

        if c.root.GenerateGraph(*args.graph):
            print("Success")
        else:
            print("Fail")

    ########################################
    #                                      #
    #             PID Options              #
    #                                      #
    ########################################

    if args.pidstart:
        pid_type, pid_number = args.pidstart

        if pid_type not in VALID_PID_TYPES:
            print("invalid pid_type: {}  (choose from '{}')".format(pid_type, "', '".join(
                    VALID_PID_TYPES)))
            sys.exit(1)

        try:
            pid_number = int(pid_number)
        except ValueError:
            print("Not a valid PID number: {}".format(pid_number))
            sys.exit(1)

        print "{} [Remote command] Start {} PID controller number {}: Server returned:".format(
                now(), pid_type, pid_number)

        reload_status = c.root.PID_start(pid_type, pid_number)

        if reload_status == 1:
            print("Success")
        else:
            print "Failure: {}".format(reload_status)
            sys.exit(1)

    if args.pidstop:
        pid_type, pid_number = args.pidstop

        if pid_type not in VALID_PID_TYPES:
            print("invalid pid_type: {}  (choose from '{}')".format(pid_type, "', '".join(
                    VALID_PID_TYPES)))
            sys.exit(1)

        try:
            pid_number = int(pid_number)
        except ValueError:
            print("Not a valid PID number: {}".format(pid_number))
            sys.exit(1)

        print "{} [Remote command] Stop {} PID controller number {}: Server returned:".format(
                now(), pid_type, pid_number),
        reload_status = c.root.PID_stop(pid_type, pid_number)
        if reload_status == 1:
            print("Success")
        else:
            print "Failure: {}".format(reload_status)
            sys.exit(1)

    if args.pidrestart:
        pid_type, pid_number = args.pidrestart

        if pid_type not in VALID_PID_TYPES:
            print("invalid pid_type: {}  (choose from '{}')".format(pid_type, "', '".join(
                    VALID_PID_TYPES)))
            sys.exit(1)

        try:
            pid_number = int(pid_number)
        except ValueError:
            print("Not a valid PID number: {}".format(pid_number))
            sys.exit(1)

        print "{} [Remote command] Restart {} PID controller number %s: Server returned:".format(
                now(), pid_type, pid_number)

        reload_status = c.root.PID_restart(pid_type, pid_number)
        if reload_status == 1:
            print("Success")
        else:
            print "Failure: {}".format(reload_status)
            sys.exit(1)

    if args.pidallrestart:
        pid_type = args.pidallrestart

        print("{} [Remote command] Restart all {} PID controllers: Server returned:".format(
                now(), pid_type))

        reload_status = c.root.all_PID_restart(pid_type)
        if reload_status == 1:
            print("Success!")
        else:
            print("Failure: ".format(reload_status))
            sys.exit(1)

    ########################################
    #                                      #
    #            Relay Options             #
    #                                      #
    ########################################

    if args.relay:
        relay_id, state = args.relay

        try:
            relay_id = int(relay_id)
        except ValueError:
            print("Not a valid Relay ID: {}".format(relay_id))
            sys.exit(1)

        try:
            state = int(state)
        except ValueError:
            print("Invalid state given: {}".format(state))
            sys.exit(1)

        # State 1 or 0 is On or Off.  Anything greater than 1 is duration for relay.
        if state <= 0:
            print("State must not be negative")
            sys.exit(1)

        if relay_id not in [0, 1]:
            print("Relay ID must be 0 or 1")
            sys.exit(1)

        if state > 1:
            print('{} [Remote command] Relay {} ON for {} seconds: Server returned:'.format(now(),
                                                                                            relay_id,
                                                                                            state))
        else:
            print(
                "{} [Remote command] Set Relay {} to {}: Server returned:".format(now(), relay_id,
                                                                                  "On" if state else "Off"))

        if c.root.ChangeRelay(relay_id, state) == 1:
            print 'Success'
        else:
            print 'Failure.'
            sys.exit(1)

    if args.sqlreload:
        relay_id = args.sqlreload

        try:
            relay_id = int(relay_id)
        except ValueError:
            print("Not a valid Relay ID: {}".format(relay_id))
            sys.exit(1)

        if relay_id == -1:
            print("{} [Remote command] Reload SQLite database: Server returned:".format(now()))
        else:
            print(
            "{} [Remote command] Reload SQLite database and initialize relay {}: Server returned:".format(
                    now(), relay_id))

        if c.root.SQLReload(relay_id) == 1:
            print("Success")
        else:
            print("Fail")

    ########################################
    #                                      #
    #           Sensor Options             #
    #                                      #
    ########################################

    if args.sensort:
        device, sensor_number = args.sensort

        device = device.upper()

        if device not in ['DS18B20']:
            print("Invalid device name.  Please select a valid device.")
            sys.exit(1)

        try:
            sensor_number = int(sensor_number)
        except ValueError:
            print("Not a valid Sensor number: {}".format(sensor_number))
            sys.exit(1)

        print("{} [Remote command] Read {} T sensor {}".format(now(), device, sensor_number))
        temperature = c.root.ReadTSensor(device, sensor_number)
        print(
            "{} [Remote Command] Daemon Returned: Temperature: {:.2f}°C".format(now(),
                                                                                temperature))

    if args.sensorht:
        device, sensor_number = args.sensorht
        device = device.upper()

        if device not in ['DHT22', 'DHT11', 'AM2302']:
            print("Invalid device name.  Please select a valid device.")
            sys.exit(1)

        try:
            sensor_number = int(sensor_number)
        except ValueError:
            print("Not a valid Sensor number: {}".format(sensor_number))
            sys.exit(1)

        print("{} [Remote command] Read {} HT sensor {}".format(now(), device, sensor_number))
        humidity, temperature = c.root.ReadHTSensor(device, sensor_number)
        print(
            "{} [Remote Command] Daemon Returned: Temperature: {:.2f}°C Humidity: {:.2f}%".format(
                    now(), temperature, humidity))

    if args.sensorco2:
        device, sensor_number = args.sensorco2
        device = device.upper()

        if device.lower() not in ['K30']:
            print("Invalid device name.  Please select a valid device.")
            sys.exit(1)

        try:
            sensor_number = int(sensor_number)
        except ValueError:
            print("Not a valid Sensor number: {}".format(sensor_number))
            sys.exit(1)

        print "{} [Remote command] Read {} CO2 sensor {}".format(now(), device, sensor_number)
        co2 = c.root.ReadCO2Sensor(device, sensor_number)
        print "{} [Remote Command] Daemon Returned: CO2: {} ppmv".format(now(), co2)

    if args.sensorpress:
        device, sensor_number = args.sensorpress
        device = device.upper()

        if device.lower() not in ['BMP085-180']:
            print("Invalid device name.  Please select a valid device.")
            sys.exit(1)

        try:
            sensor_number = int(sensor_number)
        except ValueError:
            print("Not a valid Sensor number: {}".format(sensor_number))
            sys.exit(1)

        print("{} [Remote command] Read {} Pressure sensor {}".format(now(), device, sensor_number))
        pressure, temperature, altitude = c.root.ReadPressSensor(device, sensor_number)
        print("{} [Remote Command] Daemon Returned: Pressure: {} kPa Temperature: {:2f}°C Altitude: {:.2f} m".format(
                now(), pressure, temperature, altitude))

    ########################################
    #                                      #
    #                Misc.                 #
    #                                      #
    ########################################
    if args.status:
        print "{} [Remote command] Request Status Report: Daemon is active:".format(now()),
        output, names, values = c.root.Status(1)
        if output == 1:
            print "Yes"
            print "Parsing global variables..."
        else:
            print "No"

        padding = 36
        for name, value in zip(names, values):
            print "{} {}".format(name.ljust(padding, "."), value)

    if args.terminate:
        print "{} [Remote command] Terminate all threads and daemon: Server returned:".format(
                now()),
        if c.root.Terminate(1) == 1:
            print("Success")
        else:
            print("Fail")

    if args.test_email:
        recepient = args.test_email
        print(
        "{} [Remote command] Send test email to %s: Server returned:".format(now(), recepient))
        if c.root.TestEmail(recepient) == 1:
            print "Success (check your email for confirmation)"
        else:
            print("Fail")
            sys.exit(1)


if __name__ == "__main__":
    menu2()
    sys.exit(0)

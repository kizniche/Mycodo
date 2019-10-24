#!/bin/bash
# Sleeps until able to connect to InfluxDB (port 8086)
# Used by mycodo.service to determine when it's safe to start the Mycodo daemon

until nc -z localhost 8086; do sleep 1; done

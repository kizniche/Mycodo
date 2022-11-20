#!/bin/bash

set -m

INFLUX_HOST="localhost"
INFLUX_API_PORT="8086"
API_URL="http://${INFLUX_HOST}:${INFLUX_API_PORT}"

printf "=> Starting InfluxDB...\n"
exec influxd &

# Pre create database on the initiation of the container
if [ -n "${PRE_CREATE_DB}" ]; then
    printf "=> About to create the following database: ${PRE_CREATE_DB}\n"
    if [ -f "/var/lib/influxdb/.pre_db_created" ]; then
        printf "=> Database had been created before, skipping ...\n"
    else
        arr=$(printf "${PRE_CREATE_DB}" | tr ";" "\n")

        #wait for the startup of influxdb
        RET=1
        while [[ RET -ne 0 ]]; do
            printf "=> Waiting for confirmation of InfluxDB service startup ...\n"
            sleep 3
            curl -k ${API_URL}/ping
            RET=$?
        done

        PASS=${INFLUXDB_INIT_PWD:-root}
        if [ -n "${ADMIN_USER}" ]; then
          printf "=> Creating admin user\n"
          influx -host=${INFLUX_HOST} -port=${INFLUX_API_PORT} -execute="CREATE USER ${ADMIN_USER} WITH PASSWORD '${PASS}' WITH ALL PRIVILEGES"
          for x in $arr
          do
              printf "=> Creating database: ${x}\n"
              influx -host=${INFLUX_HOST} -port=${INFLUX_API_PORT} -username="${ADMIN_USER}" -password="${PASS}" -execute="create database ${x}"
              influx -host=${INFLUX_HOST} -port=${INFLUX_API_PORT} -username="${ADMIN_USER}" -password="${PASS}" -execute="grant all PRIVILEGES on ${x} to ${ADMIN_USER}"
          done
        else
          for x in $arr
          do
              printf "=> Creating database: ${x}\n"
              influx -host=${INFLUX_HOST} -port=${INFLUX_API_PORT} -execute="create database \"${x}\""
          done
        fi

        touch "/var/lib/influxdb/.pre_db_created"
    fi
else
    printf "=> No database need to be pre-created\n"
fi

fg

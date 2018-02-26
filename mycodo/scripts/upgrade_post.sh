#!/bin/bash
#
#  upgrade_post.sh - Commands to execute after a Mycodo upgrade
#

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root\n";
    exit
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
INSTALL_DEP="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/dependencies.sh"
cd ${INSTALL_DIRECTORY}

${INSTALL_CMD} create-symlinks

printf "\n#### Removing statistics file\n"
rm ${INSTALL_DIRECTORY}/databases/statistics.csv

${INSTALL_CMD} update-swap-size

${INSTALL_CMD} setup-virtualenv

${INSTALL_CMD} update-wiringpi

${INSTALL_CMD} update-apt

${INSTALL_CMD} update-packages

${INSTALL_CMD} web-server-update

${INSTALL_CMD} update-logrotate

${INSTALL_CMD} update-pip3

${INSTALL_CMD} update-pip3-packages

${INSTALL_CMD} initialize

printf "\n#### Checking for updates to optional dependencies\n"
DEPENDENCIES=$(${INSTALL_DIRECTORY}/Mycodo/env/bin/python3 ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/dependencies_installed.py 2>&1)
IFS=, read -ra ary <<< "$DEPENDENCIES"
for opt in "${!ary[@]}"
do
    if [[ ${ary[opt]} ]] ; then
        if [ "$opt" == "Adafruit_ADS1x15" ]; then
            ${INSTALL_DEP} Adafruit_ADS1x15
        elif [ "$opt" == "Adafruit_Python_BME280" ]; then
            ${INSTALL_DEP} Adafruit_Python_BME280
        elif [ "$opt" == "Adafruit_Python_BMP" ]; then
            ${INSTALL_DEP} Adafruit_Python_BMP
        elif [ "$opt" == "Adafruit_GPIO" ]; then
            ${INSTALL_DEP} Adafruit_GPIO
        elif [ "$opt" == "Adafruit_MCP3008" ]; then
            ${INSTALL_DEP} Adafruit_MCP3008
        elif [ "$opt" == "Adafruit_TMP" ]; then
            ${INSTALL_DEP} Adafruit_TMP
        elif [ "$opt" == "MCP342x" ]; then
            ${INSTALL_DEP} MCP342x
        elif [ "$opt" == "pigpio" ]; then
            ${INSTALL_DEP} update-pigpiod
        elif [ "$opt" == "quick2wire" ]; then
            ${INSTALL_DEP} quick2wire
        elif [ "$opt" == "sht_sensor" ]; then
            ${INSTALL_DEP} sht_sensor
        elif [ "$opt" == "tsl2561" ]; then
            ${INSTALL_DEP} tsl2561
        elif [ "$opt" == "tsl2591" ]; then
            ${INSTALL_DEP} tsl2591
        elif [ "$opt" == "w1thermsensor" ]; then
            ${INSTALL_DEP} w1thermsensor
        fi
    fi
done

${INSTALL_CMD} update-influxdb

${INSTALL_CMD} update-alembic

${INSTALL_CMD} update-mycodo-startup-script

${INSTALL_CMD} compile-translations

${INSTALL_CMD} update-cron

${INSTALL_CMD} initialize

${INSTALL_CMD} restart-daemon

${INSTALL_CMD} web-server-reload

${INSTALL_CMD} web-server-connect

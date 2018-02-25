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

DEPENDENCIES=$(${INSTALL_DIRECTORY}/Mycodo/env/bin/python3 ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/dependencies_installed.py 2>&1)

IFS=, read -ra ary <<< "$DEPENDENCIES"
printf "%s\n" "${ary[@]}"

for opt in "${!ary[@]}"
do
    if [[ ${ary[opt]} ]] ; then
        if [ "$opt" == "1" ]; then
            ${INSTALL_CMD} install-pip-dependency Adafruit_ADS1x15
        elif [ "$opt" == "2" ]; then
            ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280
        elif [ "$opt" == "3" ]; then
            ${INSTALL_CMD} install-pip-dependency Adafruit_GPIO
        elif [ "$opt" == "4" ]; then
            ${INSTALL_CMD} install-pip-dependency Adafruit_MCP3008
        elif [ "$opt" == "5" ]; then
            ${INSTALL_CMD} install-pip-dependency Adafruit_TMP
        elif [ "$opt" == "6" ]; then
            ${INSTALL_CMD} install-pip-dependency MCP342x==0.3.3
        elif [ "$opt" == "7" ]; then
            ${INSTALL_CMD} update-pigpiod
        elif [ "$opt" == "8" ]; then
            ${INSTALL_CMD} install-pip-dependency sht_sensor==17.5.5
        elif [ "$opt" == "9" ]; then
            ${INSTALL_CMD} install-pip-dependency tsl2561
        elif [ "$opt" == "10" ]; then
            ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/maxlklaxl/python-tsl2591.git#egg=tsl2591
        elif [ "$opt" == "11" ]; then
            ${INSTALL_CMD} install-pip-dependency w1thermsensor==1.0.5
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

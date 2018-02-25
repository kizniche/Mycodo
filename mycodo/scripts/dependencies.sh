#!/bin/bash
#
#  dependencies.sh - Commands to install dependencies
#

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
cd ${INSTALL_DIRECTORY}

case "${1:-''}" in
    'Adafruit_ADS1x15')
        ${INSTALL_CMD} install-pip-dependency Adafruit_ADS1x15
    ;;
    'Adafruit_Python_BME280')
        ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280
    ;;
    'Adafruit_GPIO')
        ${INSTALL_CMD} install-pip-dependency Adafruit_GPIO
    ;;
    'Adafruit_MCP3008')
        ${INSTALL_CMD} install-pip-dependency Adafruit_MCP3008
    ;;
    'Adafruit_TMP')
        ${INSTALL_CMD} install-pip-dependency Adafruit_TMP
    ;;
    'MCP342x')
        ${INSTALL_CMD} install-pip-dependency MCP342x==0.3.3
    ;;
    'install-pigiod')
        ${INSTALL_CMD} install-pigpiod
        ${INSTALL_CMD} enable-pigpiod-low
    ;;
    'update-pigiod')
        ${INSTALL_CMD} update-pigpiod
    ;;
    'sht_sensor')
        ${INSTALL_CMD} install-pip-dependency sht_sensor==17.5.5
    ;;
    'tsl2561')
        ${INSTALL_CMD} install-pip-dependency tsl2561
    ;;
    'tsl2591')
        ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/maxlklaxl/python-tsl2591.git#egg=tsl2591
    ;;
    'w1thermsensor')
        ${INSTALL_CMD} install-pip-dependency w1thermsensor==1.0.5
    ;;
    *)
        printf "\nUnrecognized dependency"
    ;;
esac

${INSTALL_CMD} update-permissions

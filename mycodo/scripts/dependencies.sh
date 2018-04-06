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

printf "\n#### Installing/updating ${1}\n"

case "${1:-''}" in
    'Adafruit_ADS1x15')
        ${INSTALL_CMD} install-pip-dependency Adafruit_ADS1x15
    ;;
    'Adafruit_BME280')
        ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280 --upgrade
    ;;
    'Adafruit_BMP')
        ${INSTALL_CMD} install-pip-dependency Adafruit_BMP
    ;;
    'Adafruit_GPIO')
        ${INSTALL_CMD} install-pip-dependency Adafruit_GPIO
    ;;
    'Adafruit_MAX31855')
        ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/adafruit/Adafruit_Python_MAX31855.git#egg=adafruit-max31855 --upgrade
    ;;
    'Adafruit_MCP3008')
        ${INSTALL_CMD} install-pip-dependency Adafruit_MCP3008
    ;;
    'Adafruit_TMP')
        ${INSTALL_CMD} install-pip-dependency Adafruit_TMP
    ;;
    'bluepy')
        apt-get install -y libglib2.0-dev
        ${INSTALL_CMD} install-pip-dependency bluepy==1.1.4
    ;;
    'btlewrap')
        ${INSTALL_CMD} install-pip-dependency btlewrap==0.0.2
    ;;
    'MCP342x')
        ${INSTALL_CMD} install-pip-dependency MCP342x==0.3.3
    ;;
    'miflora')
        ${INSTALL_CMD} install-pip-dependency miflora==0.3
    ;;
    'numpy')
        ${INSTALL_CMD} install-numpy
    ;;
    'install-pigpiod')
        ${INSTALL_CMD} install-pigpiod
        ${INSTALL_CMD} enable-pigpiod-low
    ;;
    'quick2wire')
        ${INSTALL_CMD} install-pip-dependency quick2wire-api
    ;;
    'rpi_rf')
        ${INSTALL_CMD} install-pip-dependency rpi-rf
    ;;
    'update-pigpiod')
        ${INSTALL_CMD} update-pigpiod
    ;;
    'sht_sensor')
        ${INSTALL_CMD} install-pip-dependency sht_sensor==18.4.2
    ;;
    'tsl2561')
        ${INSTALL_CMD} install-pip-dependency tsl2561
    ;;
    'tsl2591')
        ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/maxlklaxl/python-tsl2591.git#egg=tsl2591 --upgrade
    ;;
    'w1thermsensor')
        ${INSTALL_CMD} install-pip-dependency w1thermsensor==1.0.5
    ;;
    'wiringpi')
        ${INSTALL_CMD} install-wiringpi
    ;;
    *)
        printf "\nUnrecognized dependency: ${1}"
    ;;
esac

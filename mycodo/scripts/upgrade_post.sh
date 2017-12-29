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

ln -sf ${INSTALL_DIRECTORY} /var/www/mycodo

printf "\n#### Removing statistics file\n"
rm ${INSTALL_DIRECTORY}/databases/statistics.csv

${INSTALL_CMD} update-swap-size

${INSTALL_CMD} setup-virtualenv

${INSTALL_CMD} update-gpiod

${INSTALL_CMD} update-wiringpi

${INSTALL_CMD} update-apt

${INSTALL_CMD} update-packages

${INSTALL_CMD} update-web-server

${INSTALL_CMD} update-logrotate

${INSTALL_CMD} update-pip3

${INSTALL_CMD} update-pip3-packages

${INSTALL_CMD} update-influxdb

${INSTALL_CMD} update-alembic

${INSTALL_CMD} update-mycodo-startup-script

${INSTALL_CMD} compile-translations

${INSTALL_CMD} update-cron

${INSTALL_CMD} initialize

${INSTALL_CMD} restart-daemon

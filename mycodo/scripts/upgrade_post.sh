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

cd ${INSTALL_DIRECTORY} || exit

${INSTALL_CMD} initialize

printf "\n#### Removing statistics files\n"
rm -f ${INSTALL_DIRECTORY}/databases/statistics.csv
rm -f ${INSTALL_DIRECTORY}/databases/statistics.id

${INSTALL_CMD} update-swap-size
${INSTALL_CMD} setup-virtualenv
${INSTALL_CMD} update-apt
${INSTALL_CMD} update-packages
${INSTALL_CMD} web-server-update
${INSTALL_CMD} update-logrotate
${INSTALL_CMD} update-pip3
${INSTALL_CMD} update-pip3-packages
${INSTALL_CMD} update-permissions

printf "\n#### Checking for updates to dependencies\n"
${INSTALL_DIRECTORY}/env/bin/python ${INSTALL_DIRECTORY}/mycodo/utils/update_installed_dependencies.py

${INSTALL_CMD} update-influxdb
${INSTALL_CMD} update-alembic
${INSTALL_CMD} update-mycodo-startup-script
${INSTALL_CMD} update-pyro-startup-script
${INSTALL_CMD} pyro-restart
${INSTALL_CMD} compile-translations
${INSTALL_CMD} update-cron
${INSTALL_CMD} update-permissions
${INSTALL_CMD} restart-daemon
${INSTALL_CMD} web-server-reload
${INSTALL_CMD} web-server-connect

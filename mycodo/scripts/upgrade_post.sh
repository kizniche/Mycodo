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

${INSTALL_CMD} initialize

printf "\n#### Removing statistics file\n"
rm ${INSTALL_DIRECTORY}/databases/statistics.csv

${INSTALL_CMD} update-swap-size
${INSTALL_CMD} setup-virtualenv
${INSTALL_CMD} update-apt
${INSTALL_CMD} update-packages
${INSTALL_CMD} web-server-update
${INSTALL_CMD} update-logrotate
${INSTALL_CMD} update-pip3
${INSTALL_CMD} update-pip3-packages
${INSTALL_CMD} update-permissions
${INSTALL_CMD} upgrade-pip3-packages

printf "\n#### Checking for updates to optional dependencies\n"
DEPENDENCIES=$(${INSTALL_DIRECTORY}/env/bin/python3 ${INSTALL_DIRECTORY}/mycodo/utils/dependencies_installed.py 2>&1)
IFS=','
for i in $DEPENDENCIES
do
    ${INSTALL_DEP} echo $i
done

${INSTALL_CMD} update-influxdb
${INSTALL_CMD} update-alembic
${INSTALL_CMD} update-mycodo-startup-script
${INSTALL_CMD} compile-translations
${INSTALL_CMD} update-cron
${INSTALL_CMD} update-permissions
${INSTALL_CMD} restart-daemon
${INSTALL_CMD} web-server-reload
${INSTALL_CMD} web-server-connect

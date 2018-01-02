#!/bin/bash
#
#  setup.sh - Mycodo install script
#
#  Usage: sudo /bin/bash ~/Mycodo/install/setup.sh
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
LOG_LOCATION=${INSTALL_DIRECTORY}/install/setup.log

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root: \"sudo /bin/bash ${INSTALL_DIRECTORY}/install/setup.sh\"\n";
    exit
fi

exec > >(tee -i -a ${LOG_LOCATION})
exec 2>&1

abort()
{
    echo >&2 '
************************************
** ERROR: Mycodo Install Aborted! **
************************************

An error occurred that may have prevented Mycodo from
being installed properly!

Please contact the developer by submitting a bug report
at https://github.com/kizniche/Mycodo/issues with the
pertinent excerpts from the setup log located at:
${INSTALL_DIRECTORY}/install/setup.log
'
    echo "An error occurred. Exiting..." >&2
    exit 1
}

trap 'abort' 0

set -e

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "### Mycodo installation beginning at $NOW\n"

${INSTALL_CMD} update-swap-size

${INSTALL_CMD} update-apt

${INSTALL_CMD} uninstall-apt-pip

${INSTALL_CMD} update-packages

${INSTALL_CMD} setup-virtualenv

${INSTALL_CMD} update-pip3

${INSTALL_CMD} update-gpiod

${INSTALL_CMD} update-wiringpi

${INSTALL_CMD} update-pip3-packages

${INSTALL_CMD} update-influxdb

${INSTALL_CMD} update-influxdb-db-user

${INSTALL_CMD} update-logrotate

${INSTALL_CMD} generate-ssl-certs

${INSTALL_CMD} update-mycodo-startup-script

${INSTALL_CMD} compile-translations

${INSTALL_CMD} update-cron

${INSTALL_CMD} initialize

${INSTALL_CMD} web-server-update

${INSTALL_CMD} web-server-restart

${INSTALL_CMD} web-server-connect

${INSTALL_CMD} update-permissions

${INSTALL_CMD} restart-daemon

trap : 0

IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

if [[ -z ${IP} ]]; then
  IP="your.IP.address.here"
fi

date
echo >&2 "
***************************************************
** Mycodo successfully installed without errors! **
***************************************************

Go to https://${IP}/, or whatever your Raspberry Pi's
IP address is, to create an admin user and log in.
"

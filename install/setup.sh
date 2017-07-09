#!/bin/bash
#
# Mycodo install script
#
# Usage: sudo /bin/bash Mycodo/install/setup.sh
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd -P )

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root: \"sudo /bin/bash ${INSTALL_DIRECTORY}/install/setup.sh\"\n";
    exit
fi

LOG_LOCATION=${INSTALL_DIRECTORY}/install/setup.log
exec > >(tee -i -a ${LOG_LOCATION})
exec 2>&1

abort()
{
    echo >&2 '
*******************************
*** ERROR: Install Aborted! ***
*******************************

An error occurred that prevented Mycodo from being installed!

Please contact the developer by submitting a bug report at
https://github.com/kizniche/Mycodo/issues with the pertinent
excerpts from the setup log located at Mycodo/install/setup.log
'
    echo "An error occurred. Exiting..." >&2
    exit 1
}

trap 'abort' 0

set -e

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "### Mycodo installation beginning at $NOW\n"

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-swap-size

printf "\n#### Uninstalling apt version of pip (if installed)\n"
apt-get update
apt-get purge -y python-pip

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-packages

pip install --upgrade pip

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh setup-virtualenv

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-gpiod

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-wiringpi

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-pip-packages

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-influxdb

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-influxdb-db-user

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-apache2

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh generate-ssl-certs

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-mycodo-startup-script

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh compile-translations

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-cron

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh initialize

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh restart-web-ui

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-permissions

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh restart-daemon

trap : 0

IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

if [[ -z ${IP} ]]; then
  IP="your.IP.here"
fi

echo >&2 "
***************************************************
** Mycodo successfully installed without errors! **
***************************************************

Go to https://${IP}/, or whatever your Pi's
IP address is, to create an admin user and log in.
"

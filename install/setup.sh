#!/bin/bash
#
#  setup.sh - Mycodo install script
#
#  Usage: sudo /bin/bash ~/Mycodo/install/setup.sh
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
INSTALL_DEP="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/dependencies.sh"
LOG_LOCATION=${INSTALL_DIRECTORY}/install/setup.log

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root: \"sudo /bin/bash ${INSTALL_DIRECTORY}/install/setup.sh\"\n";
    exit 1
fi

WHIPTAIL=$(command -v whiptail)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "\nwhiptail not installed. Install it with 'sudo apt-get install whiptail' then try the install again.\n"
    exit 1
fi

NOW=$(date)
printf "### Mycodo installation initiated $NOW\n" 2>&1 | tee -a ${LOG_LOCATION}

clear
LICENSE=$(whiptail --title "Mycodo Installer: License Agreement" \
                   --backtitle "Mycodo" \
                   --yesno "Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.\n\nMycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License along with Mycodo. If not, see gnu.org/licenses\n\nDo you agree to the license terms?" \
                   20 68 \
                   3>&1 1>&2 2>&3)

exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "Mycodo install canceled by user" 2>&1 | tee -a ${LOG_LOCATION}
    exit 1
fi

clear
INSTALL=$(whiptail --title "Mycodo Installer: Install" \
                   --backtitle "Mycodo" \
                   --yesno "Mycodo will be installed in the home directory of the current user. Several software packages will be installed via apt, including the nginx web server that the Mycodo web user interface will be hosted on. Proceed with the installation?" \
                   20 68 \
                   3>&1 1>&2 2>&3)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "Mycodo install canceled by user" 2>&1 | tee -a ${LOG_LOCATION}
    exit 1
fi

abort()
{
    printf "
**********************************
** ERROR During Mycodo Install! **
**********************************

An error occurred that may have prevented Mycodo from
being installed properly!

Open to the end of the setup log to view the full error:
${INSTALL_DIRECTORY}/install/setup.log

Please contact the developer by submitting a bug report
at https://github.com/kizniche/Mycodo/issues with the
pertinent excerpts from the setup log located at:
${INSTALL_DIRECTORY}/install/setup.log
" 2>&1 | tee -a ${LOG_LOCATION}
    exit 1
}

trap 'abort' 0

set -e

clear
SECONDS=0
NOW=$(date)
printf "#### Mycodo installation began $NOW\n" 2>&1 | tee -a ${LOG_LOCATION}

${INSTALL_CMD} update-swap-size 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-apt 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} uninstall-apt-pip 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-packages 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} setup-virtualenv 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-pip3 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-pip3-packages 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} install-wiringpi 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-influxdb 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-influxdb-db-user 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} initialize 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-logrotate 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} ssl-certs-generate 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-mycodo-startup-script 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-pyro-startup-script 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} compile-translations 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-cron 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} initialize 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} web-server-update 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} web-server-restart 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} web-server-connect 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} update-permissions 2>&1 | tee -a ${LOG_LOCATION}
${INSTALL_CMD} restart-daemon 2>&1 | tee -a ${LOG_LOCATION}

trap : 0

IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

if [[ -z ${IP} ]]; then
  IP="your.IP.address.here"
fi

CURRENT_DATE=$(date)
printf "#### Mycodo Installer finished ${CURRENT_DATE}\n" 2>&1 | tee -a ${LOG_LOCATION}

DURATION=$SECONDS
printf "#### Total install time: $(($DURATION / 60)) minutes and $(($DURATION % 60)) seconds\n" 2>&1 | tee -a ${LOG_LOCATION}

printf "
************************************
** Mycodo successfully installed! **
************************************

The full install log is located at:
${INSTALL_DIRECTORY}/install/setup.log

Go to https://${IP}/, or whatever your Raspberry Pi's
IP address is, to create an admin user and log in.
" 2>&1 | tee -a ${LOG_LOCATION}

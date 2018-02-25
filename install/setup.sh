#!/bin/bash
#
#  setup.sh - Mycodo install script
#
#  Usage: sudo /bin/bash ~/Mycodo/install/setup.sh
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd -P )
CURRENT_VERSION=$(${INSTALL_DIRECTORY}/Mycodo/env/bin/python3 ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
INSTALL_DEP="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/dependencies.sh"
LOG_LOCATION=${INSTALL_DIRECTORY}/install/setup.log
INSTALL_TYPE="Full"

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root: \"sudo /bin/bash ${INSTALL_DIRECTORY}/install/setup.sh\"\n";
    exit
fi

command -v whiptail >/dev/null || {
    printf "\nwhiptail not installed. Install it with 'sudo apt-get install whiptail' then try the install again.\n"
    exit;
}

abort()
{
    echo '
************************************
** ERROR: Mycodo Install Aborted! **
************************************

An error occurred that may have prevented Mycodo from
being installed properly!

Open to the end of the setup log to view the full error:
${INSTALL_DIRECTORY}/install/setup.log

Please contact the developer by submitting a bug report
at https://github.com/kizniche/Mycodo/issues with the
pertinent excerpts from the setup log located at:
${INSTALL_DIRECTORY}/install/setup.log
' 2>&1 | tee -a ${LOG_LOCATION}
    exit 1
}

trap 'abort' 0

set -e

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "### Mycodo installation began at $NOW\n" >>${LOG_LOCATION}

clear
LICENSE=$(whiptail --title "Mycodo Installer: License Agreement" \
                   --backtitle "Mycodo ${CURRENT_VERSION}" \
                   --yesno "Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.\nMycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with Mycodo. If not, see gnu.org/licenses.\n\nDo you agree to the license terms?" \
                   18 68 \
                   3>&1 1>&2 2>&3)

exitstatus=$?
if [ $exitstatus != 0 ]; then
    echo "Install canceled by user" >>${LOG_LOCATION}
    exit
fi

clear
INSTALL_TYPE=$(whiptail --title "Mycodo Installer: Install Type" \
                        --backtitle "Mycodo ${CURRENT_VERSION}" \
                        --notags \
                        --menu "Select the Install Type:\n\nFull: Install all dependencies\nMinimal: Install a minimal set of dependencies\nCustom: Select which dependencies to install\n\nIf unsure, choose 'Full Install'" \
                        18 68 3 \
                        "full" "Full Install (recommended)" \
                        "minimal" "Minimal Install" \
                        "custom" "Custom Install" \
                        3>&1 1>&2 2>&3)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    echo "Install canceled by user" >>${LOG_LOCATION}
    exit
fi
printf "\nInstall Type: $INSTALL_TYPE\n"

if [ "$INSTALL_TYPE" == "custom" ]; then
    clear
    INSTALL_DEP=$(whiptail --title "Mycodo Install: Custom" \
                           --backtitle "Mycodo ${CURRENT_VERSION}" \
                           --notags \
                           --checklist "Dependencies to Install" \
                           18 68 11 \
                           1 "Adafruit_ADS1x15" off \
                           2 "Adafruit_BME280" off \
                           3 "Adafruit_GPIO" off \
                           4 "Adafruit_MCP3008" off \
                           5 "Adafruit_TMP" off \
                           6 "MCP342x" off \
                           7 "pigpio" off \
                           8 "sht_sensor" off \
                           9 "tsl2561" off \
                           10 "tsl2591" off \
                           11 "w1thermsensor" off \
                           3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        echo "Install canceled by user" >>${LOG_LOCATION}
        exit
    fi
    printf "\nDependencies: $INSTALL_DEP\n" >>${LOG_LOCATION}
fi

{
    echo -e "XXX\n4\nChecking swap size... \nXXX"
    ${INSTALL_CMD} update-swap-size >>${LOG_LOCATION}

    echo -e "XXX\n5\nUpdating apt sources... \nXXX"
    ${INSTALL_CMD} update-apt >>${LOG_LOCATION}

    echo -e "XXX\n4\nRemoving apt- version of pip... \nXXX"
    ${INSTALL_CMD} uninstall-apt-pip >>${LOG_LOCATION}

    echo -e "XXX\n5\nInstall dependencies (apt)... \nXXX"
    ${INSTALL_CMD} update-packages >>${LOG_LOCATION}

    echo -e "XXX\n4\nSetting up virtualenv... \nXXX"
    ${INSTALL_CMD} setup-virtualenv >>${LOG_LOCATION}

    echo -e "XXX\n5\nUpdating pip... \nXXX"
    ${INSTALL_CMD} update-pip3 >>${LOG_LOCATION}

    echo -e "XXX\n4\nInstalling WiringPi... \nXXX"
    ${INSTALL_CMD} update-wiringpi >>${LOG_LOCATION}

    echo -e "XXX\n5\nInstalling base python packages... \nXXX"
    ${INSTALL_CMD} update-pip3-packages >>${LOG_LOCATION}

    if [ "$INSTALL_TYPE" == "minimal" ]; then
        printf '\n### Minimal install selected. No more dependencies to install.'
    elif [ "$INSTALL_TYPE" == "custom" ]; then
        printf '\n### Installing custom-selected dependencies'
        echo -e "XXX\n4\nInstalling custom python packages... \nXXX"
        for option in $INSTALL_DEP
        do
            option="${option%\"}"
            option="${option#\"}"
            if [ "$option" == "1" ]; then
                ${INSTALL_DEP} Adafruit_ADS1x15 >>${LOG_LOCATION}
            elif [ "$option" == "2" ]; then
                ${INSTALL_DEP} Adafruit_Python_BME280 >>${LOG_LOCATION}
            elif [ "$option" == "3" ]; then
                ${INSTALL_DEP} Adafruit_GPIO >>${LOG_LOCATION}
            elif [ "$option" == "4" ]; then
                ${INSTALL_DEP} Adafruit_MCP3008 >>${LOG_LOCATION}
            elif [ "$option" == "5" ]; then
                ${INSTALL_DEP} Adafruit_TMP >>${LOG_LOCATION}
            elif [ "$option" == "6" ]; then
                ${INSTALL_DEP} MCP342x >>${LOG_LOCATION}
            elif [ "$option" == "7" ]; then
                ${INSTALL_DEP} install-pigpiod >>${LOG_LOCATION}
            elif [ "$option" == "8" ]; then
                ${INSTALL_DEP} sht_sensor >>${LOG_LOCATION}
            elif [ "$option" == "9" ]; then
                ${INSTALL_DEP} tsl2561 >>${LOG_LOCATION}
            elif [ "$option" == "10" ]; then
                ${INSTALL_DEP} tsl2591 >>${LOG_LOCATION}
            elif [ "$option" == "11" ]; then
                ${INSTALL_DEP} w1thermsensor >>${LOG_LOCATION}
            fi
        done
    elif [ "$INSTALL_TYPE" == "full" ]; then
        ${INSTALL_DEP} Adafruit_ADS1x15 >>${LOG_LOCATION}
        ${INSTALL_DEP} Adafruit_Python_BME280 >>${LOG_LOCATION}
        ${INSTALL_DEP} Adafruit_GPIO >>${LOG_LOCATION}
        ${INSTALL_DEP} Adafruit_MCP3008 >>${LOG_LOCATION}
        ${INSTALL_DEP} Adafruit_TMP >>${LOG_LOCATION}
        ${INSTALL_DEP} MCP342x >>${LOG_LOCATION}
        ${INSTALL_DEP} install-pigpiod >>${LOG_LOCATION}
        ${INSTALL_DEP} sht_sensor >>${LOG_LOCATION}
        ${INSTALL_DEP} tsl2561 >>${LOG_LOCATION}
        ${INSTALL_DEP} tsl2591 >>${LOG_LOCATION}
        ${INSTALL_DEP} w1thermsensor >>${LOG_LOCATION}
    fi

    echo -e "XXX\n5\nInstalling InfluxDB... \nXXX"
    ${INSTALL_CMD} update-influxdb >>${LOG_LOCATION}

    echo -e "XXX\n4\nInstalling InfluxDB database and user... \nXXX"
    ${INSTALL_CMD} update-influxdb-db-user >>${LOG_LOCATION}

    echo -e "XXX\n5\nInstalling logrotate... \nXXX"
    ${INSTALL_CMD} update-logrotate >>${LOG_LOCATION}

    echo -e "XXX\n4\nGenerating SSL certificate... \nXXX"
    ${INSTALL_CMD} ssl-certs-generate >>${LOG_LOCATION}

    echo -e "XXX\n5\nInstalling Mycodo startup script... \nXXX"
    ${INSTALL_CMD} update-mycodo-startup-script >>${LOG_LOCATION}

    echo -e "XXX\n4\nCompiling translations... \nXXX"
    ${INSTALL_CMD} compile-translations >>${LOG_LOCATION}

    echo -e "XXX\n5\nUpdating cron... \nXXX"
    ${INSTALL_CMD} update-cron >>${LOG_LOCATION}

    echo -e "XXX\n4\nInitializing install... \nXXX"
    ${INSTALL_CMD} initialize >>${LOG_LOCATION}

    echo -e "XXX\n5\nUpdating web server... \nXXX"
    ${INSTALL_CMD} web-server-update >>${LOG_LOCATION}

    echo -e "XXX\n4\nRestarting web server... \nXXX"
    ${INSTALL_CMD} web-server-restart >>${LOG_LOCATION}

    echo -e "XXX\n5\nConnecting to web server... \nXXX"
    ${INSTALL_CMD} web-server-connect >>${LOG_LOCATION}

    echo -e "XXX\n4\nUpdating permissions... \nXXX"
    ${INSTALL_CMD} update-permissions >>${LOG_LOCATION}

    echo -e "XXX\n5\nRestarting daemon... \nXXX"
    ${INSTALL_CMD} restart-daemon >>${LOG_LOCATION}

} | whiptail --gauge "Installing Mycodo. Please wait..." 6 50 0

trap : 0

IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

if [[ -z ${IP} ]]; then
  IP="your.IP.address.here"
fi

CURRENT_DATE=$(date)
printf "Mycodo Installer finished  ${CURRENT_DATE}" 2>&1 | tee -a ${LOG_LOCATION}
echo "
************************************
** Mycodo successfully installed! **
************************************

The full install log is located at:
${INSTALL_DIRECTORY}/install/setup.log

Go to https://${IP}/, or whatever your Raspberry Pi's
IP address is, to create an admin user and log in.
" 2>&1 | tee -a ${LOG_LOCATION}

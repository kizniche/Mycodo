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
INSTALL_TYPE="Full"

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root: \"sudo /bin/bash ${INSTALL_DIRECTORY}/install/setup.sh\"\n";
    exit
fi

WHIPTAIL=$(command -v whiptail)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "\nwhiptail not installed. Install it with 'sudo apt-get install whiptail' then try the install again.\n"
    exit 1
fi

abort()
{
    printf "
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
" 2>&1 | tee -a ${LOG_LOCATION}
    exit 1
}

trap 'abort' 0

set -e

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "### Mycodo installation initiated at $NOW\n" 2>&1 | tee -a ${LOG_LOCATION}

clear
LICENSE=$(whiptail --title "Mycodo Installer: License Agreement" \
                   --backtitle "Mycodo" \
                   --yesno "Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.\n\nMycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License along with Mycodo. If not, see gnu.org/licenses\n\nDo you agree to the license terms?" \
                   20 68 \
                   3>&1 1>&2 2>&3)

exitstatus=$?
if [ $exitstatus != 0 ]; then
    echo "Install canceled by user" 2>&1 | tee -a ${LOG_LOCATION}
    exit
fi

clear
INSTALL_TYPE=$(whiptail --title "Mycodo Installer: Install Type" \
                        --backtitle "Mycodo" \
                        --notags \
                        --menu "\nSelect the Install Type:\n\nFull: Install all dependencies\nMinimal: Install a minimal set of dependencies\nCustom: Select which dependencies to install\n\nIf unsure, choose 'Full Install'" \
                        20 68 3 \
                        "full" "Full Install (recommended)" \
                        "minimal" "Minimal Install" \
                        "custom" "Custom Install" \
                        3>&1 1>&2 2>&3)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    echo "Install canceled by user" 2>&1 | tee -a ${LOG_LOCATION}
    exit
fi
printf "\nInstall Type: $INSTALL_TYPE\n" >>${LOG_LOCATION} 2>&1

if [ "$INSTALL_TYPE" == "custom" ]; then
    clear
    INSTALL_DEP=$(whiptail --title "Mycodo Install: Custom" \
                           --backtitle "Mycodo" \
                           --notags \
                           --checklist "Dependencies to Install" \
                           20 68 13 \
                           'Adafruit_ADS1x15' "Adafruit_ADS1x15" off \
                           'Adafruit_BME280' "Adafruit_BME280" off \
                           'Adafruit_BMP' "Adafruit_BMP" off \
                           'Adafruit_GPIO' "Adafruit_GPIO" off \
                           'Adafruit_MCP3008' "Adafruit_MCP3008" off \
                           'Adafruit_TMP' "Adafruit_TMP" off \
                           'MCP342x' "MCP342x" off \
                           'pigpio' "pigpio" off \
                           'quick2wire' "quick2wire" off \
                           'sht_sensor' "sht_sensor" off \
                           'tsl2561' "tsl2561" off \
                           'tsl2591' "tsl2591" off \
                           'w1thermsensor' "w1thermsensor" off \
                           3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        echo "Install canceled by user" 2>&1 | tee -a ${LOG_LOCATION}
        exit
    fi
fi

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "### Mycodo installation began at $NOW\n" 2>&1 | tee -a ${LOG_LOCATION}

{
    echo -e "XXX\n4\nChecking swap size... \nXXX"
    ${INSTALL_CMD} update-swap-size >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n9\nUpdating apt sources... \nXXX"
    ${INSTALL_CMD} update-apt >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n13\nRemoving apt version of pip... \nXXX"
    ${INSTALL_CMD} uninstall-apt-pip >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n18\nInstalling apt dependencies... \nXXX"
    ${INSTALL_CMD} update-packages >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n22\nSetting up virtualenv... \nXXX"
    ${INSTALL_CMD} setup-virtualenv >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n27\nUpdating virtualenv pip... \nXXX"
    ${INSTALL_CMD} update-pip3 >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n31\nInstalling WiringPi... \nXXX"
    ${INSTALL_CMD} update-wiringpi >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n36\nInstalling base python packages in virtualenv... \nXXX"
    ${INSTALL_CMD} update-pip3-packages >>${LOG_LOCATION} 2>&1

    if [ "$INSTALL_TYPE" == "minimal" ]; then
        printf '\n### Minimal install selected. No more dependencies to install.'
    elif [ "$INSTALL_TYPE" == "custom" ]; then
        printf '\n### Installing custom-selected dependencies'
        echo -e "XXX\n40\nInstalling custom python packages in virtualenv... \nXXX"
        for option in $INSTALL_DEP
        do
            option="${option%\"}"
            option="${option#\"}"
            if [ "$option" == "Adafruit_ADS1x15" ]; then
                ${INSTALL_DEP} Adafruit_ADS1x15 >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "Adafruit_Python_BME280" ]; then
                ${INSTALL_DEP} Adafruit_Python_BME280 >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "Adafruit_BMP" ]; then
                ${INSTALL_DEP} Adafruit_BMP >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "Adafruit_GPIO" ]; then
                ${INSTALL_DEP} Adafruit_GPIO >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "Adafruit_MCP3008" ]; then
                ${INSTALL_DEP} Adafruit_MCP3008 >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "Adafruit_TMP" ]; then
                ${INSTALL_DEP} Adafruit_TMP >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "MCP342x" ]; then
                ${INSTALL_DEP} MCP342x >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "pigpio" ]; then
                ${INSTALL_DEP} install-pigpiod >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "quick2wire" ]; then
                ${INSTALL_DEP} quick2wire >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "sht_sensor" ]; then
                ${INSTALL_DEP} sht_sensor >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "tsl2561" ]; then
                ${INSTALL_DEP} tsl2561 >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "tsl2591" ]; then
                ${INSTALL_DEP} tsl2591 >>${LOG_LOCATION} 2>&1
            elif [ "$option" == "w1thermsensor" ]; then
                ${INSTALL_DEP} w1thermsensor >>${LOG_LOCATION} 2>&1
            fi
        done
    elif [ "$INSTALL_TYPE" == "full" ]; then
        ${INSTALL_DEP} Adafruit_ADS1x15 >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} Adafruit_BMP >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} Adafruit_Python_BME280 >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} Adafruit_GPIO >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} Adafruit_MCP3008 >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} Adafruit_TMP >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} MCP342x >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} install-pigpiod >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} quick2wire >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} sht_sensor >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} tsl2561 >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} tsl2591 >>${LOG_LOCATION} 2>&1
        ${INSTALL_DEP} w1thermsensor >>${LOG_LOCATION} 2>&1
    fi

    echo -e "XXX\n45\nInstalling InfluxDB... \nXXX"
    ${INSTALL_CMD} update-influxdb >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n49\nSetting up InfluxDB database and user... \nXXX"
    ${INSTALL_CMD} update-influxdb-db-user >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n54\nSetting up logrotate... \nXXX"
    ${INSTALL_CMD} update-logrotate >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n58\nGenerating SSL certificate... \nXXX"
    ${INSTALL_CMD} ssl-certs-generate >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n63\nInstalling Mycodo startup script... \nXXX"
    ${INSTALL_CMD} update-mycodo-startup-script >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n67\nCompiling translations... \nXXX"
    ${INSTALL_CMD} compile-translations >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n72\nUpdating cron... \nXXX"
    ${INSTALL_CMD} update-cron >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n76\nSetting up files and folders... \nXXX"
    ${INSTALL_CMD} initialize >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n81\nSetting up the web server... \nXXX"
    ${INSTALL_CMD} web-server-update >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n85\nStarting the web server... \nXXX"
    ${INSTALL_CMD} web-server-restart >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n90\nCreating Mycodo database... \nXXX"
    ${INSTALL_CMD} web-server-connect >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n94\Setting permissions... \nXXX"
    ${INSTALL_CMD} update-permissions >>${LOG_LOCATION} 2>&1

    echo -e "XXX\n99\nStarting the Mycodo daemon... \nXXX"
    ${INSTALL_CMD} restart-daemon >>${LOG_LOCATION} 2>&1

} | whiptail --gauge "Installing Mycodo. Please wait..." 6 55 0

trap : 0

IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

if [[ -z ${IP} ]]; then
  IP="your.IP.address.here"
fi

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "Mycodo Installer finished  ${NOW}\n" 2>&1 | tee -a ${LOG_LOCATION}
printf "
************************************
** Mycodo successfully installed! **
************************************

The full install log is located at:
${INSTALL_DIRECTORY}/install/setup.log

Go to https://${IP}/, or whatever your Raspberry Pi's
IP address is, to create an admin user and log in.
" 2>&1 | tee -a ${LOG_LOCATION}

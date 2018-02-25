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
printf "### Mycodo installation began at $NOW\n"

INSTALL_TYPE="FULL"

printf "\nSelect the type of install you would like to perform."
printf "\nA 'full' install is recommended unless you know what you're doing.\n\n"

PS3="Please choose an option (1-3): "
select option in minimum custom full
do
    case $option in
        minimum)
            INSTALL_TYPE="MINIMAL"
            break;;
        custom)
            INSTALL_TYPE="CUSTOM"
            break;;
        full)
            INSTALL_TYPE="FULL"
            break;;
     esac
done

if [ "$INSTALL_TYPE" == "CUSTOM" ]; then
    choice () {
        local choice=$1
        if [[ ${opts[choice]} ]] # toggle
        then
            opts[choice]=
        else
            opts[choice]=+
        fi
    }

    PS3='Select which dependencies to install, then select "Done": '
    while :
    do
        clear
        options=(
            "Adafruit_ADS1x15 ${opts[1]}"
            "Adafruit_BME280 ${opts[2]}"
            "Adafruit_GPIO ${opts[3]}"
            "Adafruit_MCP3008 ${opts[4]}"
            "Adafruit_TMP ${opts[5]}"
            "MCP342x ${opts[6]}"
            "pigpio ${opts[7]}"
            "sht_sensor ${opts[8]}"
            "tsl2561 ${opts[9]}"
            "tsl2591 ${opts[10]}"
            "w1thermsensor ${opts[11]}"
            "Done"
        )
        select opt in "${options[@]}"
        do
            case $opt in
                "Adafruit_ADS1x15 ${opts[1]}")
                    choice 1
                    break
                    ;;
                "Adafruit_BME280 ${opts[2]}")
                    choice 2
                    break
                    ;;
                "Adafruit_GPIO ${opts[3]}")
                    choice 3
                    break
                    ;;
                "Adafruit_MCP3008 ${opts[4]}")
                    choice 4
                    break
                    ;;
                "Adafruit_TMP ${opts[5]}")
                    choice 5
                    break
                    ;;
                "MCP342x ${opts[6]}")
                    choice 6
                    break
                    ;;
                "pigpio ${opts[7]}")
                    choice 7
                    break
                    ;;
                "sht_sensor ${opts[8]}")
                    choice 8
                    break
                    ;;
                "tsl2561 ${opts[9]}")
                    choice 9
                    break
                    ;;
                "tsl2591 ${opts[10]}")
                    choice 10
                    break
                    ;;
                "w1thermsensor ${opts[11]}")
                    choice 11
                    break
                    ;;
                "Done")
                    break 2
                    ;;
                *) printf '\nInvalid option';;
            esac
        done
    done
fi

${INSTALL_CMD} update-swap-size

${INSTALL_CMD} update-apt

${INSTALL_CMD} uninstall-apt-pip

${INSTALL_CMD} update-packages

${INSTALL_CMD} setup-virtualenv

${INSTALL_CMD} update-pip3

${INSTALL_CMD} update-wiringpi

${INSTALL_CMD} update-pip3-packages

if [ "$INSTALL_TYPE" == "CUSTOM" ]; then
    printf '\n### Minimal install selected. No more dependencies to install.'
elif [ "$INSTALL_TYPE" == "CUSTOM" ]; then
    printf '\n### Installing custom-selected dependencies'
    for opt in "${!opts[@]}"
    do
        if [[ ${opts[opt]} ]] ; then
            if [ "$opt" == "1" ]; then
                ${INSTALL_CMD} install-pip-dependency Adafruit_ADS1x15
            elif [ "$opt" == "2" ]; then
                ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280
            elif [ "$opt" == "3" ]; then
                ${INSTALL_CMD} install-pip-dependency Adafruit_GPIO
            elif [ "$opt" == "4" ]; then
                ${INSTALL_CMD} install-pip-dependency Adafruit_MCP3008
            elif [ "$opt" == "5" ]; then
                ${INSTALL_CMD} install-pip-dependency Adafruit_TMP
            elif [ "$opt" == "6" ]; then
                ${INSTALL_CMD} install-pip-dependency MCP342x==0.3.3
            elif [ "$opt" == "7" ]; then
                ${INSTALL_CMD} install-pigpiod
                ${INSTALL_CMD} enable-pigpiod-low
            elif [ "$opt" == "8" ]; then
                ${INSTALL_CMD} install-pip-dependency sht_sensor==17.5.5
            elif [ "$opt" == "9" ]; then
                ${INSTALL_CMD} install-pip-dependency tsl2561
            elif [ "$opt" == "10" ]; then
                ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/maxlklaxl/python-tsl2591.git#egg=tsl2591
            elif [ "$opt" == "11" ]; then
                ${INSTALL_CMD} install-pip-dependency w1thermsensor==1.0.5
            fi
        fi
    done
elif [ "$INSTALL_TYPE" == "FULL" ]; then
    ${INSTALL_CMD} install-pip-dependency Adafruit_ADS1x15
    ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280
    ${INSTALL_CMD} install-pip-dependency Adafruit_GPIO
    ${INSTALL_CMD} install-pip-dependency Adafruit_MCP3008
    ${INSTALL_CMD} install-pip-dependency Adafruit_TMP
    ${INSTALL_CMD} install-pip-dependency MCP342x==0.3.3
    ${INSTALL_CMD} install-pigpiod
    ${INSTALL_CMD} enable-pigpiod-low
    ${INSTALL_CMD} install-pip-dependency sht_sensor==17.5.5
    ${INSTALL_CMD} install-pip-dependency tsl2561
    ${INSTALL_DIRECTORY}/env/bin/pip3 install -e git://github.com/maxlklaxl/python-tsl2591.git#egg=tsl2591
    ${INSTALL_CMD} install-pip-dependency w1thermsensor==1.0.5
fi

${INSTALL_CMD} update-influxdb

${INSTALL_CMD} update-influxdb-db-user

${INSTALL_CMD} update-logrotate

${INSTALL_CMD} ssl-certs-generate

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

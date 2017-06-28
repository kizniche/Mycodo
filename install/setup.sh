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

printf "#### Installing gpiod\n"
cd ${INSTALL_DIRECTORY}/install
wget --quiet -P ${INSTALL_DIRECTORY}/install abyz.co.uk/rpi/pigpio/pigpio.zip
unzip pigpio.zip
cd ${INSTALL_DIRECTORY}/install/PIGPIO
make -j4
make install
/usr/local/bin/pigpiod &
cd ${INSTALL_DIRECTORY}/install
rm -rf ./PIGPIO ./pigpio.zip

printf "#### Installing wiringpi\n"
git clone git://git.drogon.net/wiringPi ${INSTALL_DIRECTORY}/install/wiringPi
cd ${INSTALL_DIRECTORY}/install/wiringPi
./build
cd ${INSTALL_DIRECTORY}/install
rm -rf ./wiringPi

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-pip-packages

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-influxdb

printf "\n#### Creating InfluxDB database and user\n"
# Attempt to connect to influxdb 5 times, sleeping 60 seconds every fail
for i in {1..5}; do
    # Check if influxdb has successfully started and be connected to
    curl -sL -I localhost:8086/ping > /dev/null &&
    influx -execute "CREATE DATABASE mycodo_db" &&
    influx -database mycodo_db -execute "CREATE USER mycodo WITH PASSWORD 'mmdu77sj3nIoiajjs'" &&
    printf "Influxdb database and user successfully created\n" &&
    break ||
    # Else wait 60 seconds if the influxd port is not accepting connections
    printf "Could not connect to Influxdb. Waiting 60 seconds then trying again...\n" &&
    sleep 60
done

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-apache2

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh generate-ssl-certs

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-mycodo-startup-script

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh compile-translations

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-cron

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh compile-mycodo-wrapper

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh initialize

printf "\n#### Starting the Mycodo web server\n"
/etc/init.d/apache2 restart

printf "\n#### wget\n"
wget --quiet --no-check-certificate -p http://127.0.0.1 -O /dev/null

printf "\n#### Starting the Mycodo daemon\n"
service mycodo start

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

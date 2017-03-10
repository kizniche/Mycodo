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
exec > >(tee -i ${LOG_LOCATION})
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

printf "\n#### Uninstalling apt version of pip (if installed)\n"
apt-get update
apt-get purge -y python-pip

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-packages
pip install -U pip

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

printf "#### Installing pip requirements from requirements.txt\n"
cd ${INSTALL_DIRECTORY}/install
pip install -r requirements.txt --upgrade

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-influxdb
service influxdb start
printf "\n#### Creating InfluxDB database and user\n"
influx -execute "CREATE DATABASE mycodo_db"
influx -database mycodo_db -execute "CREATE USER mycodo WITH PASSWORD 'mmdu77sj3nIoiajjs'"

printf "\n#### Installing and configuring apache2 web server\n"
apt-get install -y apache2 libapache2-mod-wsgi
a2enmod wsgi ssl
ln -sf ${INSTALL_DIRECTORY}/install/mycodo_flask_apache.conf /etc/apache2/sites-enabled/000-default.conf

printf "\n#### Enabling mycodo startup script\n"
systemctl enable ${INSTALL_DIRECTORY}/install/mycodo.service

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh generate-ssl-certs

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh update-cron

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh compile-translations

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh initialize

printf "\n#### Starting the Mycodo daemon and web server\n"
service mycodo start
/etc/init.d/apache2 restart

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

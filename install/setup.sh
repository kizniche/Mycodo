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
printf "### Mycodo installation beginning at $NOW\n\n"

printf "#### Uninstalling current version of pip\n"
apt-get purge -y python-pip

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh upgrade-packages
pip install -U pip

cd ${INSTALL_DIRECTORY}/install
wget --quiet --show-progress -P ${INSTALL_DIRECTORY}/install abyz.co.uk/rpi/pigpio/pigpio.zip
unzip pigpio.zip
cd ${INSTALL_DIRECTORY}/install/PIGPIO
make -j4
make install

git clone git://git.drogon.net/wiringPi ${INSTALL_DIRECTORY}/install/wiringPi
cd ${INSTALL_DIRECTORY}/install/wiringPi
./build

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh upgrade-influxdb
service influxdb start

cd ${INSTALL_DIRECTORY}/install
pip install -r requirements.txt --upgrade

rm -rf ./PIGPIO ./pigpio.zip ./wiringPi

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh compile-translations

printf "#### Creating InfluxDB database and user\n"
influx -execute "CREATE DATABASE mycodo_db"
influx -database mycodo_db -execute "CREATE USER mycodo WITH PASSWORD 'mmdu77sj3nIoiajjs'"

printf "#### Creating cron entry to start pigpiod at boot\n"
/bin/bash ${INSTALL_DIRECTORY}/install/crontab.sh mycodo

printf "#### Installing and configuring apache2 web server\n"
apt-get install -y apache2 libapache2-mod-wsgi
a2enmod wsgi ssl
ln -sf ${INSTALL_DIRECTORY}/install/mycodo_flask_apache.conf /etc/apache2/sites-enabled/000-default.conf

printf "#### Generating SSL certificates at ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs (replace with your own if desired)\n"
mkdir -p ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs
cd ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs/

openssl req \
    -new \
    -x509 \
    -sha512 \
    -days 365 \
    -nodes \
    -out cert.pem \
    -keyout privkey.pem\
    -subj "/C=US/ST=Georgia/L=Atlanta/O=mycodo/OU=mycodo/CN=mycodo"

openssl genrsa -out certificate.key 1024

openssl req \
    -new \
    -key certificate.key \
    -out certificate.csr \
    -subj "/C=US/ST=Georgia/L=Atlanta/O=mycodo/OU=mycodo/CN=mycodo"

openssl x509 -req \
    -days 365 \
    -in certificate.csr -CA cert.pem \
    -CAkey privkey.pem \
    -set_serial $RANDOM \
    -out chain.pem

rm -f certificate.csr

printf "#### Enabling mycodo startup script\n"
systemctl enable ${INSTALL_DIRECTORY}/install/mycodo.service

printf "#### Creating SQLite databases\n"
python ${INSTALL_DIRECTORY}/init_databases.py -i all

printf "#### Setting up users, groups, and permissions\n"
/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo.sh initialize

printf "#### Starting the Mycodo daemon and web server\n"
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

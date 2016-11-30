#!/bin/bash
#
#  update_post.sh - Extra commands to execute for the update process.
#                   Used as a way to provide additional commands to
#                   execute that wouldn't be possible from the running
#                   update script.
#
#  Copyright (C) 2015  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com


if [ "$EUID" -ne 0 ]; then
    printf "Please run as root\n";
    exit
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
cd ${INSTALL_DIRECTORY}

ln -snf ${INSTALL_DIRECTORY} /var/www/mycodo
cp -f ${INSTALL_DIRECTORY}/mycodo_flask_apache.conf /etc/apache2/sites-available/

if [ -f "$INSTALL_DIRECTORY/mycodo_flask/ssl_certs/cert.pem" ] && [ ! -d "$INSTALL_DIRECTORY/mycodo/mycodo_flask/ssl_certs/" ]; then
    mkdir -p ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs/
    cp ${INSTALL_DIRECTORY}/mycodo_flask/ssl_certs/* ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs/
fi

${INSTALL_DIRECTORY}/mycodo/scripts/update_mycodo.sh upgrade-packages

printf "#### Enable mycodo service ####\n"
rm -rf /etc/systemd/system/mycodo.service
rm -rf /etc/systemd/system/multi-user.target.wants/mycodo.service
systemctl enable ${INSTALL_DIRECTORY}/mycodo/scripts/mycodo.service

printf "#### Upgrade influxdb if out-of-date ####\n"
INFLUX_VERSION=$(apt-cache policy influxdb | grep 'Installed' | gawk '{print $2}')
if [ "$INFLUX_VERSION" != "1.0.2-1" ]; then
    echo "Incorrect version of InfluxDB installed ($INFLUX_VERSION). Downloading and installing the latest tested version."
    wget https://dl.influxdata.com/influxdb/releases/influxdb_1.0.2_armhf.deb
    dpkg -i influxdb_1.0.2_armhf.deb
    rm -rf influxdb_1.0.2_armhf.deb
fi

printf "#### Move ssl certificates directory if not in correct directory\n"
if [ -d "$INSTALL_DIRECTORY/mycodo/frontend/ssl_certs" ]; then
    mv ${INSTALL_DIRECTORY}/mycodo/frontend/ssl_certs ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/
fi

printf "#### Checking if python modules are up-to-date ####\n"
pip install --upgrade -r ${INSTALL_DIRECTORY}/requirements.txt

printf "#### Upgrading database ####\n"
cd ${INSTALL_DIRECTORY}/databases
alembic upgrade head

printf "#### Removing statistics file ####\n"
rm ${INSTALL_DIRECTORY}/databases/statistics.csv

printf "#### Setting permissions ####\n"
${INSTALL_DIRECTORY}/mycodo/scripts/update_mycodo.sh initialize

printf "#### Starting Mycodo daemon and reloading Apache ####\n"
service mycodo start
touch ${INSTALL_DIRECTORY}/mycodo_flask.wsgi

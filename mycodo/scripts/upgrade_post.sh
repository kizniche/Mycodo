#!/bin/bash
#
#  upgrade_post.sh - Extra commands to execute for the upgrade process.
#                    Used as a way to provide additional commands to
#                    execute that wouldn't be possible from the running
#                    upgrade script.
#
#  Copyright (C) 2017  Kyle T. Gabriel
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

ln -sf ${INSTALL_DIRECTORY} /var/www/mycodo
ln -sf ${INSTALL_DIRECTORY}/install/mycodo_flask_apache.conf /etc/apache2/sites-enabled/000-default.conf

if [ -f "$INSTALL_DIRECTORY/mycodo_flask/ssl_certs/cert.pem" ] && [ ! -d "$INSTALL_DIRECTORY/mycodo/mycodo_flask/ssl_certs/" ]; then
    mkdir -p ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs/
    cp ${INSTALL_DIRECTORY}/mycodo_flask/ssl_certs/* ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs/
fi

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh upgrade-packages

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh upgrade-influxdb

printf "\n#### Move ssl certificates directory if not in correct directory\n"
if [ -d "$INSTALL_DIRECTORY/mycodo/frontend/ssl_certs" ]; then
    mv ${INSTALL_DIRECTORY}/mycodo/frontend/ssl_certs ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/
fi

printf "\n#### Checking if python modules are up-to-date ####\n"
pip install --upgrade -r ${INSTALL_DIRECTORY}/install/requirements.txt

printf "\n#### Upgrading database ####\n"
cd ${INSTALL_DIRECTORY}/databases
alembic upgrade head

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh compile-translations

printf "\n#### Removing statistics file ####\n"
rm ${INSTALL_DIRECTORY}/databases/statistics.csv

printf "\n#### Updating crontab entry ####\n"
/bin/bash ${INSTALL_DIRECTORY}/install/crontab.sh mycodo --remove
/bin/bash ${INSTALL_DIRECTORY}/install/crontab.sh mycodo

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh initialize

printf "\n#### Reloading systemctl, Mycodo daemon, and apache2 ####\n"
systemctl daemon-reload
service mycodo restart
/etc/init.d/apache2 restart

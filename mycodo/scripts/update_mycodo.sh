#!/bin/bash
#
#  update_mycodo.sh - Update Mycodo to the lastest version on GitHub
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
    printf "Please run as root\n"
    exit
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
cd $INSTALL_DIRECTORY

case "${1:-''}" in
    'backup')
        NOW=$(date +"%Y-%m-%d_%H-%M-%S")
        CURCOMMIT=$(git rev-parse --short HEAD)
        printf "#### $INSTALL_DIRECTORY Creating backup /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT ####\n"
        mkdir -p /var/Mycodo-backups
        mkdir -p /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT
        rsync -ah --stats $INSTALL_DIRECTORY/ /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT --exclude old --exclude .git -exclude src
    ;;
    'upgrade')
        echo "1" > $INSTALL_DIRECTORY/.updating
        NOW=$(date +"%m-%d-%Y %H:%M:%S")
        printf "#### Update Initiated $NOW ####\n"

        printf "#### Checking for Update ####\n"
        git fetch origin

        if git status -uno | grep 'Your branch is behind' > /dev/null; then
            git status -uno | grep 'Your branch is behind'
            printf "The remote git repository is newer than yours. This could mean there is an update to Mycodo.\n"

            if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
                printf "#### Stopping Mycodo Daemon ####\n"
                $INSTALL_DIRECTORY/mycodo/mycodo_client.py -t

                # Create backup
                $INSTALL_DIRECTORY/mycodo/scripts/update_mycodo.sh backup

                printf "#### Updating From GitHub ####\n"
                git fetch
                git reset --hard origin/master

                printf "#### Executing Post-Upgrade Commands ####\n"
                if [ -f $INSTALL_DIRECTORY/mycodo/scripts/update_post.sh ]; then
                    $INSTALL_DIRECTORY/mycodo/scripts/update_post.sh
                    printf "#### End Post-Upgrade Commands ####\n"
                else
                    printf "Error: update_post.sh not found\n"
                fi
                
                END=$(date +"%m-%d-%Y %H:%M:%S")
                printf "#### Update Finished $END ####\n\n"

                echo '0' > $INSTALL_DIRECTORY/.updating
                exit 0
            else
                printf "Error: No git repository found. Update stopped.\n\n"
                echo '0' > $INSTALL_DIRECTORY/.updating
                exit 1
            fi
        else
            printf "Your version of Mycodo is already the latest version.\n\n"
            echo "1" > $INSTALL_DIRECTORY/.updating
            exit 0
        fi
    ;;
    'setup')
        printf "#### Installing prerequisites\n"
        ln -snf $INSTALL_DIRECTORY /var/www/mycodo &&
        cp -f $INSTALL_DIRECTORY/mycodo_flask_apache.conf /etc/apache2/sites-available/ &&

        wget abyz.co.uk/rpi/pigpio/pigpio.zip -P $INSTALL_DIRECTORY/ &&
        unzip pigpio.zip &&
        cd $INSTALL_DIRECTORY/PIGPIO &&
        make -j4 &&
        sudo make install &&

        git clone git://git.drogon.net/wiringPi $INSTALL_DIRECTORY/wiringPi &&
        cd $INSTALL_DIRECTORY/wiringPi &&
        ./build &&

        wget https://dl.influxdata.com/influxdb/releases/influxdb_0.13.0_armhf.deb -P $INSTALL_DIRECTORY/ &&
        dpkg -i $INSTALL_DIRECTORY/influxdb_0.13.0_armhf.deb &&
        service influxdb start &&

        cd $INSTALL_DIRECTORY &&
        sudo pip install -r requirements.txt --upgrade &&

        rm -rf ./PIGPIO pigpio.zip wiringPi src influxdb_0.13.0_armhf.deb &&

        sleep 5 &&

        printf "#### Creating InfluxDB database and user\n"
        influx -execute "CREATE DATABASE mycodo_db" &&
        influx -database mycodo_db -execute "CREATE USER mycodo WITH PASSWORD 'mmdu77sj3nIoiajjs'" &&

        printf "#### Creating SQLite databases\n"
        $INSTALL_DIRECTORY/init_databases.py -i all &&

        printf "#### Creating Adminitrator User - Please answer the following questions (Note: your password will not display when you type it)\n"
        $INSTALL_DIRECTORY/init_databases.py -A &&
        
        printf "#### Creating cron entry to start pigpiod at boot\n"
        $INSTALL_DIRECTORY/mycodo/scripts/crontab.sh mycodo &&

        printf "#### Installing and configuring apache2 web server\n"
        apt-get install -y apache2 libapache2-mod-wsgi &&
        a2enmod wsgi ssl &&
        ln -s $INSTALL_DIRECTORY /var/www/mycodo &&
        ln -sf $INSTALL_DIRECTORY/mycodo_flask_apache.conf /etc/apache2/sites-enabled/000-default.conf &&

        printf "#### Creating SSL certificates at $INSTALL_DIRECTORY/mycodo/frontend/ssl_certs (replace with your own if desired)\n"
        mkdir -p $INSTALL_DIRECTORY/mycodo/frontend/ssl_certs &&
        cd $INSTALL_DIRECTORY/mycodo/frontend/ssl_certs/ &&

        openssl req \
            -new \
            -x509 \
            -sha512 \
            -days 365 \
            -nodes \
            -out cert.pem \
            -keyout privkey.pem\
            -subj "/C=US/ST=Georgia/L=Atlanta/O=mycodo/OU=mycodo/CN=mycodo" &&

        openssl genrsa -out certificate.key 1024 &&

        openssl req \
            -new \
            -key certificate.key \
            -out certificate.csr \
            -subj "/C=US/ST=Georgia/L=Atlanta/O=mycodo/OU=mycodo/CN=mycodo" &&

        openssl x509 -req \
            -days 365 \
            -in certificate.csr -CA cert.pem \
            -CAkey privkey.pem \
            -set_serial $RANDOM \
            -out chain.pem &&

        rm -f certificate.csr &&

        printf "#### Enabling mycodo startup script\n"
        sudo systemctl enable $INSTALL_DIRECTORY/mycodo/scripts/mycodo.service
    ;;
    'upgrade-packages')
        apt-get update -y
        apt-get install -y libav-tools libffi-dev libi2c-dev python-dev python-setuptools python-smbus sqlite3
        easy_install pip
    ;;
    'initialize')
        sudo useradd -M mycodo
        adduser mycodo gpio
        adduser mycodo adm

        if [ ! -e $INSTALL_DIRECTORY/.updating ]; then
            echo '0' > $INSTALL_DIRECTORY/.updating
        fi
        chown -LR mycodo.mycodo $INSTALL_DIRECTORY
        ln -snf $INSTALL_DIRECTORY /var/www/mycodo

        mkdir -p /var/log/mycodo
        chown mycodo.mycodo /var/log/mycodo

        if [ ! -e /var/log/mycodo/mycodo.log ]; then
            touch /var/log/mycodo/mycodo.log
        fi
        chown mycodo.mycodo /var/log/mycodo/mycodo.log
        
        if [ ! -e /var/log/mycodo/mycodoupdate.log ]; then
            touch /var/log/mycodo/mycodoupdate.log
        fi
        chown mycodo.mycodo /var/log/mycodo/mycodoupdate.log

        if [ ! -e /var/log/mycodo/mycodorestore.log ]; then
            touch /var/log/mycodo/mycodorestore.log
        fi
        chown mycodo.mycodo /var/log/mycodo/mycodorestore.log

        if [ ! -e /var/log/mycodo/login.log ]; then
            touch /var/log/mycodo/login.log
        fi
        chown mycodo.mycodo /var/log/mycodo/login.log

        find $INSTALL_DIRECTORY/ -type d -exec chmod u+wx,g+wx {} +
        find $INSTALL_DIRECTORY/ -type f -exec chmod u+w,g+w,o+r {} +
        # find $INSTALL_DIRECTORY/mycodo -type f -name '.?*' -prune -o -exec chmod 770 {} +
        chown root:mycodo $INSTALL_DIRECTORY/mycodo/scripts/mycodo_wrapper
        chmod 4770 $INSTALL_DIRECTORY/mycodo/scripts/mycodo_wrapper
    ;;
esac

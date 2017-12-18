#!/bin/bash
#
#  upgrade_commands.sh - Mycodo commands
#

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd -P )
APT_PKGS="apache2 fswebcam gawk gcc git libapache2-mod-wsgi-py3 libav-tools libboost-python-dev libffi-dev libgtk2.0-0 libi2c-dev logrotate moreutils python3 python3-dev python3-numpy python3-pigpio python-opencv python-setuptools python-smbus sqlite3 wget"

cd ${INSTALL_DIRECTORY}

case "${1:-''}" in
    'backup-create')
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_backup_create.sh
    ;;
    'backup-restore')
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_backup_restore.sh $2
    ;;
    'compile-translations')
        printf "\n#### Compiling Translations\n"
        cd ${INSTALL_DIRECTORY}/Mycodo/mycodo
        ${INSTALL_DIRECTORY}/Mycodo/env/bin/pybabel compile -d mycodo_flask/translations
    ;;
    'compile-translations-py3')
        printf "\n#### Compiling Translations\n"
        cd ${INSTALL_DIRECTORY}/Mycodo/mycodo
        ${INSTALL_DIRECTORY}/Mycodo/env_py3/bin/pybabel compile -d mycodo_flask/translations
    ;;
    'generate-ssl-certs')
        printf "\n#### Generating SSL certificates at ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs (replace with your own if desired)\n"
        mkdir -p ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs
        cd ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs/
        rm -f ./*.pem ./*.csr ./*.crt ./*.key

        openssl genrsa -out server.pass.key 4096
        openssl rsa -in server.pass.key -out server.key
        rm -f server.pass.key
        openssl req -new -key server.key -out server.csr \
            -subj "/O=mycodo/OU=mycodo/CN=mycodo"
        openssl x509 -req \
            -days 365 \
            -in server.csr \
            -signkey server.key \
            -out server.crt

        # Conform to current file-naming format
        # TODO: Change to appropriate names in the future
        ln -s server.key privkey.pem
        ln -s server.crt cert.pem
    ;;
    'initialize')
        printf "\n#### Compiling mycodo_wrapper\n"
        gcc ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper.c -o ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper
        chown root:mycodo ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper
        chmod 4770 ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper

        printf "\n#### Creating users and directories\n"
        useradd -M mycodo

        adduser mycodo adm
        adduser mycodo dialout
        adduser mycodo gpio
        adduser mycodo i2c
        adduser mycodo video

        ln -sfn ${INSTALL_DIRECTORY}/Mycodo /var/www/mycodo

        mkdir -p /var/log/mycodo
        mkdir -p /var/Mycodo-backups

        if [ ! -e /var/log/mycodo/mycodo.log ]; then
            touch /var/log/mycodo/mycodo.log
        fi
        if [ ! -e /var/log/mycodo/mycodobackup.log ]; then
            touch /var/log/mycodo/mycodobackup.log
        fi
        if [ ! -e /var/log/mycodo/mycodokeepup.log ]; then
            touch /var/log/mycodo/mycodokeepup.log
        fi
        if [ ! -e /var/log/mycodo/mycodoupgrade.log ]; then
            touch /var/log/mycodo/mycodoupgrade.log
        fi
        if [ ! -e /var/log/mycodo/mycodorestore.log ]; then
            touch /var/log/mycodo/mycodorestore.log
        fi
        if [ ! -e /var/log/mycodo/login.log ]; then
            touch /var/log/mycodo/login.log
        fi

        # Create empty mycodo database file if it doesn't exist
        if [ ! -e ${INSTALL_DIRECTORY}/Mycodo/databases/mycodo.db ]; then
            touch ${INSTALL_DIRECTORY}/Mycodo/databases/mycodo.db
        fi

        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh update-permissions

        systemctl daemon-reload
    ;;
    'restart-daemon')
        printf "\n#### Restarting the Mycodo daemon\n"
        service mycodo stop
        sleep 2
        ${INSTALL_DIRECTORY}/Mycodo/env/bin/python ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/restart_daemon.py
        service mycodo start
    ;;
    'restart-daemon-py3')
        printf "\n#### Restarting the Mycodo daemon\n"
        service mycodo stop
        sleep 2
        ${INSTALL_DIRECTORY}/Mycodo/env_py3/bin/python3 ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/restart_daemon.py
        service mycodo start
    ;;
    'restart-web-ui')
        printf "\n#### Restarting the Mycodo web server\n"
        apachectl restart
        sleep 5

        printf "\n#### Creating Mycodo database if it doesn't exist\n"
        # Attempt to connect to localhost 5 times, sleeping 60 seconds every fail
        for _ in {1..5}; do
            wget --quiet --no-check-certificate -p http://localhost/ -O /dev/null &&
            printf "#### Successfully connected to http://localhost\n" &&
            break ||
            # Else wait 60 seconds if localhost is not accepting connections
            # Everything below will begin executing if an error occurs before the break
            printf "#### Could not connect to http://localhost. Waiting 60 seconds then trying again (up to 5 times)...\n" &&
            sleep 60 &&
            printf "#### Trying again...\n"
        done
    ;;
    'setup-virtualenv')
        if [ ! -d ${INSTALL_DIRECTORY}/Mycodo/env ]; then
            printf "\n#### Creating virtualenv\n"
            pip install virtualenv --upgrade
            virtualenv --system-site-packages ${INSTALL_DIRECTORY}/Mycodo/env
        else
            printf "#### Virtualenv already exists, skipping creation\n"
        fi
    ;;
    'setup-virtualenv-py3')
        if [ ! -d ${INSTALL_DIRECTORY}/Mycodo/env_py3 ]; then
            pip install virtualenv --upgrade
            virtualenv --system-site-packages -p python3 ${INSTALL_DIRECTORY}/Mycodo/env_py3
        else
            printf "## Virtualenv already exists, skipping creation\n"
        fi
    ;;
    'uninstall-apt-pip')
        printf "\n#### Uninstalling apt version of pip (if installed)\n"
        apt-get purge -y python-pip
    ;;
    'update-alembic')
        printf "\n#### Upgrading Mycodo database with alembic\n"
        cd ${INSTALL_DIRECTORY}/Mycodo/databases
        ${INSTALL_DIRECTORY}/Mycodo/env/bin/alembic upgrade head
    ;;
    'update-alembic-py3')
        printf "\n#### Upgrading Mycodo database with alembic\n"
        cd ${INSTALL_DIRECTORY}/Mycodo/databases
        ${INSTALL_DIRECTORY}/Mycodo/env_py3/bin/alembic upgrade head
    ;;
    'update-apache2')
        printf "\n#### Installing and configuring apache2 web server\n"
        a2enmod wsgi ssl
        ln -sf ${INSTALL_DIRECTORY}/Mycodo/install/mycodo_flask_apache.conf /etc/apache2/sites-enabled/000-default.conf
    ;;
    'update-apt')
        printf "\n\n#### Updating apt repositories\n"
        apt-get update
    ;;
    'update-cron')
        printf "\n#### Updating Mycodo crontab entry\n"
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/install/crontab.sh mycodo --remove
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/install/crontab.sh mycodo
        printf "\n#### Updating Mycodo restart monitor crontab entry\n"
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/install/crontab.sh restart_daemon --remove
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/install/crontab.sh restart_daemon
    ;;
    'update-gpiod')
        printf "\n#### Installing gpiod\n"
        cd ${INSTALL_DIRECTORY}/Mycodo/install
        wget --quiet -P ${INSTALL_DIRECTORY}/Mycodo/install abyz.co.uk/rpi/pigpio/pigpio.zip
        unzip pigpio.zip
        cd ${INSTALL_DIRECTORY}/Mycodo/install/PIGPIO
        make -j4
        make install
        killall pigpiod || true
        /usr/local/bin/pigpiod &
        cd ${INSTALL_DIRECTORY}/Mycodo/install
        rm -rf ./PIGPIO ./pigpio.zip
    ;;
    'update-influxdb')
        printf "\n#### Ensuring compatible version of influxdb is installed ####\n"
        INSTALL_ADDRESS="https://dl.influxdata.com/influxdb/releases/"
        INSTALL_FILE="influxdb_1.4.2_armhf.deb"
        CORRECT_VERSION="1.4.2-1"
        CURRENT_VERSION=$(apt-cache policy influxdb | grep 'Installed' | gawk '{print $2}')
        if [ "${CURRENT_VERSION}" != "${CORRECT_VERSION}" ]; then
            echo "#### Incorrect InfluxDB version (v${CURRENT_VERSION}) installed. Installing v${CORRECT_VERSION}..."
            wget --quiet ${INSTALL_ADDRESS}${INSTALL_FILE}
            dpkg -i ${INSTALL_FILE}
            rm -rf ${INSTALL_FILE}
            service influxdb restart
        else
            printf "Correct version of InfluxDB currently installed\n"
        fi
    ;;
    'update-influxdb-db-user')
        printf "\n#### Creating InfluxDB database and user\n"
        # Attempt to connect to influxdb 3 times, sleeping 60 seconds every fail
        for _ in {1..3}; do
            # Check if influxdb has successfully started and be connected to
            printf "#### Attempting to connect...\n" &&
            curl -sL -I localhost:8086/ping > /dev/null &&
            influx -execute "CREATE DATABASE mycodo_db" &&
            influx -database mycodo_db -execute "CREATE USER mycodo WITH PASSWORD 'mmdu77sj3nIoiajjs'" &&
            printf "#### Influxdb database and user successfully created\n" &&
            break ||
            # Else wait 30 seconds if the influxd port is not accepting connections
            # Everything below will begin executing if an error occurs before the break
            printf "#### Could not connect to Influxdb. Waiting 30 seconds then trying again...\n" &&
            sleep 30
        done
    ;;
    'update-logrotate')
        printf "\n#### Installing logrotate script\n"
        if [ -e /etc/cron.daily/logrotate ]; then
            mv -f /etc/cron.daily/logrotate /etc/cron.hourly/
        fi
        cp -f ${INSTALL_DIRECTORY}/Mycodo/install/logrotate_mycodo /etc/logrotate.d/mycodo
        printf "logrotate moved to cron.daily and logrotate script installed"
    ;;
    'update-mycodo-startup-script')
        printf "\n#### Enabling mycodo startup script\n"
        systemctl disable mycodo.service
        rm -rf /etc/systemd/system/mycodo.service
        systemctl enable ${INSTALL_DIRECTORY}/Mycodo/install/mycodo.service
    ;;
    'update-packages')
        printf "\n#### Installing prerequisite apt packages and update pip\n"
        apt-get update -y
        apt-get install -y ${APT_PKGS}
        easy_install pip
        pip install --upgrade pip
    ;;
    'update-pip')
        printf "\n#### Updating pip\n"
        ${INSTALL_DIRECTORY}/Mycodo/env/bin/pip install --upgrade pip
    ;;
    'update-pip-py3')
        printf "\n#### Updating pip3\n"
        ${INSTALL_DIRECTORY}/Mycodo/env_py3/bin/pip3 install --upgrade pip
    ;;
    'update-pip-packages')
        printf "\n#### Installing pip requirements from requirements.txt\n"
        if [ ! -d ${INSTALL_DIRECTORY}/Mycodo/env ]; then
            printf "\n#### Error: Virtualenv doesn't exist. Create with $0 setup-virtualenv\n"
        else
            ${INSTALL_DIRECTORY}/Mycodo/env/bin/pip install --upgrade pip setuptools
            ${INSTALL_DIRECTORY}/Mycodo/env/bin/pip install --upgrade -r ${INSTALL_DIRECTORY}/Mycodo/install/requirements.txt
        fi
    ;;
    'update-pip-packages-py3')
        printf "\n#### Installing pip requirements from requirements-py3.txt\n"
        if [ ! -d ${INSTALL_DIRECTORY}/Mycodo/env_py3 ]; then
            printf "\n## Error: Virtualenv doesn't exist. Create with $0 setup-virtualenv-py3\n"
        else
            ${INSTALL_DIRECTORY}/Mycodo/env_py3/bin/pip3 install --upgrade pip setuptools
            ${INSTALL_DIRECTORY}/Mycodo/env_py3/bin/pip3 install --upgrade -r ${INSTALL_DIRECTORY}/Mycodo/install/requirements-py3.txt
        fi
    ;;
    'update-permissions')
        printf "\n#### Setting permissions\n"
        chown -LR mycodo.mycodo ${INSTALL_DIRECTORY}/Mycodo
        chown -R mycodo.mycodo /var/log/mycodo
        chown -R mycodo.mycodo /var/Mycodo-backups

        find ${INSTALL_DIRECTORY}/Mycodo -type d -exec chmod u+wx,g+wx {} +
        find ${INSTALL_DIRECTORY}/Mycodo -type f -exec chmod u+w,g+w,o+r {} +

        chown root:mycodo ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper
        chmod 4770 ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper
    ;;
    'update-swap-size')
        printf "\n#### Checking if swap size is 100 MB and needs to be changed to 512 MB\n"
        if grep -q "CONF_SWAPSIZE=100" "/etc/dphys-swapfile"; then
            printf "#### Swap currently set to 100 MB. Changing to 512 MB and restarting\n"
            sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=512/g' /etc/dphys-swapfile
            /etc/init.d/dphys-swapfile stop
            /etc/init.d/dphys-swapfile start
        else
            printf "#### Swap not currently set to 100 MB. Not changing.\n"
        fi
    ;;
    'update-wiringpi')
        printf "\n#### Installing wiringpi\n"
        git clone git://git.drogon.net/wiringPi ${INSTALL_DIRECTORY}/Mycodo/install/wiringPi
        cd ${INSTALL_DIRECTORY}/Mycodo/install/wiringPi
        ./build
        cd ${INSTALL_DIRECTORY}/Mycodo/install
        rm -rf ./wiringPi
    ;;
    'upgrade')
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_mycodo_release.sh
    ;;
    *)
        printf "Unrecognized command\n"
    ;;
esac

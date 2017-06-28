#!/bin/bash
#
#  upgrade_commands.sh -
#

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd -P )
cd ${INSTALL_DIRECTORY}

case "${1:-''}" in
    'compile-mycodo-wrapper')
        gcc ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper.c -o ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper
    ;;
    'compile-translations')
        printf "\n#### Compiling Translations\n"
        source ${INSTALL_DIRECTORY}/Mycodo/env/bin/activate
        cd ${INSTALL_DIRECTORY}/Mycodo/mycodo
        pybabel compile -d mycodo_flask/translations
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
        printf "\n#### Creating proper users, directories, and permissions\n"
        useradd -M mycodo
        adduser mycodo gpio
        adduser mycodo adm
        adduser mycodo video
        adduser mycodo dialout

        chown -LR mycodo.mycodo ${INSTALL_DIRECTORY}/Mycodo
        ln -sfn ${INSTALL_DIRECTORY}/Mycodo /var/www/mycodo

        mkdir -p /var/log/mycodo
        if [ ! -e /var/log/mycodo/mycodo.log ]; then
            touch /var/log/mycodo/mycodo.log
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
        chown -R mycodo.mycodo /var/log/mycodo

        find ${INSTALL_DIRECTORY}/Mycodo -type d -exec chmod u+wx,g+wx {} +
        find ${INSTALL_DIRECTORY}/Mycodo -type f -exec chmod u+w,g+w,o+r {} +
        # find $INSTALL_DIRECTORY/Mycodo/mycodo -type f -name '.?*' -prune -o -exec chmod 770 {} +
        chown root:mycodo ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper
        chmod 4770 ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_wrapper
    ;;
    'setup-virtualenv')
        if [ ! -d ${INSTALL_DIRECTORY}/Mycodo/env ]; then
            pip install virtualenv --upgrade
            virtualenv --system-site-packages ${INSTALL_DIRECTORY}/Mycodo/env
        else
            printf "## Virtualenv already exists, skipping creation\n"
        fi
    ;;
    'update-alembic')
        printf "\n#### Upgrading database with alembic\n"
        source ${INSTALL_DIRECTORY}/Mycodo/env/bin/activate
        cd ${INSTALL_DIRECTORY}/Mycodo/databases
        alembic upgrade head
    ;;
    'update-apache2')
        printf "\n#### Installing and configuring apache2 web server\n"
        a2enmod wsgi ssl
        ln -sf ${INSTALL_DIRECTORY}/Mycodo/install/mycodo_flask_apache.conf /etc/apache2/sites-enabled/000-default.conf

    ;;
    'update-cron')
        printf "#### Updating crontab entry\n"
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/install/crontab.sh mycodo --remove
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/install/crontab.sh mycodo
    ;;
    'update-influxdb')
        printf "\n#### Ensuring compatible version of influxdb is installed ####\n"
        INSTALL_ADDRESS="https://dl.influxdata.com/influxdb/releases/"
        INSTALL_FILE="influxdb_1.2.4_armhf.deb"
        CORRECT_VERSION="1.2.4-1"
        CURRENT_VERSION=$(apt-cache policy influxdb | grep 'Installed' | gawk '{print $2}')
        if [ "${CURRENT_VERSION}" != "${CORRECT_VERSION}" ]; then
            if [ ! -z "${CURRENT_VERSION}" ];
            then
                echo "Incorrect version of InfluxDB installed: v${CURRENT_VERSION}."
            fi
            echo "Installing ${CORRECT_VERSION}"
            wget --quiet ${INSTALL_ADDRESS}${INSTALL_FILE}
            dpkg -i ${INSTALL_FILE}
            rm -rf ${INSTALL_FILE}
            service influxdb restart
        fi
    ;;
    'update-packages')
        printf "\n#### Installing prerequisite apt packages and update pip\n"
        apt-get update -y
        apt-get install -y apache2 gawk gcc git libapache2-mod-wsgi libav-tools libboost-python-dev libffi-dev libi2c-dev python-dev python-numpy python-opencv python-setuptools python-smbus sqlite3
        easy_install pip
        pip install --upgrade pip
    ;;
    'update-pip-packages')
        printf "\n#### Installing pip requirements from requirements.txt\n"
        if [ ! -d ${INSTALL_DIRECTORY}/Mycodo/env ]; then
            printf "\n## Error: Virtualenv doesn't exist. Create with $0 setup-virtualenv\n"
        else
            source ${INSTALL_DIRECTORY}/Mycodo/env/bin/activate
            ${INSTALL_DIRECTORY}/Mycodo/env/bin/pip install --upgrade pip
            ${INSTALL_DIRECTORY}/Mycodo/env/bin/pip install --upgrade -r ${INSTALL_DIRECTORY}/Mycodo/install/requirements.txt
        fi
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
    'update-mycodo-startup-script')
        printf "\n#### Enabling mycodo startup script\n"
        systemctl disable mycodo.service
        rm -rf /etc/systemd/system/mycodo.service
        systemctl enable ${INSTALL_DIRECTORY}/Mycodo/install/mycodo.service
    ;;
    'upgrade')
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_mycodo_release.sh
    ;;
    'create-backup')
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_backup_create.sh
    ;;
    'restore-backup')
        /bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/mycodo_backup_restore.sh $2
    ;;
esac

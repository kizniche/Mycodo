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
    'compile-translations')
        printf "\n#### Compiling Translations\n"
        cd ${INSTALL_DIRECTORY}/Mycodo/mycodo
        pybabel compile -d mycodo_flask/translations
    ;;
    'generate-ssl-certs')
        printf "\n#### Generating SSL certificates at ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs (replace with your own if desired)\n"
        mkdir -p ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs
        cd ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs/
        rm -f ./*.pem

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

        rm -f certificate.csr certificate.key
    ;;
    'initialize')
        printf "\n#### Creating proper users, directories, and permissions\n"
        useradd -M mycodo
        adduser mycodo gpio
        adduser mycodo adm
        adduser mycodo video

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
        INSTALL_FILE="influxdb_1.2.1_armhf.deb"
        CORRECT_VERSION="1.2.1-1"
        CURRENT_VERSION=$(apt-cache policy influxdb | grep 'Installed' | gawk '{print $2}')
        if [ "${CURRENT_VERSION}" != "${CORRECT_VERSION}" ]; then
            echo "Incorrect version of InfluxDB installed: v${CURRENT_VERSION}. Installing ${CORRECT_VERSION}"
            wget --quiet ${INSTALL_ADDRESS}${INSTALL_FILE}
            dpkg -i ${INSTALL_FILE}
            rm -rf ${INSTALL_FILE}
            service influxdb restart
            sleep 15
        fi
    ;;
    'update-packages')
        printf "\n#### Installing prerequisite apt packages and update pip\n"
        apt-get update -y
        apt-get install -y apache2 gawk git libapache2-mod-wsgi libav-tools libffi-dev libi2c-dev python-dev python-numpy python-opencv python-setuptools python-smbus sqlite3
        easy_install pip
        pip install pip --upgrade
    ;;
    'update-pip-packages')
        printf "\n#### Installing pip requirements from requirements.txt\n"
        if [ ! -d ${INSTALL_DIRECTORY}/Mycodo/env ]; then
            printf "\n## Error: Virtualenv doesn't exist. Create with $0 setup-virtualenv\n"
        else
            source ${INSTALL_DIRECTORY}/Mycodo/env/bin/activate
            ${INSTALL_DIRECTORY}/Mycodo/env/bin/pip install pip --upgrade
            ${INSTALL_DIRECTORY}/Mycodo/env/bin/pip install -r ${INSTALL_DIRECTORY}/Mycodo/install/requirements.txt --upgrade
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
esac

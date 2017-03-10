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
        printf "\n#### Generating SSL certificates at ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs (replace with your own if desired)\n"
        mkdir -p ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs
        cd ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/ssl_certs/
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
        printf "\n#### Initialize: Create proper users, directories, and permissions\n"
        useradd -M mycodo
        adduser mycodo gpio
        adduser mycodo adm
        adduser mycodo video

        chown -LR mycodo.mycodo ${INSTALL_DIRECTORY}/Mycodo
        ln -sf ${INSTALL_DIRECTORY}/Mycodo /var/www/mycodo

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
    'update-cron')
        printf "#### Updating crontab entry\n"
        /bin/bash ${INSTALL_DIRECTORY}/install/crontab.sh mycodo --remove
        /bin/bash ${INSTALL_DIRECTORY}/install/crontab.sh mycodo
    ;;
    'update-influxdb')
        printf "\n#### Ensure compatible version of influxdb is installed ####\n"
        INSTALL_ADDRESS="https://dl.influxdata.com/influxdb/releases/"
        INSTALL_FILE="influxdb_1.1.1_armhf.deb"
        CORRECT_VERSION="1.1.1-1"
        CURRENT_VERSION=$(apt-cache policy influxdb | grep 'Installed' | gawk '{print $2}')
        if [ "${CURRENT_VERSION}" != "${CORRECT_VERSION}" ]; then
            echo "Incorrect version of InfluxDB installed: v${CURRENT_VERSION}. Installing ${CORRECT_VERSION}"
            wget --quiet ${INSTALL_ADDRESS}${INSTALL_FILE}
            dpkg -i ${INSTALL_FILE}
            rm -rf ${INSTALL_FILE}
            service influxdb restart
        fi
    ;;
    'update-packages')
        printf "\n#### Installing prerequisite apt packages.\n"
        apt-get update -y
        apt-get install -y apache2 gawk git libav-tools libffi-dev libi2c-dev python-dev python-numpy python-opencv python-setuptools python-smbus sqlite3
        easy_install pip
    ;;
    'upgrade')
        /bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_mycodo_release.sh
    ;;
esac

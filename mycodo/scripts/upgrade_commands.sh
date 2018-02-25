#!/bin/bash
#
#  upgrade_commands.sh - Mycodo commands
#

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

# Required apt packages. This has only been tested with Raspbian for the
# Raspberry Pi but should work with most debian-based systems.
APT_PKGS="fswebcam gawk gcc git libav-tools libffi-dev libi2c-dev logrotate \
          moreutils nginx python-setuptools python3 python3-dev python3-numpy \
          python3-smbus sqlite3 wget"

# Get the Mycodo root directory
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
MYCODO_PATH="$( cd -P "$( dirname "${SOURCE}" )/../.." && pwd )"
cd ${MYCODO_PATH}

case "${1:-''}" in
    'backup-create')
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/mycodo_backup_create.sh
    ;;
    'backup-restore')
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/mycodo_backup_restore.sh $2
    ;;
    'compile-mycodo-wrapper')
        printf "\n#### Compiling mycodo_wrapper\n"
        gcc ${MYCODO_PATH}/mycodo/scripts/mycodo_wrapper.c -o ${MYCODO_PATH}/mycodo/scripts/mycodo_wrapper
        chown root:mycodo ${MYCODO_PATH}/mycodo/scripts/mycodo_wrapper
        chmod 4770 ${MYCODO_PATH}/mycodo/scripts/mycodo_wrapper
    ;;
    'compile-translations')
        printf "\n#### Compiling Translations\n"
        cd ${MYCODO_PATH}/mycodo
        ${MYCODO_PATH}/env/bin/pybabel compile -d mycodo_flask/translations
    ;;
    'create-files-directories')
        printf "\n#### Creating files and directories\n"
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
        if [ ! -e ${MYCODO_PATH}/databases/mycodo.db ]; then
            touch ${MYCODO_PATH}/databases/mycodo.db
        fi
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh update-permissions
    ;;
    'create-symlinks')
        printf "\n#### Creating symlinks to Mycodo executables\n"
        ln -sfn ${MYCODO_PATH} /var/mycodo-root
        ln -sfn ${MYCODO_PATH}/mycodo/mycodo_daemon.py /usr/bin/mycodo-daemon
        ln -sfn ${MYCODO_PATH}/mycodo/mycodo_client.py /usr/bin/mycodo-client
        ln -sfn ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh /usr/bin/mycodo-commands
        ln -sfn ${MYCODO_PATH}/mycodo/scripts/mycodo_backup_create.sh /usr/bin/mycodo-backup
        ln -sfn ${MYCODO_PATH}/mycodo/scripts/mycodo_backup_restore.sh /usr/bin/mycodo-restore
        ln -sfn ${MYCODO_PATH}/mycodo/scripts/mycodo_wrapper /usr/bin/mycodo-wrapper
        ln -sfn ${MYCODO_PATH}/env/bin/pip3 /usr/bin/mycodo-pip
        ln -sfn ${MYCODO_PATH}/env/bin/python3 /usr/bin/mycodo-python
    ;;
    'create-user')
        printf "\n#### Creating mycodo user\n"
        useradd -M mycodo
        adduser mycodo adm
        adduser mycodo dialout
        adduser mycodo gpio
        adduser mycodo i2c
        adduser mycodo video
    ;;
    'initialize')
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh create-user
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh compile-mycodo-wrapper
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh create-symlinks
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh create-files-directories
        systemctl daemon-reload
    ;;
    'restart-daemon')
        printf "\n#### Restarting the Mycodo daemon\n"
        service mycodo stop
        sleep 2
        ${MYCODO_PATH}/env/bin/python ${MYCODO_PATH}/mycodo/scripts/restart_daemon.py
        service mycodo start
    ;;
    'setup-virtualenv')
        printf "\n#### Checking python 3 virtualenv\n"
        if [ ! -e ${MYCODO_PATH}/env/bin/python3 ]; then
            printf "#### Virtualenv doesn't exist. Creating...\n"
            pip install virtualenv --upgrade
            rm -rf ${MYCODO_PATH}/env
            virtualenv --system-site-packages -p /usr/bin/python3.5 ${MYCODO_PATH}/env
        else
            printf "#### Virtualenv already exists, skipping creation\n"
        fi
    ;;
    'ssl-certs-generate')
        printf "\n#### Generating SSL certificates at ${MYCODO_PATH}/mycodo/mycodo_flask/ssl_certs (replace with your own if desired)\n"
        mkdir -p ${MYCODO_PATH}/mycodo/mycodo_flask/ssl_certs
        cd ${MYCODO_PATH}/mycodo/mycodo_flask/ssl_certs/
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
    'ssl-certs-regenerate')
        printf "\n#### Regenerating SSL certificates at ${MYCODO_PATH}/mycodo/mycodo_flask/ssl_certs\n"
        rm -rf ${MYCODO_PATH}/mycodo/mycodo_flask/ssl_certs/*.pem
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh ssl-certs-generate
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh initialize
        sudo service nginx restart
        sudo service mycodoflask restart
    ;;
    'uninstall-apt-pip')
        printf "\n#### Uninstalling apt version of pip (if installed)\n"
        apt-get purge -y python-pip
    ;;
    'update-alembic')
        printf "\n#### Upgrading Mycodo database with alembic (if needed)\n"
        cd ${MYCODO_PATH}/databases
        ${MYCODO_PATH}/env/bin/alembic upgrade head
    ;;
    'update-apt')
        printf "\n\n#### Updating apt repositories\n"
        apt-get update
    ;;
    'update-cron')
        printf "\n#### Updating Mycodo crontab entry\n"
        /bin/bash ${MYCODO_PATH}/install/crontab.sh mycodo --remove
        printf "\n#### Updating Mycodo restart monitor crontab entry\n"
        /bin/bash ${MYCODO_PATH}/install/crontab.sh restart_daemon --remove
        /bin/bash ${MYCODO_PATH}/install/crontab.sh restart_daemon
    ;;
    'install-pigpiod')
        printf "\n#### Installing pigpiod\n"
        apt-get install -y python3-pigpio
        cd ${MYCODO_PATH}/install
        # wget --quiet -P ${MYCODO_PATH}/install abyz.co.uk/rpi/pigpio/pigpio.zip
        tar xf pigpio.tar
        cd ${MYCODO_PATH}/install/PIGPIO
        make -j4
        make install
        cd ${MYCODO_PATH}/install
        rm -rf ./PIGPIO
    ;;
    'disable-pigpiod')
        printf "\n#### Disabling installed pigpiod startup script\n"
        service pigpiod stop
        systemctl disable pigpiod.service
        rm -rf /etc/systemd/system/pigpiod.service
        systemctl disable pigpiod_low.service
        rm -rf /etc/systemd/system/pigpiod_low.service
        systemctl disable pigpiod_high.service
        rm -rf /etc/systemd/system/pigpiod_high.service
        rm -rf /etc/systemd/system/pigpiod_disabled.service
    ;;
    'enable-pigpiod-low')
        printf "\n#### Enabling pigpiod startup script (1 ms sample rate)\n"
        systemctl enable ${MYCODO_PATH}/install/pigpiod_low.service
        service pigpiod restart
    ;;
    'enable-pigpiod-high')
        printf "\n#### Enabling pigpiod startup script (5 ms sample rate)\n"
        systemctl enable ${MYCODO_PATH}/install/pigpiod_high.service
        service pigpiod restart
    ;;
    'enable-pigpiod-disabled')
        printf "\n#### pigpiod has been disabled. It can be enabled in the web UI configuration\n"
        touch /etc/systemd/system/pigpiod_disabled.service
    ;;
    'update-pigpiod')
        printf "\n#### Checking which pigpiod startup script is being used\n"
        GPIOD_SAMPLE_RATE=99
        if [ -e /etc/systemd/system/pigpiod_low.service ]; then
            GPIOD_SAMPLE_RATE=1
        elif [ -e /etc/systemd/system/pigpiod_high.service ]; then
            GPIOD_SAMPLE_RATE=5
        elif [ -e /etc/systemd/system/pigpiod_disabled.service ]; then
            GPIOD_SAMPLE_RATE=100
        fi

        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh disable-pigpiod

        if [ "$GPIOD_SAMPLE_RATE" -eq "1" ]; then
            /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh enable-pigpiod-low
        elif [ "$GPIOD_SAMPLE_RATE" -eq "5" ]; then
            /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh enable-pigpiod-high
        elif [ "$GPIOD_SAMPLE_RATE" -eq "100" ]; then
            /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh enable-pigpiod-disabled
        else
            printf "#### Could not determine pgiod sample rate. Setting up pigpiod with 1 ms sample rate\n"
            /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh enable-pigpiod-low
        fi
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
        printf "\n#### Installing logrotate scripts\n"
        if [ -e /etc/cron.daily/logrotate ]; then
            printf "#### logrotate execution moved from cron.daily to cron.hourly\n"
            mv -f /etc/cron.daily/logrotate /etc/cron.hourly/
        fi
        cp -f ${MYCODO_PATH}/install/logrotate_mycodo /etc/logrotate.d/mycodo
        printf "#### Mycodo logrotate script installed\n"
    ;;
    'update-mycodo-startup-script')
        printf "\n#### Disabling installed mycodo startup script\n"
        systemctl disable mycodo.service
        rm -rf /etc/systemd/system/mycodo.service
        printf "#### Enabling current mycodo startup script\n"
        systemctl enable ${MYCODO_PATH}/install/mycodo.service
    ;;
    'update-packages')
        printf "\n#### Installing prerequisite apt packages and update pip\n"
        apt-get update -y
        apt-get remove -y apache2
        apt-get install -y ${APT_PKGS}
        easy_install pip
        pip install --upgrade pip
    ;;
    'update-permissions')
        printf "\n#### Setting permissions\n"
        chown -LR mycodo.mycodo ${MYCODO_PATH}
        chown -R mycodo.mycodo /var/log/mycodo
        chown -R mycodo.mycodo /var/Mycodo-backups
        chown -R influxdb.influxdb /var/lib/influxdb/data/

        find ${MYCODO_PATH} -type d -exec chmod u+wx,g+wx {} +
        find ${MYCODO_PATH} -type f -exec chmod u+w,g+w,o+r {} +

        chown root:mycodo ${MYCODO_PATH}/mycodo/scripts/mycodo_wrapper
        chmod 4770 ${MYCODO_PATH}/mycodo/scripts/mycodo_wrapper
    ;;
    'update-pip3')
        printf "\n#### Updating pip\n"
        ${MYCODO_PATH}/env/bin/pip3 install --upgrade pip
    ;;
    'update-pip3-packages')
        printf "\n#### Installing pip requirements from requirements.txt\n"
        if [ ! -d ${MYCODO_PATH}/env ]; then
            printf "\n## Error: Virtualenv doesn't exist. Create with $0 setup-virtualenv\n"
        else
            ${MYCODO_PATH}/env/bin/pip3 install --upgrade pip setuptools
            ${MYCODO_PATH}/env/bin/pip3 install --upgrade -r ${MYCODO_PATH}/install/requirements.txt
        fi
    ;;
    'install-pip-dependency')
        printf "\n#### Installing ${2} with pip\n"
        if [ ! -d ${MYCODO_PATH}/env ]; then
            printf "\n## Error: Virtualenv doesn't exist.\n"
            /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_commands.sh setup-virtualenv
        else
            ${MYCODO_PATH}/env/bin/pip3 install --upgrade ${2}
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
    'update-wiringpi')
        printf "\n#### Installing wiringpi\n"
        git clone git://git.drogon.net/wiringPi ${MYCODO_PATH}/install/wiringPi
        cd ${MYCODO_PATH}/install/wiringPi
        ./build
        cd ${MYCODO_PATH}/install
        rm -rf ./wiringPi
    ;;
    'upgrade')
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_mycodo_release.sh
    ;;
    'upgrade-master')
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_mycodo_release.sh force-upgrade-master
    ;;
    'upgrade-post')
        /bin/bash ${MYCODO_PATH}/mycodo/scripts/upgrade_post.sh
    ;;
    'web-server-connect')
        printf "\n#### Connecting to http://localhost (creates Mycodo database if it doesn't exist)\n"
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
    'web-server-reload')
        printf "\n#### Restarting nginx\n"
        service nginx restart
        sleep 5
        printf "#### Reloading mycodoflask\n"
        service mycodoflask reload
    ;;
    'web-server-restart')
        printf "\n#### Restarting nginx\n"
        service nginx restart
        sleep 5
        printf "#### Restarting mycodoflask\n"
        service mycodoflask restart
    ;;
    'web-server-update')
        printf "\n#### Installing and configuring nginx web server\n"
        systemctl disable mycodoflask.service
        rm -rf /etc/systemd/system/mycodoflask.service
        ln -sf ${MYCODO_PATH}/install/mycodoflask_nginx.conf /etc/nginx/sites-enabled/default
        systemctl enable nginx
        systemctl enable ${MYCODO_PATH}/install/mycodoflask.service
    ;;
    *)
        printf "Error: Unrecognized command\n"
    ;;
esac

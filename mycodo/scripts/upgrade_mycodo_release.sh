#!/bin/bash

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd -P )
cd ${INSTALL_DIRECTORY}

case "${1:-''}" in
    'upgrade')
        runSelfUpgrade() {
          INSTALL_DIRECTORY=$( cd -P /var/www/mycodo/.. && pwd -P )
          echo '1' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade

          function error_found {
            echo '2' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade
            exit 1
          }

          NOW=$(date +"%Y-%m-%d_%H-%M-%S")
          CURRENT_VERSION=$(python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)
          UPDATE_URL=$(python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -m 4 2>&1)
          UPDATE_VERSION=$(python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -m 4 -v 2>&1)
          MYCODO_NEW_TMP_DIR="/tmp/Mycodo-${UPDATE_VERSION}"
          TARBALL_FILE="mycodo-${UPDATE_VERSION}"

          if [ "${CURRENT_VERSION}" == "${UPDATE_VERSION}" ] ; then
            printf "\nUnable to upgrade. You currently have the latest release installed.\n"
            error_found
          else
            printf "\nInstalled version: ${CURRENT_VERSION}\n"
            printf "Latest version: ${UPDATE_VERSION}\n"
          fi

          if [ "${UPDATE_URL}" == "None" ] ; then
            printf "\nUnable to upgrade. A URL of the latest release was not able to be obtained.\n"
            error_found
          fi

          printf "\n#### Upgrade to v${UPDATE_VERSION} initiated $NOW ####\n"
          printf "\n#### Beginning Upgrade: Stage 1 of 2 ####\n"

          printf "Stopping the Mycodo daemon..."
          if ! service mycodo stop ; then
            printf "Error: Unable to stop the daemon. Continuing anyway...\n"
          fi
          printf "Done.\n"

          printf "Downloading latest Mycodo version to ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz..."
          if ! wget --quiet -O ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz ${UPDATE_URL} ; then
            printf "Failed: Error while trying to wget new version.\n"
            printf "File requested: ${UPDATE_URL} -> ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz\n"
            error_found
          fi
          printf "Done.\n"

          if [ -d "${MYCODO_NEW_TMP_DIR}" ] ; then
            printf "The tmp directory ${MYCODO_NEW_TMP_DIR} already exists. Removing..."
            if ! rm -Rf ${MYCODO_NEW_TMP_DIR} ; then
              printf "Failed: Error while trying to delete tmp directory ${MYCODO_NEW_TMP_DIR}.\n"
              error_found
            fi
            printf "Done.\n"
          fi

          printf "Creating ${MYCODO_NEW_TMP_DIR}..."
          if ! mkdir ${MYCODO_NEW_TMP_DIR} ; then
            printf "Failed: Error while trying to create ${MYCODO_NEW_TMP_DIR}.\n"
            error_found
          fi
          printf "Done.\n"

          printf "Extracting ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz to ${MYCODO_NEW_TMP_DIR}..."
          if ! tar xzf ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz -C ${MYCODO_NEW_TMP_DIR} --strip-components=1 ; then
            printf "Failed: Error while trying to extract files from ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz to ${MYCODO_NEW_TMP_DIR}.\n"
            error_found
          fi
          printf "Done.\n"

          printf "Removing ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz..."
          if ! rm -rf ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz ; then
            printf "Failed: Error while removing ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz.\n"
            error_found
          fi
          printf "Done.\n"

          printf "Copying ${MYCODO_NEW_TMP_DIR}/.upgrade status file to ${MYCODO_NEW_TMP_DIR}..."
          if ! cp ${INSTALL_DIRECTORY}/Mycodo/.upgrade ${MYCODO_NEW_TMP_DIR} ; then
            printf "Failed: Error while trying to copy .upgrade status file.\n"
            error_found
          fi
          printf "Done.\n"

          printf "Moving databases from ${INSTALL_DIRECTORY}/Mycodo/databases/ to ${MYCODO_NEW_TMP_DIR}/databases..."
          if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/*.db ${MYCODO_NEW_TMP_DIR}/databases ; then
            printf "Failed: Error while trying to copy databases."
            error_found
          fi
          printf "Done.\n"

          if [ -e ${INSTALL_DIRECTORY}/Mycodo/databases/timelapse.pid ] && [ -e ${INSTALL_DIRECTORY}/Mycodo/databases/timelapse.csv ]; then
            printf "Moving time-lapse files from ${INSTALL_DIRECTORY}/Mycodo/databases/ to ${MYCODO_NEW_TMP_DIR}/databases..."
            if ! mv ${INSTALL_DIRECTORY}/Mycodo/databases/timelapse.* ${MYCODO_NEW_TMP_DIR}/databases ; then
              printf "Failed: Error while trying to copy time-lapse files."
              error_found
            fi
            printf "Done.\n"
          fi

          if [ -e ${INSTALL_DIRECTORY}/Mycodo/databases/statistics.id ]; then
            printf "Copying statistics ID..."
            if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/statistics.id ${MYCODO_NEW_TMP_DIR}/databases ; then
              printf "Failed: Error while trying to copy statistics ID."
              error_found
            fi
            printf "Done.\n"
          fi

          if [ -d ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs ] ; then
            printf "Copying SSL certificates..."
            if ! cp -R ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs ${MYCODO_NEW_TMP_DIR}/mycodo/mycodo_flask/ssl_certs ; then
              printf "Failed: Error while trying to copy SSL certificates."
              error_found
            fi
            printf "Done.\n"
          fi

          if [ -d ${INSTALL_DIRECTORY}/Mycodo/camera-stills ] ; then
            printf "Moving Camera stills directory..."
            if ! mv ${INSTALL_DIRECTORY}/Mycodo/camera-stills ${MYCODO_NEW_TMP_DIR} ; then
              printf "Failed: Error while trying to move camera stills directory.\n"
              error_found
            fi
            printf "Done.\n"
          fi

          if [ -d ${INSTALL_DIRECTORY}/Mycodo/camera-timelapse ] ; then
            printf "Moving Camera timelapse directory..."
            if ! mv ${INSTALL_DIRECTORY}/Mycodo/camera-timelapse ${MYCODO_NEW_TMP_DIR} ; then
              printf "Failed: Error while trying to move camera timelapse directory.\n"
              error_found
            fi
            printf "Done.\n"
          fi

          if [ -d ${INSTALL_DIRECTORY}/Mycodo/camera-video ] ; then
            printf "Moving Camera video directory..."
            if ! mv ${INSTALL_DIRECTORY}/Mycodo/camera-video ${MYCODO_NEW_TMP_DIR} ; then
              printf "Failed: Error while trying to move camera video directory.\n"
              error_found
            fi
            printf "Done.\n"
          fi

          printf "#### Stage 1 of 2 Complete ####\n"

          # Spawn upgrade script
          cat > /tmp/upgrade_mycodo_stagetwo.sh << EOF
#!/bin/bash

function error_found {
  echo '2' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade
  exit 1
}

revertInstall() {
  printf "\n\nThe upgrade has failed: Attempting to revert moving the old Mycodo install.\n"
  if ! mv /var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION} ${INSTALL_DIRECTORY}/Mycodo ; then
    printf "\nFailed: Error while trying to revert moving. Could not move /var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION} to ${INSTALL_DIRECTORY}/Mycodo.\n"
    error_occurred
  fi
  printf "\nSuccessfully reverted moving the old Mycodo install directory. Moved /var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION} to ${INSTALL_DIRECTORY}/Mycodo\n"

  if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_mycodo_release.sh initialize ; then
    printf "Failed: Error while running initialization script.\n"
    error_occurred
  fi
  printf "Done.\n"
}

printf "#### Continuing Upgrade: Stage 2 of 2 ####\n"

if [ ! -d "/var/Mycodo-backups" ] ; then
  mkdir /var/Mycodo-backups
fi

printf "\nMoving old Mycodo from ${INSTALL_DIRECTORY}/Mycodo to /var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION}..."
if ! mv ${INSTALL_DIRECTORY}/Mycodo /var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION} ; then
  printf "Failed: Error while trying to move old Mycodo install from ${INSTALL_DIRECTORY}/Mycodo to /var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION}.\n"
  revertInstall
  error_found
fi
printf "Done.\n"

printf "Moving new Mycodo from ${MYCODO_NEW_TMP_DIR} to ${INSTALL_DIRECTORY}/Mycodo..."
if ! mv ${MYCODO_NEW_TMP_DIR} ${INSTALL_DIRECTORY}/Mycodo ; then
  printf "Failed: Error while trying to move new Mycodo install from ${MYCODO_NEW_TMP_DIR} to ${INSTALL_DIRECTORY}/Mycodo.\n"
  revertInstall
  error_found
fi
printf "Done.\n"

if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_mycodo_release.sh initialize ; then
  printf "Failed: Error while running initialization script.\n"
  revertInstall
  error_found
fi

printf "\n\nRunning post-upgrade script...\n"
if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_post.sh ; then
  printf "Failed: Error while running post-upgrade script.\n"
  revertInstall
  error_found
fi
printf "Done.\n"

printf "\nUpgrade completed successfully without errors.\n"
echo '0' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade
rm \$0
EOF
          exec /bin/bash /tmp/upgrade_mycodo_stagetwo.sh
        }

        runSelfUpgrade
    ;;
    'upgrade-packages')
        printf "\n#### Installing prerequisite apt packages.\n"
        apt-get update -y
        apt-get install -y apache2 gawk git libav-tools libffi-dev libi2c-dev python-dev python-numpy python-setuptools python-smbus sqlite3
        easy_install pip
    ;;
    'compile-translations')
        printf "\n#### Compiling Translations ####\n"
        pybabel compile -d ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/translations
    ;;
    'upgrade-influxdb')
        printf "\n#### Upgrade influxdb if out-of-date or not installed ####\n"
        INFLUX_VERSION=$(apt-cache policy influxdb | grep 'Installed' | gawk '{print $2}')
        if [ "$INFLUX_VERSION" != "1.2.0-1" ]; then
            echo "Outdated version of InfluxDB installed: v${INFLUX_VERSION}. Installing v1.2.0."
            wget --quiet https://dl.influxdata.com/influxdb/releases/influxdb_1.2.0_armhf.deb
            dpkg -i influxdb_1.2.0_armhf.deb
            rm -rf influxdb_1.2.0_armhf.deb
        fi
    ;;
    'initialize')
        printf "\n#### Setting permissions ####\n"
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
esac

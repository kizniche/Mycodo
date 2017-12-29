#!/bin/bash

ARG=$1

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd -P )
cd ${INSTALL_DIRECTORY}

runSelfUpgrade() {
  INSTALL_DIRECTORY=$( cd -P /var/www/mycodo/.. && pwd -P )
  echo '1' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade

  function error_found {
    echo '2' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade
    printf "\n\n"
    printf "#### ERROR ####\n"
    printf "There was an error detected during the upgrade. Please review the log at /var/log/mycodo/mycodoupgrade.log"
    exit 1
  }

  NOW=$(date +"%Y-%m-%d_%H-%M-%S")
  CURRENT_VERSION=$(${INSTALL_DIRECTORY}/Mycodo/env/bin/python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)
  BACKUP_DIR="/var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION}"
  UPDATE_VERSION=$(${INSTALL_DIRECTORY}/Mycodo/env/bin/python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -m 5 -v 2>&1)
  MYCODO_NEW_TMP_DIR="/tmp/Mycodo-${UPDATE_VERSION}"
  UPDATE_URL=$(${INSTALL_DIRECTORY}/Mycodo/env/bin/python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -m 5 2>&1)
  TARBALL_FILE="mycodo-${UPDATE_VERSION}"

  printf "\n"

  # If this script is executed with the 'force-upgrade-master' argument,
  # an upgrade will be performed with the latest git commit from the repo
  # master instead of the release version

  if [ "$ARG" == "force-upgrade-master" ]; then
    printf "\nUpgrade script executed with the 'force-upgrade-master' argument. Upgrading from github repo master.\n"
    UPDATE_URL="https://github.com/kizniche/Mycodo/archive/master.tar.gz"
    TARBALL_FILE="Mycodo-master"
  else
    if [ "${CURRENT_VERSION}" == "${UPDATE_VERSION}" ] ; then
      printf "Unable to upgrade. You currently have the latest release installed.\n"
      error_found
    else
      printf "\nInstalled version: ${CURRENT_VERSION}\n"
      printf "Latest version: ${UPDATE_VERSION}\n"
    fi
  fi

  if [ "${UPDATE_URL}" == "None" ] ; then
    printf "\nUnable to upgrade. A URL of the latest release was not able to be obtained.\n"
    error_found
  fi

  printf "\n#### Upgrade to v${UPDATE_VERSION} initiated ${NOW} ####\n"
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

  if [ -d "${MYCODO_NEW_TMP_DIR}/old" ] ; then
    printf "The archive directory ${MYCODO_NEW_TMP_DIR}/old exists. Removing..."
    if ! rm -Rf ${MYCODO_NEW_TMP_DIR}/old ; then
      printf "Failed: Error while trying to delete archive directory ${MYCODO_NEW_TMP_DIR}/old.\n"
      error_found
    fi
    printf "Done.\n"
  fi

  printf "Removing ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz..."
  if ! rm -rf ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz ; then
    printf "Failed: Error while removing ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz.\n"
  fi
  printf "Done.\n"

  printf "Copying ${MYCODO_NEW_TMP_DIR}/.upgrade status file to ${MYCODO_NEW_TMP_DIR}..."
  if ! cp ${INSTALL_DIRECTORY}/Mycodo/.upgrade ${MYCODO_NEW_TMP_DIR} ; then
    printf "Failed: Error while trying to copy .upgrade status file.\n"
  fi
  printf "Done.\n"

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/env ] ; then
    printf "Moving env directory..."
    if ! mv ${INSTALL_DIRECTORY}/Mycodo/env ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to move env directory.\n"
      error_found
    fi
    printf "Done.\n"
  fi

  printf "Copying databases from ${INSTALL_DIRECTORY}/Mycodo/databases/ to ${MYCODO_NEW_TMP_DIR}/databases..."
  if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/*.db ${MYCODO_NEW_TMP_DIR}/databases ; then
    printf "Failed: Error while trying to copy databases."
    error_found
  fi
  printf "Done.\n"

  printf "Copying flask_secret_key from ${INSTALL_DIRECTORY}/Mycodo/databases/ to ${MYCODO_NEW_TMP_DIR}/databases..."
  if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/flask_secret_key ${MYCODO_NEW_TMP_DIR}/databases ; then
    printf "Failed: Error while trying to copy flask_secret_key."
  fi
  printf "Done.\n"

  if [ -e ${INSTALL_DIRECTORY}/Mycodo/databases/statistics.id ]; then
    printf "Copying statistics ID..."
    if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/statistics.id ${MYCODO_NEW_TMP_DIR}/databases ; then
      printf "Failed: Error while trying to copy statistics ID."
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

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/relay_usage_reports ] ; then
    printf "Moving relay_usage_reports directory..."
    if ! mv ${INSTALL_DIRECTORY}/Mycodo/relay_usage_reports ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to move relay_usage_reports directory.\n"
    fi
    printf "Done.\n"
  fi

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/cameras ] ; then
    printf "Moving cameras directory..."
    if ! mv ${INSTALL_DIRECTORY}/Mycodo/cameras ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to move cameras directory.\n"
    fi
    printf "Done.\n"
  fi

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/.upgrade ] ; then
    printf "Moving .upgrade file..."
    if ! mv ${INSTALL_DIRECTORY}/Mycodo/.upgrade ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to move .upgrade file.\n"
    fi
    printf "Done.\n"
  fi

  printf "#### Stage 1 of 2 Complete ####\n"

  # Spawn upgrade script
  cat > /tmp/upgrade_mycodo_stagetwo.sh << EOF
#!/bin/bash

function error_found {
  printf "\n\n"
  printf "There was an error during the upgrade.\n"
  printf "Initial steps to try to fix:\n"
  printf "1. Reboot\n"
  printf "2. If that doesn't fix the issue, run the following command:\n"
  printf "sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_commands.sh upgrade\n"
  printf "3. If that command returns that you are running the latest version, run the following command:\n"
  printf "sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_post.sh\n\n"
  echo '2' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade
  exit 1
}

printf "\n#### Continuing Upgrade: Stage 2 of 2 ####\n"

if [ ! -d "/var/Mycodo-backups" ] ; then
  mkdir /var/Mycodo-backups
fi

printf "\nMoving old Mycodo from ${INSTALL_DIRECTORY}/Mycodo to ${BACKUP_DIR}..."
if ! mv ${INSTALL_DIRECTORY}/Mycodo ${BACKUP_DIR} ; then
  printf "Failed: Error while trying to move old Mycodo install from ${INSTALL_DIRECTORY}/Mycodo to ${BACKUP_DIR}.\n"
  error_found
fi
printf "Done.\n"

printf "Moving new Mycodo from ${MYCODO_NEW_TMP_DIR} to ${INSTALL_DIRECTORY}/Mycodo..."
if ! mv ${MYCODO_NEW_TMP_DIR} ${INSTALL_DIRECTORY}/Mycodo ; then
  printf "Failed: Error while trying to move new Mycodo install from ${MYCODO_NEW_TMP_DIR} to ${INSTALL_DIRECTORY}/Mycodo.\n"
  error_found
fi
printf "Done.\n"

sleep 30

cd ${INSTALL_DIRECTORY}/Mycodo

if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh update-alembic ; then
  printf "Failed: Error while updating database with alembic.\n"
  error_found
fi

if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh initialize ; then
  printf "Failed: Error while running initialization.\n"
  error_found
fi

if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh update-permissions ; then
  printf "Failed: Error while setting permissions.\n"
  error_found
fi

printf "\n\nRunning post-upgrade script...\n"
if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_post.sh ; then
  printf "Failed: Error while running post-upgrade script.\n"
  error_found
fi
printf "Done.\n\n"

printf "Upgrade completed successfully without errors.\n"
printf "The web server will now be restarted. If it doesn't restart properly, execute 'sudo service mycodoflask restart' from the command line or restart your Pi in order to access the web UI.\n"

${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh restart-web-server

echo '0' > ${INSTALL_DIRECTORY}/Mycodo/.upgrade
rm \$0
EOF
  exec /bin/bash /tmp/upgrade_mycodo_stagetwo.sh
}

runSelfUpgrade

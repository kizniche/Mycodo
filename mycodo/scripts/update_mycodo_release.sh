#!/bin/bash

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

runSelfUpdate() {
  NOW=$(date +"%Y-%m-%d_%H-%M-%S")
  INSTALL_DIRECTORY=$( cd -P /var/www/mycodo/.. && pwd -P )
  CURRENT_VERSION=$(python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)
  UPDATE_URL=$(python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -m 4 2>&1)
  UPDATE_VERSION=$(python ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -m 4 -v 2>&1)
  MYCODO_OLD_TMP_DIR="${INSTALL_DIRECTORY}/Mycodo-${CURRENT_VERSION}"
  MYCODO_NEW_TMP_DIR="/tmp/Mycodo-${UPDATE_VERSION}"
  TARBALL_FILE="mycodo-${UPDATE_VERSION}"

  cd ${INSTALL_DIRECTORY}

  if [ "${CURRENT_VERSION}" == "${UPDATE_VERSION}" ] ; then
    printf "Unable to update. You currently have the latest release installed.\n"
    exit 1
  else
    printf "Installed version: ${CURRENT_VERSION}\n"
    printf "Latest version: ${UPDATE_VERSION}\n"
  fi

  if [ "${UPDATE_URL}" == "None" ] ; then
    printf "Unable to update. A URL of the latest release was not able to be obtained.\n"
    exit 1
  fi

  printf "#### Update to v${UPDATE_VERSION} initiated $NOW ####\n"
  printf "#### Beginning Upgrade: Stage 1 of 2 ####\n"

  printf "Stopping web UI and daemon..."
  if ! service mycodo stop && /etc/init.d/apache2 stop ; then
    printf "Error: Unable to stop web UI and daemon. Continuing anyway...\n"
  fi
  printf "Done.\n"

  printf "Downloading latest Mycodo version to ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz..."
  if ! wget --quiet -O ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz ${UPDATE_URL} ; then
    printf "Failed: Error while trying to wget new version.\n"
    printf "File requested: ${UPDATE_URL} -> ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz\n"
    exit 1
  fi
  printf "Done.\n"

  if [ -d "${MYCODO_NEW_TMP_DIR}" ] ; then
    printf "The tmp directory ${MYCODO_NEW_TMP_DIR} already exists. Removing..."
    if ! rm -Rf ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to delete tmp directory ${MYCODO_NEW_TMP_DIR}.\n"
      exit 1
    fi
    printf "Done.\n"
  fi

  printf "Creating ${MYCODO_NEW_TMP_DIR}..."
  if ! mkdir ${MYCODO_NEW_TMP_DIR} ; then
    printf "Failed: Error while trying to create ${MYCODO_NEW_TMP_DIR}.\n"
    exit 1
  fi
  printf "Done.\n"

  printf "Extracting ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz to ${MYCODO_NEW_TMP_DIR}..."
  if ! tar xzf ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz -C ${MYCODO_NEW_TMP_DIR} --strip-components=1 ; then
    printf "Failed: Error while trying to extract files from ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz to ${MYCODO_NEW_TMP_DIR}.\n"
    exit 1
  fi
  printf "Done.\n"
  
  printf "Removing ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz..."
  if ! rm -rf ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz ; then
    printf "Failed: Error while removing ${INSTALL_DIRECTORY}/${TARBALL_FILE}.tar.gz.\n"
    exit 1
  fi
  printf "Done.\n"

  printf "Moving databases from ${INSTALL_DIRECTORY}/Mycodo/databases/ to ${MYCODO_NEW_TMP_DIR}/databases..."
  if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/*.db ${MYCODO_NEW_TMP_DIR}/databases ; then
    printf "Failed: Error while trying to copy databases."
    exit 1
  fi
  printf "Done.\n"

  printf "Upgrading databases..."
  if ! cd ${MYCODO_NEW_TMP_DIR}/databases && alembic upgrade head ; then
    printf "Failed: Error while trying to upgrade databases."
    exit 1
  fi
  printf "Done.\n"

  printf "Copying statistics ID..."
  if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/statistics.id ${MYCODO_NEW_TMP_DIR}/databases ; then
    printf "Failed: Error while trying to copy statistics ID."
    exit 1
  fi
  printf "Done.\n"

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs ] ; then
    printf "Copying SSL certificates..."
    if ! cp -R ${INSTALL_DIRECTORY}/Mycodo/mycodo/mycodo_flask/ssl_certs ${MYCODO_NEW_TMP_DIR}/mycodo/mycodo_flask/ssl_certs ; then
      printf "Failed: Error while trying to copy SSL certificates."
      exit 1
    fi
    printf "Done.\n"
  fi

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/camera-stills ] ; then
    printf "Moving Camera stills directory..."
    if ! mv ${INSTALL_DIRECTORY}/Mycodo/camera-stills ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to move camera stills directory.\n"
      exit 1
    fi
    printf "Done.\n"
  fi

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/camera-timelapse ] ; then
    printf "Moving Camera timelapse directory..."
    if ! mv ${INSTALL_DIRECTORY}/Mycodo/camera-timelapse ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to move camera timelapse directory.\n"
      exit 1
    fi
    printf "Done.\n"
  fi

  if [ -d ${INSTALL_DIRECTORY}/Mycodo/camera-video ] ; then
    printf "Moving Camera video directory..."
    if ! mv ${INSTALL_DIRECTORY}/Mycodo/camera-video ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to move camera video directory.\n"
      exit 1
    fi
    printf "Done.\n"
  fi

  # Spawn update script
  cat > /tmp/update_mycodo.sh << EOF
#!/bin/bash

revertInstall() {
  printf "The upgrade has failed: Attempting to revert moving the old Mycodo install.\n"
  if ! mv /var/Mycodo-backups/Mycodo-backup-${CURRENT_VERSION}-${NOW} ${INSTALL_DIRECTORY}/Mycodo ; then
    printf "Failed: Error while trying to revert moving. Could not move /var/Mycodo-backups/Mycodo-backup-${CURRENT_VERSION}-${NOW} to ${INSTALL_DIRECTORY}/Mycodo.\n"
    exit 1
  fi
  printf "Successfully reverted moving the old Mycodo install directory. Moved /var/Mycodo-backups/Mycodo-backup-${CURRENT_VERSION}-${NOW} to ${INSTALL_DIRECTORY}/Mycodo\n"

  printf "Setting permissions...\n"
  if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/update_mycodo.sh initialize ; then
    printf "Failed: Error while running initialization script.\n"
    exit 1
  fi
  printf "Done.\n"
}

printf "#### Continuing Upgrade: Stage 2 of 2 ####\n"

if [ ! -d "/var/Mycodo-backups" ] ; then
  mkdir /var/Mycodo-backups
fi

printf "Moving old Mycodo from ${INSTALL_DIRECTORY}/Mycodo to /var/Mycodo-backups/Mycodo-backup-${CURRENT_VERSION}-${NOW}..."
if ! mv ${INSTALL_DIRECTORY}/Mycodo /var/Mycodo-backups/Mycodo-backup-${CURRENT_VERSION}-${NOW} ; then
  printf "Failed: Error while trying to move old Mycodo install from ${INSTALL_DIRECTORY}/Mycodo to /var/Mycodo-backups/Mycodo-backup-${CURRENT_VERSION}-${NOW}.\n"
  revertInstall
  exit 1
fi
printf "Done.\n"

printf "Moving new Mycodo from ${MYCODO_NEW_TMP_DIR} to ${INSTALL_DIRECTORY}/Mycodo..."
if ! mv ${MYCODO_NEW_TMP_DIR} ${INSTALL_DIRECTORY}/Mycodo ; then
  printf "Failed: Error while trying to move new Mycodo install from ${MYCODO_NEW_TMP_DIR} to ${INSTALL_DIRECTORY}/Mycodo.\n"
  revertInstall
  exit 1
fi
printf "Done.\n"

printf "Setting permissions for new Mycodo install...\n"
if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/update_mycodo.sh initialize ; then
  printf "Failed: Error while running initialization script.\n"
  revertInstall
  exit 1
fi
printf "Done.\n"

printf "Running post-upgrade script...\n"
if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/update_post.sh ; then
  printf "Failed: Error while running post-upgrade script.\n"
  revertInstall
  exit 1
fi
printf "Done.\n"

printf "Update completed successfully without errors.\n"
rm \$0
EOF

  exec /bin/bash /tmp/update_mycodo.sh
}

runSelfUpdate

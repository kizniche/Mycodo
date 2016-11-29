#!/bin/bash

runSelfUpdate() {
  NOW=$(date +"%Y-%m-%d_%H-%M-%S")
  INSTALL_DIRECTORY=$( cd -P /var/www/mycodo/.. && pwd -P )
  MYCODO_NEW_TMP_DIR='/tmp/Mycodo-latest'
  UPDATE_FILE='https://api.github.com/repos/kizniche/Mycodo/tarball'
  FILE_NAME='mycodo-latest'

  cd ${INSTALL_DIRECTORY}

  printf "#### Update Initiated $NOW ####\n"
  printf "#### Beginning Upgrade: Stage 1 of 2 ####\n"

  printf "Stopping web UI and daemon..."
  if ! service mycodo stop && /etc/init.d/apache2 stop ; then
    printf "Error: Unable to stop web UI and daemon. Continuing anyway...\n"
  fi
  printf "Done.\n"

  printf "Downloading latest Mycodo version to ${INSTALL_DIRECTORY}/${FILE_NAME}.tar.gz..."
  if ! wget --quiet -O ${INSTALL_DIRECTORY}/${FILE_NAME}.tar.gz ${UPDATE_FILE} ; then
    printf "Failed: Error while trying to wget new version.\n"
    printf "File requested: ${UPDATE_FILE} -> ${INSTALL_DIRECTORY}/${FILE_NAME}.tar.gz\n"
    exit 1
  fi
  printf "Done.\n"

  # Check if the tmp directory exists and delete it if it does
  if [ -d "${MYCODO_NEW_TMP_DIR}" ] ; then
    printf "The tmp directory ${MYCODO_NEW_TMP_DIR} already exists. Removing..."
    if ! rm -Rf ${MYCODO_NEW_TMP_DIR} ; then
      printf "Failed: Error while trying to delete tmp directory ${MYCODO_NEW_TMP_DIR}.\n"
      exit 1
    fi
    printf "Done.\n"
  fi

  mkdir ${MYCODO_NEW_TMP_DIR}

  printf "Extracting files..."
  if ! tar xzf ${INSTALL_DIRECTORY}/${FILE_NAME}.tar.gz -C ${MYCODO_NEW_TMP_DIR} --strip-components=1 ; then
    printf "Failed: Error while trying to extract files from ${INSTALL_DIRECTORY}/${FILE_NAME}.tar.gz to ${MYCODO_NEW_TMP_DIR}.\n"
    exit 1
  fi
  printf "Done.\n"

  printf "Moving databases..."
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

  printf "Moving statistics ID..."
  if ! cp ${INSTALL_DIRECTORY}/Mycodo/databases/statistics.id ${MYCODO_NEW_TMP_DIR}/databases ; then
    printf "Failed: Error while trying to copy statistics ID."
    exit 1
  fi
  printf "Done.\n"

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

NOW=$(date +"%Y-%m-%d_%H-%M-%S")
INSTALL_DIRECTORY=$( cd -P /var/www/mycodo/.. && pwd -P )
MYCODO_OLD_TMP_DIR="${INSTALL_DIRECTORY}/Mycodo-old"
MYCODO_NEW_TMP_DIR='/tmp/Mycodo-latest'

revertInstall() {
  printf "The upgrade has failed: Attempting to revert moving the old Mycodo install.\n"
  if ! mv /var/Mycodo-backups/Mycodo-backup-${NOW} ${INSTALL_DIRECTORY}/Mycodo ; then
    printf "Failed: Error while trying to revert moving. Could not move /var/Mycodo-backups/Mycodo-backup-${NOW} to ${INSTALL_DIRECTORY}/Mycodo.\n"
    exit 1
  fi
  printf "Successfully reverted moving the old Mycodo install directory. Moved /var/Mycodo-backups/Mycodo-backup-${NOW} to ${INSTALL_DIRECTORY}/Mycodo\n"

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

printf "Moving old Mycodo install to /var/Mycodo-backups/Mycodo-backup-${NOW}..."
if ! mv ${INSTALL_DIRECTORY}/Mycodo /var/Mycodo-backups/Mycodo-backup-${NOW} ; then
  printf "Failed: Error while trying to move old Mycodo install from ${INSTALL_DIRECTORY}/Mycodo to /var/Mycodo-backups/Mycodo-backup-${NOW}.\n"
  revertInstall
  exit 1
fi
printf "Done.\n"

printf "Moving new Mycodo install to install directory..."
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

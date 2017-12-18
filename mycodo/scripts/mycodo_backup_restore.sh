#!/bin/bash

if [ "$EUID" -ne 0 ] ; then
    printf "Please run as root.\n"
    exit 1
fi

if [ ! -e $1 ]; then
    echo "Directory does not exist"
    exit 1
elif [ ! -d $1 ]; then
    echo "Input not a directory"
    exit 2
fi

INSTALL_DIRECTORY=$( cd -P /var/www/mycodo/.. && pwd -P )
echo '1' > ${INSTALL_DIRECTORY}/Mycodo/.restore

function error_found {
    echo '2' > ${INSTALL_DIRECTORY}/Mycodo/.restore
    printf "\n\n"
    date
    printf "#### ERROR ####\n"
    printf "There was an error detected during the restore. Please review the log at /var/log/mycodo/mycodorestore.log"
    exit 1
}

CURRENT_VERSION=$(${INSTALL_DIRECTORY}/Mycodo/env_py3/bin/python3 ${INSTALL_DIRECTORY}/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)
NOW=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="/var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION}"

printf "\n#### Restore of backup $1 initiated $NOW ####\n"

printf "#### Stopping Daemon and HTTP server ####\n"
service mycodo stop
sleep 2
apachectl stop

/bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh initialize

/bin/bash ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh update-permissions

printf "\nBacking up current Mycodo from ${INSTALL_DIRECTORY}/Mycodo to ${BACKUP_DIR}..."
if ! mv ${INSTALL_DIRECTORY}/Mycodo ${BACKUP_DIR} ; then
    printf "Failed: Error while trying to back up current Mycodo install from ${INSTALL_DIRECTORY}/Mycodo to ${BACKUP_DIR}.\n"
    error_found
fi
printf "Done.\n"

printf "\nRestoring Mycodo from $1 to ${INSTALL_DIRECTORY}/Mycodo..."
if ! mv $1 ${INSTALL_DIRECTORY}/Mycodo ; then
    printf "Failed: Error while trying to restore Mycodo backup from ${INSTALL_DIRECTORY}/Mycodo to ${BACKUP_DIR}.\n"
    error_found
fi
printf "Done.\n"

if [ -d ${BACKUP_DIR}/env ] ; then
    printf "Moving env directory..."
    if ! mv ${BACKUP_DIR}/env ${INSTALL_DIRECTORY}/Mycodo ; then
        printf "Failed: Error while trying to move env directory.\n"
        error_found
    fi
    printf "Done.\n"
fi

if [ -d ${BACKUP_DIR}/cameras ] ; then
    printf "Moving cameras directory..."
    if ! mv ${BACKUP_DIR}/cameras ${INSTALL_DIRECTORY}/Mycodo/ ; then
        printf "Failed: Error while trying to move cameras directory.\n"
    fi
    printf "Done.\n"
fi

sleep 10

if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh initialize ; then
  printf "Failed: Error while running initialization.\n"
  error_found
fi

if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_commands.sh update-permissions ; then
  printf "Failed: Error while setting permissions.\n"
  error_found
fi

printf "\n\nRunning post-restore script...\n"
if ! ${INSTALL_DIRECTORY}/Mycodo/mycodo/scripts/upgrade_post.sh ; then
  printf "Failed: Error while running post-restore script.\n"
  error_found
fi
printf "Done.\n\n"

date
printf "Restore completed successfully without errors.\n"

echo '0' > ${INSTALL_DIRECTORY}/Mycodo/.restore

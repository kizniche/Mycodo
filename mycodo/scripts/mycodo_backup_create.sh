#!/bin/bash

exec 2>&1

if [ "$EUID" -ne 0 ] ; then
    printf "Please run as root.\n"
    exit 1
fi

INSTALL_DIRECTORY=$( cd -P /var/mycodo-root/.. && pwd -P )

function error_found {
    date
    printf "\n#### ERROR ####"
    printf "\nThere was an error detected while creating the backup. Please review the log at /var/log/mycodo/mycodobackup.log"
    exit 1
}

CURRENT_VERSION=$("${INSTALL_DIRECTORY}"/Mycodo/env/bin/python "${INSTALL_DIRECTORY}"/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)
NOW=$(date +"%Y-%m-%d_%H-%M-%S")
TMP_DIR="/var/tmp/Mycodo-backup-${NOW}-${CURRENT_VERSION}"
BACKUP_DIR="/var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION}"

printf "\n#### Create backup initiated %s ####\n" "${NOW}"

mkdir -p /var/Mycodo-backups

printf "Backing up current Mycodo from %s/Mycodo to %s..." "${INSTALL_DIRECTORY}" "${TMP_DIR}"
if ! rsync -avq --exclude=cameras --exclude=env "${INSTALL_DIRECTORY}"/Mycodo "${TMP_DIR}" ; then
    printf "Failed: Error while trying to back up current Mycodo install from %s/Mycodo to %s.\n" "${INSTALL_DIRECTORY}" "${BACKUP_DIR}"
    error_found
fi
printf "Done.\n"

printf "Moving %s/Mycodo to %s..." "${TMP_DIR}" "${BACKUP_DIR}"
if ! mv "${TMP_DIR}"/Mycodo "${BACKUP_DIR}" ; then
    printf "Failed: Error while trying to move %s/Mycodo to %s.\n" "${TMP_DIR}" "${BACKUP_DIR}"
    error_found
fi
printf "Done.\n"

date
printf "Backup completed successfully without errors.\n"

#!/bin/bash
#
# Mycodo upgrade script (4.x -> 5.0)
#
# Usage: sudo /bin/bash ~/upgrade_mycodo_5.sh
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P )

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root: \"sudo /bin/bash ~/upgrade_mycodo_5.sh\"\n";
    exit
fi

LOG_LOCATION=${INSTALL_DIRECTORY}/upgrade_mycodo_5.log
exec > >(tee -i ${LOG_LOCATION})
exec 2>&1


printf "Stopping the Mycodo daemon..."
  if ! service mycodo stop ; then
    printf "Error: Unable to stop the daemon. Continuing anyway...\n"
  fi
printf "Done.\n"

printf "Stopping the Mycodo daemon..."
  if ! /etc/init.d/apache2 stop ; then
    printf "Error: Unable to stop the daemon. Continuing anyway...\n"
  fi
printf "Done.\n"

abort()
{
    echo >&2 "
*******************************
*** ERROR: Install Aborted! ***
*******************************

An error occurred that prevented Mycodo from being installed!

Review the upgrade log at ${LOG_LOCATION}

Please contact the developer by submitting a bug report at
https://github.com/kizniche/Mycodo/issues with the pertinent
excerpts from the upgrade log.
"
    echo "An error occurred. Exiting..." >&2
    exit 1
}

trap 'abort' 0

set -e

NOW=$(date +"%m-%d-%Y %H:%M:%S")

cd ~

printf "\n#### Checking if ${INSTALL_DIRECTORY}/Mycodo directory exists\n"
if [ ! -d ${INSTALL_DIRECTORY}/Mycodo ] ; then
  printf "\n#### ${INSTALL_DIRECTORY}/Mycodo directory doesn't exist. Exiting.\n"
  exit 1
fi

printf "### Mycodo 4.x -> 5.0 upgrade beginning at $NOW\n"

printf "Downloading Mycodo 5.0.0..."
  if ! wget https://github.com/kizniche/Mycodo/archive/v5.0.0.tar.gz ; then
    printf "Failed: Download Mycodo 5.0.0 failed.\n"
    exit 1
  fi
printf "Done.\n"

printf "Moving ${INSTALL_DIRECTORY}/Mycodo to ${INSTALL_DIRECTORY}/Mycodo-4-old..."
  if ! mv ${INSTALL_DIRECTORY}/Mycodo ${INSTALL_DIRECTORY}/Mycodo-4 ; then
    printf "Failed: Error while moving ${INSTALL_DIRECTORY}/Mycodo to ${INSTALL_DIRECTORY}/Mycodo-4-old.\n"
    exit 1
  fi
printf "Done.\n"

printf "Creating Mycodo 5.0.0 directory..."
  if ! mkdir Mycodo ; then
    printf "Failed: Create Mycodo 5.0.0 directory.\n"
    exit 1
  fi
printf "Done.\n"

printf "Extracting Mycodo 5.0.0 files..."
  if ! tar xzf v5.0.0.tar.gz -C Mycodo --strip-components=1 ; then
    printf "Failed: Extract Mycodo 5.0.0 files.\n"
    exit 1
  fi
printf "Done.\n"

rm -f v5.0.0.tar.gz
cd Mycodo/install
sudo /bin/bash ./setup.sh

echo >&2 "
\n### Mycodo 4.x -> 5.0 upgrade script finished without errors.
"

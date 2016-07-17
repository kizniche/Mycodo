#!/bin/bash
#
# Mycodo install script
#
# Usage: sudo ./setup.sh
#

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root with \"sudo ./setup.sh\"\n";
    exit
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/" && pwd -P )
cd $INSTALL_DIRECTORY

LOG_LOCATION=$INSTALL_DIRECTORY/setup.log
exec > >(tee -i $LOG_LOCATION)
exec 2>&1

abort()
{
    echo >&2 '
***************
*** ABORTED ***
***************
'
    echo "An error occurred. Exiting..." >&2
    exit 1
}

trap 'abort' 0

set -e

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "### Mycodo installation began at $NOW\n\n"

if [ -f $INSTALL_DIRECTORY/mycodo/scripts/update_mycodo.sh ]; then
    $INSTALL_DIRECTORY/mycodo/scripts/update_mycodo.sh upgrade-packages &&
    $INSTALL_DIRECTORY/mycodo/scripts/update_mycodo.sh setup &&
    $INSTALL_DIRECTORY/mycodo/scripts/update_mycodo.sh initialize &&
else
    printf "Error: $INSTALL_DIRECTORY/mycodo/scripts/update_mycodo.sh not found\n"
fi

trap : 0

echo >&2 '
************
*** DONE *** 
************
'

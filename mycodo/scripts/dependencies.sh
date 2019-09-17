#!/bin/bash
#
#  dependencies.sh - Commands to install dependencies
#

exec 2>&1

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
cd ${INSTALL_DIRECTORY}

printf "\n#### Installing/updating ${2} (${1})\n"

case "${1}" in
    'apt')
        apt-get install -y ${2}
    ;;
    'pip-pypi')
        if [ ! -e ${INSTALL_DIRECTORY}/env/bin/python3 ]; then
            printf "\n## Error: Virtualenv doesn't exist. Creating...\n"
            /bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh setup-virtualenv
        else
            ${INSTALL_DIRECTORY}/env/bin/pip3 install --upgrade ${2}
        fi
    ;;
    'pip-git')
        if [ ! -e ${INSTALL_DIRECTORY}/env/bin/python3 ]; then
            printf "\n## Error: Virtualenv doesn't exist. Creating...\n"
            /bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh setup-virtualenv
        else
            ${INSTALL_DIRECTORY}/env/bin/pip3 install --upgrade -e ${2}
        fi
    ;;
    'pigpio')
        ${INSTALL_CMD} install-pigpiod
    ;;
    'bcm2835')
        ${INSTALL_CMD} install-bcm2835
    ;;
    *)
        printf "\nUnrecognized dependency: ${1}"
    ;;
esac

#!/bin/bash
#
#  dependencies.sh - Commands to install dependencies
#

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
        ${INSTALL_CMD} install-pip-dependency ${2}
    ;;
    'pip-git')
        ${INSTALL_CMD} install-pip-dependency -e ${2}
    ;;
    'numpy')
        ${INSTALL_CMD} install-numpy
    ;;
    'pigpio')
        ${INSTALL_CMD} install-pigpiod
        ${INSTALL_CMD} enable-pigpiod-low
    ;;
    *)
        printf "\nUnrecognized dependency: ${1}"
    ;;
esac

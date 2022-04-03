#!/bin/bash
#
#  dependencies.sh - Commands to install dependencies
#

exec 2>&1

if [ "$EUID" -ne 0 ] ; then
  printf "Must be run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
cd "${INSTALL_DIRECTORY}" || return

printf "\n#### Installing/updating %s (%s)\n" "${2}" "${1}"

case "${1}" in
    'apt')
        apt-get install -y "${2}"
    ;;
    'pip-pypi')
        if [ ! -e "${INSTALL_DIRECTORY}"/env/bin/python3 ]; then
            printf "\n## Error: Virtualenv doesn't exist. Creating...\n"
            /bin/bash "${INSTALL_DIRECTORY}"/mycodo/scripts/upgrade_commands.sh setup-virtualenv
        else
            "${INSTALL_DIRECTORY}"/env/bin/python -m pip install --upgrade "${2}"
        fi
    ;;
    'internal')
        case "${2}" in
            'pigpio')
                ${INSTALL_CMD} install-pigpiod
            ;;
            'bcm2835')
                ${INSTALL_CMD} install-bcm2835
            ;;
            *)
                printf "\nUnrecognized internal dependency: %s" "${2}"
            ;;
        esac
        ;;
    *)
        printf "\nUnrecognized dependency: %s" "${1}"
    ;;
esac

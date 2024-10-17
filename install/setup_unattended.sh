#!/bin/bash
#
#  setup_unattended.sh - Mycodo install script (unattended version)
#
#  Usage: sudo /bin/bash /opt/Mycodo/install/setup_unattended.sh [influx-option]
#  influx-option can be 1 (install influxdb 1.x), 2 (install influxdb 2.x), or 0 (don't install influxdb)

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"
LOG_LOCATION=${INSTALL_DIRECTORY}/install/setup.log

# Fix for below issue(s)
# https://github.com/pypa/setuptools/issues/3278
# https://github.com/kizniche/Mycodo/issues/1149
export SETUPTOOLS_USE_DISTUTILS=stdlib

if [ "$EUID" -ne 0 ]; then
    printf "Must be run as root: \"sudo /bin/bash %s/install/setup_unattended.sh [influx-option]\"\n" "${INSTALL_DIRECTORY}"
    exit 1
fi

case "${1:-''}" in
    '1')
        printf "#### Installing Mycodo with Influxdb 1.x\n"
    ;;
    '2')
        printf "#### Installing Mycodo with Influxdb 2.x\n"
    ;;
    '0')
        printf "#### Installing Mycodo without installing Influxdb\n"
    ;;
    *)
        printf "Error: Unrecognized command: sudo setup_unattended.sh [influxdb version] ('1' for version 1.x and '2' for 2.x)\n"
        exit 1
    ;;
esac

printf "Checking Python version...\n"
if hash python3 2>/dev/null; then
  if ! python3 "${INSTALL_DIRECTORY}"/mycodo/scripts/upgrade_check.py --min_python_version "3.8"; then
    printf "Error: Incorrect Python version found. Mycodo requires Python >= 3.8.\n"
    exit 1
  else
    printf "Python >= 3.8 found. Continuing with the install.\n"
  fi
else
  printf "\nError: python3 binary required in PATH to proceed with the install.\n"
  exit 1
fi

NOW=$(date)
printf "### Mycodo installation initiated %s\n\n" "${NOW}" 2>&1 | tee -a "${LOG_LOCATION}"

abort()
{
    printf "
**********************************
** ERROR During Mycodo Install! **
**********************************

An error occurred that may have prevented Mycodo from
being installed properly!

Open to the end of the setup log to view the full error:
%s/install/setup.log

Please contact the developer by submitting a bug report
at https://github.com/kizniche/Mycodo/issues with the
pertinent excerpts from the setup log located at:
%s/install/setup.log
" "${INSTALL_DIRECTORY}" "${INSTALL_DIRECTORY}" 2>&1 | tee -a "${LOG_LOCATION}"
    exit 1
}

trap 'abort' 0

set -e

clear
SECONDS=0
NOW=$(date)
printf "#### Mycodo installation began %s\n" "${NOW}" 2>&1 | tee -a "${LOG_LOCATION}"

${INSTALL_CMD} update-swap-size 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-apt 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} uninstall-apt-pip 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-packages 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} setup-virtualenv 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-pip3 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-pip3-packages 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} pip-clear-cache 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} install-wiringpi 2>&1 | tee -a "${LOG_LOCATION}"
if [[ ${1} == '1' ]]; then
    ${INSTALL_CMD} update-influxdb-1 2>&1 | tee -a "${LOG_LOCATION}"
    ${INSTALL_CMD} update-influxdb-1-db-user 2>&1 | tee -a "${LOG_LOCATION}"
elif [[ ${1} == '2' ]]; then
    ${INSTALL_CMD} update-influxdb-2 2>&1 | tee -a "${LOG_LOCATION}"
    ${INSTALL_CMD} update-influxdb-2-db-user 2>&1 | tee -a "${LOG_LOCATION}"
elif [[ ${1} == '0' ]]; then
    printf "Instructed to not install Influxdb/n"
fi
${INSTALL_CMD} initialize 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-logrotate 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} ssl-certs-generate 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-mycodo-startup-script 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} compile-translations 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} generate-widget-html 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} initialize 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} web-server-update 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} web-server-restart 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} web-server-connect 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-permissions 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} restart-daemon 2>&1 | tee -a "${LOG_LOCATION}"

trap : 0

IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

if [[ -z ${IP} ]]; then
  IP="your.IP.address.here"
fi

CURRENT_DATE=$(date)
printf "#### Mycodo Installer finished %s\n" "${CURRENT_DATE}" 2>&1 | tee -a "${LOG_LOCATION}"

DURATION=$SECONDS
printf "#### Total install time: %d minutes and %d seconds\n" "$((DURATION / 60))" "$((DURATION % 60))" 2>&1 | tee -a "${LOG_LOCATION}"

printf "
*********************************
** Mycodo finished installing! **
*********************************

Although the install finished, it doesn't necessarily mean it installed correctly.
If you experience issues, review the full install log located at:
%s/install/setup.log

Go to https://%s/, or whatever your device's
IP address is, to create an admin user and log in.
" "${INSTALL_DIRECTORY}" "${IP}" 2>&1 | tee -a "${LOG_LOCATION}"

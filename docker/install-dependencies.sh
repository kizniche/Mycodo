#!/bin/bash

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_PATH="$( cd -P "$( dirname "${SOURCE}" )" && pwd )"
LOG_LOCATION="${INSTALL_PATH}"/docker/docker.log

cd "${INSTALL_PATH}" || exit

case "${1:-''}" in
    "install-dependencies")
        apt-get update -y
        apt-get install -y python3-dev python3-setuptools libffi-dev libssl-dev
        easy_install3 pip
        pip install --upgrade pip

        "${INSTALL_PATH}"/mycodo/scripts/upgrade_commands.sh setup-virtualenv

#        printf "\n#### Checking for python 3 virtualenv at %s/env/bin/python3\n" "${INSTALL_PATH}" 2>&1 | tee -a "${LOG_LOCATION}"
#        if [ ! -L "${INSTALL_PATH}"/env/bin/python3 ]; then
#            printf "#### Virtualenv doesn't exist. Creating...\n" 2>&1 | tee -a "${LOG_LOCATION}"
#            pip install virtualenv --upgrade
#            rm -rf "${INSTALL_PATH}"/env
#            PYTHON_BINARY_SYS_LOC="$(python3 -c "import os; print(os.environ['_'])")"
#            virtualenv -p "${PYTHON_BINARY_SYS_LOC}" "${INSTALL_PATH}"/env
#        else
#            printf "#### Virtualenv already exists, skipping creation\n" 2>&1 | tee -a "${LOG_LOCATION}"
#        fi

        if ! [ -x "$(command -v docker)" ]; then
            printf "#### Installing docker\n" 2>&1 | tee -a "${LOG_LOCATION}"
            curl -sSL https://get.docker.com | sh
        else
            printf "#### Docker already installed. Skipping install.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        fi

        usermod -aG docker pi

        if ! [ -x "$(command -v "${INSTALL_PATH}"/env/bin/docker-compose)" ]; then
            printf "#### Installing docker-compose\n" 2>&1 | tee -a "${LOG_LOCATION}"
            "${INSTALL_PATH}"/env/bin/pip install docker-compose
        else
            printf "#### docker-compose already intalled. Skipping install.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        fi

        if ! [ -x "$(command -v logrotate)" ]; then
            printf "#### Installing logrotate\n" 2>&1 | tee -a "${LOG_LOCATION}"
            apt install logrotate
        else
            printf "#### logrotate already installed. Skipping install.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        fi

        cp "${INSTALL_PATH}"/docker/logrotate_docker /etc/logrotate.d/
        printf "#### Dependencies installed\n" 2>&1 | tee -a "${LOG_LOCATION}"

        printf "#### You must log out then back in before running 'make build'\n" 2>&1 | tee -a "${LOG_LOCATION}"
    ;;
    "test")
        docker exec -ti flask "${INSTALL_PATH}"/env/bin/pip install --upgrade -r /home/mycodo/mycodo/tests/software_tests/requirements.txt
        docker exec -ti flask pytest /home/mycodo/mycodo/tests/software_tests
    ;;
    "clean-all")
        docker container stop "$(docker container ls -a -q)" && docker system prune -a -f --volumes
    ;;
    *)
        printf "\nError: Unrecognized command: %s\n%s" "${1}" "${HELP_OPTIONS}"
        exit 1
    ;;
esac

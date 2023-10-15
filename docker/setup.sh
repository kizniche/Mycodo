#!/bin/bash

if [ "$EUID" -ne 0 ] ; then
  printf "Please run as root.\n"
  exit 1
fi

INSTALL_PATH="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
LOG_LOCATION="${INSTALL_PATH}"/docker/docker.log
touch "${LOG_LOCATION}"

cd "${INSTALL_PATH}" || exit

case "${1:-''}" in
    "dependencies")
        apt update -y
        apt install -y python3 python3-pip python3-dev python3-setuptools libffi-dev libssl-dev build-essential
        apt remove -y python3-cffi-backend
        apt clean

        python3 -m pip install --break-system-packages --upgrade pip

        # Rasppberry pi requires rust be installed
        # curl https://sh.rustup.rs -sSf | sh

        if ! [ -x "$(command -v logrotate)" ]; then
            printf "#### Installing logrotate\n" 2>&1 | tee -a "${LOG_LOCATION}"
            apt install logrotate
            cp "${INSTALL_PATH}"/docker/logrotate_docker /etc/logrotate.d/
        else
            printf "#### logrotate already installed. Skipping install.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        fi

        printf "\n#### All dependencies installed\n\n" 2>&1 | tee -a "${LOG_LOCATION}"
    ;;
    "test")
        docker exec -ti mycodo_flask "${INSTALL_PATH}"/env/bin/python -m pip install --upgrade -r /home/mycodo/mycodo/install/requirements-testing.txt
        docker exec -ti mycodo_flask "${INSTALL_PATH}"/env/bin/python -m pytest /home/mycodo/mycodo/tests/software_tests
    ;;
    "clean-all")
        docker container stop "$(docker container ls -a -q)" && docker system prune -a -f --volumes
    ;;
    *)
        printf "\nError: Unrecognized command: %s\n%s" "${1}" "${HELP_OPTIONS}"
        exit 1
    ;;
esac

#!/bin/bash
#
#  upser_commands.sh - Mycodo commands
#

# Get the Mycodo root directory
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
MYCODO_PATH="$( cd -P "$( dirname "${SOURCE}" )/../.." && pwd )"
cd ${MYCODO_PATH}

case "${1:-''}" in
    'install-pip-dependency')
        printf "\n#### Installing ${2} with pip\n"
        if [ ! -d ${MYCODO_PATH}/env ]; then
            printf "\n## Error: Virtualenv doesn't exist. Install with 'sudo $0 setup-virtualenv'\n"
        else
            ${MYCODO_PATH}/env/bin/pip3 install --upgrade ${2}
        fi
    ;;
    *)
        printf "Error: Unrecognized command\n"
    ;;
esac

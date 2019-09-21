#!/bin/bash
#
# Runs all pytests
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

cd ${INSTALL_DIRECTORY}/mycodo || exit

${INSTALL_DIRECTORY}/env/bin/pytest -s tests/software_tests

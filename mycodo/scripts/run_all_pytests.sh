#!/bin/bash
#
# Runs all pytests
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

cd ${INSTALL_DIRECTORY}/mycodo || exit

pytest -s tests/software_tests

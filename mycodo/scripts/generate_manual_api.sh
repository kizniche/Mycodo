#!/bin/bash
# Generates the API offline documentation
#
# Dependencies
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
cd ${INSTALL_DIRECTORY}

wget --no-check-certificate https://192.168.0.9/api/swagger.json ${INSTALL_DIRECTORY}/swagger.xml

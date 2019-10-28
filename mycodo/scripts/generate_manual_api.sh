#!/bin/bash
# Generates the API offline documentation
#
# Dependencies
# npm install -g redoc-cli
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
cd ${INSTALL_DIRECTORY}

wget --no-check-certificate https://192.168.0.9/api/swagger.json ${INSTALL_DIRECTORY}/swagger.json
npx redoc-cli bundle -o ${INSTALL_DIRECTORY}/mycodo-api.html ${INSTALL_DIRECTORY}/swagger.xml
cp ${INSTALL_DIRECTORY}/mycodo-api.html ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/templates/manual-api.html

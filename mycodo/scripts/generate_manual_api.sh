#!/bin/bash
# Generates the API offline HTML documentation
#
# Dependencies
# sudo apt install npm
# sudo npm install -g redoc-cli
# sudo npm install -g npx
#

API_SERV_IP="192.168.0.11"

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

cd "${INSTALL_DIRECTORY}" || return

# check if pandoc is installed
if [[ $(command -v pandoc) ]]
then
  # Generate HTML (HTML5) file
  pandoc --table-of-contents -H "${INSTALL_DIRECTORY}"/mycodo/scripts/pandoc.css_style --self-contained -s -S -t html5 -o "${INSTALL_DIRECTORY}"/mycodo/mycodo_flask/static/manual/mycodo-api-info.html "${INSTALL_DIRECTORY}"/mycodo-api.rst
fi

if curl -k -s --head --request GET https://${API_SERV_IP}/api/swagger.json | grep "200 OK" > /dev/null; then
  if [[ $(command -v redoc-cli) ]]
  then
    rm -rf /tmp/swagger.json
    wget --no-check-certificate https://${API_SERV_IP}/api/swagger.json -O /tmp/swagger.json
    npx redoc-cli bundle -o "${INSTALL_DIRECTORY}"/docs/mycodo-api.html /tmp/swagger.json
    rm -rf /tmp/swagger.json

    # Change title
    sed -i 's/<title>ReDoc documentation<\/title>/<title>Mycodo API documentation<\/title>/g' "${INSTALL_DIRECTORY}"/docs/mycodo-api.html

    cp "${INSTALL_DIRECTORY}"/docs/mycodo-api.html "${INSTALL_DIRECTORY}"/mycodo/mycodo_flask/static/manual/mycodo-api.html
  fi
else
  printf "Cannot connect to https://%s/api/swagger.json\n" "$API_SERV_IP"
fi

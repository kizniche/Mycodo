#!/bin/bash
#
# Generates the Mycodo translation .po files
#
# Requires: pybabel in virtualenv
#
# Note: The following tool is useful for rapid translation of po files
# https://github.com/naskio/po-auto-translation
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

cd "${INSTALL_DIRECTORY}"/mycodo || return

"${INSTALL_DIRECTORY}"/env/bin/pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
"${INSTALL_DIRECTORY}"/env/bin/pybabel update -i messages.pot -d mycodo_flask/translations
rm -f "${INSTALL_DIRECTORY}"/mycodo/messages.pot

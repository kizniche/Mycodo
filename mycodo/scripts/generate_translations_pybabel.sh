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
CURRENT_VERSION=$("${INSTALL_DIRECTORY}"/env/bin/python3 "${INSTALL_DIRECTORY}"/mycodo/utils/github_release_info.py -c 2>&1)

INFO_ARGS=(
  --project "Mycodo"
  --version "${CURRENT_VERSION}"
  --copyright "Kyle T. Gabriel"
  --msgid-bugs-address "mycodo@kylegabriel.com"
)

cd "${INSTALL_DIRECTORY}"/mycodo || return

"${INSTALL_DIRECTORY}"/env/bin/pybabel extract "${INFO_ARGS[@]}" -s -F babel.cfg -k lazy_gettext -o mycodo_flask/translations/messages.pot .
"${INSTALL_DIRECTORY}"/env/bin/pybabel update --update-header-comment -i mycodo_flask/translations/messages.pot -d mycodo_flask/translations

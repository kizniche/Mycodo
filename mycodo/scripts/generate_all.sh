#!/bin/bash
#
# Generates all required Mycodo files
#
# Includes:
#
# Mycodo Manual
# API Docs (swager)
# Translations
#
# Requirements (for generate_manual_api.sh):
# sudo apt install npm
# sudo npm install -g redoc-cli
# sudo npm install -g npx

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_inputs_by_measure.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_inputs.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_outputs.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_functions.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_widgets.py
/bin/bash "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_api.sh
/bin/bash "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_translations_pybabel.sh

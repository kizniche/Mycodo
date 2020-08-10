#!/bin/bash
#
# Generates all required Mycodo files
#
# Includes:
#
# Manual versions (PDF, HTML, TXT)
# Translations

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_inputs.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_outputs.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_widgets.py
/bin/bash "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_manual_api.sh
/bin/bash "${INSTALL_DIRECTORY}"/mycodo/scripts/generate_translations_pybabel.sh

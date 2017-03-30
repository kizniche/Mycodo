#!/bin/bash
# Generates the Mycodo Manual in different formats with pandoc
#
# Dependencies
#
# Debian/Ubuntu
# sudo apt-get install pandoc texlive texlive-latex-extra
#
# Fedroa
# sudo yum install pandoc texlive texlive-collection-latexextra
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
cd ${INSTALL_DIRECTORY}

# check if pandoc is installed
if [[ `command -v pandoc` ]]
then
  # output PDF file
  pandoc ${INSTALL_DIRECTORY}/mycodo/scripts/pandoc_metadata.yaml ${INSTALL_DIRECTORY}/mycodo-manual.md -s -o ${INSTALL_DIRECTORY}/mycodo-manual.pdf

  # output HTML (HTML5) file
  pandoc ${INSTALL_DIRECTORY}/mycodo-manual.md -H ${INSTALL_DIRECTORY}/mycodo/scripts/pandoc.css_style --self-contained -s -S -t html5 -o ${INSTALL_DIRECTORY}/mycodo-manual.html
  cp ${INSTALL_DIRECTORY}/mycodo-manual.html ${INSTALL_DIRECTORY}/mycodo/mycodo_flask/templates/manual.html

  # output plain text
  pandoc ${INSTALL_DIRECTORY}/mycodo-manual.md -s -S -t plain -o ${INSTALL_DIRECTORY}/mycodo-manual.txt
else
  # pandoc is not installed inform the user
  echo "The command pandoc could not be found in the PATH!\n"
fi
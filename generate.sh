#!/bin/bash
# Generates the Mycodo Manual in different formats with pandoc
#
# To install dependencies on Debian/Ubuntu:
# sudo apt-get install pandoc texlive texlive-xetex
#

# check if pandoc is installed
if [[ `command -v pandoc` ]]
then
  # output PDF file
  pandoc metadata.yaml mycodo-manual.md --latex-engine=xelatex -s -o mycodo-manual.pdf

  # output HTML (HTML5) file
  pandoc metadata.yaml mycodo-manual.md --css pandoc.css -s -S -t html5 -o mycodo-manual.html
  cp mycodo-manual.html /var/www/mycodo/mycodo/mycodo_flask/templates/manual.html

  # output plain text
  pandoc mycodo-manual.md -s -S -t plain -o mycodo-manual.txt
else
  # pandoc is not installed inform the user
  echo "The command pandoc could not be found in the PATH!\n"
fi
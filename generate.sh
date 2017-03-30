#! /usr/bin/env bash

# This BASH script generates different output files by calling pandoc

# check if pandoc is installed
if [[ `command -v pandoc` ]]
then
  # outputs the qubes cheat sheet as PDF file
  pandoc metadata.yaml mycodo-manual.md --latex-engine=xelatex -s -o mycodo-manual.pdf

  # outputs the qubes cheat sheet as HTML (HTML5) file
  pandoc metadata.yaml mycodo-manual.md -s -S -t html5 -o mycodo-manual.html
  cp mycodo-manual.html /var/www/mycodo/mycodo/mycodo_flask/templates/manual.html

  # outputs the qubes cheat sheet as plain text
  pandoc mycodo-manual.md -s -S -t plain -o mycodo-manual.txt
else
  # pandoc is not installed inform the user
  echo "The command pandoc could not be found in the PATH!\n"
fi
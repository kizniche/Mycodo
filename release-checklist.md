### Pre-Release Checklist

Notes to keep track of the steps involved in making a new release.

 - [ ] Check that the IP address in /mycodo/scripts/generate_manual_api.sh is accessible and is the latest yet-to-be released version of Mycodo.
 - [ ] Run ```/bin/bash ~/Mycodo/mycodo/scripts/generage_all.sh```
   - Generates list of Input information.
   - Inserts the list of Input information into the RST Mycodo Manual.
   - Generates the PDF, TXT, and HTML versions of the Mycodo Manual from the RST Mycodo Manual.
   - Generates the API Manual.
   - Generates the translatable .po files.
 - [ ] Verify the Input information was successfully inserted into the Mycodo Manuals.
 - [ ] Translate any new untranslated words/phrases in .po files.
 - [ ] Update config.py variables: MYCODO_VERSION, ALEMBIC_VERSION (if applicable).
 - [ ] Update version in README.rst
 - [ ] Update changes in CHANGELOG.md
   - Title in format "## 8.5.3 (2020-06-06)".
   - Section headers "### Bugfixes", "### Features", and "### Miscellaneous".
   - Changes as bullet list under each section header, with a link to issue(s) at the end of each short description (if applicable).
 - [ ] Commit changes and wait for TravisCI to finish running pytests and verify all were successful.
 - [ ] Optionally, a naive Mycodo system with code prior to the yet-to-be released version can be upgraded to master to test its ability to upgrade (useful if experimental database schema changes are being performed during the upgrade).
 - [ ] Make GitHub Release
   - Tag version follows format "vMAJOR.MINOR.BUGFIX" (e.g. v8.0.3)
   - Release title is the same, without "v" (e.g. 8.0.3)
   - Description is copied from CHANGELOG.md
 - [ ] Attempt an upgrade with a naive Mycodo at a release prior to the new release.

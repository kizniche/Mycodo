### Pre-Release Checklist

Notes to keep track of the steps involved in making a new release.

- [ ] Check that the IP address in /mycodo/scripts/generate_manual_api.sh is accessible and is the latest yet-to-be released version of Mycodo.
- [ ] Ensure the virtualenv exists with ```sudo /opt/Mycodo/mycodo/scripts/upgrade_commands.sh setup-virtualenv-full```
- [ ] Update pip packages in virtualenv with ```/opt/Mycodo/env/bin/pip install --break-system-packages -r /opt/Mycodo/docs/requirements.txt```
- [ ] Install the dependencies listed at the top of generate_manual_api.sh
- [ ] Activate the virtualenv with ```source /opt/Mycodo/env/bin/activate```
- [ ] Run ```sudo /bin/bash /opt/Mycodo/mycodo/scripts/generate_all.sh```
   - Generates Input/Output/Function/Widget/API manual pages in Mycodo/docs/, and translatable .po files in Mycodo/mycodo/mycodo_flask/translations, and translated docs.
- [ ] Verify the Input information was successfully inserted into the Mycodo Manuals.
- [ ] Pull, translate words/phrases, and submit pull request, at https://translate.kylegabriel.com/projects/mycodo/translations/ then merge into Mycodo repo
    - Note: f-strings cannot be used with gettext() for translations, use format()
- [ ] Update config.py variables MYCODO_VERSION and ALEMBIC_VERSION (if applicable).
- [ ] Update version in README.rst
- [ ] Update version in mkdocs.yml
- [ ] Update changes in CHANGELOG.md
   - Title in format "## 8.5.3 (2020-06-06)", with current date.
   - Section headers "### Bugfixes", "### Features", and "### Miscellaneous".
   - Changes as bullet list under each section header, with a link to issue(s) at the end of each short description (if applicable).
- [ ] Commit changes and wait for TravisCI to finish running pytests and verify all were successful.
- [ ] Install mkdocs dependencies:
   - ```sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libopenjp2-7```
   - ```/opt/Mycodo/env/bin/python -m pip install --break-system-packages -r /opt/Mycodo/docs/requirements.txt```
- [ ] Clone Mycodo fresh to a new directory and ensure mkdocs pip requirements are installed by running: ```cd Mycodo && sudo mycodo/scripts/upgrade_commands.sh setup-virtualenv && sudo env/bin/python -m pip install --break-system-packages -r docs/requirements.txt```
- [ ] Run ```cd Mycodo && env/bin/python -m mkdocs gh-deploy``` to generate and push docs to gh-pages branch (for https://kizniche.github.io/Mycodo)
- [ ] Optionally, a naive Mycodo system with code prior to the yet-to-be released version can be upgraded to master to test its ability to upgrade (useful if experimental database schema changes are being performed during the upgrade).
- [ ] Make GitHub Release
   - Tag version follows format "vMAJOR.MINOR.BUGFIX" (e.g. v8.0.3)
   - Release title is the same but without "v" (e.g. 8.0.3)
   - Description is copied from CHANGELOG.md
- [ ] Attempt an upgrade with a naive Mycodo at a release prior to the new release.

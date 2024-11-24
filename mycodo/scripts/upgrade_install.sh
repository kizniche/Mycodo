#!/bin/bash
# Upgrade from a previous release to this current release.
# Check currently-installed version for the ability to upgrade to this release version.

exec 2>&1

RELEASE_WIPE=$1

if [ "$EUID" -ne 0 ] ; then
  printf "Must be run as root.\n"
  exit 1
fi

runSelfUpgrade() {
  function error_found {
    echo '2' > "${INSTALL_DIRECTORY}"/Mycodo/.upgrade
    printf "\n\n"
    printf "#### ERROR ####\n"
    printf "There was an error detected during the upgrade. Please review the log at /var/log/mycodo/mycodoupgrade.log"
    exit 1
  }

  printf "\n#### Beginning Upgrade Stage 2 of 3 ####\n\n"
  TIMER_START_stage_two=$SECONDS

  printf "RELEASE_WIPE = %s\n" "$RELEASE_WIPE"

  CURRENT_MYCODO_DIRECTORY=$( cd -P /var/mycodo-root && pwd -P )
  CURRENT_MYCODO_INSTALL_DIRECTORY=$( cd -P /var/mycodo-root/.. && pwd -P )
  THIS_MYCODO_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd -P )
  NOW=$(date +"%Y-%m-%d_%H-%M-%S")

  if [ "$CURRENT_MYCODO_DIRECTORY" == "$THIS_MYCODO_DIRECTORY" ] ; then
    printf "Cannot perform upgrade to the Mycodo instance already installed. Halting upgrade.\n"
    exit 1
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}" ] ; then
    printf "Found currently-installed version of Mycodo. Checking version...\n"
    CURRENT_VERSION=$("${CURRENT_MYCODO_INSTALL_DIRECTORY}"/Mycodo/env/bin/python3 "${CURRENT_MYCODO_INSTALL_DIRECTORY}"/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)
    MAJOR=$(echo "$CURRENT_VERSION" | cut -d. -f1)
    MINOR=$(echo "$CURRENT_VERSION" | cut -d. -f2)
    REVISION=$(echo "$CURRENT_VERSION" | cut -d. -f3)
    if [ -z "$MAJOR" ] || [ -z "$MINOR" ] || [ -z "$REVISION" ] ; then
      printf "Could not determine Mycodo version\n"
      exit 1
    else
      printf "Mycodo version found installed: %s.%s.%s\n" "${MAJOR}" "${MINOR}" "${REVISION}"
    fi
  else
    printf "Could not find a current version of Mycodo installed. Check the symlink /var/mycdo-root that is supposed to point to the install directory"
    exit 1
  fi

  ################################
  # Begin tests prior to upgrade #
  ################################

  printf "\n#### Beginning pre-upgrade checks ####\n\n"

  # Upgrade requires Python >= 3.8
  printf "Checking Python version...\n"
  if hash python3 2>/dev/null; then
    if ! python3 "${CURRENT_MYCODO_DIRECTORY}"/mycodo/scripts/upgrade_check.py --min_python_version "3.8"; then
      printf "Error: Incorrect Python version found. Mycodo requires Python >= 3.8.\n"
      echo '0' > "${CURRENT_MYCODO_DIRECTORY}"/.upgrade
      exit 1
    else
      printf "Python >= 3.8 found. Continuing with the upgrade.\n"
    fi
  else
    printf "\nError: python3 binary required in PATH to proceed with the upgrade.\n"
    echo '0' > "${CURRENT_MYCODO_DIRECTORY}"/.upgrade
    exit 1
  fi

  # If upgrading from version 7 and Python >= 3.6 found (from previous check), upgrade without wiping database
  if [[ "$MAJOR" == 7 ]] && [[ "$RELEASE_WIPE" = true ]]; then
    printf "Your system was found to have Python >= 3.6 installed. Proceeding with upgrade without wiping database.\n"
    RELEASE_WIPE=false
  fi

  printf "All pre-upgrade checks passed. Proceeding with upgrade.\n\n"

  ##############################
  # End tests prior to upgrade #
  ##############################

  THIS_VERSION=$("${CURRENT_MYCODO_DIRECTORY}"/env/bin/python3 "${THIS_MYCODO_DIRECTORY}"/mycodo/utils/github_release_info.py -c 2>&1)
  printf "Upgrading Mycodo to version %s\n\n" "$THIS_VERSION"

  printf "Stopping the Mycodo daemon..."
  if ! service mycodo stop ; then
    printf "Error: Unable to stop the daemon. Continuing anyway...\n"
  fi
  printf "Done.\n"

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/env ] ; then
    printf "Moving env directory..."
    if ! mv "${CURRENT_MYCODO_DIRECTORY}"/env "${THIS_MYCODO_DIRECTORY}" ; then
      printf "Failed: Error while trying to move env directory.\n"
      error_found
    fi
    printf "Done.\n"
  fi

  printf "Copying databases..."
  if ! cp "${CURRENT_MYCODO_DIRECTORY}"/databases/*.db "${THIS_MYCODO_DIRECTORY}"/databases ; then
    printf "Failed: Error while trying to copy databases."
    error_found
  fi
  printf "Done.\n"

  if [ -f "${CURRENT_MYCODO_DIRECTORY}"/mycodo/config_override.py ] ; then
    printf "Copying config_override.py..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/config_override.py "${THIS_MYCODO_DIRECTORY}"/mycodo/ ; then
      printf "Failed: Error while trying to copy config_override.py."
    fi
    printf "Done.\n"
  fi

  printf "Copying flask_secret_key..."
  if ! cp "${CURRENT_MYCODO_DIRECTORY}"/databases/flask_secret_key "${THIS_MYCODO_DIRECTORY}"/databases ; then
    printf "Failed: Error while trying to copy flask_secret_key."
  fi
  printf "Done.\n"

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/ssl_certs ] ; then
    printf "Copying SSL certificates..."
    if ! cp -R "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/ssl_certs "${THIS_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/ssl_certs ; then
      printf "Failed: Error while trying to copy SSL certificates."
      error_found
    fi
    printf "Done.\n"
  fi

  # TODO: Remove in next major release
  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/controllers/custom_controllers ] ; then
    printf "Copying mycodo/controllers/custom_controllers..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/controllers/custom_controllers/*.py "${THIS_MYCODO_DIRECTORY}"/mycodo/functions/custom_functions/ ; then
      printf "Failed: Error while trying to copy mycodo/controllers/custom_controllers"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/functions/custom_functions ] ; then
    printf "Copying mycodo/functions/custom_functions..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/functions/custom_functions/*.py "${THIS_MYCODO_DIRECTORY}"/mycodo/functions/custom_functions/ ; then
      printf "Failed: Error while trying to copy mycodo/functions/custom_functions"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/actions/custom_actions ] ; then
    printf "Copying mycodo/actions/custom_actions..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/actions/custom_actions/*.py "${THIS_MYCODO_DIRECTORY}"/mycodo/actions/custom_actions/ ; then
      printf "Failed: Error while trying to copy mycodo/actions/custom_actions"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/inputs/custom_inputs ] ; then
    printf "Copying mycodo/inputs/custom_inputs..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/inputs/custom_inputs/*.py "${THIS_MYCODO_DIRECTORY}"/mycodo/inputs/custom_inputs/ ; then
      printf "Failed: Error while trying to copy mycodo/inputs/custom_inputs"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/outputs/custom_outputs ] ; then
    printf "Copying mycodo/outputs/custom_outputs..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/outputs/custom_outputs/*.py "${THIS_MYCODO_DIRECTORY}"/mycodo/outputs/custom_outputs/ ; then
      printf "Failed: Error while trying to copy mycodo/outputs/custom_outputs"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/widgets/custom_widgets ] ; then
    printf "Copying mycodo/widgets/custom_widgets..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/widgets/custom_widgets/*.py "${THIS_MYCODO_DIRECTORY}"/mycodo/widgets/custom_widgets/ ; then
      printf "Failed: Error while trying to copy mycodo/widgets/custom_widgets"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/user_python_code ] ; then
    printf "Copying mycodo/user_python_code..."
    if ! cp "${CURRENT_MYCODO_DIRECTORY}"/mycodo/user_python_code/*.py "${THIS_MYCODO_DIRECTORY}"/mycodo/user_python_code/ ; then
      printf "Failed: Error while trying to copy mycodo/user_python_code"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/note_attachments ] ; then
    printf "Copying mycodo/note_attachments..."
    if ! cp -r "${CURRENT_MYCODO_DIRECTORY}"/mycodo/note_attachments "${THIS_MYCODO_DIRECTORY}"/mycodo/ ; then
      printf "Failed: Error while trying to copy mycodo/note_attachments"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/js/user_js ] ; then
    printf "Copying mycodo/mycodo_flask/static/js/user_js..."
    if ! cp -r "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/js/user_js "${THIS_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/js/ ; then
      printf "Failed: Error while trying to copy mycodo/mycodo_flask/static/js/user_js"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/css/user_css ] ; then
    printf "Copying mycodo/mycodo_flask/static/css/user_css..."
    if ! cp -r "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/css/user_css "${THIS_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/css/ ; then
      printf "Failed: Error while trying to copy mycodo/mycodo_flask/static/css/user_css"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/fonts/user_fonts ] ; then
    printf "Copying mycodo/mycodo_flask/static/fonts/user_fonts..."
    if ! cp -r "${CURRENT_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/fonts/user_fonts "${THIS_MYCODO_DIRECTORY}"/mycodo/mycodo_flask/static/fonts/ ; then
      printf "Failed: Error while trying to copy mycodo/mycodo_flask/static/fonts/user_fonts"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/mycodo/user_scripts ] ; then
    printf "Copying mycodo/user_scripts..."
    if ! cp -r "${CURRENT_MYCODO_DIRECTORY}"/mycodo/user_scripts "${THIS_MYCODO_DIRECTORY}"/mycodo/ ; then
      printf "Failed: Error while trying to copy mycodo/user_scripts"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/output_usage_reports ] ; then
    printf "Moving output_usage_reports directory..."
    if ! mv "${CURRENT_MYCODO_DIRECTORY}"/output_usage_reports "${THIS_MYCODO_DIRECTORY}" ; then
      printf "Failed: Error while trying to move output_usage_reports directory.\n"
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/cameras ] ; then
    printf "Moving cameras directory..."
    if ! mv "${CURRENT_MYCODO_DIRECTORY}"/cameras "${THIS_MYCODO_DIRECTORY}" ; then
      printf "Failed: Error while trying to move cameras directory.\n"
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_MYCODO_DIRECTORY}"/.upgrade ] ; then
    printf "Moving .upgrade file..."
    if ! mv "${CURRENT_MYCODO_DIRECTORY}"/.upgrade "${THIS_MYCODO_DIRECTORY}" ; then
      printf "Failed: Error while trying to move .upgrade file.\n"
    fi
    printf "Done.\n"
  fi

  if [ ! -d "/var/Mycodo-backups" ] ; then
    mkdir /var/Mycodo-backups
  fi

  BACKUP_DIR="/var/Mycodo-backups/Mycodo-backup-${NOW}-${CURRENT_VERSION}"

  printf "Moving current Mycodo install from %s to %s..." "${CURRENT_MYCODO_DIRECTORY}" "${BACKUP_DIR}"
  if ! mv "${CURRENT_MYCODO_DIRECTORY}" "${BACKUP_DIR}" ; then
    printf "Failed: Error while trying to move old Mycodo install from %s to %s.\n" "${CURRENT_MYCODO_DIRECTORY}" "${BACKUP_DIR}"
    error_found
  fi
  printf "Done.\n"

  mkdir -p /opt

  printf "Moving downloaded Mycodo version from %s to /opt/Mycodo..." "${THIS_MYCODO_DIRECTORY}"
  if ! mv "${THIS_MYCODO_DIRECTORY}" /opt/Mycodo ; then
    printf "Failed: Error while trying to move new Mycodo install from %s to /opt/Mycodo.\n" "${THIS_MYCODO_DIRECTORY}"
    error_found
  fi
  printf "Done.\n"

  sleep 30

  cd /opt/Mycodo || return

  ############################################
  # Begin tests prior to post-upgrade script #
  ############################################

  if [ "$RELEASE_WIPE" = true ] ; then
    # Instructed to wipe configuration files (database, virtualenv)

    if [ -d /opt/Mycodo/env ] ; then
      printf "Removing virtualenv at /opt/Mycodo/env..."
      if ! rm -rf /opt/Mycodo/env ; then
        printf "Failed: Error while trying to delete virtaulenv at /opt/Mycodo/env.\n"
      fi
      printf "Done.\n"
    fi

    if [ -d /opt/Mycodo/databases/mycodo.db ] ; then
      printf "Removing database at /opt/Mycodo/databases/mycodo.db..."
      if ! rm -f /opt/Mycodo/databases/mycodo.db ; then
        printf "Failed: Error while trying to delete database at /opt/Mycodo/databases/mycodo.db.\n"
      fi
      printf "Done.\n"
    fi

  fi

  printf "\n#### Completed Upgrade Stage 2 of 3 in %s seconds ####\n" "$((SECONDS - TIMER_START_stage_two))"

  ##########################################
  # End tests prior to post-upgrade script #
  ##########################################

  printf "\n#### Beginning Upgrade Stage 3 of 3 ####\n\n"
  TIMER_START_stage_three=$SECONDS

  printf "Running post-upgrade script...\n"
  if ! /opt/Mycodo/mycodo/scripts/upgrade_post.sh ; then
    printf "Failed: Error while running post-upgrade script.\n"
    error_found
  fi

  printf "\n#### Completed Upgrade Stage 3 of 3 in %s seconds ####\n\n" "$((SECONDS - TIMER_START_stage_three))"

  printf "Upgrade completed. Review the log to ensure no critical errors were encountered\n"

  #############################
  # Begin tests after upgrade #
  #############################



  ###########################
  # End tests after upgrade #
  ###########################

  echo '0' > /opt/Mycodo/.upgrade

  exit 0
}

runSelfUpgrade

#!/bin/bash
# Downloads the version of Mycodo to upgrade to

exec 2>&1

UPGRADE_TYPE=$1
UPGRADE_MAJ_VERSION=$2

if [ "$EUID" -ne 0 ] ; then
  printf "Must be run as root.\n"
  exit 1
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd -P )
cd "${INSTALL_DIRECTORY}" || return

runDownloadMycodo() {
  INSTALL_DIRECTORY=$( cd -P /var/mycodo-root/.. && pwd -P )
  echo '1' > "${INSTALL_DIRECTORY}"/Mycodo/.upgrade

  function error_found {
    echo '2' > "${INSTALL_DIRECTORY}"/Mycodo/.upgrade
    printf "\n\n"
    printf "#### ERROR ####\n"
    printf "There was an error detected during the upgrade. Please review the log at /var/log/mycodo/mycodoupgrade.log"
    exit 1
  }
  
  CURRENT_VERSION=$("${INSTALL_DIRECTORY}"/Mycodo/env/bin/python3 "${INSTALL_DIRECTORY}"/Mycodo/mycodo/utils/github_release_info.py -c 2>&1)

  RELEASE_WIPE=false

  if [ "$UPGRADE_TYPE" == "upgrade-release-major" ] || [ "$UPGRADE_TYPE" == "upgrade-release-wipe" ] ; then

    if [ -n "$UPGRADE_MAJ_VERSION" ]; then

      UPDATE_VERSION=$("${INSTALL_DIRECTORY}"/Mycodo/env/bin/python3 "${INSTALL_DIRECTORY}"/Mycodo/mycodo/utils/github_release_info.py -m "$UPGRADE_MAJ_VERSION" -v 2>&1)
      UPDATE_URL=$("${INSTALL_DIRECTORY}"/Mycodo/env/bin/python3 "${INSTALL_DIRECTORY}"/Mycodo/mycodo/utils/github_release_info.py -m "$UPGRADE_MAJ_VERSION" 2>&1)

      if [ "${CURRENT_VERSION}" == "${UPDATE_VERSION}" ] ; then
        printf "\n\nUnable to upgrade. You currently have the latest release installed.\n"
        error_found
      else
        printf "\n\nInstalled version: %s\n" "${CURRENT_VERSION}"
        printf "Latest version: %s\n" "${UPDATE_VERSION}"
      fi

      if [ "$UPGRADE_TYPE" == "upgrade-release-wipe" ] ; then
        RELEASE_WIPE=true
      fi

    fi

  elif [ "$UPGRADE_TYPE" == "force-upgrade-master" ]; then

    # If this script is executed with the 'force-upgrade-master' argument,
    # an upgrade will be performed with the latest git commit from the repo
    # master instead of the release version

    UPDATE_VERSION="master"
    printf "\n\nUpgrade script executed with the 'force-upgrade-master' argument. Upgrading from github repo master.\n"
    UPDATE_URL="https://github.com/kizniche/Mycodo/archive/master.tar.gz"
    TARBALL_FILE="Mycodo-master"

  fi

  MYCODO_NEW_TMP_DIR="/tmp/Mycodo-${UPDATE_VERSION}"
  TARBALL_FILE="mycodo-${UPDATE_VERSION}"

  if [ "${UPDATE_URL}" == "None" ] ; then
    printf "\nUnable to upgrade. The URL for a tar.gz archive of the latest release was not able to be obtained.\n"
    error_found
  fi

  printf "\n#### Beginning Upgrade: Stage 1 of 3 ####\n\n"
  TIMER_START_stage_one=$SECONDS

  printf "Downloading latest Mycodo version %s to %s/%s.tar.gz..." "${UPDATE_VERSION}" "${INSTALL_DIRECTORY}" "${TARBALL_FILE}"
  if ! wget --quiet -O "${INSTALL_DIRECTORY}"/"${TARBALL_FILE}".tar.gz ${UPDATE_URL} ; then
    printf "Failed: Error while trying to wget new version.\n"
    printf "File requested: %s -> %s/%s.tar.gz\n" "${UPDATE_URL}" "${INSTALL_DIRECTORY}" "${TARBALL_FILE}"
    error_found
  fi
  printf "Done.\n"

  if [ -d "${MYCODO_NEW_TMP_DIR}" ] ; then
    printf "The tmp directory %s already exists. Removing..." "${MYCODO_NEW_TMP_DIR}"
    if ! rm -rf "${MYCODO_NEW_TMP_DIR}" ; then
      printf "Failed: Error while trying to delete tmp directory %s.\n" "${MYCODO_NEW_TMP_DIR}"
      error_found
    fi
    printf "Done.\n"
  fi

  printf "Creating %s..." "${MYCODO_NEW_TMP_DIR}"
  if ! mkdir "${MYCODO_NEW_TMP_DIR}" ; then
    printf "Failed: Error while trying to create %s.\n" "${MYCODO_NEW_TMP_DIR}"
    error_found
  fi
  printf "Done.\n"

  printf "Extracting %s/%s.tar.gz to %s..." "${INSTALL_DIRECTORY}" "${TARBALL_FILE}" "${MYCODO_NEW_TMP_DIR}"
  if ! tar xzf "${INSTALL_DIRECTORY}"/"${TARBALL_FILE}".tar.gz -C "${MYCODO_NEW_TMP_DIR}" --strip-components=1 ; then
    printf "Failed: Error while trying to extract files from %s/%s.tar.gz to %s.\n" "${INSTALL_DIRECTORY}" "${TARBALL_FILE}" "${MYCODO_NEW_TMP_DIR}"
    error_found
  else
    if [ "$UPGRADE_TYPE" == "force-upgrade-master" ]; then
      touch "${MYCODO_NEW_TMP_DIR}"/.master
    fi
  fi
  printf "Done.\n"

  printf "Removing %s/%s.tar.gz..." "${INSTALL_DIRECTORY}" "${TARBALL_FILE}"
  if ! rm -rf "${INSTALL_DIRECTORY}"/"${TARBALL_FILE}".tar.gz ; then
    printf "Failed: Error while removing %s/%s.tar.gz.\n" "${INSTALL_DIRECTORY}" "${TARBALL_FILE}"
  fi
  printf "Done.\n"

  printf "\n#### Completed Upgrade Stage 1 of 3 in %s seconds ####\n" "$((SECONDS - TIMER_START_stage_one))"

  exec /bin/bash "${MYCODO_NEW_TMP_DIR}"/mycodo/scripts/upgrade_install.sh $RELEASE_WIPE
}

runDownloadMycodo "$UPGRADE_TYPE" "$UPGRADE_MAJ_VERSION"

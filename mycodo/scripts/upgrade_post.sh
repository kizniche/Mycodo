#!/bin/bash
#
#  upgrade_post.sh - Commands to execute after a Mycodo upgrade
#

exec 2>&1

if [ "$EUID" -ne 0 ]; then
    printf "Must be run as root\n";
    exit
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh"

cd "${INSTALL_DIRECTORY}" || exit

rm -f "${INSTALL_DIRECTORY}"/databases/statistics.csv
rm -f "${INSTALL_DIRECTORY}"/databases/statistics.id

TIMER_START_initialize=$SECONDS
${INSTALL_CMD} initialize
TIMER_TOTAL_initialize=$((SECONDS - TIMER_START_initialize))

TIMER_START_update_swap_size=$SECONDS
${INSTALL_CMD} update-swap-size
TIMER_TOTAL_update_swap_size=$((SECONDS - TIMER_START_update_swap_size))

TIMER_START_setup_virtualenv=$SECONDS
${INSTALL_CMD} setup-virtualenv
TIMER_TOTAL_setup_virtualenv=$((SECONDS - TIMER_START_setup_virtualenv))

TIMER_START_update_apt=$SECONDS
${INSTALL_CMD} update-apt
TIMER_TOTAL_update_apt=$((SECONDS - TIMER_START_update_apt))

TIMER_START_update_packages=$SECONDS
${INSTALL_CMD} update-packages
TIMER_TOTAL_update_packages=$((SECONDS - TIMER_START_update_packages))

TIMER_START_web_server_update=$SECONDS
${INSTALL_CMD} web-server-update
TIMER_TOTAL_web_server_update=$((SECONDS - TIMER_START_web_server_update))

TIMER_START_update_logrotate=$SECONDS
${INSTALL_CMD} update-logrotate
TIMER_TOTAL_update_logrotate=$((SECONDS - TIMER_START_update_logrotate))

TIMER_START_update_pip3=$SECONDS
${INSTALL_CMD} update-pip3
TIMER_TOTAL_update_pip3=$((SECONDS - TIMER_START_update_pip3))

TIMER_START_update_pip3_packages=$SECONDS
${INSTALL_CMD} update-pip3-packages
TIMER_TOTAL_update_pip3_packages=$((SECONDS - TIMER_START_update_pip3_packages))

TIMER_START_update_dependencies=$SECONDS
${INSTALL_CMD} update-dependencies
TIMER_TOTAL_update_dependencies=$((SECONDS - TIMER_START_update_dependencies))

TIMER_START_update_influxdb=$SECONDS
${INSTALL_CMD} update-influxdb
TIMER_TOTAL_update_influxdb=$((SECONDS - TIMER_START_update_influxdb))

TIMER_START_update_alembic=$SECONDS
${INSTALL_CMD} update-alembic
TIMER_TOTAL_update_alembic=$((SECONDS - TIMER_START_update_alembic))

TIMER_START_update_alembic_post=$SECONDS
${INSTALL_CMD} update-alembic-post
TIMER_TOTAL_update_alembic_post=$((SECONDS - TIMER_START_update_alembic_post))

TIMER_START_update_mycodo_startup_script=$SECONDS
${INSTALL_CMD} update-mycodo-startup-script
TIMER_TOTAL_update_mycodo_startup_script=$((SECONDS - TIMER_START_update_mycodo_startup_script))

TIMER_START_compile_translations=$SECONDS
${INSTALL_CMD} compile-translations
TIMER_TOTAL_compile_translations=$((SECONDS - TIMER_START_compile_translations))

TIMER_START_update_cron=$SECONDS
${INSTALL_CMD} update-cron
TIMER_TOTAL_update_cron=$((SECONDS - TIMER_START_update_cron))

TIMER_START_update_permissions=$SECONDS
${INSTALL_CMD} update-permissions
TIMER_TOTAL_update_permissions=$((SECONDS - TIMER_START_update_permissions))

TIMER_START_restart_daemon=$SECONDS
${INSTALL_CMD} restart-daemon
TIMER_TOTAL_restart_daemon=$((SECONDS - TIMER_START_restart_daemon))

TIMER_START_web_server_reload=$SECONDS
${INSTALL_CMD} web-server-reload
TIMER_TOTAL_web_server_reload=$((SECONDS - TIMER_START_web_server_reload))

TIMER_START_web_server_connect=$SECONDS
${INSTALL_CMD} web-server-connect
TIMER_TOTAL_web_server_connect=$((SECONDS - TIMER_START_web_server_connect))

printf "\nStage 3 execution time summary:"
printf "\ninitialize:                   %s s" "${TIMER_TOTAL_initialize}"
printf "\nupdate-swap-size:             %s s" "${TIMER_TOTAL_update_swap_size}"
printf "\nsetup-virtualenv:             %s s" "${TIMER_TOTAL_setup_virtualenv}"
printf "\nupdate-apt:                   %s s" "${TIMER_TOTAL_update_apt}"
printf "\nupdate-packages:              %s s" "${TIMER_TOTAL_update_packages}"
printf "\nweb-server-update:            %s s" "${TIMER_TOTAL_web_server_update}"
printf "\nupdate-logrotate:             %s s" "${TIMER_TOTAL_update_logrotate}"
printf "\nupdate-pip3:                  %s s" "${TIMER_TOTAL_update_pip3}"
printf "\nupdate-pip3-packages:         %s s" "${TIMER_TOTAL_update_pip3_packages}"
printf "\nupdate-dependencies:          %s s" "${TIMER_TOTAL_update_dependencies}"
printf "\nupdate-influxdb:              %s s" "${TIMER_TOTAL_update_influxdb}"
printf "\nupdate-alembic:               %s s" "${TIMER_TOTAL_update_alembic}"
printf "\nupdate-alembic-post:          %s s" "${TIMER_TOTAL_update_alembic_post}"
printf "\nupdate-mycodo-startup-script: %s s" "${TIMER_TOTAL_update_mycodo_startup_script}"
printf "\ncompile-translations:         %s s" "${TIMER_TOTAL_compile_translations}"
printf "\nupdate-cron:                  %s s" "${TIMER_TOTAL_update_cron}"
printf "\nupdate-permissions:           %s s" "${TIMER_TOTAL_update_permissions}"
printf "\nrestart-daemon:               %s s" "${TIMER_TOTAL_restart_daemon}"
printf "\nweb-server_reload:            %s s" "${TIMER_TOTAL_web_server_reload}"
printf "\nweb-server-connect:           %s s\n\n" "${TIMER_TOTAL_web_server_connect}"

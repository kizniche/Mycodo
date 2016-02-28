#!/bin/bash
#
#  update-mycodo.sh - Update Mycodo to the lastest version on GitHub
#
#  Copyright (C) 2015  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root\n"
    exit
fi

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P )

case "${1:-''}" in
    'backup')
        NOW=$(date +"%Y-%m-%d_%H-%M-%S")
        CURCOMMIT=$(git rev-parse --short HEAD)
        printf "#### Creating backup /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT ####\n"
        mkdir -p /var/Mycodo-backups
        mkdir -p /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT
        cp -a $INSTALL_DIRECTORY/../. /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT/
    ;;
    'update')
        NOW=$(date +"%m-%d-%Y %H:%M:%S")
        printf "#### Update Started $NOW ####\n"

        PDIR="$( dirname "$DIR" )"

        cd -P $DIR

        printf "#### Checking if there is an update ####\n"
        git fetch origin

        if git status -uno | grep 'Your branch is behind' > /dev/null; then
            git status -uno | grep 'Your branch is behind'
            printf "The remote repository is newer than yours. This could mean there is an update to Mycodo.\n"

            if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
                printf "#### Stopping Daemon ####\n"
                $INSTALL_DIRECTORY/init.d/mycodo stop
                NOW=$(date +"%Y-%m-%d_%H-%M-%S")
                CURCOMMIT=$(git rev-parse --short HEAD)
                printf "#### Creating backup /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT ####\n"
                mkdir -p /var/Mycodo-backups
                mkdir -p /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT
                cp -a $INSTALL_DIRECTORY/../. /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT/

                printf "#### Updating from github ####\n"
                git fetch
                git reset --hard origin/master


                if [ ! -h /var/www/mycodo ]; then
                    ln -sf $INSTALL_DIRECTORY/public_html /var/www/mycodo
                fi
                cp $INSTALL_DIRECTORY/init.d/mycodo /etc/init.d/
                cp $INSTALL_DIRECTORY/init.d/apache2-tmpfs /etc/init.d/

                printf "#### Executing Post-Update Commands ####\n"
                if [ -f $DIR/update-post.sh ]; then
                    $INSTALL_DIRECTORY/update-post.sh
                    INSTALL_DIRECTORY="$(pwd -P /var/www/mycodo)"
                else
                    printf "Error: update-post.sh not found\n"
                fi

                printf "#### Starting Daemon ####\n"
                /etc/init.d/mycodo start

                printf "#### Update Finished ####\n\n"

                echo '0' > $INSTALL_DIRECTORY/../.updatecheck
                exit 0
            else
                printf "Error: No git repository found. Update stopped.\n\n"
                exit 1
            fi
        else
            printf "Your version of Mycodo is already the latest version. Update stopped.\n\n"
            exit 0
        fi
    ;;
    'updatecheck')
        git fetch origin
        if git status -uno | grep 'Your branch is behind' > /dev/null; then
            git status -uno | grep 'Your branch is behind'
            exit 1
        else
            exit 0
        fi
    ;;
    'fetchorigin')
        git fetch origin
    ;;
esac

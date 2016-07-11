#!/bin/bash
#
#  update_mycodo.sh - Update Mycodo to the lastest version on GitHub
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

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
cd $INSTALL_DIRECTORY

case "${1:-''}" in
    'backup')
        NOW=$(date +"%Y-%m-%d_%H-%M-%S")
        CURCOMMIT=$(git rev-parse --short HEAD)
        printf "#### $INSTALL_DIRECTORY Creating backup /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT ####\n"
        mkdir -p /var/Mycodo-backups
        mkdir -p /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT
        rsync -ah --stats $INSTALL_DIRECTORY/Mycodo/ /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT --exclude old --exclude .git
    ;;
    'upgrade')
        echo "1" > $INSTALL_DIRECTORY/.updating
        NOW=$(date +"%m-%d-%Y %H:%M:%S")
        printf "#### Update initiated $NOW ####\n"

        printf "#### Checking if there is an update ####\n"
        git fetch origin

        if git status -uno | grep 'Your branch is behind' > /dev/null; then
            git status -uno | grep 'Your branch is behind'
            printf "The remote repository is newer than yours. This could mean there is an update to Mycodo.\n"

            if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
                printf "#### Stopping Mycodo daemon ####\n"
                $INSTALL_DIRECTORY/mycodo/mycodo_client.py -t

                # Create backup
                $INSTALL_DIRECTORY/mycodo/scripts/update_mycodo.sh backup

                printf "#### Updating from github ####\n"
                git fetch
                git reset --hard origin/master

                printf "#### Executing Post-Upgrade Commands ####\n"
                if [ -f $INSTALL_DIRECTORY/mycodo/scripts/update_post.sh ]; then
                    $INSTALL_DIRECTORY/mycodo/scripts/update_post.sh
                    printf "#### End Post-Upgrade Commands ####\n"
                else
                    printf "Error: update_post.sh not found\n"
                fi
                
                END=$(date +"%Y-%m-%d_%H-%M-%S")
                printf "#### Update Finished at $END ####\n\n"

                echo '0' > $INSTALL_DIRECTORY/.updating
                exit 0
            else
                printf "Error: No git repository found. Update stopped.\n\n"
                echo '0' > $INSTALL_DIRECTORY/.updating
                exit 1
            fi
        else
            printf "Your version of Mycodo is already the latest version.\n\n"
            echo "1" > $INSTALL_DIRECTORY/.updating
            exit 0
        fi
    ;;
    'initialize')
        if [ ! -e $INSTALL_DIRECTORY/.updating ]; then
            echo '0' > $INSTALL_DIRECTORY/.updating
        fi
        chown -LR mycodo.mycodo $INSTALL_DIRECTORY
        ln -snf $INSTALL_DIRECTORY /var/www/mycodo

        mkdir -p /var/log/mycodo
        chown mycodo.mycodo /var/log/mycodo

        if [ ! -e /var/log/mycodo/mycodo.log ]; then
            touch /var/log/mycodo/mycodo.log
        fi
        chown mycodo.mycodo /var/log/mycodo/mycodo.log
        
        if [ ! -e /var/log/mycodo/mycodoupdate.log ]; then
            touch /var/log/mycodo/mycodoupdate.log
        fi
        chown mycodo.mycodo /var/log/mycodo/mycodoupdate.log

        if [ ! -e /var/log/mycodo/mycodorestore.log ]; then
            touch /var/log/mycodo/mycodorestore.log
        fi
        chown mycodo.mycodo /var/log/mycodo/mycodorestore.log

        if [ ! -e /var/log/mycodo/login.log ]; then
            touch /var/log/mycodo/login.log
        fi
        chown mycodo.mycodo /var/log/mycodo/login.log

        chown mycodo.mycodo /etc/apache2/sites-available/mycodo_flask_apache.conf
        find $INSTALL_DIRECTORY/ -type d -exec chmod u+wx,g+wx {} +
        find $INSTALL_DIRECTORY/ -type f -exec chmod u+w,g+w,o+r {} +
        # find $INSTALL_DIRECTORY/mycodo -type f -name '.?*' -prune -o -exec chmod 770 {} +
        chown root:mycodo $INSTALL_DIRECTORY/mycodo/scripts/mycodo_wrapper
        chmod 4770 $INSTALL_DIRECTORY/mycodo/scripts/mycodo_wrapper
    ;;
esac

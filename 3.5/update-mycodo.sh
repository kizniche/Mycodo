#!/bin/bash
#
#  install.sh - Mycodo install script (still a work-in-progress, use at
#               your own risk)
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
    echo "Please run as root"
    exit
fi

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PDIR="$( dirname "$DIR" )"

cd $DIR

if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "#### Stopping Daemon ####" >&2
    $DIR/init.d/mycodo stop

    NOW=$(date +"%Y-%m-%d_%H-%M-%S")
    echo "#### Creating backup in $PDIR-backups/Mycodo-$NOW ####" >&2
    mkdir -p $DIR/../../Mycodo-backups
    mkdir -p $DIR/../../Mycodo-backups/Mycodo-$NOW
    cp -r $DIR/../../Mycodo/3.5 $DIR/../../Mycodo-backups/Mycodo-$NOW/

    echo "#### Update from GIT ####" >&2
    git fetch --all
    git reset --hard origin/master

    if [ ! -h /var/www/mycodo ]; then
        ln -s $DIR /var/www/mycodo
    fi
    cp $DIR/init.d/mycodo /etc/init.d/
    cp $DIR/init.d/apache2-tmpfs /etc/init.d/

    echo "#### Update Database ####" >&2
    $DIR/setup-database.py -i update

    echo "#### Starting Daemon ####" >&2
    /etc/init.d/mycodo initialize
    /etc/init.d/mycodo start

    echo "#### Update Finished ####" >&2
else
    echo "#### No git repository found ####" >&2
fi


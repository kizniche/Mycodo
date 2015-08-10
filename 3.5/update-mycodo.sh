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
cd $DIR

if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "#### stop daemon ####" >&2
    service mycodo stop

    echo "#### backup logs ####" >&2

    now=$(date +"%Y-%m-%d_%H-%M-%S")
    mkdir -p $DIR/../../Mycodo-backups
    cp -r $DIR/../../Mycodo $DIR/../../Mycodo-backups/Mycodo_$now

    echo "#### update from git ####" >&2
    git fetch --all
    git reset --hard origin/master

else
    echo "#### Not a git repository ####" >&2
fi


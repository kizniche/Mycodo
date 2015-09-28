#!/bin/bash
#
#  restore-mycodo.sh - Restore Mycodo from a backup
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

if [ ! -e "$1" ]; then         
   echo "Directory does not exist!"         
   exit 4  
elif [ ! -d "$1" ]; then         
    echo "Not a Directory"        
    exit 5
fi

NOW=$(date +"%m-%d-%Y %H:%M:%S")
printf "#### Restore of backup initiated $NOW ####\n"

printf "#### Stopping Daemon ####\n"
/etc/init.d/mycodo stop

NOW=$(date +"%Y-%m-%d_%H-%M-%S")
CURCOMMIT=$(git rev-parse --short HEAD)
printf "#### Creating backup /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT ####\n"
mkdir -p /var/Mycodo-backups
mkdir -p /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT
cp -a /var/www/mycodo/. /var/Mycodo-backups/Mycodo-$NOW-$CURCOMMIT/

printf "#### Restoring commit $1 ####\n"
cd /var/www/mycodo/
git reset --hard $1

printf "#### Restoring databases from $DIR/config ####\n"
rm -f /var/www/mycodo/config/*
cp $1/config/*.db /var/www/mycodo/config/

printf "#### Starting Daemon ####\n"
/etc/init.d/mycodo start

printf "#### Restore Complete ####\n"

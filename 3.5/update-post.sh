#!/bin/bash
#
#  update-post.sh - Extra commands to execute for the update process.
#                   Used as a way to provide additional commands to
#                   execute that wouldn't be possible from the running
#                   update script.
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
    printf "Please run as root\n";
    exit
fi

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PDIR="$( dirname "$DIR" )"
DATABASE="/var/www/mycodo/config/mycodo.db"
db_version=`sqlite3 $DATABASE "PRAGMA user_version;"`;

cd $DIR

# Perform update based on database version
if [ ! -f $DATABASE ]; then
    printf "Mycodo database not found: $DATABASE\n";
    printf "Creating Mycodo database...\n";
    $DIR/update-database.py -i update
elif [[ $db_version -gt 0 ]]; then
	printf "Checking if databases are up-to-date...\n";
	$DIR/update-database.py -i update
elif [[ $db_version == "0" ]]; then
	printf "Mycodo database is not versioned. Recreating database...\n";
	rm -rf $DIR/config/mycodo.db
	$DIR/update-database.py -i update
elif [ -z "$db_version" ]; then
	printf "Missing Mycodo database version. Recreating database...\n";
	rm -rf $DIR/config/mycodo.db
	$DIR/update-database.py -i update
else
	printf "Unknown Mycodo database version. Recreating database...\n";
	rm -rf $DIR/config/mycodo.db
	$DIR/update-database.py -i update
fi

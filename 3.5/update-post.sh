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

DATABASE="/var/www/mycodo/config/mycodo.db"

if [ "$EUID" -ne 0 ]; then
    printf "Please run as root\n"
    exit
fi

if [ ! -f $DATABASE ]; then
    printf "Database not found: $DATABASE\n"
    exit 1
fi

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PDIR="$( dirname "$DIR" )"

cd $DIR

# Getting my data
LIST=`sqlite3 $DATABASE "SELECT Database_Version FROM Misc"`;

if [ -z "$LIST" ]; then
	printf "Missing database version, updating database\n";
	# Update mycodo SQLite database
	$DIR/setup-database.py -i update
else
	# For each row
	for ROW in $LIST; do
		# Parsing data (sqlite3 returns a pipe separated string)
		db_version=`echo $ROW | awk '{split($0,a,"|"); print a[1]}'`
		
		# Printing my data
		printf "SQLite Database version: $db_version\n";
	done
fi

# Check database version against known database versions
# Perform update based on database version
if [[ $db_version == "1" ]]; then
	printf "First version of versioned sqlite database. No update necessary.\n"
fi

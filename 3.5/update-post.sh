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
cd $DIR

DATABASEMYC="/var/www/mycodo/config/mycodo.db"
db_version_mycodo=`sqlite3 $DATABASEMYC "PRAGMA user_version;"`;

if [[ $db_version_mycodo -lt 15 ]]; then
	printf "Updating timestamps in log files (this may take a while)...\n";
	if [ -s "/var/www/mycodo/log/sensor-t.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-t.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-ht.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-ht.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-co2.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-co2.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-press.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-press.log
	fi
	if [ -s "/var/www/mycodo/log/relay.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/relay.log
	fi
fi

if [[ $db_version_mycodo -lt 16 ]]; then
	printf "Updating log file formatting (this may take a while)...\n";
	if [ -s "/var/www/mycodo/log/sensor-t.log" ]; then
		tr -s " " < /var/www/mycodo/log/sensor-t.log > /var/www/mycodo/log/sensor-t.log-new
		mv -f /var/www/mycodo/log/sensor-t.log-new /var/www/mycodo/log/sensor-t.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-ht.log" ]; then
		tr -s " " < /var/www/mycodo/log/sensor-ht.log > /var/www/mycodo/log/sensor-ht.log-new
		mv -f /var/www/mycodo/log/sensor-ht.log-new /var/www/mycodo/log/sensor-ht.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-co2.log" ]; then
		tr -s " " < /var/www/mycodo/log/sensor-co2.log > /var/www/mycodo/log/sensor-co2.log-new
		mv -f /var/www/mycodo/log/sensor-co2.log-new /var/www/mycodo/log/sensor-co2.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-press.log" ]; then
		tr -s " " < /var/www/mycodo/log/sensor-press.log > /var/www/mycodo/log/sensor-press.log-new
		mv -f /var/www/mycodo/log/sensor-press.log-new /var/www/mycodo/log/sensor-press.log
	fi
fi

if [[ $db_version_mycodo -lt 18 ]]; then
	printf "Updating timestamps in log files (this may take a while)...\n";
	if [ -s "/var/www/mycodo/log/sensor-t-changes.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-t-changes.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-ht-changes.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-ht-changes.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-co2-changes.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-co2-changes.log
	fi
	if [ -s "/var/www/mycodo/log/sensor-press-changes.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/sensor-press-changes.log
	fi
	if [ -s "/var/www/mycodo/log/relay-changes.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/relay-changes.log
	fi
	if [ -s "/var/www/mycodo/log/timer-changes.log" ]; then
		sed -i -e 's/./\//5' -e 's/./\//8' -e 's/./-/11' -e 's/./:/14' -e 's/./:/17' /var/www/mycodo/log/timer-changes.log
	fi
fi

if [[ $db_version_mycodo -lt 19 ]]; then
	if [ "$(ls -A /var/www/mycodo/cgi-bin/mycodo_python/)" ]; then  # Submodule already initialized
	    continue
	else  # Submodule directory empty, initialize
	    cd -P /var/www/mycodo/../  # git < 1.8.4 (Debian wheezy) requires being at toplevel to update submodule
	    git submodule init
	    git submodule sync
	    git submodule update
	fi
fi

# Make sure python modules are installed/updated
pip install --upgrade lockfile rpyc pyserial tentacle_pi sht-sensor

# Perform update based on database version
if [ ! -f $DATABASEMYC ]; then
    printf "Mycodo database not found: $DATABASEMYC\n";
    printf "Creating Mycodo database...\n";
    $DIR/update-database.py -i update
elif [[ $db_version_mycodo -gt 0 ]]; then
	printf "Checking if databases are up-to-date...\n";
	$DIR/update-database.py -i update
elif [[ $db_version_mycodo == "0" ]]; then
	printf "Mycodo database is not versioned. Recreating database...\n";
	rm -rf $DIR/config/mycodo.db
	$DIR/update-database.py -i update
elif [ -z "$db_version_mycodo" ]; then
	printf "Missing Mycodo database version. Recreating database...\n";
	rm -rf $DIR/config/mycodo.db
	$DIR/update-database.py -i update
else
	printf "Unknown Mycodo database version. Recreating database...\n";
	rm -rf $DIR/config/mycodo.db
	$DIR/update-database.py -i update
fi

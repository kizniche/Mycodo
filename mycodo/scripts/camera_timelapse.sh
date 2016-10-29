#!/bin/bash
#
#  camera-timelapse.sh: Control timelapse of RPi Camera
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

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
DATABASE="$INSTALL_DIRECTORY/databases/mycodo.db"

start() {
    RELAYID=$(sqlite3 $DATABASE "SELECT relay_id FROM cameratimelapse;");
    DURATION=$(sqlite3 $DATABASE "SELECT tl_duration FROM cameratimelapse;");
    EXTRA=$(sqlite3 $DATABASE "SELECT extra_parameters FROM cameratimelapse;");
    PATH=$(sqlite3 $DATABASE "SELECT path FROM cameratimelapse;");
    EXTRA=$(sqlite3 $DATABASE "SELECT extra_parameters FROM cameratimelapse;");
    PREFIX=$(sqlite3 $DATABASE "SELECT prefix FROM cameratimelapse;");
    ADD_TIMESTAMP=$(sqlite3 $DATABASE "SELECT file_timestamp FROM cameratimelapse;");
    if [ -n "$RELAYID" ]; then
        $INSTALL_DIRECTORY/mycodo/mycodo_client.py --relayon $RELAYID --duration $DURATION
    fi
    if [ ! -n "$ADD_TIMESTAMP" ]; then
        TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
        if [ ! -z "$EXTRA" ]; then
            /usr/bin/nohup /usr/bin/raspistill $EXTRA --timelapse $5 --timeout $6 --thumb none -o $INSTALL_DIRECTORY/camera-timelapse/$PREFIX$TIMESTAMP-%05d.jpg &
        else
            /usr/bin/nohup /usr/bin/raspistill --timelapse $5 --timeout $6 --thumb none -o $INSTALL_DIRECTORY/camera-timelapse/$PREFIX$TIMESTAMP-%05d.jpg &
        fi
    else
        if [ ! -z "$EXTRA" ]; then
            /usr/bin/nohup /usr/bin/raspistill $EXTRA --timelapse $5 --timeout $6 --thumb none -o $INSTALL_DIRECTORY/camera-timelapse/$PREFIX-%05d.jpg &
        else
            /usr/bin/nohup /usr/bin/raspistill --timelapse $5 --timeout $6 --thumb none -o $INSTALL_DIRECTORY/camera-timelapse/$PREFIX-%05d.jpg &
        fi
    fi
}

stop() {
    RELAYID=$(sqlite3 $DATABASE "SELECT relay_id FROM cameratimelapse;");
    if [ -n "$RELAYID" ]; then
        $INSTALL_DIRECTORY/mycodo/mycodo_client.py --relayoff $RELAYID
    fi
    pkill raspistill
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    *)
        echo $"Usage: $0 {start|stop}"
        exit 1
esac
exit 0

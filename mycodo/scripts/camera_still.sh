#!/bin/bash
#
#  camera_still.sh - Capture image from the raspberry pi camera and
#                    apply a timestamp.
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
RELAYID=$(sqlite3 $DATABASE "SELECT relay_id FROM camerastill;");
EXTRA=$(sqlite3 $DATABASE "SELECT extra_parameters FROM camerastill;");
ADD_TIMESTAMP=$(sqlite3 $DATABASE "SELECT timestamp FROM camerastill;");
IMG_TS_FMT="%Y-%m-%d %H:%M:%S"
FILE_NAME=$(date +"%Y-%m-%d_%H%M%S")
if [ -n "$RELAYID" ]; then
    $INSTALL_DIRECTORY/mycodo/mycodo_client.py --relayon $RELAYID
fi
sleep 1
if [ -n "$ADD_TIMESTAMP" ]; then
    if [ ! -z "$EXTRA" ]; then
        /usr/bin/raspistill $EXTRA -a 8 -a "$IMG_TS_FMT" -o $INSTALL_DIRECTORY/camera-stills/$FILE_NAME.jpg
    else
        /usr/bin/raspistill -a 8 -a "$IMG_TS_FMT" -o $INSTALL_DIRECTORY/camera-stills/$FILE_NAME.jpg
    fi
else
    if [ ! -z "$EXTRA" ]; then
        /usr/bin/raspistill $EXTRA -o $INSTALL_DIRECTORY/camera-stills/$FILE_NAME.jpg
    else
        /usr/bin/raspistill -o $INSTALL_DIRECTORY/camera-stills/$FILE_NAME.jpg
    fi
fi
if [ -n "$RELAYID" ]; then
    $INSTALL_DIRECTORY/mycodo/mycodo_client.py --relayoff $RELAYID
fi

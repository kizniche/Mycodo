#!/bin/bash
#
# camera-timelapse.sh: Control timelapse of RPi Camera
#
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

start() {
    if [ $1 -ne 0 ]; then
        SECON=$((($6/1000)+($5/1000)+20))
        /var/www/mycodo/cgi-bin/mycodo-client.py -r $1 $SECON
    fi

    # Getting extra command options
    DATABASE="/var/www/mycodo/config/mycodo.db"
    EXTRA=`sqlite3 $DATABASE "SELECT Extra_Parameters FROM CameraStream;"`;


    if [ $4 -ne 0 ]; then
        if [ ! -z "$EXTRA" ]; then
            /usr/bin/nohup /usr/bin/raspistill $EXTRA --timelapse $5 --timeout $6 --thumb none -o $2/$3$4-%05d.jpg &
        else
            /usr/bin/nohup /usr/bin/raspistill --timelapse $5 --timeout $6 --thumb none -o $2/$3$4-%05d.jpg &
        fi
    else
        if [ ! -z "$EXTRA" ]; then
            /usr/bin/nohup /usr/bin/raspistill $EXTRA --timelapse $5 --timeout $6 --thumb none -o $2/$3-%05d.jpg &
        else
            /usr/bin/nohup /usr/bin/raspistill --timelapse $5 --timeout $6 --thumb none -o $2/$3-%05d.jpg &
        fi
    fi
}

stop() {
    if [ $1 -ne 0 ]; then
        /var/www/mycodo/cgi-bin/mycodo-client.py -r $1 0
    fi
    
    pkill raspistill
}

case "$1" in
  start)
        if [ -z $2 ]; then
        echo "Missing required arguments to start"
        else
        start $2 $3 $4 $5 $6 $7
        fi
        ;;
  stop)
        if [ -z $2 ]; then
        stop 0
        else
        stop $2
        fi
        ;;
  *)
        echo $"Usage: $0 {start|stop}"
        exit 1
esac
exit 0

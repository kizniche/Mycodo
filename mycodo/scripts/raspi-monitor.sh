#!/bin/bash -e
#
# Usage:
# /usr/local/sbin/raspi-monitor on/off [usb_port]
#
# usb_port is optional to turn off power to a particular port
# (e.g. to turn off an LCD backlight). It can be 2, 3, 4, 5 or
# possibly other values. One USB port cannot be unpowered, so
# you may have to switch ports.
#
# Script to enable and disable the HDMI signal of the Raspberry PI
# Inspiration: http://www.raspberrypi.org/forums/viewtopic.php?t=16472&p=176258
#
# sudo apt-get update
# sudo apt-get install git gcc libusb-dev
# git clone https://github.com/codazoda/hub-ctrl.c
# gcc -o hub-ctrl ./hub-ctrl.c/hub-ctrl.c -lusb
# sudo cp hub-ctrl /usr/local/sbin/

CMD="$1"
if [ -z "$2" ]; then
    USBPORT="X"
else
    USBPORT=$2
fi

function on {
    if [ "$USBPORT" != "X" ]; then
        /usr/local/sbin/hub-ctrl -h 0 -P "${USBPORT}" -p 1
    fi

    /opt/vc/bin/tvservice --preferred

    # Hack to enable virtual terminal nr 7 again:
    chvt 6
    chvt 7
}

function off {
    if [ "$USBPORT" != "X" ]; then
        /usr/local/sbin/hub-ctrl -h 0 -P "${USBPORT}" -p 0
    fi

    /opt/vc/bin/tvservice --off
}

function must_be_root {
    if [ "${USER}" != root ]; then
        echo "ERROR: Script must be executed as the root user"
        exit 1
    fi
}

function check_files {
    if [ ! -f /usr/local/sbin/hub-ctrl ]; then
        echo "/usr/local/sbin/hub-ctrl not found!"
        exit 1
    fi
    if [ ! -f /opt/vc/bin/tvservice ]; then
        echo "/opt/vc/bin/tvservice not found!"
        exit 1
    fi
}

function main {
    must_be_root
    check_files
    if [ "$CMD" == "on" ]; then
        on
    elif [ "$CMD" == "off" ]; then
        off
    else
        echo "Usage: $0 <on|off>"
        exit 1
    fi
    exit 0
}

main

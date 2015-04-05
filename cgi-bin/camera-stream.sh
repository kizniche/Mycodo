#!/bin/bash
#
# camera-stream.sh: control starting/stopping of RPi Camera Stream
#
start() {
	mkdir /tmp/stream
    
    if [ -n "$1" ]; then
    /usr/local/bin/gpio -g write $2 $3
    fi
    
    /usr/bin/raspistill --nopreview --burst --contrast 20 --sharpness 60 --awb auto --quality 20 --vflip --hflip --width 800 --height 600 -o /tmp/stream/pic.jpg --timelapse 500 --timeout 9999999 --thumb 0:0:0 &
    touch /var/lock/mycodo_raspistill

    LD_LIBRARY_PATH=/usr/local/lib /usr/local/bin/mjpg_streamer -i "input_file.so -f /tmp/stream -n pic.jpg" -o "output_http.so -w /var/www/mycodo" &
    touch /var/lock/mycodo_mjpg_streamer
}
stop() {
    if [ -n "$1" ]; then
    /usr/local/bin/gpio -g write $2 $3
    fi
    
    pkill raspistill
    rm -f /var/lock/mycodo_raspistill
    rm -rf /tmp/stream

    pkill mjpg_streamer
    rm -f /var/lock/mycodo_mjpg_streamer
}
case "$1" in
  start)
        if [ -z $2 ]; then
        start
        else
        start 1 $2 $3
        fi
        ;;
  stop)
        if [ -z $2 ]; then
        stop
        else
        stop 1 $2 $3
        fi
        ;;
  restart|reload|condrestart)
        stop
        start
        ;;
  *)
        echo $"Usage: $0 {start|stop|restart|reload}"
        exit 1
esac
exit 0

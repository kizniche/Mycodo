#!/bin/bash
#
# camera-stream.sh: control starting/stopping of RPi Camera Stream
#
start() {
	mkdir /tmp/stream
        /usr/bin/raspistill --nopreview -co 20 -sh 60 -awb auto -br 70 -vf -hf -w 800 -h 600 -q 80 -o /tmp/stream/pic.jpg -tl 1000 -t 9999999 -th 0:0:0 &
        touch /var/lock/mycodo_raspistill

        LD_LIBRARY_PATH=/usr/local/lib /usr/local/bin/mjpg_streamer -i "input_file.so -f /tmp/stream -n pic.jpg" -o "output_http.so -w /var/www/mycodo" &
        touch /var/lock/mycodo_mjpg_streamer
}
stop() {
        pkill raspistill
        rm -f /var/lock/mycodo_raspistill
        rm -rf /tmp/stream

        pkill mjpg_streamer
        rm -f /var/lock/mycodo_mjpg_streamer
}
case "$1" in
  start)
        start
        ;;
  stop)
        stop
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

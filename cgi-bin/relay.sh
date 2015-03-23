#!/bin/bash
#
#  relay.sh - Turns relays on and off
#  By Kyle Gabriel
#  2012 - 2015
#

LOGPATH="/var/www/mycodo/log"
DATE="/bin/date"

usage() {
  echo Usage: $0 "[RELAY] [SECONDS]"
  echo "Turns relay (1 - 4) on for defined number of seconds, then turns it off"
}

if [ -n "$3" ]
then
  echo "too many inputs: only two parameters are allowed"
  echo "$0 $1 $2 $3 $4 $5"
  echo -e "use" $0 "--help for usage"
  exit
fi

  case $1 in
    -h|--help)
        usage
      ;;
    1)
        case $2 in
        0)
        /usr/local/bin/gpio mode 4 out
        /usr/local/bin/gpio write 4 0
        ;;
        1)
        /usr/local/bin/gpio mode 4 out
        /usr/local/bin/gpio write 4 1
        ;;
        *)
        /usr/local/bin/gpio mode 4 out
        /usr/local/bin/gpio write 4 1
        echo "$($DATE +"%Y %m %d %H %M %S") $2 0 0 0" >> $LOGPATH/relay.log
        /bin/sleep $2 && /usr/local/bin/gpio write 4 0 >/dev/null &
        ;;
        esac
      ;;
    2)
        case $2 in
        0)
        /usr/local/bin/gpio mode 3 out
        /usr/local/bin/gpio write 3 0
        ;;
        1)
        /usr/local/bin/gpio mode 3 out
        /usr/local/bin/gpio write 3 1
        ;;
        *)
        /usr/local/bin/gpio mode 3 out
        /usr/local/bin/gpio write 3 1
        echo "$($DATE +"%Y %m %d %H %M %S") 0 $2 0 0" >> $LOGPATH/relay.log
        /bin/sleep $2 && /usr/local/bin/gpio write 3 0 >/dev/null &
        ;;
        esac
      ;;
    3)
        case $2 in
        0)
        /usr/local/bin/gpio mode 1 out
        /usr/local/bin/gpio write 1 0
        ;;
        1)
        /usr/local/bin/gpio mode 1 out
        /usr/local/bin/gpio write 1 1
        ;;
        *)
        /usr/local/bin/gpio mode 1 out
        /usr/local/bin/gpio write 1 1
        echo "$($DATE +"%Y %m %d %H %M %S") 0 0 $2 0" >> $LOGPATH/relay.log
        /bin/sleep $2 && /usr/local/bin/gpio write 1 0 >/dev/null &
        ;;
        esac
      ;;
    4)
        case $2 in
        0)
        /usr/local/bin/gpio mode 0 out
        /usr/local/bin/gpio write 0 0
        ;;
        1)
        /usr/local/bin/gpio mode 0 out
        /usr/local/bin/gpio write 0 1
        ;;
        *)
        /usr/local/bin/gpio mode 0 out
        /usr/local/bin/gpio write 0 1
        echo "$($DATE +"%Y %m %d %H %M %S") 0 0 0 $2" >> $LOGPATH/relay.log
        /bin/sleep $2 && /usr/local/bin/gpio write 0 0 >/dev/null &
        ;;
        esac
      ;;
    *)
      echo "invalid parameter: unrecognized parameter"
      echo "$0 $1 $2 $3 $4"
      echo -e "use" $0 "--help for usage\n"
      exit
      ;;
  esac

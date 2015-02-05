#!/bin/bash

DATAPATH="/var/www/mycodo"

usage() {
  echo Usage: $0 "[RELAY] [SECONDS]"
  echo "Turns relay (1, 2, 3, or 4) on for defined number of seconds, then turns it off\n"
}

if [ -n "$3" ]
then
  echo "too many imputs: only two parameters are allowed"
  echo -e "use" $0 "--help for usage\n"
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
        echo "$(date +"%Y %m %d %H %M %S") $2 0 0 0" >> $DATAPATH/PiRelayData
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
        echo "$(date +"%Y %m %d %H %M %S") 0 $2 0 0" >> $DATAPATH/PiRelayData
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
      echo "$(date +"%Y %m %d %H %M %S") 0 0 $2 0" >> $DATAPATH/PiRelayData
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
      echo "$(date +"%Y %m %d %H %M %S") 0 0 0 $2" >> $DATAPATH/PiRelayData
      /bin/sleep $2 && /usr/local/bin/gpio write 0 0 >/dev/null &
      ;;
      esac
      ;;
    *)
      echo "invalid parameter: unrecognized parameter"
      echo "$0 $1 $2"
      echo -e "use" $0 "--help for usage\n"
      exit
      ;;
  esac

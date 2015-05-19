#!/bin/bash
#
#  graph.sh - Generates PNG graphs from sensor and relay log data
#  By Kyle Gabriel
#  2012 - 2015
#

PATHC=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
LOGPATH="/var/tmp"
IMAGEPATH="$(dirname "$PATHC")/images"
Y1MIN=0
Y1MAX=100
Y2MIN=0
Y2MAX=35

graph_colors=("#FF3100" "#0772A1" "#00B74A" "#91180B" "#582557" "#04834C" "#DC32E6" "#957EF9" "#CC8D9C" "#717412" "#0B479B")
relay1name="$(cat "/var/www/mycodo/config/mycodo.cfg" | grep "relay1name" | cut -d' ' -f 3)"
relay2name="$(cat '/var/www/mycodo/config/mycodo.cfg' | grep 'relay2name' | cut -d' ' -f 3)"
relay3name="$(cat '/var/www/mycodo/config/mycodo.cfg' | grep 'relay3name' | cut -d' ' -f 3)"
relay4name="$(cat '/var/www/mycodo/config/mycodo.cfg' | grep 'relay4name' | cut -d' ' -f 3)"
relay5name="$(cat '/var/www/mycodo/config/mycodo.cfg' | grep 'relay5name' | cut -d' ' -f 3)"
relay6name="$(cat '/var/www/mycodo/config/mycodo.cfg' | grep 'relay6name' | cut -d' ' -f 3)"
relay7name="$(cat '/var/www/mycodo/config/mycodo.cfg' | grep 'relay7name' | cut -d' ' -f 3)"
relay8name="$(cat '/var/www/mycodo/config/mycodo.cfg' | grep 'relay8name' | cut -d' ' -f 3)"

usage() {
  echo Usage: $0 "[OPTION]"
  echo "Regular Options:"
  echo "  6h              draw a gnuplot graph for the past 6 hours"
  echo "  day             draw a gnuplot graph for the past day"
  echo "  week            draw a gnuplot graph for the past week"
  echo "  month           draw a gnuplot graph for the past month"
  echo "  year            draw a gnuplot graph for the past year"
  echo "  dayweek         draw a gnuplot graph for the past day and week"
  echo "  all             draw a gnuplot graph for all the boave graphs"
  echo "Special options:"
  echo "  6h-mobile       draw a graph suitable for a mobile phone for the past 6 hours"
  echo "  day-mobile      draw a graph suitable for a mobile phone for the past day"
  echo -e "  dayweek-mobile  draw a graph suitable for a mobile phone for the past day and week\n"
}

graph_single() {
echo "reset
set terminal png size 1000,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-$file-$id.png\"
set xrange [\"`date --date="$time ago" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [$Y1MIN:$Y1MAX]
set y2range [$Y2MIN:$Y2MAX]
set my2tics 10
set ytics 10
set y2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
set title \"$time: `date --date="$time ago" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$sensor_lines$LOGPATH/sensor.log\" u 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, \\
     \"\" using 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, \\
     \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$relay_lines$LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
     \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
     \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
     \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
     \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1" | gnuplot
}

if [ -n "$3" ]
then
  echo "too many imputs: only two parameter is allowed"
  echo -e "use" $0 "--help for usage\n"
  exit
fi

if [ -z "$1" ]
then
  echo "invalid parameter: must enter a parameter"
   echo -e "use" $0 "--help for usage\n"
  exit
else
  id=$2
  case $1 in
    -h|--help)
    usage
    ;;
    legend)
echo "reset
set terminal png size 250,300
set output \"$IMAGEPATH/graph-legend-$id.png\"
unset border
unset tics
unset grid
set yrange [0:400]
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
set key center center box
plot \"$LOGPATH/sensor.log\" index 0 title \"Temperature\" w lp ls 1, \\
     \"\" u 1:8 index 0 title \"Rel. Humidity\" w lp ls 2, \\
     \"\" u 1:9 index 0 title \"Dew Point\" w lp ls 3, \\
     \"$LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4, \\
     \"\" index 0 title \"$relay2name\" w impulses ls 5, \\
     \"\" index 0 title \"$relay3name\" w impulses ls 6, \\
     \"\" index 0 title \"$relay4name\" w impulses ls 7, \\
     \"\" index 0 title \"$relay5name\" w impulses ls 8, \\
     \"\" index 0 title \"$relay6name\" w impulses ls 9, \\
     \"\" index 0 title \"$relay7name\" w impulses ls 10, \\
     \"\" index 0 title \"$relay8name\" w impulses ls 11" | gnuplot
      ;;
    legend-full)
echo "reset
set output \"$IMAGEPATH/graph-legend-full-$id.png\"
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set xrange [\"`date --date="2 hours ago" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\"
set terminal png size 800,500
set yrange [0:100]
set y2range [0:35]
set my2tics 10
set ytics 10
set y2tics 5
set xlabel \"Date and Time\"
set ylabel \"# of seconds relays on & humidity\"
set y2label \"Temperature & dew point (C)\"
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
set key outside
plot \"$LOGPATH/sensor.log\" u 1:7 index 0 title \"Temperature\" w lp ls 1 axes x1y2, \\
     \"\" u 1:8 index 0 title \"Relative Humidity\" w lp ls 2 axes x1y1, \\
     \"\" u 1:9 index 0 title \"Dew Point\" w lp ls 3 axes x1y2, \\
     \"$LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
     \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
     \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
     \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
     \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1" | gnuplot
      ;;
    1h)
      file="1h"
      time="1 hour"
      #sensor_lines="< tail -31 "
      #relay_lines="< tail -50 "
      graph_single
      ;;
    6h)
      file="6h"
      time="6 hours"
      #sensor_lines="< tail -180 "
      #relay_lines="< tail -280 "
      graph_single
      ;;
    day)
      file="day"
      time="1 day"
      graph_single
      ;;
    week)
      file="week"
      time="1 week"
      graph_single
      ;;
    month)
      file="month"
      time="1 month"
      graph_single
      ;;
    year)
      file="year"
      time="1 year"
      graph_single
      ;;
    dayweek)
echo "set terminal png size 1000,1000
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-main-$id.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [$Y1MIN:$Y1MAX]
set y2range [$Y2MIN:$Y2MAX]
set mytics 10
set my2tics 5
set ytics 0,20
set y2tics 0,5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
# set xlabel \"\"
#set ylabel \"%\"
#set y2label \"Degrees C\"
unset key
set multiplot layout 1,3
# Top graph - day
set size 1.0,0.48
set origin 0.0,0.5
plot \"$LOGPATH/sensor.log\" using 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, \\
     \"\" using 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, \\
     \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
     \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
     \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
     \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
     \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1
# Bottom graph - week
set size 1.0,0.48
set origin 0.0,0.0
set format x \"%a\n%m/%d\"
set xrange [\"`date --date="last week" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
plot \"$LOGPATH/sensor.log\" using 1:7 index 0 notitle w lp ls 1 axes x1y2, \\
     \"\" using 1:8 index 0 notitle w lp ls 2 axes x1y1, \\
     \"\" using 1:9 index 0 notitle w lp ls 3 axes x1y2
unset multiplot" | gnuplot

echo "reset
set terminal png size 1000,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-main1-$id.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [$Y1MIN:$Y1MAX]
set y2range [$Y2MIN:$Y2MAX]
set my2tics 10
set ytics 10
set y2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
set title \"Sensor 1: `date --date=yesterday +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"<awk '\$10 == 1' $LOGPATH/sensor.log\" u 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, \\
     \"\" using 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, \\
     \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"<awk '\$15 == 1' $LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
     \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
     \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
     \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
     \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1" | gnuplot
     
echo "reset
set terminal png size 1000,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-main2-$id.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [$Y1MIN:$Y1MAX]
set y2range [$Y2MIN:$Y2MAX]
set my2tics 10
set ytics 10
set y2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
set title \"Sensor 2: `date --date=yesterday +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"<awk '\$10 == 2' $LOGPATH/sensor.log\" u 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, \\
     \"\" using 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, \\
     \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"<awk '\$15 == 2' $LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
     \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
     \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
     \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
     \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1" | gnuplot

      ;;
    all)
      $0 1h $2
      $0 6h $2
      $0 day $2
      $0 week $2
      $0 month $2
      $0 year $2
      ;;
    6h-mobile)
echo "set terminal png size 900,850
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-6h-mobile.png\"
set xrange [\"`date --date="6 hours ago" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [$Y1MIN:$Y1MAX]
set y2range [$Y2MIN:$Y2MAX]
set mytics 5
set ytics 20
set y2tics 5
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
set title \"Past 6 Hours: `date --date="6 hours ago" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$LOGPATH/sensor.log\" u 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
     \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
     \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
     \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
     \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1" | gnuplot
      ;;
    day-mobile)
echo "set terminal png size 900,850
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-day-mobile.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:100]
set y2range [10:30]
set mytics 5
set ytics 20
set y2tics 5
set my2tics 5
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
set title \"Past Day: `date --date=yesterday +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$LOGPATH/sensor.log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" using 1:8 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y1, \\
     \"$LOGPATH/relay.log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
     \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
     \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
     \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
     \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1" | gnuplot
      ;;
    main-mobile)
echo "set terminal png size 900,850
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-main-mobile.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [$Y1MIN:$Y1MAX]
set y2range [$Y2MIN:$Y2MAX]
set mytics 2
set ytics 20,20
set y2tics 10,10
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '${graph_colors[0]}' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '${graph_colors[1]}' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '${graph_colors[2]}' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '${graph_colors[3]}' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '${graph_colors[4]}' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '${graph_colors[5]}' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '${graph_colors[6]}' pt 0 ps 1 lt 1 lw 1
set style line 8 lc rgb '${graph_colors[7]}' pt 0 ps 1 lt 1 lw 1
set style line 9 lc rgb '${graph_colors[8]}' pt 0 ps 1 lt 1 lw 1
set style line 10 lc rgb '${graph_colors[9]}' pt 0 ps 1 lt 1 lw 1
set style line 11 lc rgb '${graph_colors[10]}' pt 0 ps 1 lt 1 lw 1
#set xlabel \"Date and Time\"
#set ylabel \"% Humidity\"
unset key
set multiplot layout 1,3
# Top graph - day
set size 1.0,0.48
set origin 0.0,0.5
plot \"$LOGPATH/sensor.log\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$LOGPATH/relay.log\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1
# Bottom graph - week
set size 1.0,0.48
set origin 0.0,0.0
set format x \"%a\n%m/%d\"
set xrange [\"`date --date="last week" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
plot \"$LOGPATH/sensor.log\" using 1:8 index 0 notitle w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 notitle w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 notitle w lp ls 3 axes x1y2, \\
     \"$LOGPATH/relay.log\" u 1:7 index 0 notitle w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 notitle w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 notitle w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 notitle w impulses ls 7 axes x1y1
unset multiplot" | gnuplot
      ;;
    *)
      echo "invalid parameter: unrecognized parameter"
      echo -e "use" $0 "--help for usage\n"
      exit
      ;;
esac
fi

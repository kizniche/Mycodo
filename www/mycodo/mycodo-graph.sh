#!/bin/bash

IMAGEPATH="/var/www/graph"
DATAPATH="/var/www/mycodo"

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

if [ -n "$2" ]
then
  echo "too many imputs: only one parameter is allowed"
  echo -e "use" $0 "--help for usage\n"
  exit
fi

if [ -z "$1" ]
then
  echo "invalid parameter: must enter a parameter"
   echo -e "use" $0 "--help for usage\n"
  exit
else
  case $1 in
    -h|--help)
    usage
    ;;
    legend)
echo "reset
set terminal png size 150,200
set output \"$IMAGEPATH/graph-legend.png\"
unset border
unset tics
unset grid
set yrange [0:400]
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 2
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 2
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 2
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 2
set key center center box
plot \"$DATAPATH/PiSensorData\" index 0 title \" RH\" w lp ls 1, \\
     \"\" index 0 title \"T\" w lp ls 2, \\
     \"\" index 0 title \"DP\" w lp ls 3, \\
     \"$DATAPATH/PiRelayData\" index 0 title \"HEPA\" w impulses ls 4, \\
     \"\" index 0 title \"HUM\" w impulses ls 5, \\
     \"\" index 0 title \"FAN\" w impulses ls 6, \\
     \"\" index 0 title \"HEAT\" w impulses ls 7" | gnuplot
      ;;
    legend-full)
echo "reset
set output \"$IMAGEPATH/graph-legend-full.png\"
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set xrange [\"`date --date="2 hours ago" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\"
set terminal png size 600,400
set yrange [0:100]
set y2range [10:30]
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
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 2
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 2
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 2
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 2
set key top left box
plot \"$DATAPATH/PiSensorData\" u 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" u 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" u 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" u 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" u 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" u 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    1h)
echo "reset
set terminal png size 850,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-1h.png\"
set xrange [\"`date --date="1 hour ago" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:100]
set y2range [10:30]
set my2tics 10
set ytics 10
set y2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past Hour: `date --date="1 hour ago" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"< tail -31 $DATAPATH/PiSensorData\" u 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"< tail -50 $DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    6h)
echo "reset
set terminal png size 850,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-6h.png\"
set xrange [\"`date --date="6 hours ago" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:100]
set y2range [10:30]
set my2tics 10
set ytics 10
set y2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past 6 Hours: `date --date="6 hours ago" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"< tail -180 $DATAPATH/PiSensorData\" u 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"< tail -280 $DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    day)
echo "set terminal png size 850,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-day.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:100]
set y2range [10:30]
set my2tics 10
set ytics 10
set y2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past Day: `date --date=yesterday +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$DATAPATH/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    week)
echo "set terminal png size 850,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-week.png\"
set xrange [\"`date --date="last week" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%a\n%m/%d\"
set yrange [0:200]
set y2range [25:100]
set mytics 5
set ytics 20
set y2tics 5
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past Week: `date --date="last week" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$DATAPATH/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
     \"\" using 1:10 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:11 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    month)
echo "set terminal png size 850,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-month.png\"
set xrange [\"`date --date="last month" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%a\n%m/%d\"
set yrange [0:200]
set y2range [25:100]
set mytics 5
set ytics 20
set y2tics 5
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 1
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 1
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 1
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past Month: `date --date="last month" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$DATAPATH/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
     \"\" using 1:10 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:11 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    year)
echo "set terminal png size 850,490
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-year.png\"
set xrange [\"`date --date="last year" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%b\n%m/%d/%y\"
set yrange [0:200]
set y2range [25:100]
set mytics 5
set ytics 20
set y2tics 5
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 1
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 1
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 1
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past Year: `date --date="last year" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$DATAPATH/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
     \"\" using 1:10 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:11 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    dayweek)
echo "set terminal png size 830,1000
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-main.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:100]
set y2range [10:30]
set mytics 10
set my2tics 5
set ytics 0,20
set y2tics 0,5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics ytics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
# set xlabel \"\"
#set ylabel \"%\"
#set y2label \"Degrees C\"
unset key
set multiplot layout 1,3
# Top graph - day
set size 1.0,0.48
set origin 0.0,0.5
plot \"< tail -720 $DATAPATH/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"< tail -1090 $DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1
# Bottom graph - week
set size 1.0,0.48
set origin 0.0,0.0
set format x \"%a\n%m/%d\"
set xrange [\"`date --date="last week" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
plot \"< tail -4970 $DATAPATH/PiSensorData\" using 1:8 index 0 notitle w lp ls 1 axes x1y1, \\
     \"\" using 1:9 index 0 notitle w lp ls 2 axes x1y2, \\
     \"\" using 1:12 index 0 notitle w lp ls 3 axes x1y2, \\
     \"< tail -5050 $DATAPATH/PiRelayData\" u 1:7 index 0 notitle w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 notitle w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 notitle w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 notitle w impulses ls 7 axes x1y1
unset multiplot" | gnuplot
      ;;
    all)
      $0 1h
      $0 6h
      $0 day
      $0 week
      $0 month
      $0 year
      ;;
    6h-mobile)
echo "set terminal png size 800,850
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-6h-mobile.png\"
set xrange [\"`date --date="6 hours ago" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:200]
set y2range [25:100]
set mytics 5
set ytics 20
set y2tics 5
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past 6 Hours: `date --date="6 hours ago" +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$DATAPATH/PiSensorData\" u 1:8 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
     \"\" using 1:10 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:11 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    day-mobile)
echo "set terminal png size 800,850
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-day-mobile.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:200]
set y2range [25:100]
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
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
set title \"Past Day: `date --date=yesterday +"%m/%d/%Y %H:%M:%S"` - `date +"%m/%d/%Y %H:%M:%S"`\"
unset key
plot \"$DATAPATH/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
     \"\" using 1:10 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:11 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot
      ;;
    dayweek-mobile)
echo "set terminal png size 800,850
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"$IMAGEPATH/graph-main-mobile.png\"
set xrange [\"`date --date=yesterday +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
set format x \"%H:%M\n%m/%d\"
set yrange [0:200]
set y2range [25:100]
set mytics 2
set ytics 20,20
set y2tics 10,10
#set my2tics 5
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set tics nomirror
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid xtics y2tics back ls 12
set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
#set xlabel \"Date and Time\"
#set ylabel \"% Humidity\"
unset key
set multiplot layout 1,3
# Top graph - day
set size 1.0,0.48
set origin 0.0,0.5
plot \"$DATAPATH/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
     \"\" using 1:10 index 0 title \"T\" w lp ls 2 axes x1y2, \\
     \"\" using 1:11 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1
# Bottom graph - week
set size 1.0,0.48
set origin 0.0,0.0
set format x \"%a\n%m/%d\"
set xrange [\"`date --date="last week" +"%Y %m %d %H %M %S"`\":\"`date +"%Y %m %d %H %M %S"`\"]
plot \"$DATAPATH/PiSensorData\" using 1:8 index 0 notitle w lp ls 1 axes x1y2, \\
     \"\" using 1:10 index 0 notitle w lp ls 2 axes x1y2, \\
     \"\" using 1:11 index 0 notitle w lp ls 3 axes x1y2, \\
     \"$DATAPATH/PiRelayData\" u 1:7 index 0 notitle w impulses ls 4 axes x1y1, \\
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

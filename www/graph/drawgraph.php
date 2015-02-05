<?php include "auth.php";?>
<html>
<head>
<title>Custom Graph</title>
<script type="text/javascript">
function open_legend()
{
window.open("graph-legend.png","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=190, height=210");
}
function open_legend_full()
{
window.open("graph-legend-full.png","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=600, height=385");
}
</script>
</head>
<body>
<center>
<?php
/****************************************/
/*DateSelector*Author: Leon Atkinson    */
/****************************************/

if($_POST['SubmitDates']) {
$minb = $_POST['startMinute'];
$hourb = $_POST['startHour'];
$dayb = $_POST['startDay'];
$monb = $_POST['startMonth'];
$yearb = $_POST['startYear'];
$mine = $_POST['endMinute'];
$houre = $_POST['endHour'];
$daye = $_POST['endDay'];
$mone = $_POST['endMonth'];
$yeare = $_POST['endYear'];
echo `echo "set terminal png size 1000,685
set xdata time
set timefmt \"%Y %m %d %H %M %S\"
set output \"/var/www/graph/graph-cus.png\"
set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]
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
#set xlabel \"Date and Time\"
#set ylabel \"% Humidity\"
set title \"$monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
unset key
plot \"/var/www/mycodo/PiSensorData\" using 1:8 index 0 title \" RH\" w lp ls 1 axes x1y1, \\\\
     \"\" using 1:9 index 0 title \"T\" w lp ls 2 axes x1y2, \\\\
     \"\" using 1:12 index 0 title \"DP\" w lp ls 3 axes x1y2, \\\\
     \"/var/www/mycodo/PiRelayData\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\\\
     \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\\\
     \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\\\
     \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot`;
displayform2();
echo "<img src=graph-cus.png>";
echo "<p><a href='javascript:open_legend()'>Brief Graph Legend</a> - <a href='javascript:open_legend_full()'>Full Graph Legend</a>";
}
else displayform2();

function displayform2() {
echo "<FORM action=\"\" method=\"POST\">";
echo "START:";
DateSelector("start");
echo "&nbsp;&nbsp;END:";
DateSelector( "end");
echo "&nbsp;&nbsp;<input type=\"submit\" name=\"SubmitDates\" value=\"Submit\"></FORM>";
}

function DateSelector($inName, $useDate=0) {
/* create array so we can name months */
$monthName = array(1=> "January", "February", "March",
"April", "May", "June", "July", "August",
"September", "October", "November", "December");

/* if date invalid or not supplied, use current time */
if($useDate == 0) $useDate = Time();

/* month */
echo "<SELECT NAME=" . $inName . "Month>\n";
for($currentMonth = 1; $currentMonth <= 12; $currentMonth++) {
  echo "<OPTION VALUE=\"";
  echo intval($currentMonth);
  echo "\"";
  if(intval(date( "m", $useDate))==$currentMonth) {
  echo " SELECTED";
}
echo ">" . $monthName[$currentMonth] . "\n";
}
echo "</SELECT>/";

/* day */
echo "<SELECT NAME=" . $inName . "Day>\n";
for($currentDay=1; $currentDay <= 31; $currentDay++) {
  echo "<OPTION VALUE=\"$currentDay\"";
  if(intval(date( "d", $useDate))==$currentDay) echo " SELECTED";
  echo ">$currentDay\n";
}
echo "</SELECT>/";

/* year */
echo "<SELECT NAME=" . $inName . "Year>\n";
$startYear = date( "Y", $useDate);
for($currentYear = $startYear - 5; $currentYear <= $startYear+5;$currentYear++) {
  echo "<OPTION VALUE=\"$currentYear\"";
  if(date( "Y", $useDate)==$currentYear) {
    echo " SELECTED";
  }
  echo ">$currentYear\n";
}
echo "</SELECT>&nbsp;";

/* hour */
echo "<SELECT NAME=" . $inName . "Hour>\n";
for($currentHour=0; $currentHour <= 23; $currentHour++) {

  if($currentHour < 10) echo "<OPTION VALUE=\"0$currentHour\"";
  else { echo "<OPTION VALUE=\"$currentHour\""; }

  if(intval(date( "H", $useDate))==$currentHour) echo " SELECTED";

  if($currentHour < 10) echo ">0$currentHour\n";
  else { echo ">$currentHour\n";}
}
echo "</SELECT>h ";

/* minute */
echo "<SELECT NAME=" . $inName . "Minute>\n";
for($currentMinute=0; $currentMinute <= 59; $currentMinute++) {

  if($currentMinute < 10) echo "<OPTION VALUE=\"0$currentMinute\"";
  else { echo "<OPTION VALUE=\"$currentMinute\"";}

  if(intval(date( "i", $useDate))==$currentMinute) echo " SELECTED";

  if($currentMinute < 10) echo ">0$currentMinute\n";
  else { echo ">$currentMinute\n";}
}
echo "</SELECT>m";
}
?>
</center>
</body>
</html>

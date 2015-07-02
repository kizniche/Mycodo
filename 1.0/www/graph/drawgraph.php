<?php include "auth.php";?>
<HTML>
<BODY>
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
echo `grep -Ih OO /home/kiz/arduino/output/* > /var/www/graph/datas`;
echo `echo "set terminal png size 1000,685
set xdata time
set timefmt \"%Y-%m-%d-%H:%M:%S\"
set output \"/var/www/graph/graph-cus.png\"
set xrange [\"$yearb-$monb-$dayb-$hourb:$minb:00\":\"$yeare-$mone-$daye-$houre:$mine:00\"]
set format x \"%H:%M %d\"
set yrange [50:100]
set mytics 5
set ytics 5
set y2tics 5
set grid xtics mytics ytics y2tics
#set xlabel \"Date and Time\"
#set ylabel \"% Humidity\"
set title \"$monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
set key left box
plot \"/var/www/graph/datas\" using 1:2 index 0 title \" RH\" with lines, \\\\
     \"\" using 1:6 index 0 title \"T\" with lines, \\\\
     \"\" using 1:10 index 0 title \"DP\" with lines, \\\\
     \"\" using 1:11 index 0 title \"HI\" with lines" | gnuplot`;
echo `rm /var/www/graph/datas`;
displayform2();
echo "<img src=graph-cus.png>";
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
</BODY>
</HTML>

<?php
/*
*
*  menu.php - The navigation menu of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$sensor_log = getcwd() . "/log/sensor.log";


include "auth.php";

echo '<html><head><META HTTP-EQUIV="refresh" CONTENT="65"></head><body>';

if(isset($_POST['Lines'])) {
	$Lines = $_POST['Lines'];
	displayModeform();
	echo `tail -n $Lines $sensor_log | sed 's/$/<br>/'`;
}
else {
	displayModeform();
	echo `tail -n 20 $sensor_log | sed 's/$/<br>/'`;
}

function displayModeform() {
	echo "<FORM action=\"\" method=\"POST\">";
	echo "Lines: <input type=\"text\" maxlength=8 size=8 name=\"Lines\" /> ";
	echo "<input type=\"submit\" name=\"SubmitMode\" value=\"Set\"></FORM><p>Year Mo Day Hour Min Sec Timestamp RH Tc Tf DPf DPc<p>";
}

echo '</body></html>';
?>
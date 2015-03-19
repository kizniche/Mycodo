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

if (version_compare(PHP_VERSION, '5.3.7', '<')) {
    exit("Sorry, Simple PHP Login does not run on a PHP version smaller than 5.3.7 !");
} else if (version_compare(PHP_VERSION, '5.5.0', '<')) {
    require_once("libraries/password_compatibility_library.php");
}
require_once("config/db.php");
require_once("classes/Login.php");
$login = new Login();

if ($login->isUserLoggedIn() == true) {

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

} else {
        include("views/not_logged_in.php");
}
?>

<?php
/*
*
*  camera-still.php - Captures RPi still image and displays it
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$cwd = getcwd();
$still_exec = $cwd . "/cgi-bin/camera-still.sh";

if (version_compare(PHP_VERSION, '5.3.7', '<')) {
    exit("Sorry, Simple PHP Login does not run on a PHP version smaller than 5.3.7 !");
} else if (version_compare(PHP_VERSION, '5.5.0', '<')) {
    require_once("libraries/password_compatibility_library.php");
}
require_once('config/config.php');
require_once('translations/en.php');
require_once('libraries/PHPMailer.php');
require_once("classes/Login.php");
$login = new Login();

if ($login->isUserLoggedIn() == true) {

echo '<html><head><title>Camera Stills</title>';
echo '</head><body><center>';
echo '<form action="" method="POST">';
echo '<button name="Capture" type="submit" value="">Capture</button>';
echo '</form>';
if (isset($_POST['Capture'])) {
	$capture_output = shell_exec("$still_exec 2>&1; echo $?");
	if ($capture_output != 0) echo 'Abnormal output (possibly error): ' . $capture_output . '<br>';
	echo '<p><img src=image.php?span=cam-still></p>';
}
echo'</center></body></html>';

} else {
        include("views/not_logged_in.php");
}
?>

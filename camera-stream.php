<?php
/*
*
*  camera-stream.php - Starts/stops RPi camera stream and allows viewing
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$cwd = getcwd();
$stream_exec = $cwd . "/cgi-bin/camera-stream.sh";
$lock_raspistill = "/var/lock/mycodo_raspistill";
$lock_mjpg_streamer = "/var/lock/mycodo_mjpg_streamer";

if (version_compare(PHP_VERSION, '5.3.7', '<')) {
    exit("Sorry, Simple PHP Login does not run on a PHP version smaller than 5.3.7 !");
} else if (version_compare(PHP_VERSION, '5.5.0', '<')) {
    require_once("libraries/password_compatibility_library.php");
}
require_once("config/db.php");
require_once("classes/Login.php");
$login = new Login();

if ($login->isUserLoggedIn() == true) {

echo '<html><head><title>Camera Stream</title>';
echo '</head><body><center>';
echo '<form action="" method="POST">';
echo '<button name="start-stream" type="submit" value="">Start Stream</button> ';
echo '<button name="stop-stream" type="submit" value="">Stop Stream</button>';
echo '</form>';

if (isset($_POST['start-stream'])) {
        if (file_exists($lock_raspistill) || file_exists($lock_mjpg_streamer)) {
                echo 'Lock files already present. Press \'Stop Stream\' to kill processes and remove lock files.<br>';
        } else {
                shell_exec("$stream_exec start > /dev/null &");
                sleep(1);
        }
}
if (isset($_POST['stop-stream'])) shell_exec("$stream_exec stop");

if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) {

	echo 'Stream ON<p><img src="http://' . $_SERVER[HTTP_HOST] . ':8080/?action=stream" /></p>';
} else echo 'Stream OFF';

echo '</center><body></html>';

} else {
        include("views/not_logged_in.php");
}
?>

<?php
/*
*
*  camera-stil.php - Captures image and displays it
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$cwd = getcwd();
$still_exec = $cwd . "/cgi-bin/camera-still.sh";

include "auth.php";

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

?>

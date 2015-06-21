<?php
/*
*  camera-hdr.php - Captures RPi still images at different ISOs, then
*                   combines them into an HDR image
*
*  Copyright (C) 2015  Kyle T. Gabriel
*
*  This file is part of Mycodo
*
*  Mycodo is free software: you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation, either version 3 of the License, or
*  (at your option) any later version.
*
*  Mycodo is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
*
*  Contact at kylegabriel.com
*/

####### Configure #######
$install_path = "/var/www/mycodo";


$hdr_exec = $install_path . "/cgi-bin/camera-hdr.py";

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
?>

<html>
    <head>
	<title>
	    Camera Stills
	</title>
    </head>
    <body>
	<center>
	    <form action="" method="POST">
		<button name="Capture" type="submit" value="">Capture</button>
	    </form>
	    <?php
		if (isset($_POST['Capture'])) {
		    $capture_output = shell_exec("$hdr_exec 2>&1; echo $?");
		    if ($capture_output != 0) echo 'Abnormal output (possibly error): ' . $capture_output . '<br>';
		    echo '<p><img src=image.php?span=cam-hdr></p>';
		}
	    ?>
	</center>
    </body>
</html>
<?php
} else {
    include("views/not_logged_in.php");
}
?>

<?php
/*
*
*  history.php - Read log
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$cwd = getcwd();
$sensor_log = $cwd . "/log/sensor.log";
$relay_log = $cwd . "/log/relay.log";
$auth_log = $cwd . "/log/auth.log";
$daemon_log = "/var/log/mycodo.log";

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
	    Log Viewer
	</title>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    </head>
    <body>
	<FORM action="" method="POST">
	    Lines: <input type="text" maxlength=8 size=8 name="Lines" /> 
	    <input type="submit" name="Sensor" value="Sensor"> 
	    <input type="submit" name="Relay" value="Relay"> 
	    <input type="submit" name="Auth" value="Auth">
        <input type="submit" name="Daemon" value="Daemon">
	</FORM>
    <div style="font-family: monospace;">
    <pre>
	<?php
	    if(isset($_POST['Sensor'])) {
            echo '<p>Year Mo Day Hour Min Sec Timestamp RH Tc Tf DPf DPc<p>';
            if ($_POST['Lines'] != '') {
                $Lines = $_POST['Lines'];
                echo `tail -n $Lines $sensor_log`;
            } else {
                echo `tail -n 20 $sensor_log`;
            }
	    }

	    if(isset($_POST['Relay'])) {
            echo '<p>Year Mo Day Hour Min Sec R1Sec R2Sec R3Sec R4Sec</p>';
            if ($_POST['Lines'] != '') {
                $Lines = $_POST['Lines'];
                echo `tail -n $Lines $relay_log`;
            } else {
                echo `tail -n 20 $relay_log`;
            }
	    }

	    if(isset($_POST['Auth'])) {
            echo '<p>Time, Type of auth, user, IP, Hostname, Referral, Browser</p>';
            if ($_POST['Lines'] != '') {
                $Lines = $_POST['Lines'];
                echo `tail -n $Lines $auth_log`;
            } else {
                echo `tail -n 20 $auth_log`;
            }
	    }
	    if(isset($_POST['Daemon'])) {
            if ($_POST['Lines'] != '') {
                $Lines = $_POST['Lines'];
                echo `tail -n $Lines $daemon_log`;
            } else {
                echo `tail -n 20 $daemon_log`;
            }
	    }
	?>
    </pre>
    </div>
    </body>
</html>
<?php
} else {
    include("views/not_logged_in.php");
}

?>

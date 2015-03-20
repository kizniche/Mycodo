<?php
/*
*
*  Mode Change Script (popup window)
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$gpio_path = "/usr/local/bin/gpio";

$cwd = getcwd();
$sensordata_file = $cwd . "/log/sensor.log";
$config_file = $cwd . "/config/mycodo.conf";
$relay_config = $cwd . "/config/relay.conf";

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

if ($login->isUserLoggedIn() == true && $_SESSION['user_name'] != guest) {

    if (isset($_POST['Mode'])) $ModeSet = $_POST['Mode'];

    if (isset($_POST['OR'])) {
	$OR = $_POST['OR'];
	switch ($OR) {
	    case "ON":
	    webor(1);
	    break;
	    case "OFF":
	    webor(0);
	    break;
	}
    }
    if (isset($_POST['R1'])) {
	$R1 = $_POST['R1'];
	switch ($R1) {
	    case "ON":
	    echo `gpio mode 4 out`;
	    echo `gpio write 4 1`;
	    break;
	    case "OFF":
	    echo `gpio mode 4 out`;
	    echo `gpio write 4 0`;
	    break;
	}
    }
    if (isset($_POST['R2'])) {
	$R2 = $_POST['R2'];
	switch ($R2) {
	    case "ON":
	    echo `gpio mode 3 out`;
	    echo `gpio write 3 1`;
	    break;
	    case "OFF":
	    echo `gpio mode 3 out`;
	    echo `gpio write 3 0`;
	    break;
	}
    }
    if (isset($_POST['R3'])) {
	$R3 = $_POST['R3'];
	switch ($R3) {
	    case "ON":
	    echo `gpio mode 1 out`;
	    echo `gpio write 1 1`;
	    break;
	    case "OFF":
	    echo `gpio mode 1 out`;
	    echo `gpio write 1 0`;
	    break;
	}
    }
    if (isset($_POST['R4'])) {
	$R4 = $_POST['R4'];
	switch ($R4) {
	    case "ON":
	    echo `gpio mode 0 out`;
	    echo `gpio write 0 1`;
	    break;
	    case "OFF":
	    echo `gpio mode 0 out`;
	    echo `gpio write 0 0`;
	    break;
	}
    }
    if ($_POST['SubmitMode']) {
	$offTemp    = $_POST['offTemp'];
	$onTemp     = $_POST['onTemp'];
	$hiTemp     = $_POST['hiTemp'];
	$offHum     = $_POST['offHum'];
	$onHum      = $_POST['onHum'];
	$command    = $main_path . "mycodo r";
	$editconfig = shell_exec($command);
	$cpiece     = explode(" ", $editconfig);
	$editconfig = $main_path . "mycodo w " . $offTemp . " " . $onTemp . " " . $offHum . " " . $onHum . " " . $cpiece[4] . " " . $cpiece[5] . " " . $cpiece[6] . "\n";
	exec($editconfig);
    }
    if ($_POST['SubmitMode2']) {
	$webov      = $_POST['webov'];
	$tState     = $_POST['tState'];
	$hState     = $_POST['hState'];
	$command    = $main_path . "mycodo r";
	$editconfig = shell_exec($command);
	$cpiece     = explode(" ", $editconfig);
	$editconfig = $main_path . "mycodo w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $webov . " " . $tState . " " . $hState . "\n";
	exec($editconfig);
    }
    if ($_POST['1secON']) {
	$sR1 = $_POST['sR1'];
	exec(sprintf("%s/mycodo-relay.sh 1 %s > /dev/null 2>&1", $main_path, $sR1));
    }
    if ($_POST['2secON']) {
	$sR2 = $_POST['sR2'];
	exec(sprintf("%s/mycodo-relay.sh 2 %s > /dev/null 2>&1", $main_path, $sR2));
    }
    if ($_POST['3secON']) {
	$sR3 = $_POST['sR3'];
	exec(sprintf("%s/mycodo-relay.sh 3 %s > /dev/null 2>&1", $main_path, $sR3));
    }
    if ($_POST['4secON']) {
	$sR4 = $_POST['sR4'];
	exec(sprintf("%s/mycodo-relay.sh 4 %s > /dev/null 2>&1", $main_path, $sR4));
    }

?>

<html>
    <body>
	<head>
	    <title>
		Relay Control and Configuration
	    </title>

	    <?php 
		if (isset($_GET['r'])) {
		    if ($_GET['r'] == 1) echo '<META HTTP-EQUIV="refresh" CONTENT="90">';
		}
	    ?>

	</head>
	<body>
	    <div style="text-align: center;">
		<div style="display: inline-block;">
		    <div style="float: left;" align=right>
			<div>Current time: <?php echo `date +'%Y %m %d %H %M %S'`; ?></div>
			<div>Last read: <?php echo `tail -n 1 $sensordata_file | cut -d' ' -f1,2,3,4,5,6`; ?></div>
		    </div>
		    <div style="float: left; padding-left: 10px;">
			<a href="changemode.php">Refresh</a>
		    </div>
		</div>
		<div style="clear: both;"></div>
		<div style="padding: 10px 0 10px 0;">
		    RH: <b><?php echo `tail -n 1 $sensordata_file | cut -d' ' -f8`; ?> %</b> | T: <b> <?php echo `tail -n 1 $sensordata_file | cut -d' ' -f9` ?> &deg;C / <?php echo `tail -n 1 $sensordata_file | cut -d' ' -f10`; ?> &deg;F</b> | <?php $dp_c = `tail -n 1 $sensordata_file | cut -d' ' -f11`; $dp_c = ($dp_c - 32) * 5 / 9; echo "DP: <b>", round($dp_c, 1); echo "&deg;C / ", `tail -n 1 $sensordata_file | cut -d' ' -f11`, "&deg;F</b>"; ?>
		</div>
		<FORM action="" method="POST">
		    <div style="padding: 5px 0 10px 0;">
			Web Override: <b><?php $webor_read = $main_path . "mycodo r | cut -d' ' -f5"; if (shell_exec($webor_read) == 1) echo "ON"; else echo "OFF"; ?></b>
			[<input type="submit" name="OR" value="ON"> <input type="submit" name="OR" value="OFF">]
		    </div>
		    <?php
			for ($i = 1; $i <= 4; $i++) {
			    $relay_name = $i * 3;
			    $relay_name = `cat $relay_config |  tr '\n' ' ' | tr -d ';' | cut -d' ' -f$relay_name`;
			    $relay_name = substr($relay_name, 0, -1);
			    $relay_pin = ($i + 8) * 3;
			    $relay_pin = `cat $relay_config |  tr '\n' ' ' | tr -d ';' | cut -d' ' -f$relay_pin`;
			    $relay_pin = substr($relay_pin, 0, -1);
			?>
			<div style="display: inline-block; text-align: right; padding: 4px;">
			    Relay <?php echo $i . ' (' . $relay_name; ?>): <b><?php $read = $gpio_path . " read " . $relay_pin; if (shell_exec($read) == 1) echo "ON"; else echo "OFF"; ?></b>
			    [<input type="submit" name="R<?php echo $i; ?>" value="ON"> <input type="submit" name="R<?php echo $i; ?>" value="OFF">] [<input type="text" maxlength=3 size=3 name="sR<?php echo $i; ?>" />sec 
			    <input type="submit" name="1secON" value="ON">]
			</div>
			<?php 
			} 
		    ?>

		    <table style="margin: 0 auto; padding-top: 10px;">
			<tr>
			    <td>
			    </td>
			    <td>
				MnT
			    </td>
			    <td>
				MxT
			    </td>
			    <td>
				MnH
			    </td>
			    <td>
				MxH
			    </td>
			</tr>
			<tr>
			    <td>
				<input type="submit" name="SubmitMode" value="Set">
			    </td>
			    <td>
				<input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f3`; ?>" maxlength=2 size=1 name="offTemp" />
			    </td>
			    <td>
				<input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f6`; ?>" maxlength=2 size=1 name="onTemp" />
			    </td>
			    <td>
				<input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f9`; ?>" maxlength=2 size=1 name="offHum" />
			    </td>
			    <td>
				<input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f12`; ?>" maxlength=2 size=1 name="onHum" />
			    </td>
			</tr>
			<tr>
			    <td>
			    </td>
			    <td>
				wOV
			    </td>
			    <td>
				tSta
			    </td>
			    <td>
				hSta
			    </td>
			</tr>
			<tr>
			    <td>
				<input type="submit" name="SubmitMode2" value="Set">
			    </td>
			    <td>
				<input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f15`; ?>" maxlength=2 size=1 name="webov" />
			    </td>
			    <td>
				<input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f18`; ?>" maxlength=2 size=1 name="tState" />
			    </td>
			    <td>
				<input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f21`; ?>" maxlength=2 size=1 name="hState" />
			    </td>
			</tr>
		    </table>
		</div>
	    </FORM>
	</body>
    </html>

    <?php } else {
	    echo 'Configuration editing disabled for guest.';
	}

	function webor($state)
	{
	    global $main_path;

	    if ($state) {
		$command     = $main_path . "mycodo r";
		$readconfig  = shell_exec($command);
		$cpiece      = explode(" ", $editconfig);
		$writeconfig = $main_path . "mycodo w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " 1 " . $cpiece[5] . " " . $cpiece[6] . "\n";
		shell_exec($exec);
	    } else {
		$command    = $main_path . "mycodo r";
		$readconfig = shell_exec($command);
		$cpiece     = explode(" ", $editconfig);
		$editconfig = $main_path . "mycodo w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " 0 " . $cpiece[5] . " " . $cpiece[6] . "\n";
		shell_exec($editconfig);
	    }
	}
    ?>

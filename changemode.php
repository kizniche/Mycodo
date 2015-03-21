<?php
/*
*
*  changemode.php - Reads/writes configuration files
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$gpio_path = "/usr/local/bin/gpio";

$cwd = getcwd();
$mycodo_exec = $cwd . "/cgi-bin/mycodo";
$relay_exec = $cwd . "/cgi-bin/relay.sh";
$sensordata_file = $cwd . "/log/sensor.log";
$config_file = $cwd . "/config/mycodo.conf";
$relay_config = $cwd . "/config/relay_config.php";

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
	if ($_POST['R1']) change_relay(0, 1);
	else change_relay(0, 0);
    }
    if (isset($_POST['R2'])) {
	if ($_POST['R2']) change_relay(1, 1);
	else change_relay(1, 0);
    }
    if (isset($_POST['R3'])) {
	if ($_POST['R3']) change_relay(2, 1);
	else change_relay(2, 0);
    }
    if (isset($_POST['R4'])) {
	if ($_POST['R4']) change_relay(3, 1);
	else change_relay(3, 0);
    }
    if (isset($_POST['R5'])) {
	if ($_POST['R5']) change_relay(4, 1);
	else change_relay(4, 0);
    }
    if (isset($_POST['R6'])) {
	if ($_POST['R6']) change_relay(5, 1);
	else change_relay(5, 0);
    }
    if (isset($_POST['R7'])) {
	if ($_POST['R7']) change_relay(6, 1);
	else change_relay(6, 0);
    }
    if (isset($_POST['R8'])) {
	if ($_POST['R8']) change_relay(7, 1);
	else change_relay(7, 0);
    }
    if ($_POST['SubmitMode']) {
	$offTemp    = $_POST['offTemp'];
	$onTemp     = $_POST['onTemp'];
	$hiTemp     = $_POST['hiTemp'];
	$offHum     = $_POST['offHum'];
	$onHum      = $_POST['onHum'];
	$command    = $mycodo_exec . " r";
	$editconfig = shell_exec($command);
	$cpiece     = explode(" ", $editconfig);
	$editconfig = $mycodo_exec . " w " . $offTemp . " " . $onTemp . " " . $offHum . " " . $onHum . " " . $cpiece[4] . " " . $cpiece[5] . " " . $cpiece[6] . "\n";
	shell_exec($editconfig);
    }
    if ($_POST['SubmitMode2']) {
	$webov      = $_POST['webov'];
	$tState     = $_POST['tState'];
	$hState     = $_POST['hState'];
	$command    = $mycodo_exec . " r";
	$editconfig = shell_exec($command);
	$cpiece     = explode(" ", $editconfig);
	$editconfig = $mycodo_exec . " w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $webov . " " . $tState . " " . $hState . "\n";
	shell_exec($editconfig);
    }

    relay_on_seconds();
?>

<html>
    <head>
	<title>
	    Relay Control and Configuration
	</title>
	<link rel="stylesheet"  href="style.css" type="text/css" media="all" />
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
		    <div>Current time: <?php echo `date +'%Y-%m-%d %H:%M:%S'`; ?></div>
		    <div>
			Last read: <?php 
			    $time_last = `tail -n 1 $sensordata_file | cut -d' ' -f1,2,3,4,5,6`;
			    $time_last[4] = '-';
			    $time_last[7] = '-';
			    $time_last[13] = ':';
			    $time_last[16] = ':';
			    echo $time_last;
			?>
		    </div>
		</div>
		<div style="float: left; padding-left: 10px;">
		    <a href="changemode.php">Refresh</a>
		</div>
	    </div>
	    <div style="clear: both;"></div>
	    <div style="padding: 10px 0 10px 0;">
		<?php
		    $t_c = `tail -n 1 $sensordata_file | cut -d' ' -f9`;
		    $t_f = `tail -n 1 $sensordata_file | cut -d' ' -f10`;
		    $t_c_max = `$mycodo_exe r | cut -d' ' -f2`;
		    $t_c_min = `$mycodo_exe r | cut -d' ' -f1`;
		    $hum = `tail -n 1 $sensordata_file | cut -d' ' -f8`;
		    $hum_max = `$mycodo_exe r | cut -d' ' -f4`;
		    $hum_min = `$mycodo_exe r | cut -d' ' -f3`;
		    $dp_f = `tail -n 1 $sensordata_file | cut -d' ' -f11`;
		    $dp_c = ($dp_f-32)*5/9;
		    $dp_c = round($dp_c, 1);

		    echo 'RH: ' . $hum . '% | ';
		    echo 'T: ' . $t_c . '&deg;C / ' . $t_f . '&deg;F | ';
		    echo 'DP: ' . $dp_c . '&deg;C / '. $dp_f . '&deg;F';
		?>
	    </div>
	    <FORM action="" method="POST">
		<div style="padding: 5px 0 10px 0;">
		    Web Override: <b><?php $webor_read = $mycodo_exec . " r | cut -d' ' -f5"; if (shell_exec($webor_read) == 1) echo "ON"; else echo "OFF"; ?></b>
		    [<input type="submit" name="OR" value="ON"> <input type="submit" name="OR" value="OFF">]
		</div>
		<?php
		    require $relay_config;
		    for ($i = 1; $i <= 8; $i++) {
		    ?>
		    <div class="relay-state">
			Relay <?php echo $i . ' (' . $relay[$i-1][1] . '): <b>'; $read = $gpio_path . " read " . $relay[$i-1][2]; if (shell_exec($read) == 1) echo "ON"; else echo "OFF"; ?></b>
			[<button type="submit" name="R<?php echo $i; ?>" value="1">ON</button> <button type="submit" name="R<?php echo $i; ?>" value="0">OFF</button>] [<input type="text" maxlength=3 size=3 name="sR<?php echo $i; ?>" /> sec 
			<input type="submit" name="<?php echo $i; ?>secON" value="ON">]
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
	    </FORM>
	</div>
    </body>
</html>

<?php
} else {
    echo 'Configuration editing disabled for guest.';
}

function webor($state)
{
    global $mycodo_exec;

    $command     = $mycodo_exec . " r";
    $readconfig  = shell_exec($command);
    $cpiece      = explode(" ", $readconfig);	
    $writeconfig = $mycodo_exec . " w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $state . " " . $cpiece[5] . " " . $cpiece[6] . "\n";
    shell_exec($writeconfig);
}

function change_relay($relay_change, $state) {
    global $gpio_path, $relay_config;
    require $relay_config;

    $r_state = $gpio_path . " read " . $relay[$relay_change][2];
    if (shell_exec($r_state) == 1 && $state == 1) echo '<div class="error">Error: Relay ' . ($relay_change+1) . ': Can\'t turn on, it\'s already ON</div>';
    else {
	$gpio_mode = $gpio_path . ' mode ' . $relay[$relay_change][2] . ' out';
	$gpio_write = $gpio_path . ' write ' . $relay[$relay_change][2] . ' ' . $state;
	shell_exec($gpio_mode);
	shell_exec($gpio_write);
    }
}

function error_seconds($relay_num, $type_error) {
    echo '<div class="error">Error: relay ' . $relay_num . ': ';
	if ($type_error == 1) echo 'seconds on must be a positive integer.';
	else echo 'cannot turn on, relay is already on.';
	echo '</div>';
}

function relay_on_seconds() {
    global $gpio_path, $relay_config, $relay_exec;
    require $relay_config;

    if ($_POST['1secON']) {
	$sR1 = $_POST['sR1'];
	$r_state = $gpio_path . " read " . $relay[0][2];
	if (!is_numeric($sR1) || $sR1 < 1 || $sR1 != round($sR1)) error_seconds(1, 1);
	else if (shell_exec($r_state) == 1) error_seconds(1, 2);
	else exec(sprintf("%s 1 %s > /dev/null 2>&1", $relay_exec, $sR1));
    }
    if ($_POST['2secON']) {
	$sR2 = $_POST['sR2'];
	$r_state = $gpio_path . " read " . $relay[1][2];
	if (!is_numeric($sR2) || $sR2 < 1 || $sR2 != round($sR2)) error_seconds(2);
	else if (shell_exec($r_state) == 1) error_seconds(2, 2);
	else exec(sprintf("%s 2 %s > /dev/null 2>&1", $relay_exec, $sR2));
    }
    if ($_POST['3secON']) {
	$sR3 = $_POST['sR3'];
	$r_state = $gpio_path . " read " . $relay[2][2];
	if (!is_numeric($sR3) || $sR3 < 1 || $sR3 != round($sR3)) error_seconds(3);
	else if (shell_exec($r_state) == 1) error_seconds(3, 2);
	else exec(sprintf("%s 3 %s > /dev/null 2>&1", $relay_exec, $sR3));
    }
    if ($_POST['4secON']) {
	$sR4 = $_POST['sR4'];
	$r_state = $gpio_path . " read " . $relay[3][2];
	if (!is_numeric($sR4) || $sR4 < 1 || $sR4 != round($sR4)) error_seconds(4);
	else if (shell_exec($r_state) == 1) error_seconds(4, 2);
	else exec(sprintf("%s 4 %s > /dev/null 2>&1", $relay_exec, $sR4));
    }
    if ($_POST['5secON']) {
	$sR5 = $_POST['sR5'];
	$r_state = $gpio_path . " read " . $relay[4][2];
	if (!is_numeric($sR5) || $sR5 < 1 || $sR5 != round($sR5)) error_seconds(5);
	else if (shell_exec($r_state) == 1) error_seconds(5, 2);
	else exec(sprintf("%s 5 %s > /dev/null 2>&1", $relay_exec, $sR5));
    }
    if ($_POST['6secON']) {
	$sR6 = $_POST['sR6'];
	$r_state = $gpio_path . " read " . $relay[5][2];
	if (!is_numeric($sR6) || $sR6 < 1 || $sR6 != round($sR6)) error_seconds(6);
	else if (shell_exec($r_state) == 1) error_seconds(6, 2);
	else exec(sprintf("%s 6 %s > /dev/null 2>&1", $relay_exec, $sR6));
    }
    if ($_POST['7secON']) {
	$sR7 = $_POST['sR7'];
	$r_state = $gpio_path . " read " . $relay[6][2];
	if (!is_numeric($sR7) || $sR7 < 1 || $sR7 != round($sR7)) error_seconds(7);
	else if (shell_exec($r_state) == 1) error_seconds(7, 2);
	else exec(sprintf("%s 7 %s > /dev/null 2>&1", $relay_exec, $sR7));
    }
    if ($_POST['8secON']) {
	$sR8 = $_POST['sR8'];
	$r_state = $gpio_path . " read " . $relay[7][2];
	if (!is_numeric($sR8) || $sR8 < 1 || $sR8 != round($sR8)) error_seconds(8);
	else if (shell_exec($r_state) == 1) error_seconds(8, 2);
	else exec(sprintf("%s 8 %s > /dev/null 2>&1", $relay_exec, $sR8));
    }
}
?>

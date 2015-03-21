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

	// Check if Web Override has been selected to be turned on or off
    if (isset($_POST['OR'])) {
		global $mycodo_exec;
		
		if ($_POST['OR']) $t = 1;
		else $t = 0;
    }
	
    $command     = $mycodo_exec . " r";
    $readconfig  = shell_exec($command);
    $cpiece      = explode(" ", $readconfig);	
    $writeconfig = $mycodo_exec . " w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $t . " " . $cpiece[5] . " " . $cpiece[6] . "\n";
    shell_exec($writeconfig);
	
	// Check if a relay has been selected to be turned on or off
	for ($p = 1; $p <= 8; $p++) {
		if (isset($_POST['R' . $p])) {
			global $gpio_path, $relay_config;
			require $relay_config;
			
			$r_state = $gpio_path . " read " . $relay[$relay_change][2];
			if (shell_exec($r_state) == 1 && $state == 1) echo '<div class="error">Error: Relay ' . ($relay_change+1) . ': Can\'t turn on, it\'s already ON</div>';
			else {
				$gpio_mode = $gpio_path . ' mode ' . $relay[($p - 1)][2] . ' out';
				$gpio_write = $gpio_path . ' write ' . $relay[($p - 1)][2] . ' ' . $_POST['R' .$p];
				shell_exec($gpio_mode);
				shell_exec($gpio_write);
			}
		}
    }
	
	// Check if a relay has been selected to be turned on for a number of seconds
	global $gpio_path, $relay_config, $relay_exec;
    require $relay_config;
	for ($p = 1; $p <=8; $p++) {
		if (isset($_POST[$p . 'secON'])) {
			$sR = $_POST['sR' . $p];
			$r_state = $gpio_path . " read " . $relay[($p - 1)][2];
			if (!is_numeric($sR) || $sR < 1 || $sR != round($sR)) error_seconds($p, 1);
			else if (shell_exec($r_state) == 1) error_seconds($p, 2);
			else exec(sprintf("%s %s %s > /dev/null 2>&1", $relay_exec, $p, $sR));
		}
	}

	function error_seconds($relay_num, $type_error) {
		echo '<div class="error">Error: relay ' . $relay_num . ': ';
		if ($type_error == 1) echo 'seconds on must be a positive integer.';
		else echo 'cannot turn on, relay is already on.';
		echo '</div>';
	}
	
	$command    = $mycodo_exec . " r";
	$editconfig = shell_exec($command);
	$cpiece     = explode(" ", $editconfig);
		
    if ($_POST['ChangeConfig']) {
		$cpiece[0] = $_POST['offTemp'];
		$cpiece[1] = $_POST['onTemp'];
		$cpiece[2] = $_POST['offHum'];
		$cpiece[3] = $_POST['onHum'];
		$cpiece[4] = $_POST['webov'];
	}
	$editconfig = $mycodo_exec . " w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $cpiece[4] . " " . $cpiece[5] . " " . $cpiece[6] . "\n";
	shell_exec($editconfig);
		
	//ChangeState
	//	$cpiece[5]	= $_POST['tState'];
	//	$cpiece[6]= $_POST['hState'];
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
		    [<button type="submit" name="OR" value="1">ON</button> <button type="submit" name="OR" value="0">OFF</button>]
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
			<td>
			    wOV
			</td>
		    </tr>
		    <tr>
			<td>
			    <input type="submit" name="ChangeConfig" value="Set">
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
			<td>
			    <input type="text" value="<?php echo `cat $config_file | tr '\n' ' ' | tr -d ';' | cut -d' ' -f15`; ?>" maxlength=2 size=1 name="webov" />
			</td>
		 </tr>
		    <tr>
			<td>
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
			    <input type="submit" name="ChangeState" value="Set">
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
?>

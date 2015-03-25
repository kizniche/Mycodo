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
$config_path = "/var/www/mycodo/config";

$cwd = getcwd();

$mycodo_exec = $cwd . "/cgi-bin/mycodo";
$mycodo_client = $cwd . "/cgi-bin/mycodo-client.py";

$relay_exec = $cwd . "/cgi-bin/relay.sh";
$sensor_log = $cwd . "/log/sensor.log";

$config_file = $config_path . "/mycodo.cfg";
$config_cond_file = $config_path . "/mycodo-cond.conf";
$config_state_file = $config_path . "/mycodo-state.conf";
$relay_config = $config_path . "/relay_config.php";

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
		$command     = $mycodo_exec . " r";
		$readconfig  = shell_exec($command);
		$cpiece      = explode(" ", $readconfig);	
		$writeconfig = $mycodo_exec . " w cond " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $t;
    
		if ($_POST['OR']) $t = 1;
		else $t = 0;
		
		shell_exec($writeconfig);
    }

	// Check if a relay has been selected to be turned on or off
	for ($p = 1; $p <= 8; $p++) {
		if (isset($_POST['R' . $p])) {
			global $config_path, $relay_config;
			
			$r_state = $gpio_path . " read " . $relay[$relay_change][2];
			if (shell_exec($r_state) == 1 && $state == 1) echo '<div class="error">Error: Relay ' . ($relay_change+1) . ': Can\'t turn on, it\'s already ON</div>';
			else {
                $pin = `cat $config_path/mycodo.cfg | grep relay${p}pin | cut -d' ' -f3`;
				$gpio_write = $gpio_path . ' -g write ' . substr($pin, 0, -1) . ' ' . $_POST['R' .$p];
				shell_exec($gpio_write);
			}
		}
    }
	
	function error_seconds($relay_num, $type_error) {
		echo '<div class="error">Error: relay ' . $relay_num . ': ';
		if ($type_error == 1) echo 'seconds must be a positive integer that\'s >1.';
		else echo 'cannot turn on, relay is already on.';
		echo '</div>';
	}
	
	// Check if a relay has been selected to be turned on for a number of seconds
	global $gpio_path, $relay_config, $relay_exec;
    require $relay_config;
	for ($p = 1; $p <=8; $p++) {
		if (isset($_POST[$p . 'secON'])) {
			$sR = $_POST['sR' . $p];
			$r_state = $gpio_path . " read " . $relay[($p - 1)][2];
			if (!is_numeric($sR) || $sR < 2 || $sR != round($sR)) error_seconds($p, 1);
			else if (shell_exec($r_state) == 1) error_seconds($p, 2);
			else {
                $secExec = $mycodo_client . " --set " . $p . " --seconds " . $sR;
                shell_exec($secExec);
            }
		}
	}

    if ($_POST['ChangeCond']) {
		$command    = $mycodo_exec . " r";
		$editconfig = shell_exec($command);
		$cpiece     = explode(" ", $editconfig);
		$cpiece[0]  = $_POST['minTemp'];
		$cpiece[1]  = $_POST['maxTemp'];
		$cpiece[2]  = $_POST['minHum'];
        $cpiece[3]  = $_POST['maxHum'];
		$cpiece[4]  = $_POST['webov'];
		$editconfig = $mycodo_client . " --configure " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $cpiece[4];
		shell_exec($editconfig);
	}
	
	if ($_POST['ChangeState']) {
		$command    = $mycodo_exec . " r";
		$editconfig = shell_exec($command);
		$cpiece     = explode(" ", $editconfig);
		$cpiece[0]  = $_POST['tState'];
		$cpiece[1]  = $_POST['hState'];
		$editconfig = $mycodo_exec . " w state " . $cpiece[0] . " " . $cpiece[1];
		shell_exec($editconfig);
	}
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
			    $time_last = `tail -n 1 $sensor_log | cut -d' ' -f1,2,3,4,5,6`;
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
		    $t_c = `tail -n 1 $sensor_log | cut -d' ' -f9`;
            $t_f = $t_c * (9/5) + 32;
            $t_c_max = `$mycodo_exe r | cut -d' ' -f2`;
            $t_c_min = `$mycodo_exe r | cut -d' ' -f1`;
            $hum = `tail -n 1 $sensor_log | cut -d' ' -f8`;
            $hum_max = `$mycodo_exe r | cut -d' ' -f4`;
            $hum_min = `$mycodo_exe r | cut -d' ' -f3`;
            $dp_c = `tail -n 1 $sensor_log | cut -d' ' -f10`;
            $dp_f = $dp_c * (9/5) + 32;

		    echo 'RH: ' . $hum . '% | ';
		    echo 'T: ' . $t_c . '&deg;C / ' . $t_f . '&deg;F | ';
		    echo 'DP: ' . $dp_c . '&deg;C / '. $dp_f . '&deg;F';
		?>
	    </div>
	    <FORM action="" method="POST">
		<div style="padding: 5px 0 10px 0;">
		    Web Override: <b>
            <?php
                $webor_read = `cat $config_file | grep webor | cut -d' ' -f3`;
                if ($webor_read == 1) echo "ON";
                else echo "OFF";
            ?>
            </b>
		    [<button type="submit" name="OR" value="1">ON</button> <button type="submit" name="OR" value="0">OFF</button>]
		</div>
		<?php
		    require $relay_config;
		    for ($i = 1; $i <= 8; $i++) {
		    ?>
		    <div class="relay-state">Relay 
                <?php
                    $name = `cat $config_path/mycodo.cfg | grep relay${i}name | cut -d' ' -f3`;
                    $pin = `cat $config_path/mycodo.cfg | grep relay${i}pin | cut -d' ' -f3`;
                    $read = $gpio_path . " -g read " . $pin;
                    echo $i . ' (' . substr($name, 0, -1) . '): <b>';
                    if (shell_exec($read) == 1) echo "OFF";
                    else echo "ON";
                ?></b>
                [<button type="submit" name="R<?php echo $i; ?>" value="1">OFF</button> <button type="submit" name="R<?php echo $i; ?>" value="0">ON</button>] [<input type="text" maxlength=3 size=3 name="sR<?php echo $i; ?>" /> sec 
                <input type="submit" name="<?php echo $i; ?>secON" value="ON">]
		    </div>
		    <?php 
		    }
        
        $mintemp = `cat $config_file | grep mintemp | cut -d' ' -f3`;
        $maxtemp = `cat $config_file | grep maxtemp | cut -d' ' -f3`;
        $minhum = `cat $config_file | grep minhum | cut -d' ' -f3`;
        $maxhum = `cat $config_file | grep maxhum | cut -d' ' -f3`;
        $webor = `cat $config_file | grep webor | cut -d' ' -f3`;
        $tempstate = `cat $config_file | grep tempstate | cut -d' ' -f3`;
        $humstate = `cat $config_file | grep humstate | cut -d' ' -f3`;
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
			    wOR
			</td>
		    </tr>
		    <tr>
			<td>
			    <input type="submit" name="ChangeCond" value="Set">
			</td>
			<td>
			    <input type="text" value="<?php echo $mintemp; ?>" maxlength=2 size=1 name="minTemp" />
			</td>
			<td>
			    <input type="text" value="<?php echo $maxtemp; ?>" maxlength=2 size=1 name="maxTemp" />
			</td>
			<td>
			    <input type="text" value="<?php echo $minhum; ?>" maxlength=2 size=1 name="minHum" />
			</td>
			<td>
			    <input type="text" value="<?php echo $maxhum; ?>" maxlength=2 size=1 name="maxHum" />
			</td>
			<td>
			    <input type="text" value="<?php echo $webor; ?>" maxlength=2 size=1 name="webov" />
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
			    <input type="text" value="<?php echo $tempstate; ?>" maxlength=2 size=1 name="tState" />
			</td>
			<td>
			    <input type="text" value="<?php echo $humstate; ?>" maxlength=2 size=1 name="hState" />
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

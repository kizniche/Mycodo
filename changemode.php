<?php
/*
*  changemode.php - Reads/writes configuration/sensor files and modulates relays based on user input
*  By Kyle Gabriel
*  2012 - 2015
*/

####### Configure Edit Here #######

$install_path = "/var/www/mycodo";

$gpio_path = "/usr/local/bin/gpio";

########## End Configure ##########

$mycodo_client = $install_path . "/cgi-bin/mycodo-client.py";
$sensor_log = $install_path . "/log/sensor.log";
$config_file = $install_path . "/config/mycodo.cfg";

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
    
    $t_c = substr(`tail -n 1 $sensor_log | cut -d' ' -f9`, 0, -1);
    $t_f = $t_c * (9/5) + 32;
    $hum = substr(`tail -n 1 $sensor_log | cut -d' ' -f8`, 0, -1);
    $dp_c = substr(`tail -n 1 $sensor_log | cut -d' ' -f10`, 0, -1);
    $dp_f = $dp_c * (9/5) + 32;
    
    $mintemp = substr(`cat $config_file | grep mintemp | cut -d' ' -f3`, 0, -1);
    $maxtemp = substr(`cat $config_file | grep maxtemp | cut -d' ' -f3`, 0, -1);
    $minhum = substr(`cat $config_file | grep minhum | cut -d' ' -f3`, 0, -1);
    $maxhum = substr(`cat $config_file | grep maxhum | cut -d' ' -f3`, 0, -1);
    $webor = substr(`cat $config_file | grep webor | cut -d' ' -f3`, 0, -1);
        
	for ($p = 1; $p <= 8; $p++) {
        // Relay has been selected to be turned on or off
		if (isset($_POST['R' . $p])) {
			$name = substr(`cat $config_file | grep relay${p}name | cut -d' ' -f3`, 0, -1);
            $pin = substr(`cat $config_file | grep relay${p}pin | cut -d' ' -f3`,0, -1);
            $actual_state = "$gpio_path -g read $pin";
            $desired_state = $_POST['R' . $p];
            
            if (shell_exec($actual_state) == 0 && $desired_state == 0) {
                echo "<div class=\"error\">Error: Relay $p ($name): Can't turn on, it's already ON</div>";
			} else {
                $gpio_write = "$gpio_path -g write $pin $desired_state";
				shell_exec($gpio_write);
			}
		}
        
        // Relay has been selected to be turned on for a number of seconds
        if (isset($_POST[$p . 'secON'])) {
            $name = substr(`cat $config_file | grep relay${p}name | cut -d' ' -f3`, 0, -1);
            $pin = substr(`cat $config_file | grep relay${p}pin | cut -d' ' -f3`,0, -1);
			$actual_state = "$gpio_path -g read $pin";
            $seconds_on = $_POST['sR' . $p];
            
			if (!is_numeric($seconds_on) || $seconds_on < 2 || $seconds_on != round($seconds_on)) {
                   echo "<div class=\"error\">Error: Relay $p ($name): Seconds must be a positive integer >1</div>";
			} else if (shell_exec($actual_state) == 0) {
                echo "<div class=\"error\">Error: Relay $p ($name): Can't turn on for $seconds_on seconds, it's already ON</div>";
			} else {
                $relay_on_sec = "$mycodo_client --set $p --seconds $seconds_on";
                shell_exec($relay_on_sec);
            }
		}
    }
    
    // Check if Web Override has been selected to be turned on or off
    if (isset($_POST['OR'])) {
		if ($_POST['OR']) $t = 1;
		else $t = 0;
		$editconfig = "$mycodo_client --configure $mintemp $maxtemp $minhum $maxhum $t";
        echo "<pre>test${editconfig}test</pre>";
        shell_exec($editconfig);
    }

    if ($_POST['ChangeCond']) {
		$mintemp  = $_POST['minTemp'];
		$maxtemp  = $_POST['maxTemp'];
		$minhum  = $_POST['minHum'];
        $maxhum  = $_POST['maxHum'];
		$webor  = $_POST['webor'];
		$editconfig = "$mycodo_client --configure $mintemp $maxtemp $minhum $maxhum $webor";
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
	    if (isset($_GET['r']) && $_GET['r'] == 1) echo '<META HTTP-EQUIV="refresh" CONTENT="90">';
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
            echo "RH: ${hum}% | T: $t_c &deg;C / $t_f &deg;F | DP: $dp_c &deg;C / $dp_f &deg;F";
		?>
	    </div>
	    <FORM action="" method="POST">
		<div style="padding: 5px 0 10px 0;">
		    Web Override: <b>
            <?php
                if ($webor == 1) echo "ON";
                else echo "OFF";
            ?>
            </b>
		    [<button type="submit" name="OR" value="1">ON</button> <button type="submit" name="OR" value="0">OFF</button>]
		</div>
		<?php
		    for ($i = 1; $i <= 8; $i++) {
		    ?>
		    <div class="relay-state"> 
                <?php
                    $name = substr(`cat $config_file | grep relay${i}name | cut -d' ' -f3`, 0, -1);
                    $pin = substr(`cat $config_file | grep relay${i}pin | cut -d' ' -f3`, 0, -1);
                    $read = "$gpio_path -g read $pin";
                    echo "Relay ${i}: ${name}: pin ${pin}: <b>";
                    if (shell_exec($read) == 1) echo "OFF";
                    else echo "ON";
                ?></b>
                [<button type="submit" name="R<?php echo $i; ?>" value="1">OFF</button> <button type="submit" name="R<?php echo $i; ?>" value="0">ON</button>] [<input type="text" maxlength=3 size=3 name="sR<?php echo $i; ?>" /> sec 
                <input type="submit" name="<?php echo $i; ?>secON" value="ON">]
		    </div>
		    <?php 
		    }
		?>
		<table style="margin: 0 auto; padding-top: 10px;">
		    <tr>
			<td>
			    MinT
			</td>
			<td>
			    MaxT
			</td>
			<td>
			    MinH
			</td>
			<td>
			    MaxH
			</td>
			<td>
			    wOR
			</td>
            <td>
			</td>
		    </tr>
		    <tr>
			<td>
			    <input type="text" value="<?php echo $mintemp; ?>" maxlength=2 size=2 name="minTemp" />
			</td>
			<td>
			    <input type="text" value="<?php echo $maxtemp; ?>" maxlength=2 size=2 name="maxTemp" />
			</td>
			<td>
			    <input type="text" value="<?php echo $minhum; ?>" maxlength=2 size=2 name="minHum" />
			</td>
			<td>
			    <input type="text" value="<?php echo $maxhum; ?>" maxlength=2 size=2 name="maxHum" />
			</td>
			<td>
			    <input type="text" value="<?php echo $webor; ?>" maxlength=2 size=2 name="webor" />
			</td>
            <td>
			    <input type="submit" name="ChangeCond" value="Set">
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

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

function readconfig($var) {
    global $config_file;
    $value = substr(`cat $config_file | grep $var | cut -d' ' -f3`, 0, -1);
    return $value;
}

if ($login->isUserLoggedIn() == true && $_SESSION['user_name'] != guest) {

    if (isset($_POST['WriteSensorLog'])) {
		$editconfig = "$mycodo_client -w";
        shell_exec($editconfig);
        sleep(6);
    }
 
	for ($p = 1; $p <= 8; $p++) {
        // Relay has been selected to be turned on or off
		if (isset($_POST['R' . $p])) {
			$name = readconfig("relay${p}name");
            $pin = readconfig("relay${p}pin");
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
            $name = readconfig("relay${p}name");
            $pin = readconfig("relay${p}pin");
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
    
    if (isset($_POST['ModName'])) {
		for ($i = 1; $i <= 8; $i++) {
            if (isset($_POST['relay' . $i . 'name'])) {
                $relayName[$i] = str_replace(' ', '', $_POST['relay' . $i . 'name']);
            }
        }
        $editconfig = "$mycodo_client --modnames $relayName[1] $relayName[2] $relayName[3] $relayName[4] $relayName[5] $relayName[6] $relayName[7] $relayName[8]";
        shell_exec($editconfig);
        sleep(6);
    }
    
    if (isset($_POST['ModPin'])) {
		for ($i = 1; $i <= 8; $i++) {
            if (isset($_POST['relay' . $i . 'pin'])) {
                $relayPin[$i] = $_POST['relay' . $i . 'pin'];
            }
        }
        $editconfig = "$mycodo_client --modpins $relayPin[1] $relayPin[2] $relayPin[3] $relayPin[4] $relayPin[5] $relayPin[6] $relayPin[7] $relayPin[8]";
        shell_exec($editconfig);
        sleep(6);
    }
    
    // Check if Web Override has been selected to be turned on or off
    if (isset($_POST['TempOR'])) {
        if ($_POST['TempOR']) $tempor = 1;
        else $tempor = 0;
        $editconfig = "$mycodo_client --changetempor $tempor";
        shell_exec($editconfig);
        sleep(6);
    }
    if (isset($_POST['HumOR'])) {
        if ($_POST['HumOR']) $humor = 1;
        else $humor = 0;
        $editconfig = "$mycodo_client --changehumor $humor";
        shell_exec($editconfig);
        sleep(6);
    }
    
    if (isset($_POST['ChangeTempPID']) || isset($_POST['ChangeHumPID'])) {
        $relaytemp = readconfig("relaytemp");
        $settemp = readconfig("settemp");
        $temp_p  = readconfig("temp_p");
        $temp_i  = readconfig("temp_i");
        $temp_d  = readconfig("temp_d");
        $factortempseconds = readconfig("factortempseconds");
        
        $relayhum = readconfig("relayhum");
        $sethum = readconfig("sethum");
        $hum_p  = readconfig("hum_p");
        $hum_i  = readconfig("hum_i");
        $hum_d  = readconfig("hum_d");
        $factorhumseconds = readconfig("factorhumseconds");
    
        if (isset($_POST['ChangeTempPID'])) {
            $relaytemp  = $_POST['relayTemp'];
            $settemp  = $_POST['setTemp'];
            $temp_p  = $_POST['Temp_P'];
            $temp_i  = $_POST['Temp_I'];
            $temp_d  = $_POST['Temp_D'];
            $factortempseconds = $_POST['factorTempSeconds'];
            
            $editconfig = "$mycodo_client --conditionstemp $relaytemp $settemp $temp_p $temp_i $temp_d $factortempseconds";
            shell_exec($editconfig);
            sleep(6);
        }
        if (isset($_POST['ChangeHumPID'])) {
            $relayhum  = $_POST['relayHum'];
            $sethum  = $_POST['setHum'];
            $hum_p  = $_POST['Hum_P'];
            $hum_i  = $_POST['Hum_I'];
            $hum_d  = $_POST['Hum_D'];
            $factorhumseconds = $_POST['factorHumSeconds'];

            $editconfig = "$mycodo_client --conditionshum $relayhum $sethum $hum_p $hum_i $hum_d $factorhumseconds";
            shell_exec($editconfig);
            sleep(6);
        }
    }
    
    if (isset($_POST['ChangeSensor'])) {
        $dhtsensor = readconfig("dhtsensor");
        $dhtpin = readconfig("dhtpin");
        $dhtseconds = readconfig("timersecwritelog");
    
		$dhtsensor = $_POST['DHTSensor'];
        $dhtpin = $_POST['DHTPin'];
        $dhtseconds = $_POST['DHTSecs'];
        
        if ($dhtsensor == 'Other') {
            $enable_overrides = "$mycodo_client --changetempor 1";
            shell_exec($enable_overrides);
            $enable_overrides = "$mycodo_client --changehumor 1";
            shell_exec($enable_overrides);
        }
        
        $editconfig = "$mycodo_client --modsensor $dhtsensor $dhtpin $dhtseconds";
        shell_exec($editconfig);
        sleep(6);
    }
    
    $dhtsensor = readconfig("dhtsensor");
    $dhtpin = readconfig("dhtpin");
    $dhtseconds = readconfig("timersecwritelog");
    
    $relaytemp = readconfig("relaytemp");
    $relayhum = readconfig("relayhum");
    $settemp = readconfig("settemp");
    $sethum = readconfig("sethum");
    $tempor = readconfig("tempor");
    $humor = readconfig("humor");
    
    $temp_p  = readconfig("temp_p");
    $temp_i  = readconfig("temp_i");
    $temp_d  = readconfig("temp_d");
    $hum_p  = readconfig("hum_p");
    $hum_i  = readconfig("hum_i");
    $hum_d  = readconfig("hum_d");
    
    $factorhumseconds = readconfig("factorhumseconds");
    $factortempseconds = readconfig("factortempseconds");
    
    $t_c = substr(`tail -n 1 $sensor_log | cut -d' ' -f7`, 0, -1);
    $t_f = round(($t_c * (9/5) + 32), 1);
    $hum = substr(`tail -n 1 $sensor_log | cut -d' ' -f8`, 0, -1);
    $dp_c = substr(`tail -n 1 $sensor_log | cut -d' ' -f9`, 0, -1);
    $dp_f = round(($dp_c * (9/5) + 32), 1);
?>

<html>
    <head>
        <title>
            Relay Control and Configuration
        </title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
        <link rel="stylesheet" href="style.css" type="text/css" media="all" />
        <?php 
            if (isset($_GET['r']) && $_GET['r'] == 1) echo '<META HTTP-EQUIV="refresh" CONTENT="300">';
        ?>
    </head>
    <body>
        <div style="text-align: center;">
            <div style="padding-top: 5px; font-size: 18px;">
                <?php
                    echo "Temp: $t_c&deg;C ($t_f&deg;F) &nbsp; &nbsp; RH: ${hum}% &nbsp; &nbsp; DP: $dp_c&deg;C ($dp_f&deg;F)";
                ?>
            </div>
            <FORM action="" method="POST">
            <div style="display: inline-block; padding-top: 10px;">
                <div style="float: left;" align=right>
                    <div>
                        Current: <?php echo `date +'%Y-%m-%d %H:%M:%S'`; ?>
                    </div>
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
                <div style="float: left; padding-left: 7px;">
                    <div>
                        Auto Refresh
                    </div>
                    <div>
                        <?php
                            if (isset($_GET['r'])) {
                                if ($_GET['r'] == 1) echo "<b><font color=\"green\">On</font></b> | <a href=\"changemode.php\">Turn Off</a>";
                                else echo "<b><font color=\"red\">Off</font></b> | <a href=\"changemode.php?r=1\">Turn On</a>";
                            } else echo "<b><font color=\"red\">Off</font></b> | <a href=\"changemode.php?r=1\">Turn On</a>";
                        ?>
                    </div>
                </div>
                <div style="float: left; padding-left: 7px;">
                    <?php
                        if (isset($_GET['r'])) {
                            echo "<input type=\"button\" onclick=\"location.href='changemode.php?r=1'\" value=\"Refresh&#10;Page\">";
                        } else echo "<input type=\"button\" onclick=\"location.href='changemode.php'\" value=\"Refresh&#10;Page\">";
                    ?>
                </div>
                <div style="float: left; padding-left: 7px;">
                    <input type="submit" name="WriteSensorLog" value="Update&#10;Sensors" title="Take a new temperature and humidity reading">
                </div>
            </div>
            <div style="clear: both;"></div>
            <div>
                <table class="relays" style="padding-top: 15px;">
                    <tr>
                        <td align=center class="table-header">
                            Relay
                        </td>
                        <td align=left class="table-header">
                            Name
                        </td>
                        <td align=left class="table-header">
                            GPIO
                        </td>
                        <th colspan=2  align=center class="table-header">
                            State
                        </th>
                        <td align=left class="table-header">
                            Seconds On
                        </td>
                    </tr>
                    <?php
                        for ($i = 1; $i <= 8; $i++) {
                            $name = readconfig("relay${i}name");
                            $pin = readconfig("relay${i}pin");
                            $read = "$gpio_path -g read $pin";
                    ?>
                    <tr>
                        <td align=center>
                            <?php echo ${i}; ?>
                        </td>
                        <td align=center>
                            <input type="text" value="<?php echo $name; ?>" maxlength=12 size=8 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i; ?>"/>
                        </td>
                        <td align=center>
                            <input type="text" value="<?php echo $pin; ?>" maxlength=2 size=1 name="relay<?php echo $i; ?>pin" title="GPIO pin using BCM numbering, connected to relay <?php echo $i; ?>"/>
                        </td>
                        <?php
                            if (shell_exec($read) == 1) {
                                ?>
                                <th colspan=2 align=right>
                                    <button class="linkon" type="submit" name="R<?php echo $i; ?>" value="1">OFF</button> | <button style="width: 40px;" type="submit" name="R<?php echo $i; ?>" value="0">ON</button>
                                </td>
                                </th>
                                <?php
                            } else {
                                ?>
                                <th colspan=2 align=right>
                                    <button class="linkoff" type="submit" name="R<?php echo $i; ?>" value="0">ON</button> | <button style="width: 40px;" type="submit" name="R<?php echo $i; ?>" value="1">OFF</button>
                                </th>
                                <?php
                            }
                        ?>
                        <td>
                             <input type="text" maxlength=3 size=1 name="sR<?php echo $i; ?>" title="Number of seconds to turn this relay on"/> sec <input type="submit" name="<?php echo $i; ?>secON" value="ON">
                        </td>
                    </tr>
                    <?php 
                    }
                    ?>
                    <tr>
                        <td>
                        </td>
                        <td align=left>
                            <button type="submit" name="ModName" value="1" title="Change relay names to the ones specified above (Do not use spaces)">Rename</button>
                        </td>
                        <td align=left>
                            <button type="submit" name="ModPin" value="1" title="Change the (BCM) GPIO pins attached to relays to the ones specified above">Mod</button>
                        </td>
                    </tr>
                </table>
            </div>
            <div class="pid-wrapper">
                <table class="pid">
                    <tr class="shade">
                        <th rowspan=2 colspan=2>
                            PID Control
                        </th>
                        <th colspan=2 align=center>
                            Sensor
                        </th>
                        <td align=center>
                            Pin
                        </td>
                        <th colspan=2>
                            Read Period
                        </td>
                    </tr>
                    <tr>
                        <th colspan=2>
                            <select style="width: 80px;" name="DHTSensor">
                                <option <?php if ($dhtsensor == 'DHT11') echo "selected=\"selected\""; ?> value="DHT11">DHT11</option>
                                <option <?php if ($dhtsensor == 'DHT22') echo "selected=\"selected\""; ?> value="DHT22">DHT22</option>
                                <option <?php if ($dhtsensor == 'AM2302') echo "selected=\"selected\""; ?> value="AM2302">AM2302</option>
                                <option <?php if ($dhtsensor == 'Other') echo "selected=\"selected\""; ?>value="Other">Other</option>
                            </select>
                        </th>
                        <td>
                            <input type="text" value="<?php echo $dhtpin; ?>" maxlength=2 size=1 name="DHTPin" title="This is the GPIO pin connected to the DHT sensor"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $dhtseconds; ?>" maxlength=3 size=1 name="DHTSecs" title="The number of seconds between writing sensor readings to the log"/>
                        </td>
                        <td>
                            Sec
                        </td>
                        <td>
                            <input type="submit" name="ChangeSensor" value="Set">
                        </td>
                    </tr>
                    <tr style="height: 4px !important;">
                        <td colspan="8"></td>
                    </tr>
                    <?php
                        if ($dhtsensor == 'DHT11' || $dhtsensor == 'DHT22' || $dhtsensor == 'AM2302') {
                    ?>
                    <tr class="shade">
                        <td align=center>
                            Temperature
                        </td>
                        <td align=center>
                            Relay
                        </td>
                        <td align=center>
                            Set°C
                        </td>
                        <td align=center>
                            Sec
                        </td>
                        <td align=center>
                            P
                        </td>
                        <td align=center>
                            I
                        </td>
                        <td align=center>
                            D
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <?php
                                if ($tempor == 1) {
                                    ?>
                                    <span class="state off">OFF</span> | <button type="submit" name="TempOR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?>
                                    <span class="state on">ON</span> | <button type="submit" name="TempOR" value="1">OFF</button>
                                    <?php
                                }
                            ?>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $relaytemp; ?>" maxlength=1 size=1 name="relayTemp" title="This is the desired temperature"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $settemp; ?>" maxlength=4 size=1 name="setTemp" title="This is the desired temperature"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $factortempseconds; ?>" maxlength=4 size=1 name="factorTempSeconds" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $temp_p; ?>" maxlength=4 size=1 name="Temp_P" title="This is the proportional value of the PID"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $temp_i; ?>" maxlength=4 size=1 name="Temp_I" title="This is the integral value of the the PID"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $temp_d; ?>" maxlength=4 size=1 name="Temp_D" title="This is the derivative value of the PID"/>
                        </td>
                        <td>
                            <input type="submit" name="ChangeTempPID" value="Set">
                        </td>
                    </tr>
                    <tr style="height: 4px !important;">
                        <td colspan="8"></td>
                    </tr>
                    <tr class="shade">
                        <td align=center>
                            Humidity
                        </td>
                        <td align=center>
                            Relay
                        </td>
                        <td align=center>
                            Set%
                        </td>
                        <td align=center>
                            Sec
                        </td>
                        <td align=center>
                            P
                        </td>
                        <td align=center>
                            I
                        </td>
                        <td align=center>
                            D
                        </td>
                    </tr>
                    <tr>
                        <td>
                        <?php
                            if ($humor == 1) {
                                ?>
                                <span class="state off">OFF</span> | <button type="submit" name="HumOR" value="0">ON</button>
                                <?php
                            } else {
                                ?>
                                <span class="state on">ON</span> | <button type="submit" name="HumOR" value="1">OFF</button>
                                <?php
                            }
                        ?>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $relayhum; ?>" maxlength=1 size=1 name="relayHum" title="This is the desired temperature"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $sethum; ?>" maxlength=4 size=1 name="setHum" title="This is the desired humidity"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $factorhumseconds; ?>" maxlength=4 size=1 name="factorHumSeconds" title="This is the number of seconds to wait after the relay has been turned off before taking another humidity reading and applying the PID"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $hum_p; ?>" maxlength=4 size=1 name="Hum_P" title="This is the proportional value of the PID"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $hum_i; ?>" maxlength=4 size=1 name="Hum_I" title="This is the integral value of the the PID"/>
                        </td>
                        <td>
                            <input type="text" value="<?php echo $hum_d; ?>" maxlength=4 size=1 name="Hum_D" title="This is the derivative value of the PID"/>
                        </td>
                        <td>
                            <input type="submit" name="ChangeHumPID" value="Set">
                        </td>
                    </tr>
                    <?php
                        } else {
                    ?>
                    <tr style="height: 10px !important; background-color: #FFFFFF;">
                        <td colspan="8">
                            There is only built-in support for sensors on the list.
                        </td>
                    </tr>
                    <?php
                        }
                    ?>
                </table>
            </div>
            </FORM>
        </div>
    </body>
</html>

<?php
} else {
    echo 'Configuration editing disabled for guest.';
}
?>

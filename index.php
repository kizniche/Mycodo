<?php
/*
*
*  index.php - The main page of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure Edit Here #######

$install_path = "/var/www/mycodo";
$gpio_path = "/usr/local/bin/gpio";

########## End Configure ##########

$config_file = $install_path . "/config/mycodo.cfg";
$sensor_log = $install_path . "/log/sensor.log";
$relay_log = $install_path . "/log/relay.log";
$auth_log = $install_path . "/log/auth.log";
$daemon_log = $install_path . "/log/mycodo.log";
$images = $install_path . "/images";
$graph_exec = $install_path . "/cgi-bin/graph.sh";
$still_exec = $install_path . "/cgi-bin/camera-still.sh";
$stream_exec = $install_path . "/cgi-bin/camera-stream.sh";
$lock_raspistill = "/var/lock/mycodo_raspistill";
$lock_mjpg_streamer = "/var/lock/mycodo_mjpg_streamer";

if (version_compare(PHP_VERSION, '5.3.7', '<')) {
    exit("PHP Login does not run on PHP versions before 5.3.7, please update your version of PHP");
} else if (version_compare(PHP_VERSION, '5.5.0', '<')) {
    require_once("libraries/password_compatibility_library.php");
}
require_once('config/config.php');
require_once('translations/en.php');
require_once('libraries/PHPMailer.php');
require_once("classes/Login.php");
$login = new Login();

function menu_item($id, $title, $current) {
    $class = ($current == $id) ? "active" : "inactive";
    if ($current != $id) {
        echo '<a href="?tab=main&';
        if (isset($_GET['r'])){
            if ($_GET['r'] == 1) echo 'r=1&';
        }
        echo 'page=' . $id. '"><div class="inactive">' . $title . '</div></a>';
    } else echo '<div class="active">' . $title . '</div>';
}

function readconfig($var) {
    global $config_file;
    $value = substr(`cat $config_file | grep $var | cut -d' ' -f3`, 0, -1);
    return $value;
}

function DateSelector($inName, $useDate=0) {
    /* create array to name months */
    $monthName = array(1=> "January", "February", "March",
    "April", "May", "June", "July", "August",
    "September", "October", "November", "December");
    /* if date invalid or not supplied, use current time */
    if($useDate == 0) $useDate = Time();

    echo "<SELECT NAME=" . $inName . "Month>\n";
	for($currentMonth = 1; $currentMonth <= 12; $currentMonth++) {
	    echo "<OPTION VALUE=\"";
	    echo intval($currentMonth);
	    echo "\"";
	    if(intval(date( "m", $useDate))==$currentMonth) echo " SELECTED";
	    echo ">" . $monthName[$currentMonth] . "\n";
	}
	echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Day>\n";
	for($currentDay=1; $currentDay <= 31; $currentDay++) {
	    echo "<OPTION VALUE=\"$currentDay\"";
	    if(intval(date( "d", $useDate))==$currentDay) echo " SELECTED";
	    echo ">$currentDay\n";
	}
	echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Year>\n";
	$startYear = date( "Y", $useDate);
	for($currentYear = $startYear - 5; $currentYear <= $startYear+5;$currentYear++) {
	    echo "<OPTION VALUE=\"$currentYear\"";
	    if(date( "Y", $useDate)==$currentYear) echo " SELECTED";
	    echo ">$currentYear\n";
	}
	echo "</SELECT>&nbsp;&nbsp;&nbsp;";

    echo "<SELECT NAME=" . $inName . "Hour>\n";
	for($currentHour=0; $currentHour <= 23; $currentHour++) {
	    if($currentHour < 10) echo "<OPTION VALUE=\"0$currentHour\"";
	    else { echo "<OPTION VALUE=\"$currentHour\""; }
	    if(intval(date( "H", $useDate))==$currentHour) echo " SELECTED";
	    if($currentHour < 10) echo ">0$currentHour\n";
	    else { echo ">$currentHour\n";}
	}
	echo "</SELECT> : ";

    echo "<SELECT NAME=" . $inName . "Minute>\n";
	for($currentMinute=0; $currentMinute <= 59; $currentMinute++) {
	    if($currentMinute < 10) echo "<OPTION VALUE=\"0$currentMinute\"";
	    else { echo "<OPTION VALUE=\"$currentMinute\"";}
	    if(intval(date( "i", $useDate))==$currentMinute) echo " SELECTED";
	    if($currentMinute < 10) echo ">0$currentMinute\n";
	    else { echo ">$currentMinute\n";}
	}
	echo "</SELECT>";
}

function displayform() {
        echo "<div style=\"padding-left: 15px;\"><div style=\"display: inline-block;\"><FORM action=\"?tab=graph\" method=\"POST\">";
		echo "<div style=\"padding-bottom: 5px; text-align: right;\">START: ";
		DateSelector("start");
		echo "</div><div style=\"text-align: right;\">END: ";
		DateSelector("end");
		echo "</div></div><div style=\"display: inline-block;\">&nbsp;&nbsp;<input type=\"submit\" name=\"SubmitDates\" value=\"Submit\"></FORM></div></div>";
}

if ($login->isUserLoggedIn() == true) {
    $page = isset($_GET['page']) ? $_GET['page'] : 'Main';

    $config_contents = file_get_contents($config_file);
    $config_rows = explode("\n", $config_contents);
    array_shift($config_rows);
    foreach($config_rows as $row => $data) {
        $row_data = explode(' = ', $data);
        if (!empty($row_data[1])) {
            ${$row_data[0]} = $row_data[1];
        }
    }

    // All commands that elevated (!=guest) privileges are required
    for ($p = 1; $p <= 8; $p++) {
        // Relay has been selected to be turned on or off
        if (isset($_POST['R' . $p]) && $_SESSION['user_name'] != guest) {
            $name = ${"relay" . $p . "name"};
            $pin = ${"relay" . $p . "pin"};
            $actual_state = "$gpio_path -g read $pin";
            $desired_state = $_POST['R' . $p];
            
            if (shell_exec($actual_state) == 0 && $desired_state == 0) {
                echo "<div class=\"error\">Error: Relay $p ($name): Can't turn on, it's already ON</div>";
            } else {
                $gpio_write = "$gpio_path -g write $pin $desired_state";
                shell_exec($gpio_write);
            }
        } else if (isset($_POST['R' . $p]) && $_SESSION['user_name'] == guest) $guest_error = 1;
        
        // Relay has been selected to be turned on for a number of seconds
        if (isset($_POST[$p . 'secON']) && $_SESSION['user_name'] != guest) {
            $name = ${"relay" . $p . "name"};
            $pin = ${"relay" . $p . "pin"};
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
        } else if (isset($_POST[$p . 'secON']) && $_SESSION['user_name'] == guest) $guest_error = 1;
    }
        
    if (isset($_POST['WriteSensorLog']) || isset($_POST['ChangeSensor']) ||
            isset($_POST['ChangeTempPID']) || isset($_POST['ChangeHumPID']) ||
            isset($_POST['TempOR']) || isset($_POST['HumOR']) ||
            isset($_POST['ModPin']) || isset($_POST['ModName'])) {
        if ($_SESSION['user_name'] != guest) {
            
             if (isset($_POST['WriteSensorLog'])) {
                $editconfig = "$mycodo_client -w";
                shell_exec($editconfig);
                sleep(6);
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
                $editconfig = "$mycodo_client --modvar TempOR $tempor";
                shell_exec($editconfig);
                sleep(6);
            }
            if (isset($_POST['HumOR'])) {
                if ($_POST['HumOR']) $humor = 1;
                else $humor = 0;
                $editconfig = "$mycodo_client --modvar HumOR $humor";
                shell_exec($editconfig);
                sleep(6);
            }
            
            if (isset($_POST['ChangeTempPID'])) {
                $relaytemp  = $_POST['relayTemp'];
                $settemp  = $_POST['setTemp'];
                $temp_p  = $_POST['Temp_P'];
                $temp_i  = $_POST['Temp_I'];
                $temp_d  = $_POST['Temp_D'];
                $factortempseconds = $_POST['factorTempSeconds'];
                $editconfig = "$mycodo_client --modVar relayTemp $relaytemp setTemp $settemp Temp_P $temp_p Temp_I $temp_i Temp_D $temp_d factorTempSeconds $factortempseconds";
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
                $editconfig = "$mycodo_client --modvar relayHum $relayhum setHum $sethum Hum_P $hum_p Hum_I $hum_i Hum_D $hum_d factorHumSeconds $factorhumseconds";
                shell_exec($editconfig);
                sleep(6);
            }
            
            if (isset($_POST['ChangeSensor'])) {
                $dhtsensor = $_POST['DHTSensor'];
                $dhtpin = $_POST['DHTPin'];
                $dhtseconds = $_POST['DHTSec'];
                if ($dhtsensor == 'Other') {
                    $enable_overrides = "$mycodo_client --modvar TempOR 1 HumOR 1";
                    shell_exec($enable_overrides);
                }
                $editconfig = "$mycodo_client --modvar DHTSensor $dhtsensor DHTPin $dhtpin DHTSeconds $dhtseconds";
                shell_exec($editconfig);
                sleep(6);
            }
        } else $guest_error = 1;
    }
    
    if ($guest_error) { // Ensures error only displayed once
        echo "<span class=\"error\">You do not have the proper privileges to perform that task!</span>";
        $guest_error = 0;
    }
        
    foreach($config_rows as $row => $data) {
        $row_data = explode(' = ', $data);
        if (!empty($row_data[1])) {
            ${$row_data[0]} = $row_data[1];
        }
    }
    
    $last_sensor = `tail -n 1 $sensor_log`;
    $sensor_explode = explode(" ", $last_sensor);
    $t_c = $sensor_explode[6];
    $t_f = round(($t_c*(9/5) + 32), 1);
    $settemp_f = round(($settemp*(9/5) + 32), 1);
    $hum = $sensor_explode[7];
    $dp_c = substr($sensor_explode[8], 0, -1);
    $dp_f = round(($dp_c*(9/5) + 32), 1);
    
    $time_now = `date +"%Y-%m-%d %H:%M:%S"`;
    $time_last = `tail -n 1 $sensor_log`;
    $time_explode = explode(" ", $time_last);
    $time_last = $time_explode[0] . '-' . $time_explode[1] . '-' . $time_explode[2] . ' ' . $time_explode[3] . ':' . $time_explode[4] . ':' . $time_explode[5];
?>
<!doctype html>
<html lang="en" class="no-js">
<head>
    <title>Mycodo</title>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link href='http://fonts.googleapis.com/css?family=PT+Sans:400,700' rel='stylesheet' type='text/css'>
	<link rel="stylesheet" href="css/reset.css">
	<link rel="stylesheet" href="css/style.css">
	<script src="js/modernizr.js"></script>
    <script type="text/javascript">
        function open_chmode() {
            window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=500, height=630");
        }
        function open_legend() {
            window.open("image.php?span=legend","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=190, height=210");
        }
        function open_legend_full() {
            window.open("image.php?span=legend-full","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=600, height=385");
        }
    </script>
</head>
<body>
<div class="cd-tabs">
<div class="main-wrapper">
    <div class="header">
        <div style="float: left;">
            <img style="margin: 0 5px 0 5px; width: 50px; height: 50px;" src="<?php echo $login->user_gravatar_image_tag; ?>">
        </div>
        <div style="float: left;">
            <div>
                User: <?php echo $_SESSION['user_name']; ?>
            </div>
            <?php if ($_SESSION['user_name'] != guest) { ?>
            <div>
                <a href="edit.php"><?php echo WORDING_EDIT_USER_DATA; ?></a>
            </div>
            <div>
                <a href="index.php?logout"><?php echo WORDING_LOGOUT; ?></a>
            </div>
            <?php } else { ?>
            <div>
                <a href="index.php?logout"><?php echo WORDING_LOGOUT; ?></a>
            </div>
            <?php } ?>
        </div>
    </div>
    <div class="header">
        <div style="text-align: right; padding-top: 5px;">Time: <?php echo $time_now; ?></div>
        <div style="text-align: right; padding-top: 5px;">Sensor: <?php echo $time_last; ?></div>
    </div>
    <div class="header">
        <div style="padding-bottom: 3px;">
            <u>Temperature</u> <?php if ($tempor == 1) echo " <span class=\"off\">OFF</span>";
                else echo " <span class=\"on\">ON</span>"; ?>
        </div>
        <div>
            <?php echo number_format((float)$t_c, 1, '.', '') . "&deg;C (" . number_format((float)$t_f, 1, '.', '') . "&deg;F) Now"; ?>
        </div>
        <div>
             <?php 
                echo number_format((float)$settemp, 1, '.', '') . "&deg;C (" . number_format((float)$settemp_f, 1, '.', '') ."&deg;F) Set";
                
            ?>
        </div>
    </div>
    <div class="header">
        <div style="padding-bottom: 3px;">
            <u>Humidity</u> <?php  if ($humor == 1) echo " <span class=\"off\">OFF</span>";
                else echo " <span class=\"on\">ON</span>"; ?>
        </div>
        <div>
            <?php echo number_format((float)$hum, 1, '.', '') . "% Now"; ?>
        </div>
        <div>
             <?php echo number_format((float)$sethum, 1, '.', '') . "% Set"; ?>
        </div>
    </div>
    <div class="header">
        <div style="padding-bottom: 3px;">
            <u>Dew Point</u>
        </div>
        <div>
            <?php echo "${dp_c}&deg;C (${dp_f}&deg;F)"; ?>
        </div>
    </div>
</div>
<div style="clear: both; padding-top: 15px;"></div>
	<nav>
		<ul class="cd-tabs-navigation">
			<li><a data-content="main" <?php if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'main')) echo "class=\"selected\""; ?> href="#0">Main</a></li>
			<li><a data-content="configure" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'config') echo "class=\"selected\""; ?> href="#0">Configure</a></li>
			<li><a data-content="graph" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'graph') echo "class=\"selected\""; ?> href="#0">Graphs</a></li>
			<li><a data-content="camera" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'camera') echo "class=\"selected\""; ?> href="#0">Camera</a></li>
			<li><a data-content="log" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'log') echo "class=\"selected\""; ?> href="#0">Log</a></li>
			<li><a data-content="menu2" href="#0">Menu2</a></li>
		</ul> <!-- cd-tabs-navigation -->
	</nav>
	<ul class="cd-tabs-content">
		<li data-content="main" <?php if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'main')) echo "class=\"selected\""; ?>>
            <div>
                <div style="float: left; padding: 8px 45px 10px 0;">
                    <?php
                    if (isset($_GET['r']) && $_GET['r'] == 1) {
                            if (empty($page)) echo '<input type="button" onclick=\'location.href="?tab=main&r=1"\' value="Refresh">';
                            echo '<input type="button" onclick=\'location.href="?tab=main&page=' . $page . '&r=1"\' value="Refresh">';
                        } else {
                            if (empty($page)) echo '<input type="button" onclick=\'location.href="?tab=main"\' value="Refresh">';
                            echo '<input type="button" onclick=\'location.href="?tab=main&page=' . $page . '"\' value="Refresh">';
                        }
                    ?>
                    
                    Auto: <?php
                        if (isset($_GET['r']) && $_GET['r'] == 1) {
                            if (empty($page)) echo '<a href="?tab=main">OFF</a> | <span class="on">ON</span>';
                            else echo '<a href="?tab=main&page=' . $page . '">OFF</a> | <span class="on">ON</span>';
                        } else {
                            if (empty($page)) echo '<span class="off">OFF</span> | <a href="?tab=main&r=1">ON</a>';
                            echo '<span class="off">OFF</span> | <a href="?tab=main&page=' . $page . '&r=1">ON</a>';
                        }
                    ?>
                </div>
                <div style="float: left; padding: 0 45px 10px 0">
                    <?php
                        menu_item('Main', 'Main', $page);
                        menu_item('Hour', 'Hour', $page);
                        menu_item('6Hours', '6 Hours', $page);
                        menu_item('Day', 'Day', $page);
                        menu_item('Week', 'Week', $page);
                        menu_item('Month', 'Month', $page);
                        menu_item('Year', 'Year', $page);
                        menu_item('All', 'All', $page);
                    ?>
                </div>
                <div style="float: left; padding: 8px 0 10px 0;">
                    Legend: <a href="javascript:open_legend()">Brief</a> / <a href="javascript:open_legend_full()">Full</a>
                </div>
            </div>
            <div style="clear: both;"></div>
            <center>
            <?php
            if (isset($_GET['page'])) {
                switch ($_GET['page']) {
                case 'Main':
                shell_exec($graph_exec . ' dayweek');
                echo "<img src=image.php?span=main>";
                break;
                case 'Hour':
                shell_exec($graph_exec . ' 1h');
                echo "<img src=image.php?span=1h>";
                break;
                case '6Hours':
                shell_exec($graph_exec . ' 6h');
                echo "<img src=image.php?span=6h>";
                break;
                case 'Day':
                shell_exec($graph_exec . ' day');
                echo "<img src=image.php?span=day>";
                break;
                case 'Week':
                shell_exec($graph_exec . ' week');
                echo "<img src=image.php?span=week>";
                break;
                case 'Month':
                shell_exec($graph_exec . ' month');
                echo "<img src=image.php?span=month>";
                break;
                case 'Year':
                shell_exec($graph_exec . ' year');
                echo "<img src=image.php?span=year>";
                break;
                case 'All':
                shell_exec($graph_exec . ' all');
                echo "<img src=image.php?span=1h><p><img src=image.php?span=6h></p><p><img src=image.php?span=day></p><p><img src=image.php?span=week></p><p><img src=image.php?span=month></p><p><img src=image.php?span=year></p>";
                break;
                default:
                shell_exec($graph_exec . ' dayweek');
                echo "<img src=image.php?span=main>";
                break;
                }
            } else {
                shell_exec($graph_exec . ' dayweek');
                echo "<img src=image.php?span=main>";
            }
            ?>
            </center>
		</li>

		<li data-content="configure" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'config') echo "class=\"selected\""; ?>>
            <FORM action="?tab=config<?php if (isset($_GET['r'])) echo "&r=" . $_GET['r']; ?>" method="POST">
            <div style="float: left;">
                <div style="float: left; padding: 8px 15px 0 0;">
                        <?php
                        if (isset($_GET['r'])) {
                            echo "<input type=\"button\" onclick=\"location.href='?tab=config&r=1'\" value=\"Refresh\">";
                        } else echo "<input type=\"button\" onclick=\"location.href='?tab=config'\" value=\"Refresh\">";
                        ?> Auto: 
                        <?php
                            if (isset($_GET['r'])) {
                                if ($_GET['r'] == 1) echo "<a href=\"?tab=config\">OFF</a> | <span class=\"on\">ON</span>";
                                else echo "<span class=\"off\">OFF</span> | <a href=\"?tab=config&?r=1\">ON</a>";
                            } else echo "<span class=\"off\">OFF</span> | <a href=\"?tab=config&r=1\">ON</a>";
                        ?>
                </div>
                <div style="float: left; padding-top: 6px;">
                    <input type="submit" name="WriteSensorLog" value="Update Sensors" title="Take a new temperature and humidity reading">
                </div>
            </div>
            
            <div style="clear: both;"></div>
            <div style="padding-top: 25px;">
                <div style="float: left; padding-right: 15px;">
                    <table class="relays">
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
                                $name = ${"relay" . $i . "name"};
                                $pin = ${"relay" . $i . "pin"};
                                $read = "$gpio_path -g read $pin";
                        ?>
                        <tr>
                            <td align=center>
                                <?php echo ${i}; ?>
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $name; ?>" maxlength=12 size=10 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i; ?>"/>
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

                <div style="float:  left;">
                    <div style="float: left;">
                        <table class="pid">
                            <tr class="shade">
                                <th rowspan=2 colspan=2 align=center>
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
                                    <input type="text" value="<?php echo $relaytemp; ?>" maxlength=1 size=1 name="relayTemp" title="This is the relay connected to the heating device"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $settemp; ?>" maxlength=4 size=2 name="setTemp" title="This is the desired temperature"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $factortempseconds; ?>" maxlength=4 size=1 name="factorTempSeconds" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $temp_p; ?>" maxlength=4 size=1 name="Temp_P" title="This is the Proportional value of the PID"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $temp_i; ?>" maxlength=4 size=1 name="Temp_I" title="This is the Integral value of the the PID"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $temp_d; ?>" maxlength=4 size=1 name="Temp_D" title="This is the Derivative value of the PID"/>
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
                                    <input type="text" value="<?php echo $relayhum; ?>" maxlength=1 size=1 name="relayHum" title="This is the relay connected to your humidifying device"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $sethum; ?>" maxlength=4 size=2 name="setHum" title="This is the desired humidity"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $factorhumseconds; ?>" maxlength=4 size=1 name="factorHumSeconds" title="This is the number of seconds to wait after the relay has been turned off before taking another humidity reading and applying the PID"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $hum_p; ?>" maxlength=4 size=1 name="Hum_P" title="This is the Proportional value of the PID"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $hum_i; ?>" maxlength=4 size=1 name="Hum_I" title="This is the Integral value of the the PID"/>
                                </td>
                                <td>
                                    <input type="text" value="<?php echo $hum_d; ?>" maxlength=4 size=1 name="Hum_D" title="This is the Derivative value of the PID"/>
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
                </div>
            </div>
        </FORM>
		</li>

		<li data-content="graph" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'graph') echo "class=\"selected\""; ?>>
            <?php
            /* DateSelector*Author: Leon Atkinson */
            if($_POST['SubmitDates']) {
                $minb = $_POST['startMinute'];
                $hourb = $_POST['startHour'];
                $dayb = $_POST['startDay'];
                $monb = $_POST['startMonth'];
                $yearb = $_POST['startYear'];
                $mine = $_POST['endMinute'];
                $houre = $_POST['endHour'];
                $daye = $_POST['endDay'];
                $mone = $_POST['endMonth'];
                $yeare = $_POST['endYear'];
                echo `echo "set terminal png size 830,490
                set xdata time
                set timefmt \"%Y %m %d %H %M %S\"
                set output \"$images/graph-cus.png\"
                set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]
                set format x \"%H:%M\n%m/%d\"
                set yrange [0:100]
                set y2range [0:35]
                set my2tics 10
                set ytics 10
                set y2tics 5
                set style line 11 lc rgb '#808080' lt 1
                set border 3 back ls 11
                set tics nomirror
                set style line 12 lc rgb '#808080' lt 0 lw 1
                set grid xtics ytics back ls 12
                set style line 1 lc rgb '#0772a1' pt 0 ps 1 lt 1 lw 2
                set style line 2 lc rgb '#ff3100' pt 0 ps 1 lt 1 lw 2
                set style line 3 lc rgb '#00b74a' pt 0 ps 1 lt 1 lw 2
                set style line 4 lc rgb '#ffa500' pt 0 ps 1 lt 1 lw 1
                set style line 5 lc rgb '#a101a6' pt 0 ps 1 lt 1 lw 1
                set style line 6 lc rgb '#48dd00' pt 0 ps 1 lt 1 lw 1
                set style line 7 lc rgb '#d30068' pt 0 ps 1 lt 1 lw 1
                #set xlabel \"Date and Time\"
                #set ylabel \"% Humidity\"
                set title \"$monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
                unset key
                plot \"$sensor_log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, \\\\
                \"\" using 1:8 index 0 title \"T\" w lp ls 2 axes x1y1, \\\\
                \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, \\\\
                \"$relay_log\" u 1:7 index 0 title \"HEPA\" w impulses ls 4 axes x1y1, \\\\
                \"\" using 1:8 index 0 title \"HUM\" w impulses ls 5 axes x1y1, \\\\
                \"\" using 1:9 index 0 title \"FAN\" w impulses ls 6 axes x1y1, \\\\
                \"\" using 1:10 index 0 title \"HEAT\" w impulses ls 7 axes x1y1" | gnuplot`;
                displayform();
                echo "<img src=image.php?span=cus>";
                echo "<p><a href='javascript:open_legend()'>Brief Graph Legend</a> - <a href='javascript:open_legend_full()'>Full Graph Legend</a>";
            } else displayform();
            ?>
		</li>
        
		<li data-content="camera" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'camera') echo "class=\"selected\""; ?>>
            <div style="padding: 5px 0 15px 15px;">
                <form action="?tab=camera" method="POST">
                <table class="camera">
                    <tr>
                        <td>
                            <button name="Capture" type="submit" value="">Capture Still</button>
                        </td>
                        <td>
                            <button name="start-stream" type="submit" value="">Start Stream</button> 
                        </td>
                        <td>
                            <button name="stop-stream" type="submit" value="">Stop Stream</button>
                        </td>
                        <td>
                            <?php
                            if (isset($_POST['Capture'])) {
                                if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) shell_exec("$stream_exec stop");
                                $capture_output = shell_exec("$still_exec 2>&1; echo $?");
                            }
                            if (isset($_POST['start-stream'])) {
                                if (file_exists($lock_raspistill) || file_exists($lock_mjpg_streamer)) {
                                echo 'Lock files already present. Press \'Stop Stream\' to kill processes and remove lock files.<br>';
                                } else {
                                shell_exec("$stream_exec start > /dev/null &");
                                sleep(1);
                                }
                            }
                            if (isset($_POST['stop-stream'])) shell_exec("$stream_exec stop");
                            if (!file_exists($lock_raspistill) && !file_exists($lock_mjpg_streamer)) echo 'Stream <span class="off">OFF</span>';
                            else echo 'Stream <span class="on">ON</span>';
                            ?>
                        </td>
                    </tr>
                </table>
                </form>
            </div>
            <?php
                if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) {
                    echo '<img src="http://' . $_SERVER[HTTP_HOST] . ':8080/?action=stream" />';
                }
                if (isset($_POST['Capture'])) {
                    if ($capture_output != 0) echo 'Abnormal output (possibly error): ' . $capture_output . '<br>';
                    else echo '<p><img src=image.php?span=cam-still></p>';
                }
            ?>
		</li>

		<li data-content="log" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'log') echo "class=\"selected\""; ?>>
			<div style="padding: 5px 0 15px 0;">
                <FORM action="?tab=log" method="POST">
                    Lines: <input type="text" maxlength=8 size=8 name="Lines" /> 
                    <input type="submit" name="Sensor" value="Sensor"> 
                    <input type="submit" name="Relay" value="Relay"> 
                    <input type="submit" name="Auth" value="Auth">
                    <input type="submit" name="Daemon" value="Daemon">
                </FORM>
            </div>
            <div style="font-family: monospace; padding-top: 15px;">
                <pre><?php
                    if(isset($_POST['Sensor'])) {
                        echo 'Year Mo Day Hour Min Sec Timestamp Tc RH DPc<br> <br>';
                        if ($_POST['Lines'] != '') {
                            $Lines = $_POST['Lines'];
                            echo `tail -n $Lines $sensor_log`;
                        } else {
                            echo `tail -n 30 $sensor_log`;
                        }
                    }

                    if(isset($_POST['Relay'])) {
                        echo 'Year Mo Day Hour Min Sec R1Sec R2Sec R3Sec R4Sec R5Sec R6Sec R7Sec R8Sec<br> <br>';
                        if ($_POST['Lines'] != '') {
                            $Lines = $_POST['Lines'];
                            echo `tail -n $Lines $relay_log`;
                        } else {
                            echo `tail -n 30 $relay_log`;
                        }
                    }

                    if(isset($_POST['Auth'])) {
                        echo 'Time, Type of auth, user, IP, Hostname, Referral, Browser<br> <br>';
                        if ($_POST['Lines'] != '') {
                            $Lines = $_POST['Lines'];
                            echo `tail -n $Lines $auth_log`;
                        } else {
                            echo `tail -n 30 $auth_log`;
                        }
                    }
                    if(isset($_POST['Daemon'])) {
                        if ($_POST['Lines'] != '') {
                            $Lines = $_POST['Lines'];
                            echo `tail -n $Lines $daemon_log`;
                        } else {
                            echo `tail -n 30 $daemon_log`;
                        }
                    }
                ?>
                </pre>
            </div>
		</li>

		<li data-content="menu2">
			<p>Empty Menu2</p>
		</li>
	</ul> <!-- cd-tabs-content -->
</div> <!-- cd-tabs -->
<script src="js/jquery-2.1.1.js"></script>
<script src="js/main.js"></script> <!-- Resource jQuery -->
</body>
</html>
<?php
} else include("views/not_logged_in.php");
?>
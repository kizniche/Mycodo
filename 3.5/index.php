<?php
/*
*  index.php - The Mycodo front-end and the main page of the web control
*              interface
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

####### Configure Edit Here #######

$install_path = "/var/www/mycodo";
$lock_path = "/var/lock";
$gpio_path = "/usr/local/bin/gpio";

########## End Configure ##########

$config_file = $install_path . "/config/mycodo.cfg";
$auth_log = $install_path . "/log/auth.log";
$sensor_ht_log = "/var/tmp/sensor-ht.log";
$sensor_co2_log = "/var/tmp/sensor-co2.log";
$relay_log = "/var/tmp/relay.log";
$daemon_log = "/var/tmp/daemon.log";
$images = $install_path . "/images";
$mycodo_client = $install_path . "/cgi-bin/mycodo-client.py";
$still_exec = $install_path . "/cgi-bin/camera-still.sh";
$stream_exec = $install_path . "/cgi-bin/camera-stream.sh";
$lock_raspistill = $lock_path . "/mycodo_raspistill";
$lock_mjpg_streamer = $lock_path . "/mycodo_mjpg_streamer";

$error_code = "No";

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
    global $page;
    $class = ($current == $id) ? "active" : "inactive";
    if ($current != $id) {
        echo '<a href="?tab=main&page=' . $id. '&Refresh=1';
        if (isset($_GET['r']) && ($_GET['r'] == 1)) echo '&r=1';
        echo '"><div class="inactive">' . $title . '</div></a>';
    } else echo '<div class="active">' . $title . '</div>';
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
	    echo "<OPTION VALUE=\"" . intval($currentMonth) . "\"";
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
	$startYear = date("Y", $useDate);
	for($currentYear = $startYear-5; $currentYear <= $startYear+5; $currentYear++) {
	    echo "<OPTION VALUE=\"$currentYear\"";
	    if(date("Y", $useDate) == $currentYear) echo " SELECTED";
	    echo ">$currentYear\n";
	}
	echo "</SELECT>&nbsp;&nbsp;&nbsp;";

    echo "<SELECT NAME=" . $inName . "Hour>\n";
	for($currentHour=0; $currentHour <= 23; $currentHour++) {
	    if($currentHour < 10) echo "<OPTION VALUE=\"0$currentHour\"";
	    else echo "<OPTION VALUE=\"$currentHour\"";
	    if(intval(date("H", $useDate)) == $currentHour) echo " SELECTED";
	    if($currentHour < 10) echo ">0$currentHour\n";
	    else echo ">$currentHour\n";
	}
	echo "</SELECT> : ";

    echo "<SELECT NAME=" . $inName . "Minute>\n";
	for($currentMinute=0; $currentMinute <= 59; $currentMinute++) {
	    if($currentMinute < 10) echo "<OPTION VALUE=\"0$currentMinute\"";
	    else echo "<OPTION VALUE=\"$currentMinute\"";
	    if(intval(date( "i", $useDate)) == $currentMinute) echo " SELECTED";
	    if($currentMinute < 10) echo ">0$currentMinute\n";
	    else echo ">$currentMinute\n";
	}
	echo "</SELECT>";
}

function displayform() { ?>
    <FORM action="?tab=graph<?php if (isset($_GET['page'])) echo "&page=" . $_GET['page']; ?>" method="POST">
    <div style="padding: 10px 0 0 15px;">
        <div style="display: inline-block;">  
            <div style="padding-bottom: 5px; text-align: right;">START: <?php DateSelector("start"); ?></div>
            <div style="text-align: right;">END: <?php DateSelector("end"); ?></div>
        </div>
        <div style="display: inline-block;">
            <div style="display: inline-block;">
                <select name="MainType">
                    <option value="Separate" <?php
                        if (isset($_POST['MainType'])) {
                            if ($_POST['MainType'] == 'Separate') echo 'selected="selected"'; 
                        }
                        ?>>Separate</option>
                    <option value="Combined" <?php
                        if (isset($_POST['MainType'])) {
                            if ($_POST['MainType'] == 'Combined') echo 'selected="selected"'; 
                        }
                        ?>>Combined</option>
                </select>
                <input type="text" value="900" maxlength=4 size=4 name="graph-width" title="Width of the generated graph"> Width (pixels, max 4000)
            </div>
        </div>
        <div style="display: inline-block;">
            &nbsp;&nbsp;<input type="submit" name="SubmitDates" value="Submit">
        </div>
    </div>
    </FORM>
    <?php
}

function is_positive_integer($str) {
    return (is_numeric($str) && $str > 0 && $str == round($str));
}

if ($login->isUserLoggedIn() == true) {
    
    // Delete all generated graphs except for the 20 latest
    $dir = "/var/log/mycodo/images/";
    if (is_dir($dir)) {
        if ($dh = opendir($dir)) {
            $files = array();
            while (($file = readdir($dh)) !== false) {
                $files[$dir . $file] = filemtime($dir . $file);
            }
            closedir($dh);
        }
        // Now sort by timestamp (just an integer) from oldest to newest
        asort($files, SORT_NUMERIC);
        // Loop over all but the 20 newest files and delete them
        // Only need the array keys (filenames) since we don't care about timestamps now the array is in order
        $files = array_keys($files);
        for ($i = 0; $i < (count($files) - 20); $i++) {
            if (!is_dir($files[$i])) unlink($files[$i]);
        }
    }
    
    # Concatenate log files (to TempFS) to ensure the latest data is being used
    `cat /var/www/mycodo/log/daemon.log /var/www/mycodo/log/daemon-tmp.log > /var/tmp/daemon.log`;
    `cat /var/www/mycodo/log/sensor-ht.log /var/www/mycodo/log/sensor-ht-tmp.log > /var/tmp/sensor-ht.log`;
    `cat /var/www/mycodo/log/sensor-co2.log /var/www/mycodo/log/sensor-co2-tmp.log > /var/tmp/sensor-co2.log`;
    `cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log > /var/tmp/relay.log`;

    $daemon_check = `ps aux | grep "[m]ycodo.py"`;
    if (empty($daemon_check)) $daemon_check = 0;
    else $daemon_check = 1;

    $uptime = `uptime | grep -ohe 'load average[s:][: ].*' `;

    $page = isset($_GET['page']) ? $_GET['page'] : 'Main';
    $tab = isset($_GET['tab']) ? $_GET['tab'] : 'Unset';

    // Read config file, for each row set variable to value
    $config_contents = file_get_contents($config_file);
    $config_rows = explode("\n", $config_contents);
    array_shift($config_rows);
    foreach($config_rows as $row => $data) {
        $row_data = explode(' = ', $data);
        if (isset($row_data[1])) ${$row_data[0]} = $row_data[1];
        // echo $row_data[0] . "=" . $row_data[1] . '<br>';
    }

    // All commands that elevated (!= guest) privileges are required
    for ($p = 1; $p <= 8; $p++) {
        if (isset($_POST['R' . $p]) ||
                isset($_POST['Change' . $p . 'HTSensor']) ||
                isset($_POST['Change' . $p . 'Co2Sensor']) ||
                isset($_POST[$p . 'secON']) ||
                isset($_POST['ChangeTimer' . $p]) || 
                isset($_POST['Timer' . $p . 'StateChange']) ||
                isset($_POST['Change' . $p . 'TempPID']) ||
                isset($_POST['Change' . $p . 'HumPID']) ||
                isset($_POST['Change' . $p . 'Co2PID']) ||
                isset($_POST['Change' . $p . 'TempOR']) ||
                isset($_POST['Change' . $p . 'HumOR']) ||
                isset($_POST['Change' . $p . 'Co2OR'])) {
            if ($_SESSION['user_name'] != 'guest') {

                // Set HT sensor variables
                if (isset($_POST['Change' . $p . 'HTSensor'])) {
                    $sensorname = str_replace(' ', '', $_POST['sensorht' . $p . 'name']);
                    $sensordevice = str_replace(' ', '', $_POST['sensorht' . $p . 'device']);
                    $sensorpin = str_replace(' ', '', $_POST['sensorht' . $p . 'pin']);
                    $sensorperiod = str_replace(' ', '', $_POST['sensorht' . $p . 'period']);
                    if (isset($_POST['sensorht' . $p . 'activated'])) $sensoractivated = 1;
                    else $sensoractivated = 0;
                    if (isset($_POST['sensorht' . $p . 'graph'])) $sensorgraph = 1;
                    else $sensorgraph = 0;
                    $editconfig = "$mycodo_client --modhtsensor $p $sensorname $sensordevice $sensorpin $sensorperiod $sensoractivated $sensorgraph";
                    shell_exec($editconfig);
                }
                
                // Set CO2 sensor variables
                if (isset($_POST['Change' . $p . 'Co2Sensor'])) {
                    $sensorname = str_replace(' ', '', $_POST['sensorco2' . $p . 'name']);
                    $sensordevice = str_replace(' ', '', $_POST['sensorco2' . $p . 'device']);
                    $sensorpin = str_replace(' ', '', $_POST['sensorco2' . $p . 'pin']);
                    $sensorperiod = str_replace(' ', '', $_POST['sensorco2' . $p . 'period']);
                    if (isset($_POST['sensorco2' . $p . 'activated'])) $sensoractivated = 1;
                    else $sensoractivated = 0;
                    if (isset($_POST['sensorco2' . $p . 'graph'])) $sensorgraph = 1;
                    else $sensorgraph = 0;
                    $editconfig = "$mycodo_client --modco2sensor $p $sensorname $sensordevice $sensorpin $sensorperiod $sensoractivated $sensorgraph";
                    shell_exec($editconfig);
                }
            
                // Request Temperature PID override to be turned on or off
                if (isset($_POST['Change' . $p . 'TempOR'])) {
                    $tempor = $_POST['Change' . $p . 'TempOR'];
                    $editconfig = "$mycodo_client --modtempOR $p $tempor";
                    shell_exec($editconfig);
                }
                
                // Request Humidity PID override to be turned on or off
                if (isset($_POST['Change' . $p . 'HumOR'])) {
                    $humor = $_POST['Change' . $p . 'HumOR'];
                    $editconfig = "$mycodo_client --modhumOR $p $humor";
                    shell_exec($editconfig);
                }
                
                // Request CO2 PID override to be turned on or off
                if (isset($_POST['Change' . $p . 'Co2OR'])) {
                    $co2or = $_POST['Change' . $p . 'Co2OR'];
                    $editconfig = "$mycodo_client --modco2OR $p $co2or";
                    shell_exec($editconfig);
                }
                
                // Request the Temperature PID variables be changed
                if (isset($_POST['Change' . $p . 'TempPID'])) {
                    $temprelay  = $_POST['Set' . $p . 'TempRelay'];
                    $tempset  = $_POST['Set' . $p . 'TempSet'];
                    $temp_p  = $_POST['Set' . $p . 'Temp_P'];
                    $temp_i  = $_POST['Set' . $p . 'Temp_I'];
                    $temp_d  = $_POST['Set' . $p . 'Temp_D'];
                    $tempperiod = $_POST['Set' . $p . 'TempPeriod'];
                    $editconfig = "$mycodo_client --modtempPID $p $temprelay $tempset $temp_p $temp_i $temp_d $tempperiod";
                    shell_exec($editconfig);
                }
                
                // Request the Humidity PID variables be changed
                if (isset($_POST['Change' . $p . 'HumPID'])) {
                    $humrelay  = $_POST['Set' . $p . 'HumRelay'];
                    $humset  = $_POST['Set' . $p . 'HumSet'];
                    $hum_p  = $_POST['Set' . $p . 'Hum_P'];
                    $hum_i  = $_POST['Set' . $p . 'Hum_I'];
                    $hum_d  = $_POST['Set' . $p . 'Hum_D'];
                    $humperiod = $_POST['Set' . $p . 'HumPeriod'];
                    $editconfig = "$mycodo_client --modhumPID $p $humrelay $humset $hum_p $hum_i $hum_d $humperiod";
                    shell_exec($editconfig);
                }
                
                // Request the CO2 PID variables be changed
                if (isset($_POST['Change' . $p . 'Co2PID'])) {
                    $co2relay  = $_POST['Set' . $p . 'Co2Relay'];
                    $co2set  = $_POST['Set' . $p . 'Co2Set'];
                    $co2_p  = $_POST['Set' . $p . 'Co2_P'];
                    $co2_i  = $_POST['Set' . $p . 'Co2_I'];
                    $co2_d  = $_POST['Set' . $p . 'Co2_D'];
                    $co2period = $_POST['Set' . $p . 'Co2Period'];
                    $editconfig = "$mycodo_client --modco2PID $p $co2relay $co2set $co2_p $co2_i $co2_d $co2period";
                    shell_exec($editconfig);
                }
                
                // Relay has been selected to be turned on or off
                if (isset($_POST['R' . $p])) {
                    $name = ${"relay" . $p . "name"};
                    $pin = ${"relay" . $p . "pin"};
                    if(${"relay" . $p . "trigger"} == 0) $trigger_state = 'LOW';
                    else $trigger_state = 'HIGH';
                    if ($_POST['R' . $p] == 0) $desired_state = 'LOW';
                    else $desired_state = 'HIGH';
                    
                    $GPIO_state = shell_exec("$gpio_path -g read $pin");
                    if ($GPIO_state == 0 && $trigger_state == 'HIGH') $actual_state = 'LOW';
                    else if ($GPIO_state == 0 && $trigger_state == 'LOW') $actual_state = 'HIGH';
                    else if ($GPIO_state == 1 && $trigger_state == 'HIGH') $actual_state = 'HIGH';    
                    else if ($GPIO_state == 1 && $trigger_state == 'LOW') $actual_state = 'LOW';
                    
                    if ($actual_state == 'LOW' && $desired_state == 'LOW') {
                        $error_code = 'already_off';
                    } else if ($actual_state == 'HIGH' && $desired_state == 'HIGH') {
                        $error_code = 'already_on';
                    } else {
                        if ($desired_state == 'HIGH') $desired_state = 1;
                        else $desired_state = 0;
                        $gpio_write = "$mycodo_client -r $p $desired_state";
                        shell_exec($gpio_write);
                    }
                }
                
                // Relay has been selected to be turned on for a number of seconds
                if (isset($_POST[$p . 'secON'])) {
                    $name = ${"relay" . $p . "name"};
                    $pin = ${"relay" . $p . "pin"};
                    if(${"relay" . $p . "trigger"} == 0) $trigger_state = 'LOW';
                    else $trigger_state = 'HIGH';
                    if ($_POST['R' . $p] == 0) $desired_state = 'LOW';
                    else $desired_state = 'HIGH';
                    
                    $GPIO_state = shell_exec("$gpio_path -g read $pin");
                    if ($GPIO_state == 0 && $trigger_state == 'HIGH') $actual_state = 'LOW';
                    else if ($GPIO_state == 0 && $trigger_state == 'LOW') $actual_state = 'HIGH';
                    else if ($GPIO_state == 1 && $trigger_state == 'HIGH') $actual_state = 'HIGH';    
                    else if ($GPIO_state == 1 && $trigger_state == 'LOW') $actual_state = 'LOW';
                    $seconds_on = $_POST['sR' . $p];
                    
                    if (!is_numeric($seconds_on) || $seconds_on < 2 || $seconds_on != round($seconds_on)) {
                        echo "<div class=\"error\">Error: Relay $p ($name): Seconds must be a positive integer >1</div>";
                    } else if ($actual_state == 'HIGH' && $desired_state == 'HIGH') {
                        $error_code = 'already_on';
                    } else {
                        $relay_on_sec = "$mycodo_client -r $p $seconds_on";
                        shell_exec($relay_on_sec);
                    }
                }
                
                if ((isset($_POST['ChangeTimer' . $p]) || isset($_POST['Timer' . $p . 'StateChange'])) && $_SESSION['user_name'] != 'guest') {
                    
                    $timerrelay = $_POST['Timer' . $p . 'Relay'];
                    $timeron = $_POST['Timer' . $p . 'On'];
                    $timeroff = $_POST['Timer' . $p . 'Off'];
                        
                     // Set timer variables
                    if (isset($_POST['ChangeTimer' . $p])) {
                        $timerstate = ${'timer' . $p . 'state'};
                        $changetimer = "$mycodo_client --modtimer $p $timerstate $timerrelay $timeron $timeroff";
                        shell_exec($changetimer);
                    } else if (isset($_POST['ChangeTimer' . $p]) && $_SESSION['user_name'] == 'guest') $error_code = 'guest';
                    
                    // Set timer state
                    if (isset($_POST['Timer' . $p . 'StateChange'])) {
                        $timerstate = $_POST['Timer' . $p . 'StateChange'];
                        $changetimer = "$mycodo_client --modtimer $p $timerstate $timerrelay $timeron $timeroff";
                        shell_exec($changetimer);
                    }
                }
            } else $error_code = 'guest';
        }
    }
    
    if (isset($_POST['WriteHTSensorLog']) || isset($_POST['WriteCo2SensorLog']) ||
            isset($_POST['ModRelayPin']) || isset($_POST['ModRelayName']) ||
            isset($_POST['ModRelayTrigger']) || isset($_POST['Auth']) ||
            isset($_POST['Capture']) || isset($_POST['start-stream']) ||
            isset($_POST['stop-stream']) || isset($_POST['ChangeNoRelays']) ||
            isset($_POST['ChangeNoHTSensors']) || isset($_POST['ChangeNoCo2Sensors']) ||
            isset($_POST['ChangeNoTimers']) || isset($_POST['ChangeNotify'])) {
        if ($_SESSION['user_name'] != 'guest') {
            if (isset($_POST['Capture'])) {
                if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) shell_exec("$stream_exec stop");
                if (isset($_POST['lighton'])) {
                    $lightrelay = $_POST['lightrelay'];
                    if (${"relay" . $lightrelay . "trigger"} == 1) $trigger = 1;
                    else $trigger = 0;
                    $capture_output = shell_exec("$still_exec " . ${'relay' . $lightrelay . "pin"} . " $trigger 2>&1; echo $?");
                } else $capture_output = shell_exec("$still_exec 2>&1; echo $?");
            }
            if (isset($_POST['start-stream'])) {
                if (file_exists($lock_raspistill) || file_exists($lock_mjpg_streamer)) {
                echo 'Lock files already present. Press \'Stop Stream\' to kill processes and remove lock files.<br>';
                } else {
                    if (isset($_POST['lighton'])) {
                        $lightrelay = $_POST['lightrelay'];
                        if (${"relay" . $lightrelay . "trigger"} == 1) $trigger = 1;
                        else $trigger = 0;
                        shell_exec("$stream_exec start " . ${'relay' . $lightrelay . "pin"} . " $trigger > /dev/null &");
                        sleep(1);
                    } else {
                        shell_exec("$stream_exec start > /dev/null &");
                        sleep(1);
                    }
                }
            }
            if (isset($_POST['stop-stream'])) {
                if (isset($_POST['lighton'])) {
                    $lightrelay = $_POST['lightrelay'];
                    if (${"relay" . $lightrelay . "trigger"} == 1) $trigger = 0;
                    else $trigger = 1;
                    shell_exec("$stream_exec stop " . ${'relay' . $lightrelay . "pin"} . " $trigger > /dev/null &");
                } else shell_exec("$stream_exec stop");
                sleep(1);
            }
            
            // Request HT sensor read log write
             if (isset($_POST['WriteHTSensorLog'])) {
                $editconfig = "$mycodo_client --writehtsensorlog 0";
                shell_exec($editconfig);
            }
            
            // Request CO2 sensor read and log write
             if (isset($_POST['WriteCo2SensorLog'])) {
                $editconfig = "$mycodo_client --writeco2sensorlog 0";
                shell_exec($editconfig);
            }
            
            // Request the relay name(s) be renamed
            if (isset($_POST['ModRelayName'])) {
                for ($i = 1; $i <= 8; $i++) {
                    if (isset($_POST['relay' . $i . 'name'])) {
                        ${'relay' . $i . 'name'} = str_replace(' ', '', $_POST['relay' . $i . 'name']);
                    }
                }
                $editconfig = "$mycodo_client --modrelaynames $relay1name $relay2name $relay3name $relay4name $relay5name $relay6name $relay7name $relay8name";
                shell_exec($editconfig);
            }
            
            // Request the relay pin(s) be renumbered
            if (isset($_POST['ModRelayPin'])) {
                for ($i = 1; $i <= 8; $i++) {
                    if (isset($_POST['relay' . $i . 'pin'])) {
                        ${'relay' . $i . 'pin'} = $_POST['relay' . $i . 'pin'];
                    }
                }
                $editconfig = "$mycodo_client --modrelaypins $relay1pin $relay2pin $relay3pin $relay4pin $relay5pin $relay6pin $relay7pin $relay8pin";
                shell_exec($editconfig);
            }
            
            // Request the relay trigger(s) be renumbered
            if (isset($_POST['ModRelayTrigger'])) {
                for ($i = 1; $i <= 8; $i++) {
                    if (isset($_POST['relay' . $i . 'trigger'])) {
                        ${'relay' . $i . 'trigger'} = $_POST['relay' . $i . 'trigger'];
                    }
                }
                $editconfig = "$mycodo_client --modrelaytrigger $relay1trigger $relay2trigger $relay3trigger $relay4trigger $relay5trigger $relay6trigger $relay7trigger $relay8trigger";
                shell_exec($editconfig);
            }
            
            // Change number of relays
            if (isset($_POST['ChangeNoRelays'])) {
                $numrelays = $_POST['numrelays'];
                $editconfig = "$mycodo_client --modvar numRelays $numrelays";
                shell_exec($editconfig);
            }
            
            // Change number of HT sensors
            if (isset($_POST['ChangeNoHTSensors'])) {
                $numhtsensors = $_POST['numhtsensors'];
                $editconfig = "$mycodo_client --modvar numHTSensors $numhtsensors";
                shell_exec($editconfig);
            }
            
            // Change number of CO2 sensors
            if (isset($_POST['ChangeNoCo2Sensors'])) {
                $numco2sensors = $_POST['numco2sensors'];
                $editconfig = "$mycodo_client --modvar numCo2Sensors $numco2sensors";
                shell_exec($editconfig);
            }
            
            // Change number of timers
            if (isset($_POST['ChangeNoTimers'])) {
                $numtimers = $_POST['numtimers'];
                $editconfig = "$mycodo_client --modvar numTimers $numtimers";
                shell_exec($editconfig);
            }
            
            // Change email notify settings
            if (isset($_POST['ChangeNotify'])) {
                $smtp_host  = $_POST['smtp_host'];
                $smtp_port  = $_POST['smtp_port'];
                $smtp_user  = $_POST['smtp_user'];
                $smtp_pass  = $_POST['smtp_pass'];
                $email_from  = $_POST['email_from'];
                $email_to  = $_POST['email_to'];
                $editconfig = "$mycodo_client --modvar smtp_host $smtp_host smtp_port $smtp_port smtp_user $smtp_user smtp_pass $smtp_pass email_from $email_from email_to $email_to";
                shell_exec($editconfig);
            }
        } else $error_code = 'guest';
    }
      
    $config_contents = file_get_contents($config_file);
    $config_rows = explode("\n", $config_contents);
    foreach($config_rows as $row => $data) {
        $row_data = explode(' = ', $data);
        if (isset($row_data[1])) {
            ${$row_data[0]} = $row_data[1];
        }
    }
    
    $last_ht_sensor[1] = `awk '$10 == 1' /var/tmp/sensor-ht.log | tail -n 1`;
    $last_ht_sensor[2] = `awk '$10 == 2' /var/tmp/sensor-ht.log | tail -n 1`;
    $last_ht_sensor[3] = `awk '$10 == 3' /var/tmp/sensor-ht.log | tail -n 1`;
    $last_ht_sensor[4] = `awk '$10 == 4' /var/tmp/sensor-ht.log | tail -n 1`;
    
    for ($p = 1; $p <= $numhtsensors; $p++) {
        $sensor_explode = explode(" ", $last_ht_sensor[$p]);
        $t_c[$p] = $sensor_explode[6];
        $hum[$p] = $sensor_explode[7];
        $t_f[$p] = round(($t_c[$p]*(9/5) + 32), 1);
        $dp_c[$p] = substr($sensor_explode[8], 0, -1);
        $dp_f[$p] = round(($dp_c[$p]*(9/5) + 32), 1);
        $settemp_f[$p] = round((${'temp' . $p . 'set'}*(9/5) + 32), 1);
    }
    
    $last_co2_sensor[1] = `awk '$8 == 1' /var/tmp/sensor-co2.log | tail -n 1`;
    $last_co2_sensor[2] = `awk '$8 == 2' /var/tmp/sensor-co2.log | tail -n 1`;
    $last_co2_sensor[3] = `awk '$8 == 3' /var/tmp/sensor-co2.log | tail -n 1`;
    $last_co2_sensor[4] = `awk '$8 == 4' /var/tmp/sensor-co2.log | tail -n 1`;
    
    for ($p = 1; $p <= $numco2sensors; $p++) {
        $sensor_explode = explode(" ", $last_co2_sensor[$p]);
        $co2[$p] = $sensor_explode[6];
    }
    
    $time_now = `date +"%Y-%m-%d %H:%M:%S"`;
    $time_last = `tail -n 1 $sensor_ht_log`;
    $time_explode = explode(" ", $time_last);
    $time_last = $time_explode[0] . '-' . $time_explode[1] . '-' . $time_explode[2] . ' ' . $time_explode[3] . ':' . $time_explode[4] . ':' . $time_explode[5];
?>
<!doctype html>
<html lang="en" class="no-js">
<head>
    <title>Mycodo</title>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex">
	<link href='http://fonts.googleapis.com/css?family=PT+Sans:400,700' rel='stylesheet' type='text/css'>
	<link rel="stylesheet" href="css/reset.css">
	<link rel="stylesheet" href="css/style.css">
	<script src="js/modernizr.js"></script>
    <script type="text/javascript">
        function open_legend() {
            window.open("image.php?span=legend-small","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=250, height=300");
        }
        function open_legend_full() {
            window.open("image.php?span=legend-full","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=820, height=550");
        }
    </script>
    <?php include_once("analyticstracking.php") ?>
    <?php
        if (isset($_GET['r']) && ($_GET['r'] == 1)) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";
    ?>
</head>
<body>
<div class="cd-tabs">
<?php
// Ensures error only displayed once
switch ($error_code) {
    case "guest":
        echo "<span class=\"error\">You cannot perform that task as a guest</span>";
        break;
    case "already_on":
        echo "<div class=\"error\">Error: Can't turn relay On, it's already On</div>";
        break;
    case "already_off":
        echo "<div class=\"error\">Error: Can't turn relay Off, it's already Off</div>";
        break;
}
$error_code = "no";
?>
<div class="main-wrapper">
    <div class="header">
        <div style="float: left;">
            <img style="margin: 0 0.2em 0 0.2em; width: 50px; height: 50px;" src="<?php echo $login->user_gravatar_image_tag; ?>">
        </div>
        <div style="float: left;">
            <div>
                User: <?php echo $_SESSION['user_name']; ?>
            </div>
            <?php if ($_SESSION['user_name'] != 'guest') { ?>
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
        <div style="padding-bottom: 0.1em;"><?php
            if ($daemon_check) echo '<input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="daemon_change" value="0"> Daemon';
            else echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="daemon_change" value="1"> Daemon';
            ?></div>
        <div style="padding-bottom: 0.1em;"><?php if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) {
                    echo '<input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="" value="0">';
                } else echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0">';?> Stream</div>
        <div><?php
            if (isset($_GET['r'])) { ?><div style="display:inline-block; vertical-align:top;"><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="" value="0"></div><div style="display:inline-block; padding-left: 0.3em;"><div>Refresh</div><div><span style="font-size: 0.7em">(<?php echo $tab; ?>)</span></div></div><?php 
            } else echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0"> Refresh'; ?></div>
    </div>
    <div style="float: left; vertical-align:top; height: 4.5em; padding: 1em 0.8em 0 0.3em;">
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;">Time now: <?php echo $time_now; ?></div>
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;">Last read: <?php echo $time_last; ?></div>
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;"><?php echo $uptime; ?></div>
    </div>
    <?php
    for ($s = 1; $s <= $numhtsensors; $s++) {
        if (${'sensorht' . $s . 'activated'} == 1) {
    ?>
    <div class="header">
    <table>
        <tr>
            <td colspan=2 align=center style="border-bottom:1pt solid black;"><?php echo $s . ": " . ${'sensorht' . $s . 'name'}; ?></td>
        </tr>
        <tr>
            <td>
    <div style="font-size: 0.8em; padding-right: 0.5em;"><?php
            echo "Now<br><span title=\"" . number_format((float)$t_f[$s], 1, '.', '') . "&deg;F\">" . number_format((float)$t_c[$s], 1, '.', '') . "&deg;C</span>";
            echo "<br>" . number_format((float)$hum[$s], 1, '.', '') . "%"; 
        ?>
    </div>
            </td>
            <td>
    <div style="font-size: 0.8em;"><?php
            echo "Set<br><span title=\"" . number_format((float)$settemp_f[$s], 1, '.', '') ."&deg;F\">" . number_format((float)${'temp' . $s . 'set'}, 1, '.', '') . "&deg;C";
            echo "<br>" . number_format((float)${'hum' . $s . 'set'}, 1, '.', '') . "%";
            ?>
    </div>
            </td>
        </tr>
    </table>
    </div>
    <?php
        }
    }
    ?>
    
    <?php
    for ($s = 1; $s <= $numco2sensors; $s++) {
        if (${'sensorco2' . $s . 'activated'} == 1) {
    ?>
    <div class="header">
    <table>
        <tr>
            <td colspan=2 align=center style="border-bottom:1pt solid black;">
                <?php echo $s . ": " . ${'sensorco2' . $s . 'name'}; ?>
            </td>
        </tr>
        <tr>
            <td>
                <div style="font-size: 0.8em; padding-right: 0.5em;"><?php echo "Now<br>" . $co2[$s]; ?></div>
            </td>
            <td>
                <div style="font-size: 0.8em;"><?php echo "Set<br>" . ${'co2' . $s . 'set'}; ?></div>
            </td>
        </tr>
    </table>
    </div>
    <?php
        }
    }
    ?>
</div>
<div style="clear: both; padding-top: 15px;"></div>
	<nav>
		<ul class="cd-tabs-navigation">
			<li><a data-content="main" <?php if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'main')) echo "class=\"selected\""; ?> href="#0">Main</a></li>
			<li><a data-content="configure" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'config') echo "class=\"selected\""; ?> href="#0">Configure</a></li>
			<li><a data-content="graph" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'graph') echo "class=\"selected\""; ?> href="#0">Graphs</a></li>
			<li><a data-content="camera" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'camera') echo "class=\"selected\""; ?> href="#0">Camera</a></li>
			<li><a data-content="log" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'log') echo "class=\"selected\""; ?> href="#0">Log</a></li>
			<li><a data-content="advanced" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'adv') echo "class=\"selected\""; ?> href="#0">Advanced</a></li>
		</ul> <!-- cd-tabs-navigation -->
	</nav>
	<ul class="cd-tabs-content">
		<li data-content="main" <?php if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'main')) echo "class=\"selected\""; ?>>
        <FORM action="?tab=main<?php 
            if (isset($_GET['page'])) echo "&page=" . $_GET['page'];
            if (isset($_GET['Refresh']) || isset($_POST['Refresh'])) echo "&Refresh=1";
            if (isset($_GET['r'])) echo "&r=" . $_GET['r'];
            ?>" method="POST">
            <div>
                <div style="padding-top: 0.5em;">
                    <div style="float: left; padding: 0 1.5em 1em 0.5em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">Auto Refresh</div>
                        <div style="text-align: center;"><?php
                            if (isset($_GET['r']) && $_GET['r'] == 1) {
                                if (empty($page)) echo '<a href="?tab=main">OFF</a> | <span class="on">ON</span>';
                                else echo '<a href="?tab=main&page=' . $page . '">OFF</a> | <span class="on">ON</span>';
                            } else {
                                if (empty($page)) echo '<span class="off">OFF</span> | <a href="?tab=main&Refresh=1&r=1">ON</a>';
                                echo '<span class="off">OFF</span> | <a href="?tab=main&page=' . $page . '&Refresh=1&r=1">ON</a>';
                            }
                        ?>
                        </div>
                    </div>
                    <div style="float: left; padding: 0 2em 1em 0.5em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">Refresh</div>
                        <div>
                            <div style="float: left; padding-right: 0.1em;">
                                <input type="button" onclick='location.href="?tab=main<?php
                                if (isset($_GET['page'])) { if ($_GET['page']) echo "&page=" . $page; }
                                echo "&Refresh=1";
                                if (isset($_GET['r'])) { if ($_GET['r'] == 1) echo "&r=1"; } ?>"' value="Graph">
                            </div>
                            <div style="float: left; padding-right: 0.1em;">
                                <input type="button" onclick='location.href="?tab=main<?php
                                if (isset($_GET['page'])) { if ($_GET['page']) echo "&page=" . $page; }
                                if (isset($_GET['r'])) { if ($_GET['r'] == 1) echo "&r=1"; } ?>"' value="Page">
                            </div>
                            <div style="float: left;">
                                <input type="submit" name="WriteSensorLog" value="Sensors" title="Take a new temperature and humidity reading">
                            </div>
                        </div>
                    </div>
                    <div style="float: left; padding: 0.2em 0 1em 0.5em">
                        <div>
                            <div class="Row-title">Separate</div>
                            <?php
                            
                            menu_item('Separate1h', '1 Hour', $page);
                            menu_item('Separate6h', '6 Hours', $page);
                            menu_item('Separate1d', '1 Day', $page);
                            menu_item('Separate3d', '3 Days', $page);
                            menu_item('Separate1w', '1 Week', $page);
                            menu_item('Separate1m', '1 Month', $page);
                            menu_item('Separate3m', '3 Months', $page);
                            menu_item('Main', 'Main', $page);
                        ?>
                        </div>
                        <div>
                            <div class="Row-title">Combined</div>
                            <?php
                            menu_item('Combined1h', '1 Hour', $page);
                            menu_item('Combined6h', '6 Hours', $page);
                            menu_item('Combined1d', '1 Day', $page);
                            menu_item('Combined3d', '3 Days', $page);
                            menu_item('Combined1w', '1 Week', $page);
                            menu_item('Combined1m', '1 Month', $page);
                            menu_item('Combined3m', '3 Months', $page);
                        ?>
                        </div>
                    </div>
                </div>
                <div style="clear: both;"></div>
                <div>
                    <?php
                    $ref = 0;
                    if (isset($_GET['Refresh']) == 1) $ref = 1;
                    
                    if (!isset($_SESSION["ID"])) {
                        $id = uniqid();
                        $_SESSION["ID"] = $id;
                        $ref = 1;
                    } else $id = $_SESSION["ID"];
                    
                    if (strpos($_GET['page'], 'Combined') === 0) {
                        echo "<div style=\"padding: 1em 0 3em 0;\"><img class=\"main-image\" style=\"max-width:100%;height:auto;\" src=image.php?span=";
                        if ($_GET['page'] == 'Combined1h') {
                            $editconfig = $mycodo_client . ' --graph combined1h ' . $id . ' 0';
                            if ($ref) shell_exec($editconfig);
                            echo "combined1h&mod=" . $id . ">";
                        } else if ($_GET['page'] == 'Combined6h') {
                            $editconfig = $mycodo_client . ' --graph combined6h ' . $id . ' 0';
                            if ($ref) shell_exec($editconfig);
                            echo "combined6h&mod=" . $id . ">";
                        } else if ($_GET['page'] == 'Combined1d') {
                            $editconfig = $mycodo_client . ' --graph combined1d ' . $id . ' 0';
                            if ($ref) shell_exec($editconfig);
                            echo "combined1d&mod=" . $id . ">";
                        } else if ($_GET['page'] == 'Combined3d') {
                            $editconfig = $mycodo_client . ' --graph combined3d ' . $id . ' 0';
                            if ($ref) shell_exec($editconfig);
                            echo "combined3d&mod=" . $id . ">";
                        } else if ($_GET['page'] == 'Combined1w') {
                            $editconfig = $mycodo_client . ' --graph combined1w ' . $id . ' 0';
                            if ($ref) shell_exec($editconfig);
                            echo "combined1w&mod=" . $id . ">";
                        } else if ($_GET['page'] == 'Combined1m') {
                            $editconfig = $mycodo_client . ' --graph combined1m ' . $id . ' 0';
                            if ($ref) shell_exec($editconfig);
                            echo "combined1m&mod=" . $id . ">";
                        } else if ($_GET['page'] == 'Combined3m') {
                            $editconfig = $mycodo_client . ' --graph combined3m ' . $id . ' 0';
                            if ($ref) shell_exec($editconfig);
                            echo "combined3m&mod=" . $id . ">";
                        }
                        sleep(3);
                        echo "</div>";
                    } else {
                        for ($n = 1; $n <= $numhtsensors; $n++ ) {
                            if (isset($_GET['page']) and ${'sensorht' . $n . 'graph'} == 1) {
                                echo "<div style=\"padding: 1em 0 3em 0;\"><img class=\"main-image\" style=\"max-width:100%;height:auto;\" src=image.php?span=";
                                switch ($_GET['page']) {
                                    case 'Main':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htdayweek ' . $id . ' ' . $n);
                                        echo "htmain&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1h':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htseparate1h ' . $id . ' ' . $n);
                                        echo "htseparate1h&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate6h':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htseparate6h ' . $id . ' ' . $n);
                                        echo "htseparate6h&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1d':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htseparate1d ' . $id . ' ' . $n);
                                        echo "htseparate1d&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate3d':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htseparate3d ' . $id . ' ' . $n);
                                        echo "htseparate3d&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1w':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htseparate1w ' . $id . ' ' . $n);
                                        echo "htseparate1w&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1m':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htseparate1m ' . $id . ' ' . $n);
                                        echo "htseparate1m&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate3m':
                                        if ($ref) shell_exec($mycodo_client . ' --graph htseparate3m ' . $id . ' ' . $n);
                                        echo "htseparate3m&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    default:
                                        if ($ref) shell_exec($mycodo_client . ' --graph htdayweek ' . $id . ' ' . $n);
                                        echo "htmain&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                }
                                echo "</div>";
                            } else if (${'sensorht' . $n . 'graph'} == 1) {
                                echo "<div style=\"padding: 1em 0 3em 0;\"><img class=\"main-image\" style=\"max-width:100%;height:auto;\" src=image.php?span=";
                                if ($ref) shell_exec($mycodo_client . ' --graph htdayweek ' . $id . ' ' . $n);
                                echo "htmain&mod=" . $id . "&sensor=" . $n . "></div>";
                            }
                            if ($n != $numhtsensors || $sensorco21graph == 1 || $sensorco22graph == 1 || $sensorco23graph == 1 || $sensorco24graph == 1) {
                                echo "<hr class=\"fade\"/>"; }
                        }
                        for ($n = 1; $n <= $numco2sensors; $n++ ) {
                            if (isset($_GET['page']) and ${'sensorco2' . $n . 'graph'} == 1) {
                                echo "<div style=\"padding: 1em 0 3em 0;\"><img class=\"main-image\" style=\"max-width:100%;height:auto;\" src=image.php?span=";
                                switch ($_GET['page']) {
                                    case 'Main':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2dayweek ' . $id . ' ' . $n);
                                        echo "co2main&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1h':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2separate1h ' . $id . ' ' . $n);
                                        echo "co2separate1h&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate6h':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2separate6h ' . $id . ' ' . $n);
                                        echo "co2separate6h&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1d':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2separate1d ' . $id . ' ' . $n);
                                        echo "co2separate1d&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate3d':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2separate3d ' . $id . ' ' . $n);
                                        echo "co2separate3d&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1w':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2separate1w ' . $id . ' ' . $n);
                                        echo "co2separate1w&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate1m':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2separate1m ' . $id . ' ' . $n);
                                        echo "co2separate1m&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    case 'Separate3m':
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2separate3m ' . $id . ' ' . $n);
                                        echo "co2separate3m&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                    default:
                                        if ($ref) shell_exec($mycodo_client . ' --graph co2dayweek ' . $id . ' ' . $n);
                                        echo "co2main&mod=" . $id . "&sensor=" . $n . ">";
                                        break;
                                }
                                echo "</div>";
                            } else if (${'sensorco2' . $n . 'graph'} == 1) {
                                echo "<div style=\"padding: 1em 0 3em 0;\"><img class=\"main-image\" style=\"max-width:100%;height:auto;\" src=image.php?span=";
                                if ($ref) shell_exec($mycodo_client . ' --graph co2dayweek ' . $id . ' ' . $n);
                                echo "co2main&mod=" . $id . "&sensor=" . $n . "></div>";
                            }
                            if ($n != $numco2sensors) { echo "<hr class=\"fade\"/>"; }
                        }
                    }
                    ?>
                </div>
                <div style="width: 100%; padding: 1em 0 0 0; text-align: center;">
                    Legend: <a href="javascript:open_legend()">Brief</a> / <a href="javascript:open_legend_full()">Full</a>
                    <div style="text-align: center; padding-top: 0.5em;"><a href="https://github.com/kizniche/Automated-Mushroom-Cultivator" target="_blank">Mycodo on GitHub</a></div>
                </div>
                </div>
            </form>
		</li>

		<li data-content="configure" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'config') echo "class=\"selected\""; ?>>
            <FORM action="?tab=config<?php
                if (isset($_GET['page'])) echo "&page=" . $_GET['page'];
                if (isset($_GET['r'])) echo "&r=" . $_GET['r'];
            ?>" method="POST">
            <div style="padding-top: 0.5em;">
                <div style="float: left; padding: 0.0em 0.5em 1em 0;">
                    <div style="text-align: center; padding-bottom: 0.2em;">Auto Refresh</div>
                    <div style="text-align: center;"><?php
                        if (isset($_GET['r'])) {
                            if ($_GET['r'] == 1) echo "<a href=\"?tab=config\">OFF</a> | <span class=\"on\">ON</span>";
                            else echo "<span class=\"off\">OFF</span> | <a href=\"?tab=config&?r=1\">ON</a>";
                        } else echo "<span class=\"off\">OFF</span> | <a href=\"?tab=config&r=1\">ON</a>";
                    ?>
                    </div>
                </div>
                <div style="float: left; padding: 0.0em 0.5em 1em 0;">
                    <div style="float: left; padding-right: 2em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">Refresh</div>
                        <div style="float: left;">
                            <input type="submit" name="Refresh" value="Page" title="Refresh page">
                        </div>
                        <div style="float: left;">
                            <input type="submit" name="WriteSensorLog" value="Sensors" title="Take a new temperature and humidity reading">
                        </div>
                    </div>
                    <div style="float: left; padding-right: 1em;">
                        <div style="float: left; padding: 0 0 1em 1em;">
                            <div style="text-align: center; padding-bottom: 0.2em;">Relays</div>
                            <div>
                                <select name="numrelays">
                                    <option value="0" <?php if ($numrelays == 0) echo "selected=\"selected\""; ?>>0</option>
                                    <option value="1" <?php if ($numrelays == 1) echo "selected=\"selected\""; ?>>1</option>
                                    <option value="2" <?php if ($numrelays == 2) echo "selected=\"selected\""; ?>>2</option>
                                    <option value="3" <?php if ($numrelays == 3) echo "selected=\"selected\""; ?>>3</option>
                                    <option value="4" <?php if ($numrelays == 4) echo "selected=\"selected\""; ?>>4</option>
                                    <option value="5" <?php if ($numrelays == 5) echo "selected=\"selected\""; ?>>5</option>
                                    <option value="6" <?php if ($numrelays == 6) echo "selected=\"selected\""; ?>>6</option>
                                    <option value="7" <?php if ($numrelays == 7) echo "selected=\"selected\""; ?>>7</option>
                                    <option value="8" <?php if ($numrelays == 8) echo "selected=\"selected\""; ?>>8</option>
                                </select>
                                <input type="submit" name="ChangeNoRelays" value="Save">
                            </div>
                        </div>
                    </div>
                    <div style="float: left; padding-right: 1em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">CO<sub>2</sub> Sensors</div>
                        <div style="text-align: center;">
                            <select name="numco2sensors">
                                <option value="0" <?php if ($numco2sensors == 0) echo "selected=\"selected\""; ?>>0</option>
                                <option value="1" <?php if ($numco2sensors == 1) echo "selected=\"selected\""; ?>>1</option>
                                <option value="2" <?php if ($numco2sensors == 2) echo "selected=\"selected\""; ?>>2</option>
                                <option value="3" <?php if ($numco2sensors == 3) echo "selected=\"selected\""; ?>>3</option>
                                <option value="4" <?php if ($numco2sensors == 4) echo "selected=\"selected\""; ?>>4</option>
                            </select>
                            <input type="submit" name="ChangeNoCo2Sensors" value="Save">
                        </div>
                    </div>
                    <div style="float: left;">
                        <div style="text-align: center; padding-bottom: 0.2em;">HT Sensors</div>
                        <div style="text-align: center;"">
                            <select name="numhtsensors">
                                <option value="0" <?php if ($numhtsensors == 0) echo "selected=\"selected\""; ?>>0</option>
                                <option value="1" <?php if ($numhtsensors == 1) echo "selected=\"selected\""; ?>>1</option>
                                <option value="2" <?php if ($numhtsensors == 2) echo "selected=\"selected\""; ?>>2</option>
                                <option value="3" <?php if ($numhtsensors == 3) echo "selected=\"selected\""; ?>>3</option>
                                <option value="4" <?php if ($numhtsensors == 4) echo "selected=\"selected\""; ?>>4</option>
                            </select>
                            <input type="submit" name="ChangeNoHTSensors" value="Save">
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="clear: both;"></div>
            <div>
                <div style="padding-top: 1em;">
                    <div style="padding: 0 0 1em 0; font-weight: bold;">Relays</div>
                    <?php if ($numrelays > 0) { ?>
                    <table class="relays">
                        <tr>
                            <td align=center class="table-header">Relay<br>No.</td>
                            <td align=center class="table-header">Relay<br>Name</td>
                            <th align=center class="table-header">Current<br>State</th>
                            <td align=center class="table-header">Seconds<br>On</td>
                            <td align=center class="table-header">GPIO<br>Pin</td>
                            <td align=center class="table-header">Trigger<br>ON</td>
                        </tr>
                        <?php for ($i = 1; $i <= $numrelays; $i++) {
                                $name = ${"relay" . $i . "name"};
                                $pin = ${"relay" . $i . "pin"};
                                $trigger = ${"relay" . $i . "trigger"};
                                $read = "$gpio_path -g read $pin";
                        ?>
                        <tr>
                            <td align=center>
                                <?php echo ${'i'}; ?>
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $name; ?>" maxlength=12 size=10 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i; ?>"/>
                            </td>
                            <?php
                                if ((shell_exec($read) == 1 && $trigger == 0) || (shell_exec($read) == 0 && $trigger == 1)) {
                                    ?>
                                    <td class="onoff">
                                        <nobr><input type="image" style="height: 0.95em; vertical-align: middle;" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="R<?php echo $i; ?>" value="0"> | <button style="width: 3em;" type="submit" name="R<?php echo $i; ?>" value="1">ON</button></nobr>
                                    </td>
                                    <?php
                                } else {
                                    ?>
                                    <td class="onoff">
                                        <nobr><input type="image" style="height: 0.95em; vertical-align: middle;" src="/mycodo/img/on.jpg" alt="On" title="On" name="R<?php echo $i; ?>" value="1"> | <button style="width: 3em;" type="submit" name="R<?php echo $i; ?>" value="0">OFF</button></nobr>
                                    </td>
                                    <?php
                                }
                            ?>
                            <td>
                                 [<input type="text" maxlength=3 size=1 name="sR<?php echo $i; ?>" title="Number of seconds to turn this relay on"/><input type="submit" name="<?php echo $i; ?>secON" value="ON">]
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $pin; ?>" maxlength=2 size=1 name="relay<?php echo $i; ?>pin" title="GPIO pin using BCM numbering, connected to relay <?php echo $i; ?>"/>
                            </td>
                            <td align=center>
                                <select style="width: 65px;" name="relay<?php echo $i; ?>trigger">
                                    <option <?php if ($trigger == 1) echo "selected=\"selected\""; ?> value="1">HIGH</option>
                                    <option <?php if ($trigger == 0) echo "selected=\"selected\""; ?> value="0">LOW</option>
                                </select>
                            </td>
                        </tr>
                        <?php 
                        } }
                        ?>
                        <tr>
                            <td>
                            </td>
                            <td align=center>
                                <button type="submit" name="ModRelayName" value="1" title="Change relay names to the ones specified above (Do not use spaces)">Rename</button>
                            </td>
                            <td>
                            </td>
                            <td>
                            </td>
                            <td align=center>
                                <button type="submit" name="ModRelayPin" value="1" title="Change the (BCM) GPIO pins attached to relays to the ones specified above">Set</button>
                            </td>
                            <td align=center>
                                <button type="submit" name="ModRelayTrigger" value="1" title="Change the ON trigger state of the relays.">Set</button>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <?php if ($numhtsensors > 0) { ?>
                <div style="padding: 2.5em 0 1em 0; font-weight: bold;">Humidity & Temperature Sensors</div>
                <div style="padding-right: 1em;">
                    <?php for ($i = 1; $i <= $numhtsensors; $i++) {
                        $device = ${"sensorht" . $i . "device"};
                        ?>
                    <div style="padding-bottom: 0.5em;">
                        <table class="pid" style="width: 42em;">
                        <tr class="shade">
                            <td align=center>Sensor<br>No.</td>
                            <td align=center>Sensor<br>Name</td>
                            <td align=center>Sensor<br>Device</td>
                            <td align=center>GPIO<br>Pin</td>
                            <td align=center>Log Interval<br>(seconds)</td>
                            <td align=center>Activate<br>Logging</td>
                            <td align=center>Activate<br>Graphing</td>
                            </td></td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td class="shade" style="vertical-align: middle;" align=center>
                                <?php echo $i; ?>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${"sensorht" . $i . "name"}; ?>" maxlength=12 size=10 name="sensorht<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 80px;" name="sensorht<?php echo $i; ?>device">
                                    <option <?php if ($device == 'DHT11') echo "selected=\"selected\""; ?> value="DHT11">DHT11</option>
                                    <option <?php if ($device == 'DHT22') echo "selected=\"selected\""; ?> value="DHT22">DHT22</option>
                                    <option <?php if ($device == 'AM2302') echo "selected=\"selected\""; ?> value="AM2302">AM2302</option>
                                    <option <?php if ($device == 'Other') echo "selected=\"selected\""; ?>value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${"sensorht" . $i . "pin"}; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>pin" title="This is the GPIO pin connected to the DHT sensor"/>
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo ${"sensorht" . $i . "period"}; ?>" maxlength=3 size=1 name="sensorht<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorht<?php echo $i; ?>activated" value="1" <?php if (${'sensorht' . $i . 'activated'} == 1) echo "checked"; ?>> 
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorht<?php echo $i; ?>graph" value="1" <?php if (${'sensorht' . $i . 'graph'} == 1) echo "checked"; ?>> 
                            </td>
                            <td>
                                <input type="submit" name="Change<?php echo $i; ?>HTSensor" value="Set">
                            </td>
                        </tr>
                    </table>
                    </div>
               
                    <div style="padding-bottom: 2em;">
                    <table class="pid" style="width: 42em;">
                        <tr class="shade">
                            <td align=center>PID<br>Type</td>
                            <td align=center>Current<br>State</td>
                            <td style="vertical-align: middle;" align=center>Relay<br>No.</td>
                            <td align=center>PID<br>Set Point</td>
                            <td style="vertical-align: middle;" align=center>Interval<br>(seconds)</td>
                            <td style="vertical-align: middle;" align=center>P</td>
                            <td style="vertical-align: middle;" align=center>I</td>
                            <td style="vertical-align: middle;" align=center>D</td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td>Temperature</td>
                            <td class="onoff">
                                <?php
                                    if (${'temp' . $i . 'or'} == 1) {
                                        ?>
                                        <input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>TempOR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>TempOR" value="0">ON</button>
                                        <?php
                                    } else {
                                        ?>
                                        <input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>TempOR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>TempOR" value="1">OFF</button>
                                        <?php
                                    }
                                ?>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'temp' . $i . 'relay'}; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>TempRelay" title="This is the relay connected to the heating device"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'temp' . $i . 'set'}; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>TempSet" title="This is the desired temperature"/> °C
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo ${'temp' . $i . 'period'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'temp' . $i . 'p'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'temp' . $i . 'i'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'temp' . $i . 'd'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_D" title="This is the Derivative value of the PID"/>
                            </td>
                            <td>
                                <input type="submit" name="Change<?php echo $i; ?>TempPID" value="Set">
                            </td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td>Humidity</td>
                            <td class="onoff">
                            <?php
                                if (${'hum' . $i . 'or'} == 1) {
                                    ?>
                                    <input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>HumOR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>HumOR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?>
                                    <input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>HumOR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>HumOR" value="1">OFF</button>
                                    <?php
                                }
                            ?>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'hum' . $i . 'relay'}; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>HumRelay" title="This is the relay connected to your humidifying device"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'hum' . $i . 'set'}; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>HumSet" title="This is the desired humidity"/> %
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo ${'hum' . $i . 'period'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>HumPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another humidity reading and applying the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'hum' . $i . 'p'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'hum' . $i . 'i'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'hum' . $i . 'd'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_D" title="This is the Derivative value of the PID"/>
                            </td>
                            <td>
                                <input type="submit" name="Change<?php echo $i; ?>HumPID" value="Set">
                            </td>
                        </tr>
                    </table>
                    </div>
                <?php
                }
                ?>
                </div>
                <?php
                }
                ?>

                <?php if ($numco2sensors > 0) { ?>
                <div style="padding: 1.5em 0 1em 0; font-weight: bold;">CO<sub>2</sub> Sensors</div>
                <div style="padding-bottom: 3em; padding-right: 1em;">
                    <?php for ($i = 1; $i <= $numco2sensors; $i++) {
                        $device = ${"sensorco2" . $i . "device"};
                        ?>
                    <div style="padding-bottom: 0.5em;">
                        <table class="pid" style="width: 42em;">
                        <tr class="shade">
                            <td align=center>Sensor<br>No.</td>
                            <td align=center>Sensor<br>Name</td>
                            <td align=center>Sensor<br>Device</td>
                            <td align=center>GPIO<br>Pin</td>
                            <td align=center>Log Interval<br>(seconds)</td>
                            <td align=center>Activate<br>Logging</td>
                            <td align=center>Activate<br>Graphing</td>
                            </td></td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td class="shade" style="vertical-align: middle;" align=center>
                                <?php echo $i; ?>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${"sensorco2" . $i . "name"}; ?>" maxlength=12 size=10 name="sensorco2<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 80px;" name="sensorco2<?php echo $i; ?>device">
                                    <option <?php if ($device == 'K30') echo "selected=\"selected\""; ?> value="K30">K30</option>
                                    <option <?php if ($device == 'Other') echo "selected=\"selected\""; ?>value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${"sensorco2" . $i . "pin"}; ?>" maxlength=2 size=1 name="sensorco2<?php echo $i; ?>pin" title="This is the GPIO pin connected to the CO2 sensor"/>
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo ${"sensorco2" . $i . "period"}; ?>" maxlength=3 size=1 name="sensorco2<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorco2<?php echo $i; ?>activated" value="1" <?php if (${'sensorco2' . $i . 'activated'} == 1) echo "checked"; ?>> 
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorco2<?php echo $i; ?>graph" value="1" <?php if (${'sensorco2' . $i . 'graph'} == 1) echo "checked"; ?>> 
                            </td>
                            <td>
                                <input type="submit" name="Change<?php echo $i; ?>Co2Sensor" value="Set">
                            </td>
                        </tr>
                    </table>
                    </div>
               
                    <div style="padding-bottom: 2em;">
                    <table class="pid" style="width: 42em;">
                        <tr class="shade">
                            <td align=center>PID<br>Type</td>
                            <td align=center>Current<br>State</td>
                            <td style="vertical-align: middle;" align=center>Relay<br>No.</td>
                            <td align=center>PID<br>Set Point</td>
                            <td style="vertical-align: middle;" align=center>Interval<br>(seconds)</td>
                            <td style="vertical-align: middle;" align=center>P</td>
                            <td style="vertical-align: middle;" align=center>I</td>
                            <td style="vertical-align: middle;" align=center>D</td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td>CO<sub>2</sub></td>
                            <td class="onoff">
                                <?php
                                    if (${'co2' . $i . 'or'} == 1) {
                                        ?>
                                        <input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>Co2OR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>Co2OR" value="0">ON</button>
                                        <?php
                                    } else {
                                        ?>
                                        <input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>Co2OR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>Co2OR" value="1">OFF</button>
                                        <?php
                                    }
                                ?>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'co2' . $i . 'relay'}; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>Co2Relay" title="This is the relay connected to the device that modulates CO2"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'co2' . $i . 'set'}; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>Co2Set" title="This is the desired CO2 level"/> ppm
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo ${'co2' . $i . 'period'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2Period" title="This is the number of seconds to wait after the relay has been turned off before taking another CO2 reading and applying the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'co2' . $i . 'p'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'co2' . $i . 'i'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'co2' . $i . 'd'}; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2_D" title="This is the Derivative value of the PID"/>
                            </td>
                            <td>
                                <input type="submit" name="Change<?php echo $i; ?>Co2PID" value="Set">
                            </td>
                        </tr>
                    </table>
                    </div>
                <?php
                }
                ?>
                </div>
                <?php
                }
                ?>
                
            </div>
        </FORM>
		</li>

		<li data-content="graph" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'graph') echo "class=\"selected\""; ?>>
            <?php
            /* DateSelector*Author: Leon Atkinson */
            if (isset($_POST['SubmitDates']) and $_SESSION['user_name'] != 'guest') {
                if ($_POST['SubmitDates']) {
                    displayform();
                    $id2 = uniqid();
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
                    
                    if (is_positive_integer($_POST['graph-width']) and $_POST['graph-width'] <= 4000 and $_POST['graph-width']) {
                        $graph_width = $_POST['graph-width'];
                    } else $graph_width = 900;
                    
                    if ($_POST['MainType'] == 'Combined') {
                        echo `echo "set terminal png size $graph_width,1600
                        set xdata time
                        set timefmt \"%Y %m %d %H %M %S\"
                        set output \"$images/graph-cuscom-$id2.png\"
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
                        set style line 1 lc rgb '#7164a3' pt 0 ps 1 lt 1 lw 2
                        set style line 2 lc rgb '#599e86' pt 0 ps 1 lt 1 lw 2
                        set style line 3 lc rgb '#c3ae4f' pt 0 ps 1 lt 1 lw 2
                        set style line 4 lc rgb '#c3744f' pt 0 ps 1 lt 1 lw 2
                        set style line 5 lc rgb '#91180B' pt 0 ps 1 lt 1 lw 1
                        set style line 6 lc rgb '#582557' pt 0 ps 1 lt 1 lw 1
                        set style line 7 lc rgb '#04834C' pt 0 ps 1 lt 1 lw 1
                        set style line 8 lc rgb '#DC32E6' pt 0 ps 1 lt 1 lw 1
                        set style line 9 lc rgb '#957EF9' pt 0 ps 1 lt 1 lw 1
                        set style line 10 lc rgb '#CC8D9C' pt 0 ps 1 lt 1 lw 1
                        set style line 11 lc rgb '#717412' pt 0 ps 1 lt 1 lw 1
                        set style line 12 lc rgb '#0B479B' pt 0 ps 1 lt 1 lw 1
                        #set xlabel \"Date and Time\"
                        #set ylabel \"% Humidity\"
                        set multiplot layout 3, 1 title \"Combined Sensor Data - $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
                        set title \"Combined Temperatures\"
                        unset key
                        plot \"<awk '\\$10 == 1' $sensor_ht_log\" using 1:7 index 0 title \"T1\" w lp ls 1 axes x1y2, \\
                        \"<awk '\\$10 == 2' $sensor_ht_log\" using 1:7 index 0 title \"T2\" w lp ls 2 axes x1y2, \\
                        \"<awk '\\$10 == 3' $sensor_ht_log\" using 1:7 index 0 title \"T3\" w lp ls 3 axes x1y2, \\
                        \"<awk '\\$10 == 4' $sensor_ht_log\" using 1:7 index 0 title \"T4\" w lp ls 4 axes x1y2 \\
                        set key autotitle column
                        set title \"Combined Humidities\"
                        unset key
                        plot \"<awk '\\$10 == 1' $sensor_ht_log\" using 1:8 index 0 title \"RH1\" w lp ls 1 axes x1y1, \\
                        \"<awk '\\$10 == 2' $sensor_ht_log\" using 1:8 index 0 title \"RH2\" w lp ls 2 axes x1y1, \\
                        \"<awk '\\$10 == 3' $sensor_ht_log\" using 1:8 index 0 title \"RH3\" w lp ls 3 axes x1y1, \\
                        \"<awk '\\$10 == 4' $sensor_ht_log\" using 1:8 index 0 title \"RH4\" w lp ls 4 axes x1y1 \\
                        set key
                        set key autotitle column
                        set title \"Relay Run Time\"
                        plot \"$relay_log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 5 axes x1y1, \\
                        \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 6 axes x1y1, \\
                        \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 7 axes x1y1, \\
                        \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 8 axes x1y1, \\
                        \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 9 axes x1y1, \\
                        \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 10 axes x1y1, \\
                        \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 11 axes x1y1, \\
                        \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 12 axes x1y1 \\
                        unset multiplot" | gnuplot`;
                        echo "<div style=\"width: 100%; text-align: center; padding: 1em 0 3em 0;\"><img src=image.php?span=cuscom&mod=" . $id2 . "&sensor=" . $n . "></div>";
                    } else if ($_POST['MainType'] == 'Separate') {
                        for ($n = 1; $n <= $numsensors; $n++) {
                            if (${'sensor' . $n . 'graph'} == 1) {
                                echo `echo "set terminal png size $graph_width,490
                                set xdata time
                                set timefmt \"%Y %m %d %H %M %S\"
                                set output \"$images/graph-cussep-$id2-$n.png\"
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
                                set style line 1 lc rgb '#FF3100' pt 0 ps 1 lt 1 lw 2
                                set style line 2 lc rgb '#0772A1' pt 0 ps 1 lt 1 lw 2
                                set style line 3 lc rgb '#00B74A' pt 0 ps 1 lt 1 lw 2
                                set style line 4 lc rgb '#91180B' pt 0 ps 1 lt 1 lw 1
                                set style line 5 lc rgb '#582557' pt 0 ps 1 lt 1 lw 1
                                set style line 6 lc rgb '#04834C' pt 0 ps 1 lt 1 lw 1
                                set style line 7 lc rgb '#DC32E6' pt 0 ps 1 lt 1 lw 1
                                set style line 8 lc rgb '#957EF9' pt 0 ps 1 lt 1 lw 1
                                set style line 9 lc rgb '#CC8D9C' pt 0 ps 1 lt 1 lw 1
                                set style line 10 lc rgb '#717412' pt 0 ps 1 lt 1 lw 1
                                set style line 11 lc rgb '#0B479B' pt 0 ps 1 lt 1 lw 1
                                #set xlabel \"Date and Time\"
                                #set ylabel \"% Humidity\"
                                set title \"Sensor $n: ${'sensor' . $n . 'name'}  $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
                                unset key
                                plot \"<awk '\\$10 == $n' $sensor_ht_log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
                                \"\" using 1:8 index 0 title \"T\" w lp ls 2 axes x1y1, \\
                                \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
                                \"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay1name\" w impulses ls 4 axes x1y1, \\
                                \"\" using 1:8 index 0 title \"$relay2name\" w impulses ls 5 axes x1y1, \\
                                \"\" using 1:9 index 0 title \"$relay3name\" w impulses ls 6 axes x1y1, \\
                                \"\" using 1:10 index 0 title \"$relay4name\" w impulses ls 7 axes x1y1, \\
                                \"\" using 1:11 index 0 title \"$relay5name\" w impulses ls 8 axes x1y1, \\
                                \"\" using 1:12 index 0 title \"$relay6name\" w impulses ls 9 axes x1y1, \\
                                \"\" using 1:13 index 0 title \"$relay7name\" w impulses ls 10 axes x1y1, \\
                                \"\" using 1:14 index 0 title \"$relay8name\" w impulses ls 11 axes x1y1" | gnuplot`;
                                echo "<div style=\"width: 100%; text-align: center; padding: 1em 0 3em 0;\"><img src=image.php?span=cussep&mod=" . $id2 . "&sensor=" . $n . "></div>";
                            }
                            if ($n != $numsensors) { echo "<hr class=\"fade\"/>"; }
                        }
                    }
                    echo "<div style=\"width: 100%; text-align: center;\"><a href='javascript:open_legend()'>Brief Graph Legend</a> - <a href='javascript:open_legend_full()'>Full Graph Legend</a></div>";
                }
            } else if (isset($_POST['SubmitDates']) and $_SESSION['user_name'] == 'guest') {
                displayform();
                echo "<div>Guest access has been revoked for graph generation until further notice (thank those who have been attempting bad stuff)";
            } else displayform();
            ?>
		</li>
        
		<li data-content="camera" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'camera') echo "class=\"selected\""; ?>>
            <div style="padding: 10px 0 15px 15px;">
                <form action="?tab=camera<?php
                    if (isset($_GET['page'])) echo "&page=" . $_GET['page'];
                ?>" method="POST">
                <table class="camera">
                    <tr>
                        <td>
                            Light Relay: <input type="text" value="<?php echo $cameralight; ?>" maxlength=4 size=1 name="lightrelay" title=""/>
                        </td>
                        <td>
                            Light On? <input type="checkbox" name="lighton" value="1" <?php if (isset($_POST['lighton'])) echo "checked=\"checked\""; ?>>
                        </td>
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
                            if (!file_exists($lock_raspistill) && !file_exists($lock_mjpg_streamer)) echo 'Stream <span class="off">OFF</span>';
                            else echo 'Stream <span class="on">ON</span>';
                            ?>
                        </td>
                    </tr>
                </table>
                </form>
            </div>
            <center>
            <?php
                if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) {
                    echo '<img src="http://' . $_SERVER[HTTP_HOST] . ':8080/?action=stream" />';
                }
                if (isset($_POST['Capture']) && $_SESSION['user_name'] != 'guest') {
                    if ($capture_output != 0) echo 'Abnormal output (possibly error): ' . $capture_output . '<br>';
                    else echo '<p><img src=image.php?span=cam-still></p>';
                }
            ?>
            </center>
		</li>

		<li data-content="log" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'log') echo "class=\"selected\""; ?>>
			<div style="padding: 10px 0 0 15px;">
                <div style="padding-bottom: 15px;">
                    <FORM action="?tab=log<?php
                        if (isset($_GET['page'])) echo "&page=" . $_GET['page'];
                    ?>" method="POST">
                        Lines: <input type="text" maxlength=8 size=8 name="Lines" /> 
                        <input type="submit" name="HTSensor" value="HT Sensor"> 
                        <input type="submit" name="Co2Sensor" value="Co2 Sensor"> 
                        <input type="submit" name="Relay" value="Relay"> 
                        <input type="submit" name="Auth" value="Auth">
                        <input type="submit" name="Daemon" value="Daemon">
                    </FORM>
                </div>
                <div style="font-family: monospace;">
                    <pre><?php
                        if(isset($_POST['HTSensor'])) {
                            echo 'Year Mo Day Hour Min Sec Tc RH DPc Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $sensor_ht_log`;
                            } else {
                                echo `tail -n 30 $sensor_ht_log`;
                            }
                        }
                        
                        if(isset($_POST['Co2Sensor'])) {
                            echo 'Year Mo Day Hour Min Sec Co2 Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $sensor_co2_log`;
                            } else {
                                echo `tail -n 30 $sensor_co2_log`;
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

                        if(isset($_POST['Auth']) && $_SESSION['user_name'] != 'guest') {
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
            </div>
		</li>

		<li data-content="advanced" <?php if (isset($_GET['tab']) && $_GET['tab'] == 'adv') echo "class=\"selected\""; ?>>
            <div style="padding-left:1em;">
            <div class="advanced">
                <FORM action="?tab=adv<?php
                    if (isset($_GET['page'])) echo "&page=" . $_GET['page'];
                ?>" method="POST">
                <div style="padding: 0 0 1em 1em;">
                    Number of Timers 
                    <select name="numtimers">
                        <option value="1" <?php if ($numtimers == 1) echo "selected=\"selected\""; ?>>1</option>
                        <option value="2" <?php if ($numtimers == 2) echo "selected=\"selected\""; ?>>2</option>
                        <option value="3" <?php if ($numtimers == 3) echo "selected=\"selected\""; ?>>3</option>
                        <option value="4" <?php if ($numtimers == 4) echo "selected=\"selected\""; ?>>4</option>
                        <option value="5" <?php if ($numtimers == 5) echo "selected=\"selected\""; ?>>5</option>
                        <option value="6" <?php if ($numtimers == 6) echo "selected=\"selected\""; ?>>6</option>
                        <option value="7" <?php if ($numtimers == 7) echo "selected=\"selected\""; ?>>7</option>
                        <option value="8" <?php if ($numtimers == 8) echo "selected=\"selected\""; ?>>8</option>
                    </select>
                    <input type="submit" name="ChangeNoTimers" value="Save">
                </div>
                <?php if ($numtimers > 0) { ?>
                <div>
                    
                    <table class="timers">
                        <tr>
                            <td>
                                Timer
                            </td>
                            <th align="center" colspan="2">
                                State
                            </th>
                            <td>
                                Relay
                            </td>
                            <td>
                                On (sec)
                            </td>
                            <td>
                                Off (sec)
                            </td>
                            <td>
                            </td>
                        </tr>
                        <?php for ($i = 1; $i <= $numtimers; $i++) { ?>
                        <tr>
                            <td>
                                <?php echo $i; ?>
                            </td>
                            <?php if (${'timer'. $i . 'state'} == 0) { ?>
                                <th colspan=2 align=right>
                                    <nobr><input type="image" style="height: 0.9em;" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="Timer<?php echo $i; ?>StateChange" value="0"> | <button style="width: 40px;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="1">ON</button></nobr>
                                </td>
                                </th>
                                <?php
                            } else {
                                ?>
                                <th colspan=2 align=right>
                                    <nobr><input type="image" style="height: 0.9em;" src="/mycodo/img/on.jpg" alt="On" title="On" name="Timer<?php echo $i; ?>StateChange" value="1"> | <button style="width: 40px;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="0">OFF</button></nobr>
                                </th>
                            <?php
                            }
                            ?>
                            <td>
                                <input type="text" value="<?php echo ${'timer'. $i . 'relay'}; ?>" maxlength=1 size=1 name="Timer<?php echo $i; ?>Relay" title="This is the relay number for timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'timer'. $i . 'durationon'}; ?>" maxlength=7 size=4 name="Timer<?php echo $i; ?>On" title="This is On duration of timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo ${'timer'. $i . 'durationoff'}; ?>" maxlength=7 size=4 name="Timer<?php echo $i; ?>Off" title="This is Off duration for timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input type="submit" name="ChangeTimer<?php echo $i; ?>" value="Save">
                            </td>
                        </tr>
                        <?php } ?>
                    </table>
                </div>
                </FORM>
                <?php } ?>
            </div>
            
            <div class="advanced">
                <FORM action="?tab=adv" method="POST">
                <div class="notify-title">
                    Email Notification Settings
                </div>
                <div class="notify">
                    <label class="notify">SMTP Host</label><input class="smtp" type="text" value="<?php echo $smtp_host; ?>" maxlength=30 size=20 name="smtp_host" title=""/>
                </div>
                <div class="notify">
                    <label class="notify">SMTP Port</label><input class="smtp" type="text" value="<?php echo $smtp_port; ?>" maxlength=30 size=20 name="smtp_port" title=""/>
                </div>
                <div class="notify">
                    <label class="notify">User</label><input class="smtp" type="text" value="<?php echo $smtp_user; ?>" maxlength=30 size=20 name="smtp_user" title=""/>
                </div>
                <div class="notify">
                    <label class="notify">Password</label><input class="smtp" type="password" value="<?php echo $smtp_pass; ?>" maxlength=30 size=20 name="smtp_pass" title=""/>
                </div>
                <div class="notify">
                    <label class="notify">From</label><input class="smtp" type="text" value="<?php echo $email_from; ?>" maxlength=30 size=20 name="email_from" title=""/>
                </div>
                <div class="notify">
                    <label class="notify">To</label><input class="smtp" type="text" value="<?php echo $email_to; ?>" maxlength=30 size=20 name="email_to" title=""/>
                </div>
                <div class="notify">
                    <input type="submit" name="ChangeNotify" value="Save">
                </div>
                </FORM>
            </div>
            </div>
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

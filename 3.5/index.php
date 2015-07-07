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

$sqlite_db = $install_path . "/config/mycodo.sqlite3";
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
require_once("functions/functions.php");

$login = new Login();

if ($login->isUserLoggedIn() == true) {
    // Graph-generation cookie of unique ID for graphs
    $ref = 0;
    if (isset($_GET['Refresh']) == 1 or !isset($_COOKIE['id'])) {
        $uniqueid = uniqid();
        setcookie('id', $uniqueid);
        $id  = $uniqueid;
        $ref = 1;
    } else {
        $id = $_COOKIE['id'];
    }

    $db = new SQLite3($sqlite_db);

    // Initial read of SQL database
    require("functions/sql.php");

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

    // Check if daemon is running
    $daemon_check = `ps aux | grep "[m]ycodo.py"`;
    if (empty($daemon_check)) $daemon_check = 0;
    else $daemon_check = 1;

    $uptime = `uptime | grep -ohe 'load average[s:][: ].*' `;

    $page = isset($_GET['page']) ? $_GET['page'] : 'Main';
    $tab = isset($_GET['tab']) ? $_GET['tab'] : 'Unset';
    $sql_reload = False;

    // Check form submissions
    for ($p = 1; $p <= 8; $p++) {
        // Modify the SQLite database and require the daemon to reload variables
        if (isset($_POST['Mod' . $p . 'Relay']) ||
                isset($_POST['Change' . $p . 'HTSensor']) ||
                isset($_POST['Change' . $p . 'Co2Sensor']) ||
                isset($_POST['ChangeTimer' . $p]) ||
                isset($_POST['Timer' . $p . 'StateChange']) ||
                isset($_POST['Change' . $p . 'TempPID']) ||
                isset($_POST['Change' . $p . 'HumPID']) ||
                isset($_POST['Change' . $p . 'Co2PID']) ||
                isset($_POST['Change' . $p . 'TempOR']) ||
                isset($_POST['Change' . $p . 'HumOR']) ||
                isset($_POST['Change' . $p . 'Co2OR'])) {

            // All commands where elevated (!= guest) privileges are required
            if ($_SESSION['user_name'] != 'guest') {
                $sql_reload = True;

                // Set relay variables
                if (isset($_POST['Mod' . $p . 'Relay'])) {
                    $stmt = $db->prepare("UPDATE Relays SET Name=:name, Pin=:pin, Trigger=:trigger WHERE Id=:id");
                    $stmt->bindValue(':name', $_POST['relay' . $p . 'name'], SQLITE3_TEXT);
                    $stmt->bindValue(':pin', (int)$_POST['relay' . $p . 'pin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':trigger', (int)$_POST['relay' . $p . 'trigger'], SQLITE3_INTEGER);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                }

                // Set Temperature/Humidity sensor variables
                if (isset($_POST['Change' . $p . 'HTSensor'])) {
                    $stmt = $db->prepare("UPDATE HTSensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph WHERE Id=:id");
                    $stmt->bindValue(':name', str_replace(' ', '', $_POST['sensorht' . $p . 'name']), SQLITE3_TEXT);
                    $stmt->bindValue(':device', str_replace(' ', '', $_POST['sensorht' . $p . 'device']), SQLITE3_TEXT);
                    $stmt->bindValue(':pin', (int)$_POST['sensorht' . $p . 'pin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':period', (int)$_POST['sensorht' . $p . 'period'], SQLITE3_INTEGER);
                    if (isset($_POST['sensorht' . $p . 'activated'])) {
                        $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
                    } else {
                        $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
                    }
                    if (isset($_POST['sensorht' . $p . 'graph'])) {
                        $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
                    } else {
                        $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
                    }
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                }

                // Set Temperature PID variables
                if (isset($_POST['Change' . $p . 'TempPID'])) {
                    $stmt = $db->prepare("UPDATE HTSensor SET Temp_Relay=:temprelay, Temp_Set=:tempset, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd WHERE Id=:id");
                    $stmt->bindValue(':temprelay', (int)$_POST['Set' . $p . 'TempRelay'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempset', (float)$_POST['Set' . $p . 'TempSet'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempperiod', (int)$_POST['Set' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempp', (float)$_POST['Set' . $p . 'Temp_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempi', (float)$_POST['Set' . $p . 'Temp_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempd', (float)$_POST['Set' . $p . 'Temp_D'], SQLITE3_FLOAT);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                    if ($pid_temp_or[$p] == 0) {
                        pid_reload($mycodo_client, 'Temp', $p);
                    }
                }

                // Set Temperature PID override on or off
                if (isset($_POST['Change' . $p . 'TempOR'])) {
                    $stmt = $db->prepare("UPDATE HTSensor SET Temp_OR=:humor WHERE Id=:id");
                    $stmt->bindValue(':humor', (int)$_POST['Change' . $p . 'TempOR'], SQLITE3_INTEGER);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                }

                // Set Humidity PID variables
                if (isset($_POST['Change' . $p . 'HumPID'])) {
                    $stmt = $db->prepare("UPDATE HTSensor SET Hum_Relay=:humrelay, Hum_Set=:humset, Hum_Period=:humperiod, Hum_P=:hump, Hum_I=:humi, Hum_D=:humd WHERE Id=:id");
                    $stmt->bindValue(':humrelay', (int)$_POST['Set' . $p . 'HumRelay'], SQLITE3_INTEGER);
                    $stmt->bindValue(':humset', (float)$_POST['Set' . $p . 'HumSet'], SQLITE3_FLOAT);
                    $stmt->bindValue(':humperiod', (int)$_POST['Set' . $p . 'HumPeriod'], SQLITE3_INTEGER);
                    $stmt->bindValue(':hump', (float)$_POST['Set' . $p . 'Hum_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':humi', (float)$_POST['Set' . $p . 'Hum_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':humd', (float)$_POST['Set' . $p . 'Hum_D'], SQLITE3_FLOAT);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                    if ($pid_hum_or[$p] == 0) {
                        pid_reload($mycodo_client, 'Hum', $p);
                    }
                }

                // Set Humidity PID override on or off
                if (isset($_POST['Change' . $p . 'HumOR'])) {
                    $stmt = $db->prepare("UPDATE HTSensor SET Hum_OR=:humor WHERE Id=:id");
                    $stmt->bindValue(':humor', (int)$_POST['Change' . $p . 'HumOR'], SQLITE3_INTEGER);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                }

                // Set CO2 sensor variables
                if (isset($_POST['Change' . $p . 'Co2Sensor'])) {
                    $stmt = $db->prepare("UPDATE CO2Sensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph WHERE Id=:id");
                    $stmt->bindValue(':name', str_replace(' ', '', $_POST['sensorco2' . $p . 'name']), SQLITE3_TEXT);
                    $stmt->bindValue(':device', str_replace(' ', '', $_POST['sensorco2' . $p . 'device']), SQLITE3_TEXT);
                    $stmt->bindValue(':pin', (int)$_POST['sensorco2' . $p . 'pin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':period', (int)$_POST['sensorco2' . $p . 'period'], SQLITE3_INTEGER);
                    if (isset($_POST['sensorco2' . $p . 'activated'])) {
                        $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
                    } else {
                        $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
                    }
                    if (isset($_POST['sensorco2' . $p . 'graph'])) {
                        $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
                    } else {
                        $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
                    }
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                }

                // Set CO2 PID variables
                if (isset($_POST['Change' . $p . 'Co2PID'])) {
                    $stmt = $db->prepare("UPDATE CO2Sensor SET CO2_Relay=:co2relay, CO2_Set=:co2set, CO2_Period=:co2period, CO2_P=:co2p, CO2_I=:co2i, CO2_D=:co2d WHERE Id=:id");
                    $stmt->bindValue(':co2relay', (int)$_POST['Set' . $p . 'Co2Relay'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2set', (float)$_POST['Set' . $p . 'Co2Set'], SQLITE3_FLOAT);
                    $stmt->bindValue(':co2period', (int)$_POST['Set' . $p . 'Co2Period'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2p', (float)$_POST['Set' . $p . 'Co2_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':co2i', (float)$_POST['Set' . $p . 'Co2_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':co2d', (float)$_POST['Set' . $p . 'Co2_D'], SQLITE3_FLOAT);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                    if ($pid_co2_or[$p] == 0) {
                        pid_reload($mycodo_client, 'CO2', $p);
                    }
                }

                // Set CO2 PID override on or off
                if (isset($_POST['Change' . $p . 'Co2OR'])) {
                    $stmt = $db->prepare("UPDATE CO2Sensor SET CO2_OR=:co2or WHERE Id=:id");
                    $stmt->bindValue(':co2or', (int)$_POST['Change' . $p . 'Co2OR'], SQLITE3_INTEGER);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                }

                 // Set timer variables
                if (isset($_POST['ChangeTimer' . $p])) {
                    $stmt = $db->prepare("UPDATE Timers SET Name=:name, State=:state, Relay=:relay, DurationOn=:durationon, DurationOff=:durationoff WHERE Id=:id");
                    $stmt->bindValue(':name', $_POST['Timer' . $p . 'Name'], SQLITE3_TEXT);
                    $stmt->bindValue(':state', (int)$_POST['Timer' . $p . 'State'], SQLITE3_INTEGER);
                    $stmt->bindValue(':relay', (int)$_POST['Timer' . $p . 'Relay'], SQLITE3_INTEGER);
                    $stmt->bindValue(':durationon', (int)$_POST['Timer' . $p . 'On'], SQLITE3_INTEGER);
                    $stmt->bindValue(':durationoff', (int)$_POST['Timer' . $p . 'Off'], SQLITE3_INTEGER);
                    $stmt->bindValue(':id', $p, SQLITE3_TEXT);
                    $stmt->execute();

                } else if (isset($_POST['ChangeTimer' . $p]) && $_SESSION['user_name'] == 'guest') $error_code = 'guest';

                // Set timer state
                if (isset($_POST['Timer' . $p . 'StateChange'])) {
                    $stmt = $db->prepare("UPDATE Timers SET State=:state WHERE Id=:id");
                    $stmt->bindValue(':state', (int)$_POST['Timer' . $p . 'StateChange'], SQLITE3_INTEGER);
                    $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
                    $stmt->execute();
                }
            } else $error_code = 'guest';
        }

        // All commands that do not modify the SQLite database
        if (isset($_POST['R' . $p]) || isset($_POST[$p . 'secON'])) {
            if ($_SESSION['user_name'] != 'guest') {

                // Send client command to turn relay on or off
                if (isset($_POST['R' . $p])) {
                    $name = $_POST['relay' . $p . 'name'];
                    $pin = $_POST['relay' . $p . 'pin'];
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

                // Send client command to turn relay on for a number of seconds
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
            } else $error_code = 'guest';
        }
    }

    if (isset($_POST['WriteSensorLog']) ||
            isset($_POST['Capture']) || isset($_POST['start-stream']) ||
            isset($_POST['stop-stream']) || isset($_POST['ChangeNoRelays']) ||
            isset($_POST['ChangeNoHTSensors']) || isset($_POST['ChangeNoCo2Sensors']) ||
            isset($_POST['ChangeNoTimers']) || isset($_POST['ChangeNotify'])) {
        if ($_SESSION['user_name'] != 'guest') {

            // Change email notify settings
            if (isset($_POST['ChangeNotify'])) {
                $stmt = $db->prepare("UPDATE SMTP SET Host=:host, SSL=:ssl, Port=:port, User=:user, Pass=:password, Email_From=:emailfrom, Email_To=:emailto");
                $stmt->bindValue(':host', $_POST['smtp_host'], SQLITE3_TEXT);
                $stmt->bindValue(':ssl', (int)$_POST['smtp_ssl'], SQLITE3_INTEGER);
                $stmt->bindValue(':port', (int)$_POST['smtp_port'], SQLITE3_INTEGER);
                $stmt->bindValue(':user', $_POST['smtp_user'], SQLITE3_TEXT);
                $stmt->bindValue(':password', $_POST['smtp_pass'], SQLITE3_TEXT);
                $stmt->bindValue(':emailfrom', $_POST['smtp_email_from'], SQLITE3_TEXT);
                $stmt->bindValue(':emailto', $_POST['smtp_email_to'], SQLITE3_TEXT);
                $stmt->execute();
                $sql_reload = True;
            }

            // Change number of relays
            if (isset($_POST['ChangeNoRelays'])) {
                $stmt = $db->prepare("UPDATE Numbers SET Relays=:relays");
                $stmt->bindValue(':relays', (int)$_POST['numrelays'], SQLITE3_INTEGER);
                $stmt->execute();
                $sql_reload = True;
            }

            // Change number of HT sensors
            if (isset($_POST['ChangeNoHTSensors'])) {
                $stmt = $db->prepare("UPDATE Numbers SET HTSensors=:htsensors");
                $stmt->bindValue(':htsensors', (int)$_POST['numhtsensors'], SQLITE3_INTEGER);
                $stmt->execute();
                $sql_reload = True;
            }

            // Change number of CO2 sensors
            if (isset($_POST['ChangeNoCo2Sensors'])) {
                $stmt = $db->prepare("UPDATE Numbers SET CO2Sensors=:co2sensors");
                $stmt->bindValue(':co2sensors', (int)$_POST['numco2sensors'], SQLITE3_INTEGER);
                $stmt->execute();
                $sql_reload = True;
            }

            // Change number of timers
            if (isset($_POST['ChangeNoTimers'])) {
                $stmt = $db->prepare("UPDATE Numbers SET Timers=:timers");
                $stmt->bindValue(':timers', (int)$_POST['numtimers'], SQLITE3_INTEGER);
                $stmt->execute();
                $sql_reload = True;
            }

            // Capture still image from camera (with or without light activation)
            if (isset($_POST['Capture'])) {
                if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) shell_exec("$stream_exec stop");
                if (isset($_POST['lighton'])) {
                    $lightrelay = $_POST['lightrelay'];
                    $lightrelay_pin = $relay_pin[$lightrelay];
                    $lightrelay_trigger = $_POST['relay' . $lightrelay . 'trigger'];
                    if ($lightrelay_trigger == 1) $trigger = 1;
                    else $trigger = 0;
                    $capture_output = shell_exec("$still_exec " . $lightrelay_pin . " $trigger 2>&1; echo $?");
                } else $capture_output = shell_exec("$still_exec 2>&1; echo $?");
            }

            // Start video stream
            if (isset($_POST['start-stream'])) {
                if (file_exists($lock_raspistill) || file_exists($lock_mjpg_streamer)) {
                echo 'Lock files already present. Press \'Stop Stream\' to kill processes and remove lock files.<br>';
                } else {
                    if (isset($_POST['lighton'])) { // Turn light on
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

            // Stop video stream
            if (isset($_POST['stop-stream'])) {
                if (isset($_POST['lighton'])) { // Turn light off
                    $lightrelay = $_POST['lightrelay'];
                    if (${"relay" . $lightrelay . "trigger"} == 1) $trigger = 0;
                    else $trigger = 1;
                    shell_exec("$stream_exec stop " . ${'relay' . $lightrelay . "pin"} . " $trigger > /dev/null &");
                } else shell_exec("$stream_exec stop");
                sleep(1);
            }

            // Request sensor read and log write
             if (isset($_POST['WriteSensorLog'])) {
                $editconfig = "$mycodo_client --writehtlog 0";
                shell_exec($editconfig);
                $editconfig = "$mycodo_client --writeco2log 0";
                shell_exec($editconfig);
            }
        } else $error_code = 'guest';
    }

    if ($sql_reload) {
        // Reread SQL database to catch any changes made above
        require("functions/sql.php");

        $editconfig = "$mycodo_client --sqlreload";
        shell_exec($editconfig);
    }

    // Concatenate Sensor log files (to TempFS) to ensure the latest data is being used
    `cat /var/www/mycodo/log/sensor-ht.log /var/www/mycodo/log/sensor-ht-tmp.log > /var/tmp/sensor-ht.log`;
    `cat /var/www/mycodo/log/sensor-co2.log /var/www/mycodo/log/sensor-co2-tmp.log > /var/tmp/sensor-co2.log`;

    $last_ht_sensor[1] = `awk '$10 == 1' /var/tmp/sensor-ht.log | tail -n 1`;
    $last_ht_sensor[2] = `awk '$10 == 2' /var/tmp/sensor-ht.log | tail -n 1`;
    $last_ht_sensor[3] = `awk '$10 == 3' /var/tmp/sensor-ht.log | tail -n 1`;
    $last_ht_sensor[4] = `awk '$10 == 4' /var/tmp/sensor-ht.log | tail -n 1`;

    for ($p = 1; $p <= $sensor_ht_num; $p++) {
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

    for ($p = 1; $p <= $sensor_co2_num; $p++) {
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
// Display any auth error that occurred
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
    for ($i = 1; $i <= $sensor_ht_num; $i++) {
        if ($sensor_ht_activated[$i] == 1) {
    ?>
    <div class="header">
    <table>
        <tr>
            <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo "HT" . $i . ": " . $sensor_ht_name[$i]; ?></td>
        </tr>
        <tr>
            <td>
    <div style="font-size: 0.8em; padding-right: 0.5em;"><?php
            echo "Now<br><span title=\"" . number_format((float)$t_f[$i], 1, '.', '') . "&deg;F\">" . number_format((float)$t_c[$i], 1, '.', '') . "&deg;C</span>";
            echo "<br>" . number_format((float)$hum[$i], 1, '.', '') . "%";
        ?>
    </div>
            </td>
            <td>
    <div style="font-size: 0.8em;"><?php
            echo "Set<br><span title=\"" . number_format((float)$settemp_f[$i], 1, '.', '') ."&deg;F\">" . number_format((float)$pid_temp_set[$i], 1, '.', '') . "&deg;C";
            echo "<br>" . number_format((float)$pid_hum_set[$i], 1, '.', '') . "%";
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
    for ($i = 1; $i <= $sensor_co2_num; $i++) {
        if ($sensor_co2_activated[$i] == 1) {
    ?>
    <div class="header">
    <table>
        <tr>
            <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;">
                <?php echo "CO<sub>2</sub>" . $i . ": " . $sensor_co2_name[$i]; ?>
            </td>
        </tr>
        <tr>
            <td>
                <div style="font-size: 0.8em; padding-right: 0.5em;"><?php echo "Now<br>" . $co2[$i]; ?></div>
            </td>
            <td>
                <div style="font-size: 0.8em;"><?php echo "Set<br>" . $pid_co2_set[$i]; ?></div>
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
                                <input type="submit" name="WriteSensorLog" value="Sensors" title="Reread all sensors and write logs">
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

                    //if (!isset($_SESSION["ID"])) {
                    //    $id = uniqid();
                    //    $_SESSION["ID"] = $id;
                    //    $ref = 1;
                    //} else $id = $_SESSION["ID"];

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
                        for ($n = 1; $n <= $sensor_ht_num; $n++ ) {
                            if (isset($_GET['page']) and $sensor_ht_graph[$n] == 1) {
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
                            if ($n != $sensor_ht_num || $sensor_co2_graph[1] == 1 || $sensor_co2_graph[2] == 1 || $sensor_co2_graph[3] == 1 || $sensor_co2_graph[4] == 1) {
                                echo "<hr class=\"fade\"/>"; }
                        }
                        for ($n = 1; $n <= $sensor_co2_num; $n++ ) {
                            if (isset($_GET['page']) and $sensor_co2_graph[$n] == 1) {
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
                            } else if ($sensor_co2_graph[$n] == 1) {
                                echo "<div style=\"padding: 1em 0 3em 0;\"><img class=\"main-image\" style=\"max-width:100%;height:auto;\" src=image.php?span=";
                                if ($ref) shell_exec($mycodo_client . ' --graph co2dayweek ' . $id . ' ' . $n);
                                echo "co2main&mod=" . $id . "&sensor=" . $n . "></div>";
                            }
                            if ($n != $sensor_co2_num) { echo "<hr class=\"fade\"/>"; }
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
                            <input type="submit" name="WriteSensorLog" value="Sensors" title="Reread all sensors and write logs">
                        </div>
                    </div>
                </div>
            </div>

            <div style="clear: both;"></div>

            <div>
                <div style="padding: 1em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoRelays" value="Save ->">
                        <select name="numrelays">
                            <option value="0" <?php if ($relay_num == 0) echo "selected=\"selected\""; ?>>0</option>
                            <option value="1" <?php if ($relay_num == 1) echo "selected=\"selected\""; ?>>1</option>
                            <option value="2" <?php if ($relay_num == 2) echo "selected=\"selected\""; ?>>2</option>
                            <option value="3" <?php if ($relay_num == 3) echo "selected=\"selected\""; ?>>3</option>
                            <option value="4" <?php if ($relay_num == 4) echo "selected=\"selected\""; ?>>4</option>
                            <option value="5" <?php if ($relay_num == 5) echo "selected=\"selected\""; ?>>5</option>
                            <option value="6" <?php if ($relay_num == 6) echo "selected=\"selected\""; ?>>6</option>
                            <option value="7" <?php if ($relay_num == 7) echo "selected=\"selected\""; ?>>7</option>
                            <option value="8" <?php if ($relay_num == 8) echo "selected=\"selected\""; ?>>8</option>
                        </select>
                    </div>
                    <div style="float: left; font-weight: bold;">Relays</div>
                    <div style="clear: both;"></div>
                </div>

                <?php if ($relay_num > 0) { ?>
                <div style="padding-bottom: 1em;">
                    <table class="relays">
                        <tr>
                            <td align=center class="table-header">Relay<br>No.</td>
                            <td align=center class="table-header">Relay<br>Name</td>
                            <th align=center class="table-header">Current<br>State</th>
                            <td align=center class="table-header">Seconds<br>On</td>
                            <td align=center class="table-header">GPIO<br>Pin</td>
                            <td align=center class="table-header">Trigger<br>ON</td>
                            <td align=center class="table-header">Change<br>Values</td>
                        </tr>
                        <?php for ($i = 1; $i <= $relay_num; $i++) {
                            $read = "$gpio_path -g read $relay_pin[$i]";
                        ?>
                        <tr>
                            <td align=center>
                                <?php echo $i; ?>
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $relay_name[$i]; ?>" maxlength=12 size=10 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i; ?>"/>
                            </td>
                            <?php
                                if ((shell_exec($read) == 1 && $relay_trigger[$i] == 0) || (shell_exec($read) == 0 && $relay_trigger[$i] == 1)) {
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
                                <input type="text" value="<?php echo $relay_pin[$i]; ?>" maxlength=2 size=1 name="relay<?php echo $i; ?>pin" title="GPIO pin using BCM numbering, connected to relay <?php echo $i; ?>"/>
                            </td>
                            <td align=center>
                                <select style="width: 65px;" name="relay<?php echo $i; ?>trigger">
                                    <option <?php if ($relay_trigger[$i] == 1) echo "selected=\"selected\""; ?> value="1">HIGH</option>
                                    <option <?php if ($relay_trigger[$i] == 0) echo "selected=\"selected\""; ?> value="0">LOW</option>
                                </select>
                            </td>
                            <td>
                                <button type="submit" name="Mod<?php echo $i; ?>Relay" value="1" title="Change the ON trigger state of the relays.">Set</button>
                            </td>
                        </tr>
                        <?php
                        } ?>
                    </table>
                </div>
                <?php }
                    ?>

                <div style="padding: 1em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoHTSensors" value="Save ->">
                        <select name="numhtsensors">
                            <option value="0" <?php if ($sensor_ht_num == 0) echo "selected=\"selected\""; ?>>0</option>
                            <option value="1" <?php if ($sensor_ht_num == 1) echo "selected=\"selected\""; ?>>1</option>
                            <option value="2" <?php if ($sensor_ht_num == 2) echo "selected=\"selected\""; ?>>2</option>
                            <option value="3" <?php if ($sensor_ht_num == 3) echo "selected=\"selected\""; ?>>3</option>
                            <option value="4" <?php if ($sensor_ht_num == 4) echo "selected=\"selected\""; ?>>4</option>
                        </select>
                    </div>
                    <div style="float: left; font-weight: bold;">Humidity & Temperature Sensors</div>
                    <div style="clear: both;"></div>
                </div>

                <?php if ($sensor_ht_num > 0) { ?>
                <div style="padding-right: 1em;">
                    <?php for ($i = 1; $i <= $sensor_ht_num; $i++) {
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
                                <input type="text" value="<?php echo $sensor_ht_name[$i]; ?>" maxlength=12 size=10 name="sensorht<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 80px;" name="sensorht<?php echo $i; ?>device">
                                    <option <?php if ($sensor_ht_device[$i] == 'DHT11') echo "selected=\"selected\""; ?> value="DHT11">DHT11</option>
                                    <option <?php if ($sensor_ht_device[$i] == 'DHT22') echo "selected=\"selected\""; ?> value="DHT22">DHT22</option>
                                    <option <?php if ($sensor_ht_device[$i] == 'AM2302') echo "selected=\"selected\""; ?> value="AM2302">AM2302</option>
                                    <option <?php if ($sensor_ht_device[$i] == 'Other') echo "selected=\"selected\""; ?>value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $sensor_ht_pin[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>pin" title="This is the GPIO pin connected to the DHT sensor"/>
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $sensor_ht_period[$i]; ?>" maxlength=4 size=1 name="sensorht<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorht<?php echo $i; ?>activated" value="1" <?php if ($sensor_ht_activated[$i] == 1) echo "checked"; ?>>
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorht<?php echo $i; ?>graph" value="1" <?php if ($sensor_ht_graph[$i] == 1) echo "checked"; ?>>
                            </td>
                            <td>
                                <input type="submit" name="Change<?php echo $i; ?>HTSensor" value="Set">
                            </td>
                        </tr>
                    </table>
                    </div>

                    <?php if ($i == $sensor_ht_num) {
                        echo '<div style="padding-bottom: 1em;">';
                    } else {
                        echo '<div style="padding-bottom: 2em;">';
                    } ?>
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
                                    if ($pid_temp_or[$i] == 1) {
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
                                <input type="text" value="<?php echo $pid_temp_relay[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>TempRelay" title="This is the relay connected to the heating device"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_temp_set[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>TempSet" title="This is the desired temperature"/> °C
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $pid_temp_period[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_temp_p[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_temp_i[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_temp_d[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_D" title="This is the Derivative value of the PID"/>
                            </td>
                            <td>
                                <input type="submit" name="Change<?php echo $i; ?>TempPID" value="Set">
                            </td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td>Humidity</td>
                            <td class="onoff">
                            <?php
                                if ($pid_hum_or[$i] == 1) {
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
                                <input type="text" value="<?php echo $pid_hum_relay[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>HumRelay" title="This is the relay connected to your humidifying device"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_hum_set[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>HumSet" title="This is the desired humidity"/> %
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $pid_hum_period[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>HumPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another humidity reading and applying the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_hum_p[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_hum_i[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_hum_d[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_D" title="This is the Derivative value of the PID"/>
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

                <div style="padding: 1em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoCo2Sensors" value="Save ->">
                        <select name="numco2sensors">
                            <option value="0" <?php if ($sensor_co2_num == 0) echo "selected=\"selected\""; ?>>0</option>
                            <option value="1" <?php if ($sensor_co2_num == 1) echo "selected=\"selected\""; ?>>1</option>
                            <option value="2" <?php if ($sensor_co2_num == 2) echo "selected=\"selected\""; ?>>2</option>
                            <option value="3" <?php if ($sensor_co2_num == 3) echo "selected=\"selected\""; ?>>3</option>
                            <option value="4" <?php if ($sensor_co2_num == 4) echo "selected=\"selected\""; ?>>4</option>
                        </select>
                    </div>
                    <div style="float: left; font-weight: bold;">CO<sub>2</sub> Sensors</div>
                    <div style="clear: both;"></div>
                </div>

                <?php if ($sensor_co2_num > 0) { ?>

                <div>
                    <?php for ($i = 1; $i <= $sensor_co2_num; $i++) {
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
                                <input type="text" value="<?php echo $sensor_co2_name[$i]; ?>" maxlength=12 size=10 name="sensorco2<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 80px;" name="sensorco2<?php echo $i; ?>device">
                                    <option <?php if ($sensor_co2_device[$i] == 'K30') echo "selected=\"selected\""; ?> value="K30">K30</option>
                                    <option <?php if ($sensor_co2_device[$i] == 'Other') echo "selected=\"selected\""; ?>value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $sensor_co2_pin[$i]; ?>" maxlength=2 size=1 name="sensorco2<?php echo $i; ?>pin" title="This is the GPIO pin connected to the CO2 sensor"/>
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $sensor_co2_period[$i]; ?>" maxlength=4 size=1 name="sensorco2<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorco2<?php echo $i; ?>activated" value="1" <?php if ($sensor_co2_activated[$i] == 1) echo "checked"; ?>>
                            </td>
                            <td align=center>
                                <input type="checkbox" name="sensorco2<?php echo $i; ?>graph" value="1" <?php if ($sensor_co2_graph[$i] == 1) echo "checked"; ?>>
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
                                    if ($pid_co2_or[$i] == 1) {
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
                                <input type="text" value="<?php echo $pid_co2_relay[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>Co2Relay" title="This is the relay connected to the device that modulates CO2"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_co2_set[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>Co2Set" title="This is the desired CO2 level"/> ppm
                            </td>
                            <td align=center>
                                <input type="text" value="<?php echo $pid_co2_period[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2Period" title="This is the number of seconds to wait after the relay has been turned off before taking another CO2 reading and applying the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_co2_p[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_co2_i[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $pid_co2_d[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2_D" title="This is the Derivative value of the PID"/>
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
                            Light Relay: <input type="text" value="<?php echo $camera_relay; ?>" maxlength=4 size=1 name="lightrelay" title=""/>
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
                        <input type="submit" name="SQL" value="SQL">
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
                            `cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log > /var/tmp/relay.log`;
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
                            `cat /var/www/mycodo/log/daemon.log /var/www/mycodo/log/daemon-tmp.log > /var/tmp/daemon.log`;
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $daemon_log`;
                            } else {
                                echo `tail -n 30 $daemon_log`;
                            }
                        }
                        if(isset($_POST['SQL'])) {
                            view_sql_db();
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
                        <option value="1" <?php if ($timer_num == 1) echo "selected=\"selected\""; ?>>1</option>
                        <option value="2" <?php if ($timer_num == 2) echo "selected=\"selected\""; ?>>2</option>
                        <option value="3" <?php if ($timer_num == 3) echo "selected=\"selected\""; ?>>3</option>
                        <option value="4" <?php if ($timer_num == 4) echo "selected=\"selected\""; ?>>4</option>
                        <option value="5" <?php if ($timer_num == 5) echo "selected=\"selected\""; ?>>5</option>
                        <option value="6" <?php if ($timer_num == 6) echo "selected=\"selected\""; ?>>6</option>
                        <option value="7" <?php if ($timer_num == 7) echo "selected=\"selected\""; ?>>7</option>
                        <option value="8" <?php if ($timer_num == 8) echo "selected=\"selected\""; ?>>8</option>
                    </select>
                    <input type="submit" name="ChangeNoTimers" value="Save">
                </div>
                <?php if ($timer_num > 0) { ?>
                <div>

                    <table class="timers">
                        <tr>
                            <td>
                                Timer
                            </td>
                            <td>
                                Name
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
                        <?php for ($i = 1; $i <= $timer_num; $i++) { ?>
                        <tr>
                            <td>
                                <?php echo $i; ?>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $timer_name[$i]; ?>" maxlength=5 size=5 name="Timer<?php echo $i; ?>Name" title="This is the relay name for timer <?php echo $i; ?>"/>
                            </td>
                            <?php if ($timer_state[$i] == 0) { ?>
                                <th colspan=2 align=right>
                                    <nobr><input type="hidden" name="Timer<?php echo $i; ?>State" value="0"><input type="image" style="height: 0.9em;" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="Timer<?php echo $i; ?>StateChange" value="0"> | <button style="width: 40px;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="1">ON</button></nobr>
                                </td>
                                </th>
                                <?php
                            } else {
                                ?>
                                <th colspan=2 align=right>
                                    <nobr><input type="hidden" name="Timer<?php echo $i; ?>State" value="1"><input type="image" style="height: 0.9em;" src="/mycodo/img/on.jpg" alt="On" title="On" name="Timer<?php echo $i; ?>StateChange" value="1"> | <button style="width: 40px;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="0">OFF</button></nobr>
                                </th>
                            <?php
                            }
                            ?>
                            <td>
                                <input type="text" value="<?php echo $timer_relay[$i]; ?>" maxlength=1 size=1 name="Timer<?php echo $i; ?>Relay" title="This is the relay number for timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $timer_duration_on[$i]; ?>" maxlength=7 size=4 name="Timer<?php echo $i; ?>On" title="This is On duration of timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input type="text" value="<?php echo $timer_duration_off[$i]; ?>" maxlength=7 size=4 name="Timer<?php echo $i; ?>Off" title="This is Off duration for timer <?php echo $i; ?>"/>
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
                    <label class="notify">From</label><input class="smtp" type="text" value="<?php echo $smtp_email_from; ?>" maxlength=30 size=20 name="smtp_email_from" title=""/>
                </div>
                <div class="notify">
                    <label class="notify">To</label><input class="smtp" type="text" value="<?php echo $smtp_email_to; ?>" maxlength=30 size=20 name="smtp_email_to" title=""/>
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

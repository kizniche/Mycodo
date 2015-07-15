<?php
/*
*  restricted.php - Code can only be executed by non-guest users
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

// Check for changes to relay and timer variables (up to 8)
for ($p = 1; $p <= 8; $p++) {
    // Set relay variables
    if (isset($_POST['Mod' . $p . 'Relay'])) {
        $stmt = $db->prepare("UPDATE Relays SET Name=:name, Pin=:pin, Trigger=:trigger WHERE Id=:id");
        $stmt->bindValue(':name', $_POST['relay' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':pin', (int)$_POST['relay' . $p . 'pin'], SQLITE3_INTEGER);
        $stmt->bindValue(':trigger', (int)$_POST['relay' . $p . 'trigger'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
        $stmt->execute();
        if ($_POST['relay' . $p . 'pin'] != $relay_pin[$p]) {
            shell_exec($mycodo_client . ' --sqlreload ' . $p);
        }
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
        shell_exec($mycodo_client . ' --sqlreload 0');
    }

    // Set timer state
    if (isset($_POST['Timer' . $p . 'StateChange'])) {
        $stmt = $db->prepare("UPDATE Timers SET State=:state WHERE Id=:id");
        $stmt->bindValue(':state', (int)$_POST['Timer' . $p . 'StateChange'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $p, SQLITE3_INTEGER);
        $stmt->execute();
        shell_exec($mycodo_client . ' --sqlreload 0');
    }
}

// Check for changes to sensor variables (up to 4)
for ($p = 1; $p <= 4; $p++) {
    // Set Temperature/Humidity sensor variables
    if (isset($_POST['Change' . $p . 'HTSensor'])) {
        $stmt = $db->prepare("UPDATE HTSensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph WHERE Id=:id");
        $stmt->bindValue(':name', $_POST['sensorht' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':device', $_POST['sensorht' . $p . 'device'], SQLITE3_TEXT);
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
        shell_exec($mycodo_client . ' --sqlreload 0');
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
        if ((int)$_POST['Change' . $p . 'TempOR']) {
            shell_exec($mycodo_client . ' --pidstop Temp ' . $p);
            shell_exec($mycodo_client . ' --sqlreload 0');
        } else {
            shell_exec($mycodo_client . ' --sqlreload 0');
            shell_exec($mycodo_client . ' --pidstart Temp ' . $p);
        }
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
        if ((int)$_POST['Change' . $p . 'HumOR']) {
            shell_exec($mycodo_client . ' --pidstop Hum ' . $p);
            shell_exec($mycodo_client . ' --sqlreload 0');
        } else {
            shell_exec($mycodo_client . ' --sqlreload 0');
            shell_exec($mycodo_client . ' --pidstart Hum ' . $p);
        }
    }

    // Set CO2 sensor variables
    if (isset($_POST['Change' . $p . 'Co2Sensor'])) {
        $stmt = $db->prepare("UPDATE CO2Sensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph WHERE Id=:id");
        $stmt->bindValue(':name', $_POST['sensorco2' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':device', $_POST['sensorco2' . $p . 'device'], SQLITE3_TEXT);
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
        shell_exec($mycodo_client . ' --sqlreload 0');
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
        if ((int)$_POST['Change' . $p . 'Co2OR']) {
            shell_exec($mycodo_client . ' --pidstop CO2 ' . $p);
            shell_exec($mycodo_client . ' --sqlreload 0');
        } else {
            shell_exec($mycodo_client . ' --sqlreload 0');
            shell_exec($mycodo_client . ' --pidstart CO2 ' . $p);
        }
    }
}

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
    shell_exec($mycodo_client . ' --sqlreload 0');
}

// Change number of relays
if (isset($_POST['ChangeNoRelays'])) {
    $stmt = $db->prepare("UPDATE Numbers SET Relays=:relays");
    $stmt->bindValue(':relays', (int)$_POST['numrelays'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec($mycodo_client . ' --sqlreload 0');
}

// Change number of HT sensors
if (isset($_POST['ChangeNoHTSensors'])) {
    $stmt = $db->prepare("UPDATE Numbers SET HTSensors=:htsensors");
    $stmt->bindValue(':htsensors', (int)$_POST['numhtsensors'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec($mycodo_client . ' --sqlreload 0');
}

// Change number of CO2 sensors
if (isset($_POST['ChangeNoCo2Sensors'])) {
    $stmt = $db->prepare("UPDATE Numbers SET CO2Sensors=:co2sensors");
    $stmt->bindValue(':co2sensors', (int)$_POST['numco2sensors'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec($mycodo_client . ' --sqlreload 0');
}

// Change number of timers
if (isset($_POST['ChangeNoTimers'])) {
    $stmt = $db->prepare("UPDATE Numbers SET Timers=:timers");
    $stmt->bindValue(':timers', (int)$_POST['numtimers'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec($mycodo_client . ' --sqlreload 0');
}

// Change light relay
if (isset($_POST['ChangeCamera'])) {
    $stmt = $db->prepare("UPDATE Misc SET Camera_Relay=:lightrelay");
    $stmt->bindValue(':lightrelay', (int)$_POST['lightrelay'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec($mycodo_client . ' --sqlreload 0');
}

for ($p = 1; $p <= 8; $p++) {
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
}

// Capture still image from camera (with or without light activation)
if (isset($_POST['Capture'])) {
    if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) shell_exec("$stream_exec stop");
    if (isset($_POST['lighton'])) {
        if ($relay_trigger[$camera_relay] == 1) $trigger = 1;
        else $trigger = 0;
        $capture_output = shell_exec("$still_exec " . $relay_pin[$camera_relay] . " " . $trigger . " 2>&1; echo $?");
    } else $capture_output = shell_exec("$still_exec 2>&1; echo $?");
}

// Start video stream
if (isset($_POST['start-stream'])) {
    if (file_exists($lock_raspistill) || file_exists($lock_mjpg_streamer)) {
    echo 'Lock files already present. Press \'Stop Stream\' to kill processes and remove lock files.<br>';
    } else {
        if (isset($_POST['lighton'])) { // Turn light on
            if ($relay_trigger[$camera_relay] == 1) $trigger = 1;
            else $trigger = 0;
            shell_exec("$stream_exec start " . $relay_pin[$camera_relay] . " " . $trigger . " > /dev/null &");
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
        if ($relay_trigger[$camera_relay] == 1) $trigger = 0;
        else $trigger = 1;
        shell_exec("$stream_exec stop " . $relay_pin[$camera_relay] . " " . $trigger . " > /dev/null &");
    } else shell_exec("$stream_exec stop");
    sleep(1);
}

// Start time-lapse
if (isset($_POST['start-timelapse'])) {
    if (isset($_POST['timelapse_duration']) && isset($_POST['timelapse_runtime'])) {
        if (file_exists($lock_raspistill) || file_exists($lock_time_lapse)) {
        echo 'Lock files already present. Press \'Stop Timelapse\' to kill processes and remove lock files.<br>';
        } else {
            if (isset($_POST['timelapse_lighton'])) { // Turn light on
                if ($relay_trigger[$camera_relay] == 1) $trigger = 1;
                else $trigger = 0;
                shell_exec("$mycodo_client --timelapse start " . $relay_pin[$camera_relay] . " " . $trigger . " > /dev/null &");
                sleep(1);
            } else {
                shell_exec("$mycodo_client --timelapse start > /dev/null &");
                sleep(1);
            }
        }
    }
}

// Stop time-lapse
if (isset($_POST['stop-timelapse'])) {
    if (isset($_POST['timelapse_lighton'])) { // Turn light off
        if ($relay_trigger[$camera_relay] == 1) $trigger = 0;
        else $trigger = 1;
        shell_exec("$mycodo_client --timelapse stop " . $relay_pin[$camera_relay] . " " . $trigger . " > /dev/null &");
    } else shell_exec("$mycodo_client --timelapse stop");
    sleep(1);
}

// Request sensor read and log write
 if (isset($_POST['WriteSensorLog'])) {
    $editconfig = "$mycodo_client --writehtlog 0";
    shell_exec($editconfig);
    $editconfig = "$mycodo_client --writeco2log 0";
    shell_exec($editconfig);
}

?>

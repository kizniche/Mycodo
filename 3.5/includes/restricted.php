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

if (isset($_POST['UpdateMycodo'])) {
    $settings_error = shell_exec("$install_path/cgi-bin/mycodo-wrapper update");
}

if (isset($_POST['DaemonStop'])) {
    if (!file_exists($lock_daemon)) {
        $settings_error = 'Lock-file not present: ' . $lock_daemon . ' Is the daemon really running? Checking for and force-closing any running daemon.';
    } else {
        exec("$install_path/cgi-bin/mycodo-wrapper stop 2>&1 > /dev/null");
    }
}

if (isset($_POST['DaemonStart'])) {
    if (file_exists($lock_daemon)) {
        $settings_error = 'Lock-file present: ' . $lock_daemon . ' Is the daemon aready running? Delete the lock file to start or select "Restart Daemon"';
    } else {
        exec("$install_path/cgi-bin/mycodo-wrapper start 2>&1 > /dev/null");
    }
}

if (isset($_POST['DaemonRestart'])) {
    if (!file_exists($lock_daemon)) {
        $settings_error = 'Lock-file not present: ' . $lock_daemon . ' Is the daemon really running? Checking for and force-closing any running daemon before attempting to start.';
    } else {
        exec("$install_path/cgi-bin/mycodo-wrapper restart 2>&1 > /dev/null");
    }
}

if (isset($_POST['DaemonDebug'])) {
    exec("$install_path/cgi-bin/mycodo-wrapper debug 2>&1 > /dev/null");
}


// Check for changes to relay and timer variables (up to 8)
for ($p = 0; $p < count($relay_id); $p++) {
    // Set relay variables
    if (isset($_POST['Mod' . $p . 'Relay'])) {
        $stmt = $db->prepare("UPDATE Relays SET Name=:name, Pin=:pin, Trigger=:trigger, Start_State=:startstate WHERE Id=:id");
        $stmt->bindValue(':name', $_POST['relay' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':pin', (int)$_POST['relay' . $p . 'pin'], SQLITE3_INTEGER);
        $stmt->bindValue(':trigger', (int)$_POST['relay' . $p . 'trigger'], SQLITE3_INTEGER);
        $stmt->bindValue(':startstate', (int)$_POST['relay' . $p . 'startstate'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $relay_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        if ($_POST['relay' . $p . 'pin'] != $relay_pin[$p]) {
            shell_exec("$mycodo_client --sqlreload $p");
        } else {
            shell_exec("$mycodo_client --sqlreload 0");
        }
    }

    // Delete Relay
    if (isset($_POST['Delete' . $p . 'Relay'])) {
        $stmt = $db->prepare("DELETE FROM Relays WHERE Id=:id");
        $stmt->bindValue(':id', $relay_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --sqlreload 0");
    }

    // Send client command to turn relay on or off
    if (isset($_POST['R' . $p])) {
        $pin = $relay_pin[$p];
        if($relay_trigger[$p] == 0) $trigger_state = 'LOW';
        else $trigger_state = 'HIGH';
        if ($_POST['R' . $p] == 0) $desired_state = 'OFF';
        else $desired_state = 'ON';

        $GPIO_state = shell_exec("$gpio_path -g read $pin");
        if ($GPIO_state == 0 && $trigger_state == 'HIGH') $actual_state = 'LOW';
        else if ($GPIO_state == 0 && $trigger_state == 'LOW') $actual_state = 'HIGH';
        else if ($GPIO_state == 1 && $trigger_state == 'HIGH') $actual_state = 'HIGH';
        else if ($GPIO_state == 1 && $trigger_state == 'LOW') $actual_state = 'LOW';
        $relay = $p+1;
        if ($actual_state == 'LOW' && $desired_state == 'OFF') {
            $settings_error = "Error: Can't turn relay $relay Off, it's already Off";
        } else if ($actual_state == 'HIGH' && $desired_state == 'ON') {
            $settings_error = "Error: Can't turn relay $relay On, it's already On";
        } else {
            if ($desired_state == 'ON') $desired_state = 1;
            else $desired_state = 0;
            $relay = $p + 1;
            shell_exec("$mycodo_client -r $relay $desired_state");
        }
    }

    // Send client command to turn relay on for a number of seconds
    if (isset($_POST[$p . 'secON'])) {
        $name = $relay_name[$p];
        $pin = $relay_pin[$p];
        if($relay_trigger[$p] == 0) $trigger_state = 'LOW';
        else $trigger_state = 'HIGH';

        $GPIO_state = shell_exec("$gpio_path -g read $pin");
        if ($GPIO_state == 0 && $trigger_state == 'HIGH') $actual_state = 'LOW';
        else if ($GPIO_state == 0 && $trigger_state == 'LOW') $actual_state = 'HIGH';
        else if ($GPIO_state == 1 && $trigger_state == 'HIGH') $actual_state = 'HIGH';
        else if ($GPIO_state == 1 && $trigger_state == 'LOW') $actual_state = 'LOW';
        $seconds_on = $_POST['sR' . $p];

        if (!is_numeric($seconds_on) || $seconds_on < 2 || $seconds_on != round($seconds_on)) {
            $settings_error = "Error: Relay $p ($name): Seconds On must be a positive integer and > 1</div>";
        } else if ($actual_state == 'HIGH' && $desired_state == 'HIGH') {
            $settings_error = "Error: Can't turn relay $p On, it's already On";
        } else {
            shell_exec("$mycodo_client -r $p $seconds_on");
        }
    }
}

// Add relays
if (isset($_POST['AddRelays']) && isset($_POST['AddRelaysNumber'])) {
    for ($j = 0; $j < $_POST['AddRelaysNumber']; $j++) {
        $stmt = $db->prepare("INSERT INTO Relays VALUES(:id, 'Relay', 0, 0, 0)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->execute();
    }
    shell_exec("$mycodo_client --sqlreload 0");
}


for ($p = 0; $p < count($timer_id); $p++) {
    // Set timer variables
    if (isset($_POST['ChangeTimer' . $p])) {
        $stmt = $db->prepare("UPDATE Timers SET Name=:name, Relay=:relay, DurationOn=:durationon, DurationOff=:durationoff WHERE Id=:id");
        $stmt->bindValue(':name', $_POST['Timer' . $p . 'Name'], SQLITE3_TEXT);
        $stmt->bindValue(':relay', (int)$_POST['Timer' . $p . 'Relay'], SQLITE3_INTEGER);
        $stmt->bindValue(':durationon', (int)$_POST['Timer' . $p . 'On'], SQLITE3_INTEGER);
        $stmt->bindValue(':durationoff', (int)$_POST['Timer' . $p . 'Off'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $timer_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        shell_exec("$mycodo_client --sqlreload 0");
    }

    // Set timer state
    if (isset($_POST['Timer' . $p . 'StateChange'])) {
        $stmt = $db->prepare("UPDATE Timers SET State=:state WHERE Id=:id");
        $stmt->bindValue(':state', (int)$_POST['Timer' . $p . 'StateChange'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $timer_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        shell_exec("$mycodo_client --sqlreload 0");
        if ((int)$_POST['Timer' . $p . 'StateChange'] == 0) {
            $relay = $timer_relay[$p];
            shell_exec("$mycodo_client -r $relay 0");
        }
    }

    // Delete Timer
    if (isset($_POST['Delete' . $p . 'Timer'])) {
        $stmt = $db->prepare("DELETE FROM Timers WHERE Id=:id");
        $stmt->bindValue(':id', $timer_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --sqlreload 0");
    }
}

// Add timers
if (isset($_POST['AddTimers']) && isset($_POST['AddTimersNumber'])) {
    for ($j = 0; $j < $_POST['AddTimersNumber']; $j++) {
        $stmt = $db->prepare("INSERT INTO Timers VALUES(:id, 'Timer', 0, 0, 60, 360)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->execute();
    }
    shell_exec("$mycodo_client --sqlreload 0");
}


for ($p = 0; $p < count($sensor_t_id); $p++) {

    // Set Temperature PID override on or off
    if (isset($_POST['ChangeT' . $p . 'TempOR'])) {
        $stmt = $db->prepare("UPDATE TSensor SET Temp_OR=:tempor WHERE Id=:id");
        $stmt->bindValue(':tempor', (int)$_POST['ChangeT' . $p . 'TempOR'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        if ((int)$_POST['ChangeT' . $p . 'TempOR']) {
            shell_exec("$mycodo_client --pidstop TTemp $p");
            shell_exec("$mycodo_client --sqlreload 0");
        } else {
            shell_exec("$mycodo_client --sqlreload 0");
            shell_exec("$mycodo_client --pidstart TTemp $p");
        }
    }

    // Overwrite preset for Temperature sensor and PID variables
    if (isset($_POST['Change' . $p . 'TSensorOverwrite'])) {

        if (isset($_POST['sensort' . $p . 'preset']) && $_POST['sensort' . $p . 'preset'] != 'default') {
            $stmt = $db->prepare("UPDATE TSensorPreset SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph, Temp_Relay_High=:temprelayhigh, Temp_Relay_Low=:temprelaylow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd WHERE Preset=:preset");
            $stmt->bindValue(':name', $_POST['sensort' . $p . 'name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $_POST['sensort' . $p . 'device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', (int)$_POST['sensort' . $p . 'pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', (int)$_POST['sensort' . $p . 'period'], SQLITE3_INTEGER);
            if (isset($_POST['sensort' . $p . 'activated'])) {
                $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
            }
            if (isset($_POST['sensort' . $p . 'graph'])) {
                $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
            }
            $stmt->bindValue(':temprelayhigh', (int)$_POST['SetT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', (int)$_POST['SetT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', (float)$_POST['SetT' . $p . 'TempSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', (float)$_POST['SetT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', (int)$_POST['SetT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', (float)$_POST['SetT' . $p . 'Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', (float)$_POST['SetT' . $p . 'Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', (float)$_POST['SetT' . $p . 'Temp_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->execute();
        }

        $stmt = $db->prepare("UPDATE TSensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph, Temp_Relay_High=:temprelayhigh, Temp_Relay_Low=:temprelaylow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
        $stmt->bindValue(':name', $_POST['sensort' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':device', $_POST['sensort' . $p . 'device'], SQLITE3_TEXT);
        $stmt->bindValue(':pin', (int)$_POST['sensort' . $p . 'pin'], SQLITE3_INTEGER);
        $stmt->bindValue(':period', (int)$_POST['sensort' . $p . 'period'], SQLITE3_INTEGER);
        if (isset($_POST['sensort' . $p . 'activated'])) {
            $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
        } else {
            $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
        }
        if (isset($_POST['sensort' . $p . 'graph'])) {
            $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
        } else {
            $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
        }
        $stmt->bindValue(':temprelayhigh', (int)$_POST['SetT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
        $stmt->bindValue(':temprelaylow', (int)$_POST['SetT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
        $stmt->bindValue(':tempset', (float)$_POST['SetT' . $p . 'TempSet'], SQLITE3_FLOAT);
        $stmt->bindValue(':tempsetdir', (float)$_POST['SetT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
        $stmt->bindValue(':tempperiod', (int)$_POST['SetT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
        $stmt->bindValue(':tempp', (float)$_POST['SetT' . $p . 'Temp_P'], SQLITE3_FLOAT);
        $stmt->bindValue(':tempi', (float)$_POST['SetT' . $p . 'Temp_I'], SQLITE3_FLOAT);
        $stmt->bindValue(':tempd', (float)$_POST['SetT' . $p . 'Temp_D'], SQLITE3_FLOAT);
        $stmt->execute();

        if ($pid_ht_temp_or[$p] == 0) {
            pid_reload($mycodo_client, 'TTemp', $p);
        }
        if  ($pid_t_temp_or[$p] != 0) {
            shell_exec("$mycodo_client --sqlreload 0");
        }
    }

    // Load Temperature sensor and PID variables from preset
    if (isset($_POST['Change' . $p . 'TSensorLoad']) && $_POST['sensort' . $p . 'preset'] != 'default') {

        $stmt = $db->prepare('SELECT * FROM TSensorPreset WHERE Preset=:preset');
        $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset']);
        $result = $stmt->execute();
        $exist = $result->fetchArray();

        // Preset exists, change values to preset
        if ($exist != False) {

            $stmt = $db->prepare('SELECT Name, Pin, Device, Period, Activated, Graph, Temp_Relay_High, Temp_Relay_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D FROM TSensorPreset WHERE Preset=:preset');
            $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset']);
            $result = $stmt->execute();
            $row = $result->fetchArray();

            $stmt = $db->prepare("UPDATE TSensor SET Name=:name, Pin=:pin, Device=:device, Period=:period, Activated=:activated, Graph=:graph, Temp_Relay_High=:temprelayhigh, Temp_Relay_Low=:temprelaylow, Temp_OR=:tempor, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $row['Name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $row['Device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', $row['Pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', $row['Period'], SQLITE3_INTEGER);
            if ($row['Activated']) {
                $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
            }
            if ($row['Graph']) {
                $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
            }
            $stmt->bindValue(':temprelayhigh', $row['Temp_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', $row['Temp_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempor', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', $row['Temp_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', $row['Temp_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', $row['Temp_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', $row['Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', $row['Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', $row['Temp_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_t_temp_or[$p] == 0) {
                shell_exec("$mycodo_client --pidstop TTemp $p");
            }
            if  ($pid_t_temp_or[$p] != 0) {
                shell_exec("$mycodo_client --sqlreload 0");
            }
        } else {
            $sensor_error = 'Something wrnt wrong. The preset you selected doesn\'t exist.';
        }
    }

    // Save Temperature sensor and PID variables to a new preset
    if (isset($_POST['Change' . $p . 'TSensorNewPreset'])) {
        if(in_array($_POST['sensort' . $p . 'presetname'], $sensor_t_preset)) {
            $name = $_POST['sensort' . $p . 'presetname'];
            $sensor_error = "The preset name '$name' is already in use. Use a different name.";
        } else {
            if (isset($_POST['sensort' . $p . 'presetname']) && $_POST['sensort' . $p . 'presetname'] != '') {

                $stmt = $db->prepare("INSERT INTO TSensorPreset (Preset, Name, Pin, Device, Period, Activated, Graph, Temp_Relay_High, Temp_Relay_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D) VALUES(:preset, :name, :pin, :device, :period, :activated, :graph, :temprelayhigh, :temprelaylow, :tempset, :tempsetdir, :tempperiod, :tempp, :tempi, :tempd)");
                $stmt->bindValue(':preset', $_POST['sensort' . $p . 'presetname'], SQLITE3_TEXT);
                $stmt->bindValue(':name', $_POST['sensort' . $p . 'name'], SQLITE3_TEXT);
                $stmt->bindValue(':device', $_POST['sensort' . $p . 'device'], SQLITE3_TEXT);
                $stmt->bindValue(':pin', (int)$_POST['sensort' . $p . 'pin'], SQLITE3_INTEGER);
                $stmt->bindValue(':period', (int)$_POST['sensort' . $p . 'period'], SQLITE3_INTEGER);
                if (isset($_POST['sensort' . $p . 'activated'])) {
                    $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
                } else {
                    $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
                }
                if (isset($_POST['sensort' . $p . 'graph'])) {
                    $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
                } else {
                    $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
                }
                $stmt->bindValue(':temprelayhigh', (int)$_POST['SetT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaylow', (int)$_POST['SetT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempset', (float)$_POST['SetT' . $p . 'TempSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempsetdir', (float)$_POST['SetT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempperiod', (int)$_POST['SetT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempp', (float)$_POST['SetT' . $p . 'Temp_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempi', (float)$_POST['SetT' . $p . 'Temp_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempd', (float)$_POST['SetT' . $p . 'Temp_D'], SQLITE3_FLOAT);
                $stmt->execute();
            } else {
                $sensor_error = 'You must enter a name to create a new preset.';
            }
        }
    }

    // Rename Temperature preset
    if (isset($_POST['Change' . $p . 'TSensorRenamePreset']) && $_POST['sensort' . $p . 'preset'] != 'default') {
        if(in_array($_POST['sensort' . $p . 'presetname'], $sensor_t_preset)) {
            $name = $_POST['sensort' . $p . 'presetname'];
            $sensor_error = "The preset name '$name' is already in use. Use a different name.";
        } else {
            $stmt = $db->prepare("UPDATE TSensorPreset SET Preset=:presetnew WHERE Preset=:presetold");
            $stmt->bindValue(':presetold', $_POST['sensort' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->bindValue(':presetnew', $_POST['sensort' . $p . 'presetname'], SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    // Delete Temperature preset
    if (isset($_POST['Change' . $p . 'TSensorDelete']) && $_POST['sensort' . $p . 'preset'] != 'default') {
        $stmt = $db->prepare("DELETE FROM TSensorPreset WHERE Preset=:preset");
        $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset']);
        $stmt->execute();
    }

    // Delete Temperature sensors
    if (isset($_POST['Delete' . $p . 'TSensor'])) {
        $stmt = $db->prepare("DELETE FROM TSensor WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidrestart T");
    }
}

// Add Temperature sensors
if (isset($_POST['AddTSensors']) && isset($_POST['AddTSensorsNumber'])) {
    for ($j = 0; $j < $_POST['AddTSensorsNumber']; $j++) {
        $stmt = $db->prepare("INSERT INTO TSensor VALUES(:id, 'T-S', 0, 'DS18B20', 120, 0, 0, 0, 0, 1, 25.0, 0, 90, 0, 0, 0)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidrestart T");
    }
}




for ($p = 0; $p < count($sensor_ht_id); $p++) {

    // Set Temperature PID override on or off
    if (isset($_POST['ChangeHT' . $p . 'TempOR'])) {
        $stmt = $db->prepare("UPDATE HTSensor SET Temp_OR=:humor WHERE Id=:id");
        $stmt->bindValue(':humor', (int)$_POST['ChangeHT' . $p . 'TempOR'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        if ((int)$_POST['ChangeHT' . $p . 'TempOR']) {
            shell_exec("$mycodo_client --pidstop HTTemp $p");
            shell_exec("$mycodo_client --sqlreload 0");
        } else {
            shell_exec("$mycodo_client --sqlreload 0");
            shell_exec("$mycodo_client --pidstart HTTemp $p");
        }
    }

    // Set Humidity PID override on or off
    if (isset($_POST['ChangeHT' . $p . 'HumOR'])) {
        $stmt = $db->prepare("UPDATE HTSensor SET Hum_OR=:humor WHERE Id=:id");
        $stmt->bindValue(':humor', (int)$_POST['ChangeHT' . $p . 'HumOR'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        if ((int)$_POST['ChangeHT' . $p . 'HumOR']) {
            shell_exec("$mycodo_client --pidstop HTHum $p");
            shell_exec("$mycodo_client --sqlreload 0");
        } else {
            shell_exec("$mycodo_client --sqlreload 0");
            shell_exec("$mycodo_client --pidstart HTHum $p");
        }
    }


    // Overwrite preset for Temperature/Humidity sensor and PID variables
    if (isset($_POST['Change' . $p . 'HTSensorOverwrite'])) {

        if (isset($_POST['sensorht' . $p . 'preset']) && $_POST['sensorht' . $p . 'preset'] != 'default') {
            $stmt = $db->prepare("UPDATE HTSensorPreset SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph, Temp_Relay_High=:temprelayhigh, Temp_Relay_Low=:temprelaylow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Hum_Relay_High=:humrelayhigh, Hum_Relay_Low=:humrelaylow, Hum_Set=:humset, Hum_Set_Direction=:humsetdir, Hum_Period=:humperiod, Hum_P=:hum, Hum_I=:hum, Hum_D=:humd WHERE Preset=:preset");
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
            $stmt->bindValue(':temprelayhigh', (int)$_POST['SetHT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', (int)$_POST['SetHT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', (float)$_POST['SetHT' . $p . 'TempSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', (float)$_POST['SetHT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', (int)$_POST['SetHT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', (float)$_POST['SetHT' . $p . 'Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', (float)$_POST['SetHT' . $p . 'Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', (float)$_POST['SetHT' . $p . 'Temp_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':humrelayhigh', (int)$_POST['SetHT' . $p . 'HumRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':humrelaylow', (int)$_POST['SetHT' . $p . 'HumRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':humset', (float)$_POST['SetHT' . $p . 'HumSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':humsetdir', (float)$_POST['SetHT' . $p . 'HumSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':humperiod', (int)$_POST['SetHT' . $p . 'HumPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':hump', (float)$_POST['SetHT' . $p . 'Hum_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':humi', (float)$_POST['SetHT' . $p . 'Hum_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':humd', (float)$_POST['SetHT' . $p . 'Hum_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->execute();
        }

        $stmt = $db->prepare("UPDATE HTSensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph, Temp_Relay_High=:temprelayhigh, Temp_Relay_Low=:temprelaylow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Hum_Relay_High=:humrelayhigh, Hum_Relay_Low=:humrelaylow, Hum_Set=:humset, Hum_Set_Direction=:humsetdir, Hum_Period=:humperiod, Hum_P=:hump, Hum_I=:humi, Hum_D=:humd WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
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
        $stmt->bindValue(':temprelayhigh', (int)$_POST['SetHT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
        $stmt->bindValue(':temprelaylow', (int)$_POST['SetHT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
        $stmt->bindValue(':tempset', (float)$_POST['SetHT' . $p . 'TempSet'], SQLITE3_FLOAT);
        $stmt->bindValue(':tempsetdir', (float)$_POST['SetHT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
        $stmt->bindValue(':tempperiod', (int)$_POST['SetHT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
        $stmt->bindValue(':tempp', (float)$_POST['SetHT' . $p . 'Temp_P'], SQLITE3_FLOAT);
        $stmt->bindValue(':tempi', (float)$_POST['SetHT' . $p . 'Temp_I'], SQLITE3_FLOAT);
        $stmt->bindValue(':tempd', (float)$_POST['SetHT' . $p . 'Temp_D'], SQLITE3_FLOAT);
        $stmt->bindValue(':humrelayhigh', (int)$_POST['SetHT' . $p . 'HumRelayHigh'], SQLITE3_INTEGER);
        $stmt->bindValue(':humrelaylow', (int)$_POST['SetHT' . $p . 'HumRelayLow'], SQLITE3_INTEGER);
        $stmt->bindValue(':humset', (float)$_POST['SetHT' . $p . 'HumSet'], SQLITE3_FLOAT);
        $stmt->bindValue(':humsetdir', (float)$_POST['SetHT' . $p . 'HumSetDir'], SQLITE3_INTEGER);
        $stmt->bindValue(':humperiod', (int)$_POST['SetHT' . $p . 'HumPeriod'], SQLITE3_INTEGER);
        $stmt->bindValue(':hump', (float)$_POST['SetHT' . $p . 'Hum_P'], SQLITE3_FLOAT);
        $stmt->bindValue(':humi', (float)$_POST['SetHT' . $p . 'Hum_I'], SQLITE3_FLOAT);
        $stmt->bindValue(':humd', (float)$_POST['SetHT' . $p . 'Hum_D'], SQLITE3_FLOAT);
        $stmt->execute();

        if ($pid_ht_temp_or[$p] == 0) {
            pid_reload($mycodo_client, 'HTTemp', $p);
        }
        if ($pid_ht_hum_or[$p] == 0) {
            pid_reload($mycodo_client, 'HTHum', $p);
        }
        if  ($pid_ht_temp_or[$p] != 0 or $pid_ht_hum_or[$p] != 0) {
            shell_exec("$mycodo_client --sqlreload 0");
        }
    }


    // Load Temperature/Humidity sensor and PID variables from preset
    if (isset($_POST['Change' . $p . 'HTSensorLoad']) && $_POST['sensorht' . $p . 'preset'] != 'default') {

        $stmt = $db->prepare('SELECT * FROM HTSensorPreset WHERE Preset=:preset');
        $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset']);
        $result = $stmt->execute();
        $exist = $result->fetchArray();

        // Preset exists, change values to preset
        if ($exist != False) {

            $stmt = $db->prepare('SELECT Name, Pin, Device, Period, Activated, Graph, Temp_Relay_High, Temp_Relay_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relay_High, Hum_Relay_Low, Hum_Set, Hum_Set_Direction, Hum_Period, Hum_P, Hum_I, Hum_D FROM HTSensorPreset WHERE Preset=:preset');
            $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset']);
            $result = $stmt->execute();
            $row = $result->fetchArray();

            $stmt = $db->prepare("UPDATE HTSensor SET Name=:name, Pin=:pin, Device=:device, Period=:period, Activated=:activated, Graph=:graph, Temp_Relay_High=:temprelayhigh, Temp_Relay_Low=:temprelaylow, Temp_OR=:tempor, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Hum_Relay_High=:humrelayhigh, Hum_Relay_Low=:humrelaylow, Hum_OR=:humor, Hum_Set=:humset, Hum_Set_Direction=:humsetdir, Hum_Period=:humperiod, Hum_P=:hump, Hum_I=:humi, Hum_D=:humd WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $row['Name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $row['Device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', $row['Pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', $row['Period'], SQLITE3_INTEGER);
            if ($row['Activated']) {
                $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
            }
            if ($row['Graph']) {
                $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
            }
            $stmt->bindValue(':temprelayhigh', $row['Temp_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', $row['Temp_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempor', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', $row['Temp_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', $row['Temp_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', $row['Temp_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', $row['Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', $row['Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', $row['Temp_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':humrelayhigh', $row['Hum_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':humrelaylow', $row['Hum_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':humor', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':humset', $row['Hum_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':humsetdir', $row['Hum_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':humperiod', $row['Hum_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':hump', $row['Hum_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':humi', $row['Hum_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':humd', $row['Hum_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_ht_temp_or[$p] == 0) {
                shell_exec("$mycodo_client --pidstop HTTemp $p");
            }
            if ($pid_ht_hum_or[$p] == 0) {
                shell_exec("$mycodo_client --pidstop HTHum $p");
            }
            if  ($pid_ht_temp_or[$p] != 0 or $pid_ht_hum_or[$p] != 0) {
                shell_exec("$mycodo_client --sqlreload 0");
            }
        } else {
            $sensor_error = 'Something wrnt wrong. The preset you selected doesn\'t exist.';
        }
    }


    // Save Temperature/Humidity sensor and PID variables to a new preset
    if (isset($_POST['Change' . $p . 'HTSensorNewPreset'])) {
        if(in_array($_POST['sensorht' . $p . 'presetname'], $sensor_ht_preset)) {
            $name = $_POST['sensorht' . $p . 'presetname'];
            $sensor_error = "The preset name '$name' is already in use. Use a different name.";
        } else {
            if (isset($_POST['sensorht' . $p . 'presetname']) && $_POST['sensorht' . $p . 'presetname'] != '') {

                $stmt = $db->prepare("INSERT INTO HTSensorPreset (Preset, Name, Pin, Device, Period, Activated, Graph, Temp_Relay_High, Temp_Relay_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relay_High, Hum_Relay_Low, Hum_Set, Hum_Set_Direction, Hum_Period, Hum_P, Hum_I, Hum_D) VALUES(:preset, :name, :pin, :device, :period, :activated, :graph, :temprelayhigh, :temprelaylow, :tempset, :tempsetdir, :tempperiod, :tempp, :tempi, :tempd, :humrelayhigh, :humrelaylow, :humset, :humsetdir, :humperiod, :hump, :humi, :humd)");
                $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'presetname'], SQLITE3_TEXT);
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
                $stmt->bindValue(':temprelayhigh', (int)$_POST['SetHT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaylow', (int)$_POST['SetHT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempset', (float)$_POST['SetHT' . $p . 'TempSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempsetdir', (float)$_POST['SetHT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempperiod', (int)$_POST['SetHT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempp', (float)$_POST['SetHT' . $p . 'Temp_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempi', (float)$_POST['SetHT' . $p . 'Temp_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempd', (float)$_POST['SetHT' . $p . 'Temp_D'], SQLITE3_FLOAT);
                $stmt->bindValue(':humrelayhigh', (int)$_POST['SetHT' . $p . 'HumRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':humrelaylow', (int)$_POST['SetHT' . $p . 'HumRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':humset', (float)$_POST['SetHT' . $p . 'HumSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':humsetdir', (float)$_POST['SetHT' . $p . 'HumSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':humperiod', (int)$_POST['SetHT' . $p . 'HumPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':hump', (float)$_POST['SetHT' . $p . 'Hum_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':humi', (float)$_POST['SetHT' . $p . 'Hum_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':humd', (float)$_POST['SetHT' . $p . 'Hum_D'], SQLITE3_FLOAT);
                $stmt->execute();
            } else {
                $sensor_error = 'You must enter a name to create a new preset.';
            }
        }
    }

    // Rename Temperature/Humidity preset
    if (isset($_POST['Change' . $p . 'HTSensorRenamePreset']) && $_POST['sensorht' . $p . 'preset'] != 'default') {
        if(in_array($_POST['sensorht' . $p . 'presetname'], $sensor_ht_preset)) {
            $name = $_POST['sensorht' . $p . 'presetname'];
            $sensor_error = "The preset name '$name' is already in use. Use a different name.";
        } else {
            $stmt = $db->prepare("UPDATE HTSensorPreset SET Preset=:presetnew WHERE Preset=:presetold");
            $stmt->bindValue(':presetold', $_POST['sensorht' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->bindValue(':presetnew', $_POST['sensorht' . $p . 'presetname'], SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    // Delete Temperature/Humidity preset
    if (isset($_POST['Change' . $p . 'HTSensorDelete']) && $_POST['sensorht' . $p . 'preset'] != 'default') {
        $stmt = $db->prepare("DELETE FROM HTSensorPreset WHERE Preset=:preset");
        $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset']);
        $stmt->execute();
    }

    // Delete HT sensors
    if (isset($_POST['Delete' . $p . 'HTSensor'])) {
        $stmt = $db->prepare("DELETE FROM HTSensor WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidrestart HT");
    }
}

// Add HT sensors
if (isset($_POST['AddHTSensors']) && isset($_POST['AddHTSensorsNumber'])) {
    for ($j = 0; $j < $_POST['AddHTSensorsNumber']; $j++) {
        $stmt = $db->prepare("INSERT INTO HTSensor VALUES(:id, 'HT-S', 0, 'DHT22', 120, 0, 0, 0, 0, 1, 25.0, 0, 90, 0, 0, 0, 0, 0, 1, 50.0, 0, 90, 0, 0, 0)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidrestart HT");
    }
}



for ($p = 0; $p < count($sensor_co2_id); $p++) {

    // Set CO2 PID override on or off
    if (isset($_POST['ChangeCO2' . $p . 'CO2OR'])) {
        $stmt = $db->prepare("UPDATE CO2Sensor SET CO2_OR=:co2or WHERE Id=:id");
        $stmt->bindValue(':co2or', (int)$_POST['ChangeCO2' . $p . 'CO2OR'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        if ((int)$_POST['ChangeCO2' . $p . 'CO2OR']) {
            shell_exec("$mycodo_client --pidstop CO2 $p");
            shell_exec("$mycodo_client --sqlreload 0");
        } else {
            shell_exec("$mycodo_client --sqlreload 0");
            shell_exec("$mycodo_client --pidstart CO2 $p");
        }
    }

    // Overwrite preset for CO2 sensor and PID variables
    if (isset($_POST['Change' . $p . 'CO2SensorOverwrite'])) {

        if (isset($_POST['sensorco2' . $p . 'preset']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {
            $stmt = $db->prepare("UPDATE CO2SensorPreset SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph, CO2_Relay_High=:co2relayhigh, CO2_Relay_Low=:co2relaylow, CO2_Set=:co2set, CO2_Set_Direction=:co2setdir, CO2_Period=:co2period, CO2_P=:co2p, CO2_I=:co2i, CO2_D=:co2d WHERE Preset=:preset");
            $stmt->bindValue(':name', $_POST['sensorco2' . $p . 'name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $_POST['sensorco2' . $p . 'device'], SQLITE3_TEXT);
            if ($_POST['sensorco2' . $p . 'device'] == 'K30') {
                $stmt->bindValue(':pin', $sensor_co2_pin[$p], SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':pin', (int)$_POST['sensorco2' . $p . 'pin'], SQLITE3_INTEGER);
            }
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
            $stmt->bindValue(':co2relayhigh', (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2relaylow', (int)$_POST['SetCO2' . $p . 'CO2RelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2set', (float)$_POST['SetCO2' . $p . 'CO2Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2setdir', (float)$_POST['SetCO2' . $p . 'CO2SetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2period', (int)$_POST['SetCO2' . $p . 'CO2Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2p', (float)$_POST['SetCO2' . $p . 'CO2_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2i', (float)$_POST['SetCO2' . $p . 'CO2_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2d', (float)$_POST['SetCO2' . $p . 'CO2_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->execute();
        }

        $stmt = $db->prepare("UPDATE CO2Sensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Activated=:activated, Graph=:graph, CO2_Relay_High=:co2relayhigh, CO2_Relay_Low=:co2relaylow, CO2_Set=:co2set, CO2_Set_Direction=:co2setdir, CO2_Period=:co2period, CO2_P=:co2p, CO2_I=:co2i, CO2_D=:co2d WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
        $stmt->bindValue(':name', $_POST['sensorco2' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':device', $_POST['sensorco2' . $p . 'device'], SQLITE3_TEXT);
        if ($_POST['sensorco2' . $p . 'device'] == 'K30') {
            $stmt->bindValue(':pin', $sensor_co2_pin[$p], SQLITE3_INTEGER);
        } else {
            $stmt->bindValue(':pin', (int)$_POST['sensorco2' . $p . 'pin'], SQLITE3_INTEGER);
        }
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
        $stmt->bindValue(':co2relayhigh', (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'], SQLITE3_INTEGER);
        $stmt->bindValue(':co2relaylow', (int)$_POST['SetCO2' . $p . 'CO2RelayLow'], SQLITE3_INTEGER);
        $stmt->bindValue(':co2set', (float)$_POST['SetCO2' . $p . 'CO2Set'], SQLITE3_FLOAT);
        $stmt->bindValue(':co2setdir', (float)$_POST['SetCO2' . $p . 'CO2SetDir'], SQLITE3_INTEGER);
        $stmt->bindValue(':co2period', (int)$_POST['SetCO2' . $p . 'CO2Period'], SQLITE3_INTEGER);
        $stmt->bindValue(':co2p', (float)$_POST['SetCO2' . $p . 'CO2_P'], SQLITE3_FLOAT);
        $stmt->bindValue(':co2i', (float)$_POST['SetCO2' . $p . 'CO2_I'], SQLITE3_FLOAT);
        $stmt->bindValue(':co2d', (float)$_POST['SetCO2' . $p . 'CO2_D'], SQLITE3_FLOAT);

        $stmt->execute();

        if ($pid_co2_or[$p] == 0) {
            pid_reload($mycodo_client, 'CO2', $p);
        }
        if  ($pid_co2_or[$p] != 0) {
            shell_exec("$mycodo_client --sqlreload 0");
        }
    }

    // Load CO2 sensor and PID variables from preset
    if (isset($_POST['Change' . $p . 'CO2SensorLoad']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {

        $stmt = $db->prepare('SELECT * FROM CO2SensorPreset WHERE Preset=:preset');
        $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset']);
        $result = $stmt->execute();
        $exist = $result->fetchArray();

        // Preset exists, change values to preset
        if ($exist != False) {

            $stmt = $db->prepare('SELECT Name, Pin, Device, Period, Activated, Graph, CO2_Relay_High, CO2_Relay_Low, CO2_Set, CO2_Set_Direction, CO2_Period, CO2_P, CO2_I, CO2_D FROM CO2SensorPreset WHERE Preset=:preset');
            $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset']);
            $result = $stmt->execute();
            $row = $result->fetchArray();

            $stmt = $db->prepare("UPDATE CO2Sensor SET Name=:name, Pin=:pin, Device=:device, Period=:period, Activated=:activated, Graph=:graph, CO2_Relay_High=:co2relayhigh, CO2_Relay_Low=:co2relaylow, CO2_OR=:co2or, CO2_Set=:co2set, CO2_Set_Direction=:co2setdir, CO2_Period=:co2period, CO2_P=:co2p, CO2_I=:co2i, CO2_D=:co2d WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $row['Name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $row['Device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', $row['Pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', $row['Period'], SQLITE3_INTEGER);
            if ($row['Activated']) {
                $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
            }
            if ($row['Graph']) {
                $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
            }
            $stmt->bindValue(':co2relayhigh', $row['CO2_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2relaylow', $row['CO2_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2or', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':co2set', $row['CO2_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2setdir', $row['CO2_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2period', $row['CO2_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2p', $row['CO2_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2i', $row['CO2_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2d', $row['CO2_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_co2_or[$p] == 0) {
                shell_exec("$mycodo_client --pidstop CO2 $p");
            }
            if  ($pid_co2_or[$p] != 0) {
                shell_exec("$mycodo_client --sqlreload 0");
            }
        } else {
            $sensor_error = 'Something wrnt wrong. The preset you selected doesn\'t exist.';
        }
    }

    // Save CO2 sensor and PID variables to a new preset
    if (isset($_POST['Change' . $p . 'CO2SensorNewPreset'])) {
        if(in_array($_POST['sensorco2' . $p . 'presetname'], $sensor_co2_preset)) {
            $name = $_POST['sensorco2' . $p . 'presetname'];
            $sensor_error = "The preset name '$name' is already in use. Use a different name.";
        } else {
            if (isset($_POST['sensorco2' . $p . 'presetname']) && $_POST['sensorco2' . $p . 'presetname'] != '') {

                $stmt = $db->prepare("INSERT INTO CO2SensorPreset (Preset, Name, Pin, Device, Period, Activated, Graph, CO2_Relay_High, CO2_Relay_Low, CO2_Set, CO2_Set_Direction, CO2_Period, CO2_P, CO2_I, CO2_D) VALUES(:preset, :name, :pin, :device, :period, :activated, :graph, :co2relayhigh, :co2relaylow, :co2set, :co2setdir, :co2period, :co2p, :co2i, :co2d)");
                $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'presetname'], SQLITE3_TEXT);
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
                $stmt->bindValue(':co2relayhigh', (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2relaylow', (int)$_POST['SetCO2' . $p . 'CO2RelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2set', (float)$_POST['SetCO2' . $p . 'CO2Set'], SQLITE3_FLOAT);
                $stmt->bindValue(':co2setdir', (float)$_POST['SetCO2' . $p . 'CO2SetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2period', (int)$_POST['SetCO2' . $p . 'CO2Period'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2p', (float)$_POST['SetCO2' . $p . 'CO2_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':co2i', (float)$_POST['SetCO2' . $p . 'CO2_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':co2d', (float)$_POST['SetCO2' . $p . 'CO2_D'], SQLITE3_FLOAT);
                $stmt->execute();
            } else {
                $sensor_error = 'You must enter a name to create a new preset.';
            }
        }
    }

    // Rename CO2 preset
    if (isset($_POST['Change' . $p . 'CO2SensorRenamePreset']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {
        if(in_array($_POST['sensorco2' . $p . 'presetname'], $sensor_co2_preset)) {
            $name = $_POST['sensorco2' . $p . 'presetname'];
            $sensor_error = "The preset name '$name' is already in use. Use a different name.";
        } else {
            $stmt = $db->prepare("UPDATE CO2SensorPreset SET Preset=:presetnew WHERE Preset=:presetold");
            $stmt->bindValue(':presetold', $_POST['sensorco2' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->bindValue(':presetnew', $_POST['sensorco2' . $p . 'presetname'], SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    // Delete CO2 preset
    if (isset($_POST['Change' . $p . 'CO2SensorDelete']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {
        $stmt = $db->prepare("DELETE FROM CO2SensorPreset WHERE Preset=:preset");
        $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset']);
        $stmt->execute();
    }

    // Delete CO2 sensors
    if (isset($_POST['Delete' . $p . 'CO2Sensor'])) {
        $stmt = $db->prepare("DELETE FROM CO2Sensor WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidrestart CO2");
    }
}

// Add CO2 sensors
if (isset($_POST['AddCO2Sensors']) && isset($_POST['AddCO2SensorsNumber'])) {
    for ($j = 0; $j < $_POST['AddCO2SensorsNumber']; $j++) {
        $stmt = $db->prepare("INSERT INTO CO2Sensor VALUES(:id, 'CO2-S', 0, 'K30', 120, 0, 0, 0, 0, 1, 25.0, 0, 90, 0, 0, 0)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidrestart T");
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
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change number of relays
if (isset($_POST['ChangeNoRelays'])) {
    $stmt = $db->prepare("UPDATE Numbers SET Relays=:relays");
    $stmt->bindValue(':relays', (int)$_POST['numrelays'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change number of T sensors
if (isset($_POST['ChangeNoTSensors'])) {
    $stmt = $db->prepare("UPDATE Numbers SET TSensors=:tsensors");
    $stmt->bindValue(':tsensors', (int)$_POST['numtsensors'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change number of HT sensors
if (isset($_POST['ChangeNoHTSensors'])) {
    $stmt = $db->prepare("UPDATE Numbers SET HTSensors=:htsensors");
    $stmt->bindValue(':htsensors', (int)$_POST['numhtsensors'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}


// Change number of CO2 sensors
if (isset($_POST['ChangeNoCo2Sensors'])) {
    $stmt = $db->prepare("UPDATE Numbers SET CO2Sensors=:co2sensors");
    $stmt->bindValue(':co2sensors', (int)$_POST['numco2sensors'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change number of timers
if (isset($_POST['ChangeNoTimers'])) {
    $stmt = $db->prepare("UPDATE Numbers SET Timers=:timers");
    $stmt->bindValue(':timers', (int)$_POST['numtimers'], SQLITE3_INTEGER);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change camera still image settings
if (isset($_POST['ChangeStill'])) {
    $stmt = $db->prepare("UPDATE CameraStill SET Relay=:relay, Timestamp=:timestamp, Display_Last=:displaylast, Extra_Parameters=:extra");
    $stmt->bindValue(':relay', (int)$_POST['Still_Relay'], SQLITE3_INTEGER);
    $stmt->bindValue(':timestamp', (int)$_POST['Still_Timestamp'], SQLITE3_INTEGER);
    $stmt->bindValue(':displaylast', (int)$_POST['Still_DisplayLast'], SQLITE3_INTEGER);
    $stmt->bindValue(':extra', $_POST['Still_Extra_Parameters'], SQLITE3_TEXT);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change camera video stream settings
if (isset($_POST['ChangeStream'])) {
    $stmt = $db->prepare("UPDATE CameraStream SET Relay=:relay, Extra_Parameters=:extra");
    $stmt->bindValue(':relay', (int)$_POST['Stream_Relay'], SQLITE3_INTEGER);
    $stmt->bindValue(':extra', $_POST['Stream_Extra_Parameters'], SQLITE3_TEXT);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change camera timelapse settings
if (isset($_POST['ChangeTimelapse'])) {
    $stmt = $db->prepare("UPDATE CameraTimelapse SET Relay=:relay, Path=:path, Prefix=:prefix, File_Timestamp=:timestamp, Display_Last=:displaylast, Extra_Parameters=:extra");
    $stmt->bindValue(':relay', (int)$_POST['Timelapse_Relay'], SQLITE3_INTEGER);
    $stmt->bindValue(':path', $_POST['Timelapse_Path'], SQLITE3_TEXT);
    $stmt->bindValue(':prefix', $_POST['Timelapse_Prefix'], SQLITE3_TEXT);
    $stmt->bindValue(':timestamp', (int)$_POST['Timelapse_Timestamp'], SQLITE3_INTEGER);
    $stmt->bindValue(':displaylast', (int)$_POST['Timelapse_DisplayLast'], SQLITE3_INTEGER);
    $stmt->bindValue(':extra', $_POST['Timelapse_Extra_Parameters'], SQLITE3_TEXT);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload 0");
}

// Change interface settings
if (isset($_POST['ChangeInterface'])) {
    $stmt = $db->prepare("UPDATE Misc SET Refresh_Time=:refreshtime");
    $stmt->bindValue(':refreshtime', (int)$_POST['refresh_time'], SQLITE3_INTEGER);
    $stmt->execute();
}


// Camera error check
if (isset($_POST['CaptureStill']) || isset($_POST['start-stream']) || isset($_POST['start-timelapse'])) {
    if (file_exists($lock_raspistill)) {
        $camera_error = "Error: Still image lock file present. Kill raspistill process and remove lock file: $lock_raspistill";
    } else if (file_exists($lock_mjpg_streamer)) {
        $camera_error = "Error: Stream lock file present. Stop stream to kill processes and remove lock file $lock_mjpg_streamer";
    } else if (file_exists($lock_timelapse)) {
        $camera_error = "Error: Timelapse lock file present. Stop time-lapse to kill processes and remove lock files $lock_timelapse";
    }
}

// Capture still image from camera (with or without light activation)
if (isset($_POST['CaptureStill']) && !file_exists($lock_raspistill) && !file_exists($lock_mjpg_streamer) && !file_exists($lock_timelapse)) {
    shell_exec("touch $lock_raspistill");
    if ($still_relay) {
        if ($relay_trigger[$still_relay-1] == 1) $trigger = 1;
        else $trigger = 0;
        $rpin = $relay_pin[$still_relay-1];
        if ($still_timestamp) {
            $cmd = "$still_exec $rpin $trigger 1 2>&1; echo $?";
        } else {
            $cmd = "$still_exec $rpin $trigger 0 2>&1; echo $?";
        }
    } else {
        if ($still_timestamp) {
            $cmd = "$still_exec 0 0 1 2>&1; echo $?";
        } else {
            $cmd = "$still_exec 0 0 0 2>&1; echo $?";
        }
    }
    shell_exec($cmd);
    shell_exec("rm -f $lock_raspistill");
}

// Start video stream
if (isset($_POST['start-stream']) && !file_exists($lock_raspistill) && !file_exists($lock_mjpg_streamer) && !file_exists($lock_timelapse)) {
    shell_exec("touch $lock_mjpg_streamer");
    if ($stream_relay) { // Turn light on
        if ($relay_trigger[$stream_relay-1] == 1) $trigger = 1;
        else $trigger = 0;
        $rpin = $relay_pin[$stream_relay-1];
        shell_exec("touch $lock_mjpg_streamer_relay");
        shell_exec("$stream_exec start $rpin $trigger > /dev/null &");
        sleep(1);
    } else {
        shell_exec("$stream_exec start > /dev/null &");
        sleep(1);
    }
}

// Stop video stream
if (isset($_POST['stop-stream'])) {
    if (file_exists($lock_mjpg_streamer_relay)) { // Turn light off
        if ($relay_trigger[$stream_relay] == 1) $trigger = 0;
        else $trigger = 1;
        $rpin = $relay_pin[$stream_relay-1];
        shell_exec("rm -f $lock_mjpg_streamer_relay");
        shell_exec("$stream_exec stop $rpin $trigger > /dev/null &");
    } else shell_exec("$stream_exec stop");
    shell_exec("rm -f $lock_mjpg_streamer");
    sleep(1);
}

// Start time-lapse
if (isset($_POST['start-timelapse'])) {
    if (isset($_POST['timelapse_duration']) && isset($_POST['timelapse_runtime']) && !file_exists($lock_raspistill) && !file_exists($lock_mjpg_streamer) && !file_exists($lock_timelapse)) {

        if ($timelapse_relay) {
            if ($relay_trigger[$timelapse_relay-1] == 1) $trigger = 1;
            else $trigger = 0;
        } else $trigger = 0;

        if ($timelapse_timestamp) $timestamp = substr(`date +"%Y%m%d%H%M%S"`, 0, -1);
        else $timelapse = 0;

        $duration = $_POST['timelapse_duration'] * 60 * 1000;
        $timeout = $_POST['timelapse_runtime'] * 60 * 1000;

        shell_exec("touch $lock_timelapse");

        if ($timelapse_relay) shell_exec("touch $lock_timelapse_light");

        shell_exec("$timelapse_exec start $timelapse_relay $timelapse_path $timelapse_prefix $timestamp $duration $timeout > /dev/null &");

        sleep(1);
    }
}

// Stop time-lapse
if (isset($_POST['stop-timelapse'])) {
    if (file_exists($lock_timelapse_light)) { // Turn light off
        shell_exec("rm -f $lock_timelapse_light");
        shell_exec("$timelapse_exec stop $timelapse_relay > /dev/null &");
    } else shell_exec("$timelapse_exec stop > /dev/null &");
    shell_exec("rm -f $lock_timelapse");
    sleep(1);
}

// Request sensor read and log write
 if (isset($_POST['WriteSensorLog'])) {
    shell_exec("$mycodo_client --writetlog 0");
    shell_exec("$mycodo_client --writehtlog 0");
    shell_exec("$mycodo_client --writeco2log 0");
}
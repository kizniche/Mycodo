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


/*
 *
 * System Update
 *
 */


if (isset($_POST['UpdateCheck'])) {
    exec("$install_path/cgi-bin/mycodo-wrapper updatecheck 2>&1", $update_check_output, $update_check_return);
    if ($update_check_return) {
        $settings_error = "There is a newer version of Mycodo available.";
    } else {
        $settings_error = "You are running the latest version of Mycodo.";
    }
}

if (isset($_POST['UpdateMycodo'])) {
    exec("$install_path/cgi-bin/mycodo-wrapper updatecheck 2>&1", $update_check_output, $update_check_return);
    if ($update_check_return) {
        exec("$install_path/cgi-bin/mycodo-wrapper update >> /var/www/mycodo/log/update.log &");
        $settings_error = "The update process has begun. You can follow the progress of the update from the Update Log under the Data tab.";
    } else {
        $settings_error = "You are already running the latest version of Mycodo.";
    }
}




/*
 *
 * Daemon Control
 *
 */


if (isset($_POST['DaemonStop'])) {
    if (!file_exists($lock_daemon)) {
        $settings_error = 'Error: Lock-file not present: ' . $lock_daemon . ' Is the daemon really running? Checking for and force-closing any running daemon.';
    } else {
        exec("$install_path/cgi-bin/mycodo-wrapper stop 2>&1 > /dev/null");
    }
}

if (isset($_POST['DaemonStart'])) {
    if (file_exists($lock_daemon)) {
        $settings_error = 'Error: Lock-file present: ' . $lock_daemon . ' Is the daemon aready running? Delete the lock file to start or select "Restart Daemon"';
    } else {
        exec("$install_path/cgi-bin/mycodo-wrapper start 2>&1 > /dev/null");
    }
}

if (isset($_POST['DaemonRestart'])) {
    if (!file_exists($lock_daemon)) {
        $settings_error = 'Error: Lock-file not present: ' . $lock_daemon . ' Is the daemon really running? Checking for and force-closing any running daemon before attempting to start.';
    } else {
        exec("$install_path/cgi-bin/mycodo-wrapper restart 2>&1 > /dev/null");
    }
}

if (isset($_POST['DaemonDebug'])) {
    exec("$install_path/cgi-bin/mycodo-wrapper debug 2>&1 > /dev/null");
}




/*
 *
 * Relays
 *
 */


// Add relays
if (isset($_POST['AddRelays']) && isset($_POST['AddRelaysNumber'])) {
    for ($j = 0; $j < $_POST['AddRelaysNumber']; $j++) {
        

        $stmt = $db->prepare("INSERT INTO Relays VALUES(:id, 'Relay', 0, 0, 0)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->execute();
    }
    shell_exec("$mycodo_client --sqlreload -1");
}


// Check for changes to relay variables (up to 8)
for ($p = 0; $p < count($relay_id); $p++) {
    // Set relay variables
    if (isset($_POST['Mod' . $p . 'Relay'])) {
        $stmt = $db->prepare("UPDATE Relays SET Name=:name, Pin=:pin, Amps=:amps, Trigger=:trigger, Start_State=:startstate WHERE Id=:id");
        $stmt->bindValue(':name', $_POST['relay' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':pin', (int)$_POST['relay' . $p . 'pin'], SQLITE3_INTEGER);
        $stmt->bindValue(':amps', (float)$_POST['relay' . $p . 'amps'], SQLITE3_FLOAT);
        $stmt->bindValue(':trigger', (int)$_POST['relay' . $p . 'trigger'], SQLITE3_INTEGER);
        $stmt->bindValue(':startstate', (int)$_POST['relay' . $p . 'startstate'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $relay_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        if ((int)$_POST['relay' . $p . 'pin'] != $relay_pin[$p]) {
            shell_exec("$mycodo_client --sqlreload $p");
        } else {
            shell_exec("$mycodo_client --sqlreload -1");
        }

        $pin = (int)$_POST['relay' . $p . 'pin'];
        shell_exec("gpio -g mode $pin output");

        if ((int)$_POST['relay' . $p . 'trigger'] == 1) {
            if ((int)$_POST['relay' . $p . 'startstate'] == 1) {
                shell_exec("gpio -g write $pin 1");
            } else {
                shell_exec("gpio -g write $pin 0");
            }
        } else if ((int)$_POST['relay' . $p . 'trigger'] == 0) {
            if ((int)$_POST['relay' . $p . 'startstate'] == 1) {
                shell_exec("gpio -g write $pin 0");
            } else {
                shell_exec("gpio -g write $pin 1");
            }
        }
    }

    // Delete Relay
    if (isset($_POST['Delete' . $p . 'Relay'])) {
        $stmt = $db->prepare("DELETE FROM Relays WHERE Id=:id");
        $stmt->bindValue(':id', $relay_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --sqlreload -1");
    }

    // Check for errors
    if (isset($_POST['R' . $p]) || isset($_POST[$p . 'secON'])) {
        $total_amps = 0.0;
        for ($i = 0; $i < count($relay_id); $i++) {
            $read = "$gpio_path -g read $relay_pin[$i]";
            $row = $results->fetchArray();
            if ((shell_exec($read) == 1 && $relay_trigger[$i] == 1) || (shell_exec($read) == 0 && $relay_trigger[$i] == 0)) {
                $total_amps = $total_amps + $relay_amps[$i];
            }
        }
        $read = "$gpio_path -g read $relay_pin[$p]";
        $row = $results->fetchArray();
        if ((shell_exec($read) == 1 && $relay_trigger[$p] == 0) || (shell_exec($read) == 0 && $relay_trigger[$p] == 1)) {
            $total_amps = $total_amps + $relay_amps[$p];
        }
        if ($total_amps > $max_amps) {
            $sensor_error = "Error: Cannot turn relay $p on. This will exceed the maximum set amp draw ($max_amps amps).";
        }
    }

    if (!isset($sensor_error)) {

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
                $sensor_error = "Error: Can't turn relay $relay Off, it's already Off";
            } else if ($actual_state == 'HIGH' && $desired_state == 'ON') {
                $sensor_error = "Error: Can't turn relay $relay On, it's already On";
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
                $sensor_error = "Error: Relay $p ($name): Seconds On must be a positive integer and > 1</div>";
            } else if ($actual_state == 'HIGH' && $desired_state == 'HIGH') {
                $sensor_error = "Error: Can't turn relay $p On, it's already On";
            } else {
                $relay = $p+1;
                shell_exec("$mycodo_client -r $relay $seconds_on");
            }
        }
    }
}


// Add relay conditional statement
if (isset($_POST['AddRelayConditional'])) {

    // Check for errors
    if ((int)$_POST['conditionrelayifrelay'] == (int)$_POST['conditionrelaydorelay']) {
        $sensor_error = 'Error: Creating Conditional Statement: Relays cannot be the same.';
    }

    // If no errors encountered in the form data, proceed
    if (!isset($sensor_error)) {
        $stmt = $db->prepare("INSERT INTO RelayConditional (Id, Name, If_Relay, If_Action, If_Duration, Do_Relay, Do_Action, Do_Duration) VALUES(:id, :name, :ifrelay, :ifaction, :ifduration, :dorelay, :doaction, :doduration)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->bindValue(':name', $_POST['conditionrelayname'], SQLITE3_TEXT);
        $stmt->bindValue(':ifrelay', (int)$_POST['conditionrelayifrelay'], SQLITE3_INTEGER);
        $stmt->bindValue(':ifaction', $_POST['conditionrelayifaction'], SQLITE3_TEXT);
        $stmt->bindValue(':ifduration', (float)$_POST['conditionrelayifduration'], SQLITE3_FLOAT);
        $stmt->bindValue(':dorelay', (int)$_POST['conditionrelaydorelay'], SQLITE3_INTEGER);
        $stmt->bindValue(':doaction', $_POST['conditionrelaydoaction'], SQLITE3_TEXT);
        $stmt->bindValue(':doduration', (float)$_POST['conditionrelaydoduration'], SQLITE3_FLOAT);
        $stmt->execute();

        shell_exec("$mycodo_client --sqlreload -1");
    }
}


# Delete relay conditional statement
for ($p = 0; $p < count($conditional_relay_id); $p++) {

    if (isset($_POST['DeleteRelay' . $p . 'Conditional'])) {
        $stmt = $db->prepare("DELETE FROM RelayConditional WHERE Id=:id");
        $stmt->bindValue(':id', $conditional_relay_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --sqlreload -1");
    }
}




/*
 *
 * Timers
 *
 */


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
        shell_exec("$mycodo_client --sqlreload -1");
    }

    // Set timer state
    if (isset($_POST['Timer' . $p . 'StateChange'])) {
        $stmt = $db->prepare("UPDATE Timers SET State=:state WHERE Id=:id");
        $stmt->bindValue(':state', (int)$_POST['Timer' . $p . 'StateChange'], SQLITE3_INTEGER);
        $stmt->bindValue(':id', $timer_id[$p], SQLITE3_TEXT);
        $stmt->execute();
        shell_exec("$mycodo_client --sqlreload -1");
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

        shell_exec("$mycodo_client --sqlreload -1");
    }
}

// Add timers
if (isset($_POST['AddTimers']) && isset($_POST['AddTimersNumber'])) {
    for ($j = 0; $j < $_POST['AddTimersNumber']; $j++) {
        $stmt = $db->prepare("INSERT INTO Timers VALUES(:id, 'Timer', 0, 0, 60, 360)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->execute();
    }
    shell_exec("$mycodo_client --sqlreload -1");
}


/*
 *
 * Add Sensors
 *
 */

if (isset($_POST['AddSensor'])) {
    if (isset($_POST['AddSensorName']) && ctype_alnum($_POST['AddSensorName'])) {
        switch ($_POST['AddSensorDev']) {
            case "DS18B20":
                $stmt = $db->prepare("INSERT INTO TSensor (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D) VALUES(:id, :name, 0, 'DS18B20', 120, 0, 0, 0, 0, -100, 100, 25, 5, 0, 35, 5, 5, '0', '0', 0, 0, 0, 0, 1, 0, 0, 90, 0, 0, 0)");
                $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
                $stmt->bindValue(':name', $_POST['AddSensorName'], SQLITE3_TEXT);
                $stmt->execute();
                shell_exec("$mycodo_client --pidallrestart T");
                break;
            case "DHT11":
            case "DHT22":
            case "AM2302":
                $stmt = $db->prepare("INSERT INTO HTSensor (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Hum_Min, YAxis_Hum_Max, YAxis_Hum_Tics, YAxis_Hum_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relays_Up, Hum_Relays_Down, Hum_Relay_High, Hum_Outmax_High, Hum_Relay_Low, Hum_Outmax_Low, Hum_OR, Hum_Set, Hum_Set_Direction, Hum_Period, Hum_P, Hum_I, Hum_D) VALUES(:id, :name, 0, :dev, 120, 0, 0, 0, 0, -100, 100, 25, 5, 0, 35, 5, 5, 0, 100, 10, 5, '0', '0', 0, 0, 0, 0, 1, 25.0, 0, 90, 0, 0, 0, '0', '0', 0, 0, 0, 0, 1, 50.0, 0, 90, 0, 0, 0)");
                $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
                $stmt->bindValue(':name', $_POST['AddSensorName'], SQLITE3_TEXT);
                $stmt->bindValue(':dev', $_POST['AddSensorDev'], SQLITE3_TEXT);
                $stmt->execute();
                shell_exec("$mycodo_client --pidallrestart HT");
                break;
            case "K30":
                $stmt = $db->prepare("INSERT INTO CO2Sensor (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_CO2_Min, YAxis_CO2_Max, YAxis_CO2_Tics, YAxis_CO2_MTics, CO2_Relays_Up, CO2_Relays_Down, CO2_Relay_High, CO2_Outmax_High, CO2_Relay_Low, CO2_Outmax_Low, CO2_OR, CO2_Set, CO2_Set_Direction, CO2_Period, CO2_P, CO2_I, CO2_D) VALUES(:id, :name, 0, 'K30', 120, 0, 0, 0, 0, -100, 100, 25, 5, 0, 5000, 500, 5, '0', '0', 0, 0, 0, 0, 1, 25.0, 0, 90, 0, 0, 0)");
                $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
                $stmt->bindValue(':name', $_POST['AddSensorName'], SQLITE3_TEXT);
                $stmt->execute();
                shell_exec("$mycodo_client --pidallrestart CO2");
                break;
            case "BMP":
                $stmt = $db->prepare("INSERT INTO PressSensor (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Press_Min, YAxis_Press_Max, YAxis_Press_Tics, YAxis_Press_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Press_Relays_Up, Press_Relays_Down, Press_Relay_High, Press_Outmax_High, Press_Relay_Low, Press_Outmax_Low, Press_OR, Press_Set, Press_Set_Direction, Press_Period, Press_P, Press_I, Press_D) VALUES(:id, :name, 0, 'BMP085-180', 120, 0, 0, 0, 0, -100, 100, 25, 5, 0, 35, 5, 5, 97000, 100000, 500, 5, '0', '0', 0, 0, 0, 0, 1, 25.0, 0, 90, 0, 0, 0, '0', '0', 0, 0, 0, 0, 1, 50.0, 0, 90, 0, 0, 0)");
                $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
                $stmt->bindValue(':name', $_POST['AddSensorName'], SQLITE3_TEXT);
                $stmt->execute();
                shell_exec("$mycodo_client --pidallrestart Press");
                break;
        }
    } else {
        $sensor_error = "Error: Missing name. Enter a name when adding a sensor.";
    }
}


/*
 *
 * Temperature Sensors
 *
 */

for ($p = 0; $p < count($sensor_t_id); $p++) {

    // Add T Conditional statement
    if (isset($_POST['AddT' . $p . 'Conditional'])) {
        $stmt = $db->prepare("INSERT INTO TSensorConditional (Id, Name, Sensor, State, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On) VALUES(:id, :name, :sensor, 0, :direction, :setpoint, :period, :relay, :relaystate, :relaysecondson)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->bindValue(':name', $_POST['conditiont' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':sensor', $p, SQLITE3_INTEGER);
        $stmt->bindValue(':direction', (int)$_POST['conditiont' . $p . 'direction'], SQLITE3_INTEGER);
        $stmt->bindValue(':setpoint', (float)$_POST['conditiont' . $p . 'setpoint'], SQLITE3_FLOAT);
        $stmt->bindValue(':period', (int)$_POST['conditiont' . $p . 'period'], SQLITE3_INTEGER);
        $stmt->bindValue(':relay', (int)$_POST['conditiont' . $p . 'relay'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaystate', (int)$_POST['conditiont' . $p . 'relaystate'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaysecondson', (int)$_POST['conditiont' . $p . 'relaysecondson'], SQLITE3_INTEGER);
        $stmt->execute();
    }

    if (isset($conditional_t_id[$p])) {
        for ($z = 0; $z < count($conditional_t_id[$p]); $z++) {
            // Delete T Conditional Statement
            if (isset($_POST['DeleteT' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("DELETE FROM TSensorConditional WHERE Id=:id");
                $stmt->bindValue(':id', $conditional_t_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            // Turn T Conditional Statements On/Off
            if (isset($_POST['TurnOnT' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE TSensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 1);
                $stmt->bindValue(':id', $conditional_t_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            if (isset($_POST['TurnOffT' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE TSensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 0);
                $stmt->bindValue(':id', $conditional_t_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }
        }
    }


    // Check for errors
    if ((isset($_POST['ChangeT' . $p . 'TempOR']) && (int)$_POST['ChangeT' . $p . 'TempOR'] == 0) ||
        ($pid_t_temp_or[$p] == 0 && isset($_POST['Change' . $p . 'TSensorOverwrite'])) ||
        ($pid_t_temp_or[$p] == 0 && isset($_POST['Change' . $p . 'TSensorLoad']) && $_POST['sensort' . $p . 'preset'] != 'default')) {

        if ((float)$_POST['SetT' . $p . 'TempSetDir'] == 0 && ((int)$_POST['SetT' . $p . 'TempRelayLow'] < 1 || (int)$_POST['SetT' . $p . 'TempRelayHigh'] < 1)) {
            $sensor_error = 'Error: If "PID Regulate" is set to Both, "Up Relay" and "Down Relay" is required to be set.';
        } else if ((float)$_POST['SetT' . $p . 'TempSetDir'] == 1 && (int)$_POST['SetT' . $p . 'TempRelayLow'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Up, "Up Relay" is required to be set.';
        } else if ((float)$_POST['SetT' . $p . 'TempSetDir'] == -1 && (int)$_POST['SetT' . $p . 'TempRelayHigh'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Down, "Down Relay" is required to be set.';
        }
    }

    if (isset($_POST['Change' . $p . 'TSensorOverwrite'])) {
        $re = '/^\d+(?:,\d+)*$/';
        if (($_POST['SetT' . $p . 'TempRelaysUp'] != '0' and
            (!ctype_digit($_POST['SetT' . $p . 'TempRelaysUp']) and !preg_match($re, $_POST['SetT' . $p . 'TempRelaysUp']))) or
            ($_POST['SetT' . $p . 'TempRelaysUp'] == '') or
            ($_POST['SetT' . $p . 'TempRelaysDown'] != '0' and
            (!ctype_digit($_POST['SetT' . $p . 'TempRelaysDown']) and !preg_match($re, $_POST['SetT' . $p . 'TempRelaysDown']))) or
            ($_POST['SetT' . $p . 'TempRelaysDown'] == '')) {
            $sensor_error = 'Error: Graph Relays must contain digits separated by commas or be set to 0.';
        }
    }


    // If no errors encountered in the form data, proceed
    if (!isset($sensor_error)) {

        // Set Temperature PID override on or off
        if (isset($_POST['ChangeT' . $p . 'TempOR'])) {
            $stmt = $db->prepare("UPDATE TSensor SET Temp_OR=:tempor WHERE Id=:id");
            $stmt->bindValue(':tempor', (int)$_POST['ChangeT' . $p . 'TempOR'], SQLITE3_INTEGER);
            $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
            $stmt->execute();
            if ((int)$_POST['ChangeT' . $p . 'TempOR']) {
                shell_exec("$mycodo_client --pidstop TTemp $p");
                shell_exec("$mycodo_client --sqlreload -1");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
                shell_exec("$mycodo_client --pidstart TTemp $p");
            }
        }


        // Overwrite preset for Temperature sensor and PID variables
        if (isset($_POST['Change' . $p . 'TSensorOverwrite'])) {

            if (isset($_POST['sensort' . $p . 'preset']) && $_POST['sensort' . $p . 'preset'] != 'default') {
                $stmt = $db->prepare("UPDATE TSensorPreset SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd WHERE Id=:preset");
                $stmt->bindValue(':name', $_POST['sensort' . $p . 'name'], SQLITE3_TEXT);
                $stmt->bindValue(':device', $_POST['sensort' . $p . 'device'], SQLITE3_TEXT);
                $stmt->bindValue(':pin', (int)$_POST['sensort' . $p . 'pin'], SQLITE3_INTEGER);
                $stmt->bindValue(':period', (int)$_POST['sensort' . $p . 'period'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_relay', (int)$_POST['sensort' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_dur', (int)$_POST['sensort' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
                $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetT' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetT' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetT' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetT' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetT' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetT' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetT' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetT' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaysup', $_POST['SetT' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelaysdown', $_POST['SetT' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelayhigh', (int)$_POST['SetT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetT' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaylow', (int)$_POST['SetT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetT' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempset', (float)$_POST['SetT' . $p . 'TempSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempsetdir', (float)$_POST['SetT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempperiod', (int)$_POST['SetT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempp', (float)$_POST['SetT' . $p . 'Temp_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempi', (float)$_POST['SetT' . $p . 'Temp_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempd', (float)$_POST['SetT' . $p . 'Temp_D'], SQLITE3_FLOAT);
                $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset'], SQLITE3_TEXT);
                $stmt->execute();
            }

            $stmt = $db->prepare("UPDATE TSensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $_POST['sensort' . $p . 'name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $_POST['sensort' . $p . 'device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', (int)$_POST['sensort' . $p . 'pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', (int)$_POST['sensort' . $p . 'period'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_relay', (int)$_POST['sensort' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_dur', (int)$_POST['sensort' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
            $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetT' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetT' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetT' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetT' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetT' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetT' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetT' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetT' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaysup', $_POST['SetT' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelaysdown', $_POST['SetT' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelayhigh', (int)$_POST['SetT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetT' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', (int)$_POST['SetT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetT' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', (float)$_POST['SetT' . $p . 'TempSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', (float)$_POST['SetT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', (int)$_POST['SetT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', (float)$_POST['SetT' . $p . 'Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', (float)$_POST['SetT' . $p . 'Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', (float)$_POST['SetT' . $p . 'Temp_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_t_temp_or[$p] == 0 &&
                ($pid_t_temp_relay_high[$p] != (int)$_POST['SetT' . $p . 'TempRelayHigh'] ||
                $pid_t_temp_outmax_high[$p] != (int)$_POST['SetT' . $p . 'TempOutmaxHigh'] ||
                $pid_t_temp_relay_low[$p] != (int)$_POST['SetT' . $p . 'TempRelayLow'] ||
                $pid_t_temp_outmax_low[$p] != (int)$_POST['SetT' . $p . 'TempOutmaxLow'] ||
                $pid_t_temp_set[$p] != (float)$_POST['SetT' . $p . 'TempSet'] ||
                $pid_t_temp_set_dir[$p] != (float)$_POST['SetT' . $p . 'TempSetDir'] ||
                $pid_t_temp_period[$p] != (int)$_POST['SetT' . $p . 'TempPeriod'] ||
                $pid_t_temp_p[$p] != (float)$_POST['SetT' . $p . 'Temp_P'] ||
                $pid_t_temp_i[$p] != (float)$_POST['SetT' . $p . 'Temp_I'] ||
                $pid_t_temp_d[$p] != (float)$_POST['SetT' . $p . 'Temp_D'])) {
                shell_exec("$mycodo_client --pidrestart TTemp $p");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
            }
        }

        // Load Temperature sensor and PID variables from preset
        if (isset($_POST['Change' . $p . 'TSensorLoad']) && $_POST['sensort' . $p . 'preset'] != 'default') {

            $stmt = $db->prepare('SELECT * FROM TSensorPreset WHERE Id=:preset');
            $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset']);
            $result = $stmt->execute();
            $exist = $result->fetchArray();

            // Id exists, change values to preset
            if ($exist != False) {

                $stmt = $db->prepare('SELECT Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, Temp_Relays_Up, Temp_Relays_Down Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D FROM TSensorPreset WHERE Id=:preset');
                $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset']);
                $result = $stmt->execute();
                $row = $result->fetchArray();

                $stmt = $db->prepare("UPDATE TSensor SET Name=:name, Pin=:pin, Device=:device, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_OR=:tempor, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd WHERE Id=:id");
                $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
                $stmt->bindValue(':name', $row['Name'], SQLITE3_TEXT);
                $stmt->bindValue(':device', $row['Device'], SQLITE3_TEXT);
                $stmt->bindValue(':pin', $row['Pin'], SQLITE3_INTEGER);
                $stmt->bindValue(':period', $row['Period'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_relay', $row['Pre_Measure_Relay'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_dur', $row['Pre_Measure_Dur'], SQLITE3_INTEGER);
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
                $stmt->bindValue(':yaxis_relay_min', $row['YAxis_Relay_Min'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_max', $row['YAxis_Relay_Max'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_tics', $row['YAxis_Relay_Tics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_mtics', $row['YAxis_Relay_MTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_min', $row['YAxis_Temp_Min'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_max', $row['YAxis_Temp_Max'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_tics', $row['YAxis_Temp_Tics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_mtics', $row['YAxis_Temp_MTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaysup', $row['Temp_Relays_Up'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelaysdown', $row['Temp_Relays_Down'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelayhigh', $row['Temp_Relay_High'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxhigh', $row['Temp_Outmax_High'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaylow', $row['Temp_Relay_Low'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxlow', $row['Temp_Outmax_Low'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempor', 1, SQLITE3_INTEGER);
                $stmt->bindValue(':tempset', $row['Temp_Set'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempsetdir', $row['Temp_Set_Direction'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempperiod', $row['Temp_Period'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempp', $row['Temp_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempi', $row['Temp_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempd', $row['Temp_D'], SQLITE3_FLOAT);
                $stmt->execute();

                if ($pid_t_temp_or[$p] == 0) {
                    shell_exec("$mycodo_client --pidrestart TTemp $p");
                } else {
                    shell_exec("$mycodo_client --sqlreload -1");
                }
            } else {
                $sensor_error = 'Error: Something went wrong. The preset you selected doesn\'t exist.';
            }
        }
    }

    // Save Temperature sensor and PID variables to a new preset
    if (isset($_POST['Change' . $p . 'TSensorNewPreset'])) {
        if(in_array($_POST['sensort' . $p . 'presetname'], $sensor_t_preset)) {
            $name = $_POST['sensort' . $p . 'presetname'];
            $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
        } else {
            if (isset($_POST['sensort' . $p . 'presetname']) && $_POST['sensort' . $p . 'presetname'] != '') {

                $stmt = $db->prepare("INSERT INTO TSensorPreset (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D) VALUES(:preset, :name, :pin, :device, :period, :premeas_relay, :premeas_dur, :activated, :graph, :yaxis_relay_min, :yaxis_relay_max, :yaxis_relay_tics, :yaxis_relay_mtics, :yaxis_temp_min, :yaxis_temp_max, :yaxis_temp_tics, :yaxis_temp_mtics, :temprelaysup, :temprelaysdown, :temprelayhigh, :tempoutmaxhigh, :temprelaylow, :tempoutmaxlow, :tempset, :tempsetdir, :tempperiod, :tempp, :tempi, :tempd)");
                $stmt->bindValue(':preset', $_POST['sensort' . $p . 'presetname'], SQLITE3_TEXT);
                $stmt->bindValue(':name', $_POST['sensort' . $p . 'name'], SQLITE3_TEXT);
                $stmt->bindValue(':device', $_POST['sensort' . $p . 'device'], SQLITE3_TEXT);
                $stmt->bindValue(':pin', (int)$_POST['sensort' . $p . 'pin'], SQLITE3_INTEGER);
                $stmt->bindValue(':period', (int)$_POST['sensort' . $p . 'period'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_relay', (int)$_POST['sensort' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_dur', (int)$_POST['sensort' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
                $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetT' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetT' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetT' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetT' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetT' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetT' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetT' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetT' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaysup', $_POST['SetT' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelaysdown', $_POST['SetT' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelayhigh', (int)$_POST['SetT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetT' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaylow', (int)$_POST['SetT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetT' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempset', (float)$_POST['SetT' . $p . 'TempSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempsetdir', (float)$_POST['SetT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempperiod', (int)$_POST['SetT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempp', (float)$_POST['SetT' . $p . 'Temp_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempi', (float)$_POST['SetT' . $p . 'Temp_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempd', (float)$_POST['SetT' . $p . 'Temp_D'], SQLITE3_FLOAT);
                $stmt->execute();
            } else {
                $sensor_error = 'Error: You must enter a name to create a new preset.';
            }
        }
    }

    // Rename Temperature preset
    if (isset($_POST['Change' . $p . 'TSensorRenamePreset']) && $_POST['sensort' . $p . 'preset'] != 'default') {
        if(in_array($_POST['sensort' . $p . 'presetname'], $sensor_t_preset)) {
            $name = $_POST['sensort' . $p . 'presetname'];
            $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
        } else {
            $stmt = $db->prepare("UPDATE TSensorPreset SET Id=:presetnew WHERE Id=:presetold");
            $stmt->bindValue(':presetold', $_POST['sensort' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->bindValue(':presetnew', $_POST['sensort' . $p . 'presetname'], SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    // Delete Temperature preset
    if (isset($_POST['Change' . $p . 'TSensorDelete']) && $_POST['sensort' . $p . 'preset'] != 'default') {
        $stmt = $db->prepare("DELETE FROM TSensorPreset WHERE Id=:preset");
        $stmt->bindValue(':preset', $_POST['sensort' . $p . 'preset']);
        $stmt->execute();
    }

    // Delete Temperature sensors
    if (isset($_POST['Delete' . $p . 'TSensor'])) {
        $stmt = $db->prepare("DELETE FROM TSensor WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_t_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidallrestart T");
    }
}



/*
 *
 * Humidity/Temperature Sensors
 *
 */

for ($p = 0; $p < count($sensor_ht_id); $p++) {

    // Add HT Conditional statement
    if (isset($_POST['AddHT' . $p . 'Conditional'])) {
        $stmt = $db->prepare("INSERT INTO HTSensorConditional (Id, Name, Sensor, State, Condition, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On) VALUES(:id, :name, :sensor, 0, :condition, :direction, :setpoint, :period, :relay, :relaystate, :relaysecondson)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->bindValue(':name', $_POST['conditionht' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':sensor', $p, SQLITE3_INTEGER);
        $stmt->bindValue(':condition', $_POST['conditionht' . $p . 'condition'], SQLITE3_TEXT);
        $stmt->bindValue(':direction', (int)$_POST['conditionht' . $p . 'direction'], SQLITE3_INTEGER);
        $stmt->bindValue(':setpoint', (float)$_POST['conditionht' . $p . 'setpoint'], SQLITE3_FLOAT);
        $stmt->bindValue(':period', (int)$_POST['conditionht' . $p . 'period'], SQLITE3_INTEGER);
        $stmt->bindValue(':relay', (int)$_POST['conditionht' . $p . 'relay'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaystate', (int)$_POST['conditionht' . $p . 'relaystate'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaysecondson', (int)$_POST['conditionht' . $p . 'relaysecondson'], SQLITE3_INTEGER);
        $stmt->execute();
    }

    if (isset($conditional_ht_id[$p])) {
        for ($z = 0; $z < count($conditional_ht_id[$p]); $z++) {
            // Delete HT Conditional Statement
            if (isset($_POST['DeleteHT' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("DELETE FROM HTSensorConditional WHERE Id=:id");
                $stmt->bindValue(':id', $conditional_ht_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            // Turn HT Conditional Statements On/Off
            if (isset($_POST['TurnOnHT' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE HTSensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 1);
                $stmt->bindValue(':id', $conditional_ht_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            if (isset($_POST['TurnOffHT' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE HTSensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 0);
                $stmt->bindValue(':id', $conditional_ht_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }
        }
    }


    // Check for errors
    if ((isset($_POST['ChangeHT' . $p . 'TempOR']) && (int)$_POST['ChangeHT' . $p . 'TempOR'] == 0) ||
        ($pid_ht_temp_or[$p] == 0 && isset($_POST['Change' . $p . 'HTSensorOverwrite'])) ||
        ($pid_ht_temp_or[$p] == 0 && isset($_POST['Change' . $p . 'HTSensorLoad']) && $_POST['sensort' . $p . 'preset'] != 'default')) {

        if ((float)$_POST['SetHT' . $p . 'TempSetDir'] == 0 && ((int)$_POST['SetHT' . $p . 'TempRelayLow'] < 1 || (int)$_POST['SetHT' . $p . 'TempRelayHigh'] < 1)) {
            $sensor_error = 'Error: If "PID Regulate" is set to Both, "Up Relay" and "Down Relay" is required to be set.';
        } else if ((float)$_POST['SetHT' . $p . 'TempSetDir'] == 1 && (int)$_POST['SetHT' . $p . 'TempRelayLow'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Up, "Up Relay" is required to be set.';
        } else if ((float)$_POST['SetHT' . $p . 'TempSetDir'] == -1 && (int)$_POST['SetHT' . $p . 'TempRelayHigh'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Down, "Down Relay" is required to be set.';
        }
    }

    if ((isset($_POST['ChangeHT' . $p . 'HumOR']) && (int)$_POST['ChangeHT' . $p . 'HumOR'] == 0) ||
        ($pid_ht_hum_or[$p] == 0 && isset($_POST['Change' . $p . 'HTSensorOverwrite'])) ||
        ($pid_ht_hum_or[$p] == 0 && isset($_POST['Change' . $p . 'HTSensorLoad']) && $_POST['sensort' . $p . 'preset'] != 'default')) {

        if ((float)$_POST['SetHT' . $p . 'HumSetDir'] == 0 && ((int)$_POST['SetHT' . $p . 'HumRelayLow'] < 1 || (int)$_POST['SetHT' . $p . 'HumRelayHigh'] < 1)) {
            $sensor_error = 'Error: If "PID Regulate" is set to Both, "Up Relay" and "Down Relay" is required to be set.';
        } else if ((float)$_POST['SetHT' . $p . 'HumSetDir'] == 1 && (int)$_POST['SetHT' . $p . 'HumRelayLow'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Up, "Up Relay" is required to be set.';
        } else if ((float)$_POST['SetHT' . $p . 'HumSetDir'] == -1 && (int)$_POST['SetHT' . $p . 'HumRelayHigh'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Down, "Down Relay" is required to be set.';
        }
    }

    if (isset($_POST['Change' . $p . 'HTSensorOverwrite'])) {
        $re = '/^\d+(?:,\d+)*$/';
        if (($_POST['SetHT' . $p . 'TempRelaysUp'] != '0' and
            (!ctype_digit($_POST['SetHT' . $p . 'TempRelaysUp']) and !preg_match($re, $_POST['SetHT' . $p . 'TempRelaysUp']))) or
            ($_POST['SetHT' . $p . 'TempRelaysUp'] == '') or
            ($_POST['SetHT' . $p . 'TempRelaysDown'] != '0' and
            (!ctype_digit($_POST['SetHT' . $p . 'TempRelaysDown']) and !preg_match($re, $_POST['SetHT' . $p . 'TempRelaysDown']))) or
            ($_POST['SetHT' . $p . 'TempRelaysDown'] == '')) {
            $sensor_error = 'Error: Graph Relays must contain digits separated by commas or be set to 0.';
        } else if (($_POST['SetHT' . $p . 'HumRelaysUp'] != '0' and
            (!ctype_digit($_POST['SetHT' . $p . 'HumRelaysUp']) and !preg_match($re, $_POST['SetHT' . $p . 'HumRelaysUp']))) or
            ($_POST['SetHT' . $p . 'HumRelaysUp'] == '') or
            ($_POST['SetHT' . $p . 'HumRelaysDown'] != '0' and
            (!ctype_digit($_POST['SetHT' . $p . 'HumRelaysDown']) and !preg_match($re, $_POST['SetHT' . $p . 'HumRelaysDown']))) or
            ($_POST['SetHT' . $p . 'HumRelaysDown'] == '')) {
            $sensor_error = 'Error: Graph Relays must contain digits separated by commas or be set to 0.';
        }
    }


    // If no errors encountered in the form data, proceed
    if (!isset($sensor_error)) {

        // Set Humidity PID override on or off
        if (isset($_POST['ChangeHT' . $p . 'TempOR'])) {

            $stmt = $db->prepare("UPDATE HTSensor SET Temp_OR=:humor WHERE Id=:id");
            $stmt->bindValue(':humor', (int)$_POST['ChangeHT' . $p . 'TempOR'], SQLITE3_INTEGER);
            $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
            $stmt->execute();
            if ((int)$_POST['ChangeHT' . $p . 'TempOR']) {
                shell_exec("$mycodo_client --pidstop HTTemp $p");
                shell_exec("$mycodo_client --sqlreload -1");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
                shell_exec("$mycodo_client --pidstart HTTemp $p");
            }
        }

        if (isset($_POST['ChangeHT' . $p . 'HumOR'])) {

            if (!isset($sensor_error)) {
                $stmt = $db->prepare("UPDATE HTSensor SET Hum_OR=:humor WHERE Id=:id");
                $stmt->bindValue(':humor', (int)$_POST['ChangeHT' . $p . 'HumOR'], SQLITE3_INTEGER);
                $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
                $stmt->execute();
                if ((int)$_POST['ChangeHT' . $p . 'HumOR']) {
                    shell_exec("$mycodo_client --pidstop HTHum $p");
                    shell_exec("$mycodo_client --sqlreload -1");
                } else {
                    shell_exec("$mycodo_client --sqlreload -1");
                    shell_exec("$mycodo_client --pidstart HTHum $p");
                }
            }
        }

        // Overwrite preset for Temperature/Humidity sensor and PID variables
        if (isset($_POST['Change' . $p . 'HTSensorOverwrite'])) {

            if (isset($_POST['sensorht' . $p . 'preset']) && $_POST['sensorht' . $p . 'preset'] != 'default') {
                $stmt = $db->prepare("UPDATE HTSensorPreset SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, YAxis_Hum_Min=:yaxis_hum_min, YAxis_Hum_Max=:yaxis_hum_max, YAxis_Hum_Tics=:yaxis_hum_tics, YAxis_Hum_MTics=:yaxis_hum_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Hum_Relays_Up=:humrelaysup, Hum_Relays_Down=:humrelaysdown, Hum_Relay_High=:humrelayhigh, Hum_Outmax_High=:humoutmaxhigh, Hum_Relay_Low=:humrelaylow, Hum_Outmax_Low=:humoutmaxlow, Hum_Set=:humset, Hum_Set_Direction=:humsetdir, Hum_Period=:humperiod, Hum_P=:hum, Hum_I=:hum, Hum_D=:humd WHERE Id=:preset");
                $stmt->bindValue(':name', $_POST['sensorht' . $p . 'name'], SQLITE3_TEXT);
                $stmt->bindValue(':device', $_POST['sensorht' . $p . 'device'], SQLITE3_TEXT);
                $stmt->bindValue(':pin', (int)$_POST['sensorht' . $p . 'pin'], SQLITE3_INTEGER);
                $stmt->bindValue(':period', (int)$_POST['sensorht' . $p . 'period'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_relay', (int)$_POST['sensorht' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_dur', (int)$_POST['sensorht' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
                $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetHT' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetHT' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetHT' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetHT' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetHT' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetHT' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetHT' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetHT' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_hum_min', (int)$_POST['SetHT' . $p . 'YAxisHumMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_hum_max', (int)$_POST['SetHT' . $p . 'YAxisHumMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_hum_tics', (int)$_POST['SetHT' . $p . 'YAxisHumTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_hum_mtics', (int)$_POST['SetHT' . $p . 'YAxisHumMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaysup', $_POST['SetHT' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelaysdown', $_POST['SetHT' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelayhigh', (int)$_POST['SetHT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetHT' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaylow', (int)$_POST['SetHT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetHT' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempset', (float)$_POST['SetHT' . $p . 'TempSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempsetdir', (float)$_POST['SetHT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempperiod', (int)$_POST['SetHT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempp', (float)$_POST['SetHT' . $p . 'Temp_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempi', (float)$_POST['SetHT' . $p . 'Temp_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempd', (float)$_POST['SetHT' . $p . 'Temp_D'], SQLITE3_FLOAT);
                $stmt->bindValue(':humrelaysup', $_POST['SetHT' . $p . 'HumRelaysUp'], SQLITE3_TEXT);
                $stmt->bindValue(':humrelaysdown', $_POST['SetHT' . $p . 'HumRelaysDown'], SQLITE3_TEXT);
                $stmt->bindValue(':humrelayhigh', (int)$_POST['SetHT' . $p . 'HumRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':humoutmaxhigh', (int)$_POST['SetHT' . $p . 'HumOutmaxHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':humrelaylow', (int)$_POST['SetHT' . $p . 'HumRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':humoutmaxlow', (int)$_POST['SetHT' . $p . 'HumOutmaxLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':humset', (float)$_POST['SetHT' . $p . 'HumSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':humsetdir', (float)$_POST['SetHT' . $p . 'HumSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':humperiod', (int)$_POST['SetHT' . $p . 'HumPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':hump', (float)$_POST['SetHT' . $p . 'Hum_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':humi', (float)$_POST['SetHT' . $p . 'Hum_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':humd', (float)$_POST['SetHT' . $p . 'Hum_D'], SQLITE3_FLOAT);
                $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset'], SQLITE3_TEXT);
                $stmt->execute();
            }

            $stmt = $db->prepare("UPDATE HTSensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, YAxis_Hum_Min=:yaxis_hum_min, YAxis_Hum_Max=:yaxis_hum_max, YAxis_Hum_Tics=:yaxis_hum_tics, YAxis_Hum_MTics=:yaxis_hum_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Hum_Relays_Up=:humrelaysup, Hum_Relays_Down=:humrelaysdown, Hum_Relay_High=:humrelayhigh, Hum_Outmax_High=:humoutmaxhigh, Hum_Relay_Low=:humrelaylow, Hum_Outmax_Low=:humoutmaxlow, Hum_Set=:humset, Hum_Set_Direction=:humsetdir, Hum_Period=:humperiod, Hum_P=:hump, Hum_I=:humi, Hum_D=:humd WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $_POST['sensorht' . $p . 'name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $_POST['sensorht' . $p . 'device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', (int)$_POST['sensorht' . $p . 'pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', (int)$_POST['sensorht' . $p . 'period'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_relay', (int)$_POST['sensorht' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_dur', (int)$_POST['sensorht' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
            $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetHT' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetHT' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetHT' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetHT' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetHT' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetHT' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetHT' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetHT' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_min', (int)$_POST['SetHT' . $p . 'YAxisHumMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_max', (int)$_POST['SetHT' . $p . 'YAxisHumMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_tics', (int)$_POST['SetHT' . $p . 'YAxisHumTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_mtics', (int)$_POST['SetHT' . $p . 'YAxisHumMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaysup', $_POST['SetHT' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelaysdown', $_POST['SetHT' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelayhigh', (int)$_POST['SetHT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetHT' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', (int)$_POST['SetHT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetHT' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', (float)$_POST['SetHT' . $p . 'TempSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', (float)$_POST['SetHT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', (int)$_POST['SetHT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', (float)$_POST['SetHT' . $p . 'Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', (float)$_POST['SetHT' . $p . 'Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', (float)$_POST['SetHT' . $p . 'Temp_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':humrelaysup', $_POST['SetHT' . $p . 'HumRelaysUp'], SQLITE3_TEXT);
            $stmt->bindValue(':humrelaysdown', $_POST['SetHT' . $p . 'HumRelaysDown'], SQLITE3_TEXT);
            $stmt->bindValue(':humrelayhigh', (int)$_POST['SetHT' . $p . 'HumRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':humoutmaxhigh', (int)$_POST['SetHT' . $p . 'HumOutmaxHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':humrelaylow', (int)$_POST['SetHT' . $p . 'HumRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':humoutmaxlow', (int)$_POST['SetHT' . $p . 'HumOutmaxLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':humset', (float)$_POST['SetHT' . $p . 'HumSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':humsetdir', (float)$_POST['SetHT' . $p . 'HumSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':humperiod', (int)$_POST['SetHT' . $p . 'HumPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':hump', (float)$_POST['SetHT' . $p . 'Hum_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':humi', (float)$_POST['SetHT' . $p . 'Hum_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':humd', (float)$_POST['SetHT' . $p . 'Hum_D'], SQLITE3_FLOAT);
            $stmt->execute();

            $reload = 1;
            if ($pid_ht_temp_or[$p] == 0 &&
                ($pid_ht_temp_relay_high[$p] != (int)$_POST['SetHT' . $p . 'TempRelayHigh'] ||
                $pid_ht_temp_outmax_high[$p] != (int)$_POST['SetHT' . $p . 'TempOutmaxHigh'] ||
                $pid_ht_temp_relay_low[$p] != (int)$_POST['SetHT' . $p . 'TempRelayLow'] ||
                $pid_ht_temp_outmax_low[$p] != (int)$_POST['SetHT' . $p . 'TempOutmaxLow'] ||
                $pid_ht_temp_set[$p] != (float)$_POST['SetHT' . $p . 'TempSet'] ||
                $pid_ht_temp_set_dir[$p] != (float)$_POST['SetHT' . $p . 'TempSetDir'] ||
                $pid_ht_temp_period[$p] != (int)$_POST['SetHT' . $p . 'TempPeriod'] ||
                $pid_ht_temp_p[$p] != (float)$_POST['SetHT' . $p . 'Temp_P'] ||
                $pid_ht_temp_i[$p] != (float)$_POST['SetHT' . $p . 'Temp_I'] ||
                $pid_ht_temp_d[$p] != (float)$_POST['SetHT' . $p . 'Temp_D'])) {
                shell_exec("$mycodo_client --pidrestart HTTemp $p");
                $reload = 0;
            }
            if ($pid_ht_hum_or[$p] == 0 &&
                ($pid_ht_hum_relay_high[$p] != (int)$_POST['SetHT' . $p . 'HumRelayHigh'] ||
                $pid_ht_hum_outmax_high[$p] != (int)$_POST['SetHT' . $p . 'HumOutmaxHigh'] ||
                $pid_ht_hum_relay_low[$p] != (int)$_POST['SetHT' . $p . 'HumRelayLow'] ||
                $pid_ht_hum_outmax_low[$p] != (int)$_POST['SetHT' . $p . 'HumOutmaxLow'] ||
                $pid_ht_hum_set[$p] != (float)$_POST['SetHT' . $p . 'HumSet'] ||
                $pid_ht_hum_set_dir[$p] != (float)$_POST['SetHT' . $p . 'HumSetDir'] ||
                $pid_ht_hum_period[$p] != (int)$_POST['SetHT' . $p . 'HumPeriod'] ||
                $pid_ht_hum_p[$p] != (float)$_POST['SetHT' . $p . 'Hum_P'] ||
                $pid_ht_hum_i[$p] != (float)$_POST['SetHT' . $p . 'Hum_I'] ||
                $pid_ht_hum_d[$p] != (float)$_POST['SetHT' . $p . 'Hum_D'])) {
                shell_exec("$mycodo_client --pidrestart HTHum $p");
                $reload = 0;
            }
            if ($reload) {
                shell_exec("$mycodo_client --sqlreload -1");
            }
        }

        // Save Temperature/Humidity sensor and PID variables to a new preset
        if (isset($_POST['Change' . $p . 'HTSensorNewPreset'])) {
            if(in_array($_POST['sensorht' . $p . 'presetname'], $sensor_ht_preset)) {
                $name = $_POST['sensorht' . $p . 'presetname'];
                $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
            } else {
                if (isset($_POST['sensorht' . $p . 'presetname']) && $_POST['sensorht' . $p . 'presetname'] != '') {

                    $stmt = $db->prepare("INSERT INTO HTSensorPreset (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Hum_Min, YAxis_Hum_Max, YAxis_Hum_Tics, YAxis_Hum_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relays_Up, Hum_Relays_Down, Hum_Relay_High, Hum_Outmax_High, Hum_Relay_Low, Hum_Outmax_Low, Hum_Set, Hum_Set_Direction, Hum_Period, Hum_P, Hum_I, Hum_D) VALUES(:preset, :name, :pin, :device, :period, :premeas_relay, :premeas_dur, :activated, :graph, :yaxis_relay_min, :yaxis_relay_max, :yaxis_relay_tics, :yaxis_relay_mtics, :yaxis_temp_min, :yaxis_temp_max, :yaxis_temp_tics, :yaxis_temp_mtics, :yaxis_hum_min, :yaxis_hum_max, :yaxis_hum_tics, :yaxis_hum_mtics, :temprelaysup, :temprelaysdown, :temprelayhigh, :tempoutmaxhigh, :temprelaylow, :tempoutmaxlow, :tempset, :tempsetdir, :tempperiod, :tempp, :tempi, :tempd, :humrelaysup, :humrelaysdown, :humrelayhigh, :humoutmaxhigh, :humrelaylow, :humoutmaxlow, :humset, :humsetdir, :humperiod, :hump, :humi, :humd)");
                    $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'presetname'], SQLITE3_TEXT);
                    $stmt->bindValue(':name', $_POST['sensorht' . $p . 'name'], SQLITE3_TEXT);
                    $stmt->bindValue(':device', $_POST['sensorht' . $p . 'device'], SQLITE3_TEXT);
                    $stmt->bindValue(':pin', (int)$_POST['sensorht' . $p . 'pin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':period', (int)$_POST['sensorht' . $p . 'period'], SQLITE3_INTEGER);
                    $stmt->bindValue(':premeas_relay', (int)$_POST['sensorht' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                    $stmt->bindValue(':premeas_dur', (int)$_POST['sensorht' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
                    $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetHT' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetHT' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetHT' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetHT' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetHT' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetHT' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetHT' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetHT' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_hum_min', (int)$_POST['SetHT' . $p . 'YAxisHumMin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_hum_max', (int)$_POST['SetHT' . $p . 'YAxisHumMax'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_hum_tics', (int)$_POST['SetHT' . $p . 'YAxisHumTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_hum_mtics', (int)$_POST['SetHT' . $p . 'YAxisHumMTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':temprelaysup', $_POST['SetHT' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
                    $stmt->bindValue(':temprelaysdown', $_POST['SetHT' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
                    $stmt->bindValue(':temprelayhigh', (int)$_POST['SetHT' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetHT' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':temprelaylow', (int)$_POST['SetHT' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetHT' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempset', (float)$_POST['SetHT' . $p . 'TempSet'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempsetdir', (float)$_POST['SetHT' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempperiod', (int)$_POST['SetHT' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempp', (float)$_POST['SetHT' . $p . 'Temp_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempi', (float)$_POST['SetHT' . $p . 'Temp_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempd', (float)$_POST['SetHT' . $p . 'Temp_D'], SQLITE3_FLOAT);
                    $stmt->bindValue(':humrelaysup', $_POST['SetHT' . $p . 'HumRelaysUp'], SQLITE3_TEXT);
                    $stmt->bindValue(':humrelaysdown', $_POST['SetHT' . $p . 'HumRelaysDown'], SQLITE3_TEXT);
                    $stmt->bindValue(':humrelayhigh', (int)$_POST['SetHT' . $p . 'HumRelayHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':humoutmaxhigh', (int)$_POST['SetHT' . $p . 'HumOutmaxHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':humrelaylow', (int)$_POST['SetHT' . $p . 'HumRelayLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':humoutmaxlow', (int)$_POST['SetHT' . $p . 'HumOutmaxLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':humset', (float)$_POST['SetHT' . $p . 'HumSet'], SQLITE3_FLOAT);
                    $stmt->bindValue(':humsetdir', (float)$_POST['SetHT' . $p . 'HumSetDir'], SQLITE3_INTEGER);
                    $stmt->bindValue(':humperiod', (int)$_POST['SetHT' . $p . 'HumPeriod'], SQLITE3_INTEGER);
                    $stmt->bindValue(':hump', (float)$_POST['SetHT' . $p . 'Hum_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':humi', (float)$_POST['SetHT' . $p . 'Hum_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':humd', (float)$_POST['SetHT' . $p . 'Hum_D'], SQLITE3_FLOAT);
                    $stmt->execute();
                } else {
                    $sensor_error = 'Error: You must enter a name to create a new preset.';
                }
            }
        }
    }


    // Load Temperature/Humidity sensor and PID variables from preset
    if (isset($_POST['Change' . $p . 'HTSensorLoad']) && $_POST['sensorht' . $p . 'preset'] != 'default') {

        $stmt = $db->prepare('SELECT * FROM HTSensorPreset WHERE Id=:preset');
        $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset']);
        $result = $stmt->execute();
        $exist = $result->fetchArray();

        // Id exists, change values to preset
        if ($exist != False) {

            $stmt = $db->prepare('SELECT Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Hum_Min, YAxis_Hum_Max, YAxis_Hum_Tics, YAxis_Hum_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relays_Up, Hum_Relays_Down, Hum_Relay_High, Hum_Outmax_High, Hum_Relay_Low, Hum_Outmax_Low, Hum_Set, Hum_Set_Direction, Hum_Period, Hum_P, Hum_I, Hum_D FROM HTSensorPreset WHERE Id=:preset');
            $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset']);
            $result = $stmt->execute();
            $row = $result->fetchArray();

            $stmt = $db->prepare("UPDATE HTSensor SET Name=:name, Pin=:pin, Device=:device, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, YAxis_Hum_Min=:yaxis_hum_min, YAxis_Hum_Max=:yaxis_hum_max, YAxis_Hum_Tics=:yaxis_hum_tics, YAxis_Hum_MTics=:yaxis_hum_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_OR=:tempor, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Hum_Relays_Up=:humrelaysup, Hum_Relays_Down=:humrelaysdown, Hum_Relay_High=:humrelayhigh, Hum_Outmax_High=:humoutmaxhigh, Hum_Relay_Low=:humrelaylow, Hum_Outmax_Low=:humoutmaxlow, Hum_OR=:humor, Hum_Set=:humset, Hum_Set_Direction=:humsetdir, Hum_Period=:humperiod, Hum_P=:hump, Hum_I=:humi, Hum_D=:humd WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $row['Name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $row['Device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', $row['Pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', $row['Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_relay', $row['Pre_Measure_Relay'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_dur', $row['Pre_Measure_Dur'], SQLITE3_INTEGER);
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
            $stmt->bindValue(':yaxis_relay_min', $row['YAxis_Relay_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_max', $row['YAxis_Relay_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_tics', $row['YAxis_Relay_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_mtics', $row['YAxis_Relay_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_min', $row['YAxis_Temp_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_max', $row['YAxis_Temp_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_tics', $row['YAxis_Temp_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_mtics', $row['YAxis_Temp_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_min', $row['YAxis_Hum_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_max', $row['YAxis_Hum_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_tics', $row['YAxis_Hum_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_hum_mtics', $row['YAxis_Hum_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaysup', $row['Temp_Relays_Up'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelaysdown', $row['Temp_Relays_Down'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelayhigh', $row['Temp_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxhigh', $row['Temp_Outmax_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', $row['Temp_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxlow', $row['Temp_Outmax_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempor', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', $row['Temp_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', $row['Temp_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', $row['Temp_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', $row['Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', $row['Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', $row['Temp_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':humrelaysup', $row['Hum_Relays_Up'], SQLITE3_TEXT);
            $stmt->bindValue(':humrelaysdown', $row['Hum_Relays_Down'], SQLITE3_TEXT);
            $stmt->bindValue(':humrelayhigh', $row['Hum_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':humoutmaxhigh', $row['Hum_Outmax_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':humrelaylow', $row['Hum_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':humoutmaxlow', $row['Hum_Outmax_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':humor', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':humset', $row['Hum_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':humsetdir', $row['Hum_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':humperiod', $row['Hum_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':hump', $row['Hum_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':humi', $row['Hum_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':humd', $row['Hum_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_ht_temp_or[$p] == 0) {
                shell_exec("$mycodo_client --pidrestart HTTemp $p");
            }
            if ($pid_ht_hum_or[$p] == 0) {
                shell_exec("$mycodo_client --pidrestart HTHum $p");
            }
            if ($pid_ht_temp_or[$p] != 0 or $pid_ht_hum_or[$p] != 0) {
                shell_exec("$mycodo_client --sqlreload -1");
            }
        } else {
            $sensor_error = 'Error: Something went wrong. The preset you selected doesn\'t exist.';
        }
    }

    // Rename Temperature/Humidity preset
    if (isset($_POST['Change' . $p . 'HTSensorRenamePreset']) && $_POST['sensorht' . $p . 'preset'] != 'default') {
        if(in_array($_POST['sensorht' . $p . 'presetname'], $sensor_ht_preset)) {
            $name = $_POST['sensorht' . $p . 'presetname'];
            $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
        } else {
            $stmt = $db->prepare("UPDATE HTSensorPreset SET Id=:presetnew WHERE Id=:presetold");
            $stmt->bindValue(':presetold', $_POST['sensorht' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->bindValue(':presetnew', $_POST['sensorht' . $p . 'presetname'], SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    // Delete Temperature/Humidity preset
    if (isset($_POST['Change' . $p . 'HTSensorDelete']) && $_POST['sensorht' . $p . 'preset'] != 'default') {
        $stmt = $db->prepare("DELETE FROM HTSensorPreset WHERE Id=:preset");
        $stmt->bindValue(':preset', $_POST['sensorht' . $p . 'preset']);
        $stmt->execute();
    }

    // Delete HT sensors
    if (isset($_POST['Delete' . $p . 'HTSensor'])) {
        $stmt = $db->prepare("DELETE FROM HTSensor WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_ht_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidallrestart HT");
    }
}



/*
 *
 * CO2 Sensors
 *
 */

for ($p = 0; $p < count($sensor_co2_id); $p++) {

    // Add CO2 Conditional statement
    if (isset($_POST['AddCO2' . $p . 'Conditional'])) {
        $stmt = $db->prepare("INSERT INTO CO2SensorConditional (Id, Name, Sensor, State, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On) VALUES(:id, :name, :sensor, 0, :direction, :setpoint, :period, :relay, :relaystate, :relaysecondson)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->bindValue(':name', $_POST['conditionco2' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':sensor', $p, SQLITE3_INTEGER);
        $stmt->bindValue(':direction', (int)$_POST['conditionco2' . $p . 'direction'], SQLITE3_INTEGER);
        $stmt->bindValue(':setpoint', (float)$_POST['conditionco2' . $p . 'setpoint'], SQLITE3_FLOAT);
        $stmt->bindValue(':period', (int)$_POST['conditionco2' . $p . 'period'], SQLITE3_INTEGER);
        $stmt->bindValue(':relay', (int)$_POST['conditionco2' . $p . 'relay'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaystate', (int)$_POST['conditionco2' . $p . 'relaystate'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaysecondson', (int)$_POST['conditionco2' . $p . 'relaysecondson'], SQLITE3_INTEGER);
        $stmt->execute();
    }

    if (isset($conditional_co2_id[$p])) {
        for ($z = 0; $z < count($conditional_co2_id[$p]); $z++) {
            // Delete CO2 Conditional Statement
            if (isset($_POST['DeleteCO2' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("DELETE FROM CO2SensorConditional WHERE Id=:id");
                $stmt->bindValue(':id', $conditional_co2_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            // Turn CO2 Conditional Statements On/Off
            if (isset($_POST['TurnOnCO2' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE CO2SensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 1);
                $stmt->bindValue(':id', $conditional_co2_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            if (isset($_POST['TurnOffCO2' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE CO2SensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 0);
                $stmt->bindValue(':id', $conditional_co2_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }
        }
    }


    // Check for errors
    if ((isset($_POST['Change' . $p . 'CO2OR']) && (int)$_POST['Change' . $p . 'CO2OR'] == 0) ||
        ($pid_co2_or[$p] == 0 && isset($_POST['Change' . $p . 'CO2SensorOverwrite'])) ||
        ($pid_co2_or[$p] == 0 && isset($_POST['Change' . $p . 'CO2SensorLoad']) && $_POST['sensorco2' . $p . 'preset'] != 'default')) {

        if ((float)$_POST['SetCO2' . $p . 'CO2SetDir'] == 0 && ((int)$_POST['SetCO2' . $p . 'CO2RelayLow'] < 1 || (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'] < 1)) {
            $sensor_error = 'Error: If "PID Regulate" is set to Both, "Up Relay" and "Down Relay" is required to be set.';
        } else if ((float)$_POST['SetCO2' . $p . 'CO2SetDir'] == 1 && (int)$_POST['SetCO2' . $p . 'CO2RelayLow'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Up, "Up Relay" is required to be set.';
        } else if ((float)$_POST['SetCO2' . $p . 'CO2SetDir'] == -1 && (int)$_POST['SetT' . $p . 'CO2RelayHigh'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Down, "Down Relay" is required to be set.';
        }
    }

    if (isset($_POST['Change' . $p . 'CO2SensorOverwrite'])) {
        $re = '/^\d+(?:,\d+)*$/';
        if (($_POST['SetCO2' . $p . 'CO2RelaysUp'] != '0' and
            (!ctype_digit($_POST['SetCO2' . $p . 'CO2RelaysUp']) and !preg_match($re, $_POST['SetCO2' . $p . 'CO2RelaysUp']))) or
            ($_POST['SetCO2' . $p . 'CO2RelaysUp'] == '') or
            ($_POST['SetCO2' . $p . 'CO2RelaysDown'] != '0' and
            (!ctype_digit($_POST['SetCO2' . $p . 'CO2RelaysDown']) and !preg_match($re, $_POST['SetCO2' . $p . 'CO2RelaysDown']))) or
            ($_POST['SetCO2' . $p . 'CO2RelaysDown'] == '')) {
            $sensor_error = 'Error: Graph Relays must contain digits separated by commas or be set to 0.';
        }
    }

    // If no errors encountered in the form data, proceed
    if (!isset($sensor_error)) {

        // Set CO2 PID override on or off
        if (isset($_POST['ChangeCO2' . $p . 'CO2OR'])) {

            $stmt = $db->prepare("UPDATE CO2Sensor SET CO2_OR=:co2or WHERE Id=:id");
            $stmt->bindValue(':co2or', (int)$_POST['ChangeCO2' . $p . 'CO2OR'], SQLITE3_INTEGER);
            $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
            $stmt->execute();
            if ((int)$_POST['ChangeCO2' . $p . 'CO2OR']) {
                shell_exec("$mycodo_client --pidstop CO2 $p");
                shell_exec("$mycodo_client --sqlreload -1");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
                shell_exec("$mycodo_client --pidstart CO2 $p");
            }
        }

        // Overwrite preset for CO2 sensor and PID variables
        if (isset($_POST['Change' . $p . 'CO2SensorOverwrite'])) {

            if (isset($_POST['sensorco2' . $p . 'preset']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {

                $stmt = $db->prepare("UPDATE CO2SensorPreset SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_CO2_Min=:yaxis_co2_min, YAxis_CO2_Max=:yaxis_co2_max, YAxis_CO2_Tics=:yaxis_co2_tics, YAxis_CO2_MTics=:yaxis_co2_mtics, CO2_Relays_Up=:co2relaysup, CO2_Relays_Down=:co2relaysdown, CO2_Relay_High=:co2relayhigh, CO2_Outmax_High=:co2outmaxhigh, CO2_Relay_Low=:co2relaylow, CO2_Outmax_Low=:co2outmaxlow, CO2_Set=:co2set, CO2_Set_Direction=:co2setdir, CO2_Period=:co2period, CO2_P=:co2p, CO2_I=:co2i, CO2_D=:co2d WHERE Id=:preset");
                $stmt->bindValue(':name', $_POST['sensorco2' . $p . 'name'], SQLITE3_TEXT);
                $stmt->bindValue(':device', $_POST['sensorco2' . $p . 'device'], SQLITE3_TEXT);
                if ($_POST['sensorco2' . $p . 'device'] == 'K30') {
                    $stmt->bindValue(':pin', $sensor_co2_pin[$p], SQLITE3_INTEGER);
                } else {
                    $stmt->bindValue(':pin', (int)$_POST['sensorco2' . $p . 'pin'], SQLITE3_INTEGER);
                }
                $stmt->bindValue(':period', (int)$_POST['sensorco2' . $p . 'period'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_relay', (int)$_POST['sensorco2' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_dur', (int)$_POST['sensorco2' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
                $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetCO2' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetCO2' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetCO2' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetCO2' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_co2_min', (int)$_POST['SetCO2' . $p . 'YAxisCO2Min'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_co2_max', (int)$_POST['SetCO2' . $p . 'YAxisCO2Max'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_co2_tics', (int)$_POST['SetCO2' . $p . 'YAxisCO2Tics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_co2_mtics', (int)$_POST['SetCO2' . $p . 'YAxisCO2MTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2relaysup', $_POST['SetCO2' . $p . 'CO2RelaysUp'], SQLITE3_TEXT);
                $stmt->bindValue(':co2relaysdown', $_POST['SetCO2' . $p . 'CO2RelaysDown'], SQLITE3_TEXT);
                $stmt->bindValue(':co2relayhigh', (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2outmaxhigh', (int)$_POST['SetCO2' . $p . 'CO2OutmaxHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2relaylow', (int)$_POST['SetCO2' . $p . 'CO2RelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2outmaxlow', (int)$_POST['SetCO2' . $p . 'CO2OutmaxLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2set', (float)$_POST['SetCO2' . $p . 'CO2Set'], SQLITE3_FLOAT);
                $stmt->bindValue(':co2setdir', (float)$_POST['SetCO2' . $p . 'CO2SetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2period', (int)$_POST['SetCO2' . $p . 'CO2Period'], SQLITE3_INTEGER);
                $stmt->bindValue(':co2p', (float)$_POST['SetCO2' . $p . 'CO2_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':co2i', (float)$_POST['SetCO2' . $p . 'CO2_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':co2d', (float)$_POST['SetCO2' . $p . 'CO2_D'], SQLITE3_FLOAT);
                $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset'], SQLITE3_TEXT);
                $stmt->execute();
            }

            $stmt = $db->prepare("UPDATE CO2Sensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_CO2_Min=:yaxis_co2_min, YAxis_CO2_Max=:yaxis_co2_max, YAxis_CO2_Tics=:yaxis_co2_tics, YAxis_CO2_MTics=:yaxis_co2_mtics, CO2_Relays_Up=:co2relaysup, CO2_Relays_Down=:co2relaysdown, CO2_Relay_High=:co2relayhigh, CO2_Outmax_High=:co2outmaxhigh, CO2_Relay_Low=:co2relaylow, CO2_Outmax_Low=:co2outmaxlow, CO2_Set=:co2set, CO2_Set_Direction=:co2setdir, CO2_Period=:co2period, CO2_P=:co2p, CO2_I=:co2i, CO2_D=:co2d WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $_POST['sensorco2' . $p . 'name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $_POST['sensorco2' . $p . 'device'], SQLITE3_TEXT);
            if ($_POST['sensorco2' . $p . 'device'] == 'K30') {
                $stmt->bindValue(':pin', $sensor_co2_pin[$p], SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':pin', (int)$_POST['sensorco2' . $p . 'pin'], SQLITE3_INTEGER);
            }
            $stmt->bindValue(':period', (int)$_POST['sensorco2' . $p . 'period'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_relay', (int)$_POST['sensorco2' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_dur', (int)$_POST['sensorco2' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
            $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetCO2' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetCO2' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetCO2' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetCO2' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_min', (int)$_POST['SetCO2' . $p . 'YAxisCO2Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_max', (int)$_POST['SetCO2' . $p . 'YAxisCO2Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_tics', (int)$_POST['SetCO2' . $p . 'YAxisCO2Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_mtics', (int)$_POST['SetCO2' . $p . 'YAxisCO2MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2relaysup', $_POST['SetCO2' . $p . 'CO2RelaysUp'], SQLITE3_TEXT);
            $stmt->bindValue(':co2relaysdown', $_POST['SetCO2' . $p . 'CO2RelaysDown'], SQLITE3_TEXT);
            $stmt->bindValue(':co2relayhigh', (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2outmaxhigh', (int)$_POST['SetCO2' . $p . 'CO2OutmaxHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2relaylow', (int)$_POST['SetCO2' . $p . 'CO2RelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2outmaxlow', (int)$_POST['SetCO2' . $p . 'CO2OutmaxLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2set', (float)$_POST['SetCO2' . $p . 'CO2Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2setdir', (float)$_POST['SetCO2' . $p . 'CO2SetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2period', (int)$_POST['SetCO2' . $p . 'CO2Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2p', (float)$_POST['SetCO2' . $p . 'CO2_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2i', (float)$_POST['SetCO2' . $p . 'CO2_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2d', (float)$_POST['SetCO2' . $p . 'CO2_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_co2_or[$p] == 0 &&
                ($pid_co2_relay_high[$p] != (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'] ||
                $pid_co2_outmax_high[$p] != (int)$_POST['SetCO2' . $p . 'CO2OutmaxHigh'] ||
                $pid_co2_relay_low[$p] != (int)$_POST['SetCO2' . $p . 'CO2RelayLow'] ||
                $pid_co2_outmax_low[$p] != (int)$_POST['SetCO2' . $p . 'CO2OutmaxLow'] ||
                $pid_co2_set[$p] != (float)$_POST['SetCO2' . $p . 'CO2Set'] ||
                $pid_co2_set_dir[$p] != (float)$_POST['SetCO2' . $p . 'CO2SetDir'] ||
                $pid_co2_period[$p] != (int)$_POST['SetCO2' . $p . 'CO2Period'] ||
                $pid_co2_p[$p] != (float)$_POST['SetCO2' . $p . 'CO2_P'] ||
                $pid_co2_i[$p] != (float)$_POST['SetCO2' . $p . 'CO2_I'] ||
                $pid_co2_d[$p] != (float)$_POST['SetCO2' . $p . 'CO2_D'])) {
                shell_exec("$mycodo_client --pidrestart CO2 $p");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
            }
        }

        // Save CO2 sensor and PID variables to a new preset
        if (isset($_POST['Change' . $p . 'CO2SensorNewPreset'])) {
            if (in_array($_POST['sensorco2' . $p . 'presetname'], $sensor_co2_preset)) {
                $name = $_POST['sensorco2' . $p . 'presetname'];
                $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
            } else {
                if (isset($_POST['sensorco2' . $p . 'presetname']) && $_POST['sensorco2' . $p . 'presetname'] != '') {

                    $stmt = $db->prepare("INSERT INTO CO2SensorPreset (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_CO2_Min, YAxis_CO2_Max, YAxis_CO2_Tics, YAxis_CO2_MTics, CO2_Relays_Up, CO2_Relays_Down, CO2_Relay_High, CO2_Outmax_High, CO2_Relay_Low, CO2_Outmax_Low, CO2_Set, CO2_Set_Direction, CO2_Period, CO2_P, CO2_I, CO2_D) VALUES(:preset, :name, :pin, :device, :period, :premeas_relay, :premeas_dur, :activated, :graph, :yaxis_relay_min, :yaxis_relay_max, :yaxis_relay_tics, :yaxis_relay_mtics, :yaxis_co2_min, :yaxis_co2_max, :yaxis_co2_tics, :yaxis_co2_mtics, :co2relaysup, :co2relaysdown, :co2relayhigh, :co2outmaxhigh, :co2relaylow, :co2outmaxlow, :co2set, :co2setdir, :co2period, :co2p, :co2i, :co2d)");
                    $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'presetname'], SQLITE3_TEXT);
                    $stmt->bindValue(':name', $_POST['sensorco2' . $p . 'name'], SQLITE3_TEXT);
                    $stmt->bindValue(':device', $_POST['sensorco2' . $p . 'device'], SQLITE3_TEXT);
                    $stmt->bindValue(':pin', (int)$_POST['sensorco2' . $p . 'pin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':period', (int)$_POST['sensorco2' . $p . 'period'], SQLITE3_INTEGER);
                    $stmt->bindValue(':premeas_relay', (int)$_POST['sensorco2' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                    $stmt->bindValue(':premeas_dur', (int)$_POST['sensorco2' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
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
                    $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetCO2' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetCO2' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetCO2' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetCO2' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_co2_min', (int)$_POST['SetCO2' . $p . 'YAxisCO2Min'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_co2_max', (int)$_POST['SetCO2' . $p . 'YAxisCO2Max'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_co2_tics', (int)$_POST['SetCO2' . $p . 'YAxisCO2Tics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_co2_mtics', (int)$_POST['SetCO2' . $p . 'YAxisCO2MTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2relaysup', $_POST['SetCO2' . $p . 'CO2RelaysUp'], SQLITE3_TEXT);
                    $stmt->bindValue(':co2relaysdown', $_POST['SetCO2' . $p . 'CO2RelaysDown'], SQLITE3_TEXT);
                    $stmt->bindValue(':co2relayhigh', (int)$_POST['SetCO2' . $p . 'CO2RelayHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2outmaxhigh', (int)$_POST['SetCO2' . $p . 'CO2OutmaxHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2relaylow', (int)$_POST['SetCO2' . $p . 'CO2RelayLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2outmaxlow', (int)$_POST['SetCO2' . $p . 'CO2OutmaxLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2set', (float)$_POST['SetCO2' . $p . 'CO2Set'], SQLITE3_FLOAT);
                    $stmt->bindValue(':co2setdir', (float)$_POST['SetCO2' . $p . 'CO2SetDir'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2period', (int)$_POST['SetCO2' . $p . 'CO2Period'], SQLITE3_INTEGER);
                    $stmt->bindValue(':co2p', (float)$_POST['SetCO2' . $p . 'CO2_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':co2i', (float)$_POST['SetCO2' . $p . 'CO2_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':co2d', (float)$_POST['SetCO2' . $p . 'CO2_D'], SQLITE3_FLOAT);
                    $stmt->execute();
                } else {
                    $sensor_error = 'Error: You must enter a name to create a new preset.';
                }
            }
        }
    }

    // Load CO2 sensor and PID variables from preset
    if (isset($_POST['Change' . $p . 'CO2SensorLoad']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {

        $stmt = $db->prepare('SELECT * FROM CO2SensorPreset WHERE Id=:preset');
        $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset']);
        $result = $stmt->execute();
        $exist = $result->fetchArray();

        // Id exists, change values to preset
        if ($exist != False) {

            $stmt = $db->prepare('SELECT Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_CO2_Min, YAxis_CO2_Max, YAxis_CO2_Tics, YAxis_CO2_MTics, CO2_Relays_Up, CO2_Relays_Down, CO2_Relay_High, CO2_Outmax_High, CO2_Relay_Low, CO2_Outmax_Low, CO2_Set, CO2_Set_Direction, CO2_Period, CO2_P, CO2_I, CO2_D FROM CO2SensorPreset WHERE Id=:preset');
            $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset']);
            $result = $stmt->execute();
            $row = $result->fetchArray();

            $stmt = $db->prepare("UPDATE CO2Sensor SET Name=:name, Pin=:pin, Device=:device, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_CO2_Min=:yaxis_co2_min, YAxis_CO2_Max=:yaxis_co2_max, YAxis_CO2_Tics=:yaxis_co2_tics, YAxis_CO2_MTics=:yaxis_co2_mtics, CO2_Relays_Up=:co2relaysup, CO2_Relays_Down=:co2relaysdown, CO2_Relay_High=:co2relayhigh, CO2_Outmax_High=:co2outmaxhigh, CO2_Relay_Low=:co2relaylow, CO2_Outmax_Low=:co2outmaxlow, CO2_OR=:co2or, CO2_Set=:co2set, CO2_Set_Direction=:co2setdir, CO2_Period=:co2period, CO2_P=:co2p, CO2_I=:co2i, CO2_D=:co2d WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $row['Name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $row['Device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', $row['Pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', $row['Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_relay', $row['Pre_Measure_Relay'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_dur', $row['Pre_Measure_Dur'], SQLITE3_INTEGER);
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
            $stmt->bindValue(':yaxis_relay_min', $row['YAxis_Relay_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_max', $row['YAxis_Relay_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_tics', $row['YAxis_Relay_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_mtics', $row['YAxis_Relay_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_min', $row['YAxis_CO2_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_max', $row['YAxis_CO2_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_tics', $row['YAxis_CO2_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_co2_mtics', $row['YAxis_CO2_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2relaysup', $row['CO2_Relays_Up'], SQLITE3_TEXT);
            $stmt->bindValue(':co2relaysdown', $row['CO2_Relays_Down'], SQLITE3_TEXT);
            $stmt->bindValue(':co2relayhigh', $row['CO2_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2outmaxhigh', $row['CO2_Outmax_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2relaylow', $row['CO2_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2outmaxlow', $row['CO2_Outmax_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2or', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':co2set', $row['CO2_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2setdir', $row['CO2_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2period', $row['CO2_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':co2p', $row['CO2_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2i', $row['CO2_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':co2d', $row['CO2_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_co2_or[$p] == 0) {
                shell_exec("$mycodo_client --pidrestart CO2 $p");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
            }
        } else {
            $sensor_error = 'Error: Something went wrong. The preset you selected doesn\'t exist.';
        }
    }

    // Rename CO2 preset
    if (isset($_POST['Change' . $p . 'CO2SensorRenamePreset']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {
        if(in_array($_POST['sensorco2' . $p . 'presetname'], $sensor_co2_preset)) {
            $name = $_POST['sensorco2' . $p . 'presetname'];
            $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
        } else {
            $stmt = $db->prepare("UPDATE CO2SensorPreset SET Id=:presetnew WHERE Id=:presetold");
            $stmt->bindValue(':presetold', $_POST['sensorco2' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->bindValue(':presetnew', $_POST['sensorco2' . $p . 'presetname'], SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    // Delete CO2 preset
    if (isset($_POST['Change' . $p . 'CO2SensorDelete']) && $_POST['sensorco2' . $p . 'preset'] != 'default') {
        $stmt = $db->prepare("DELETE FROM CO2SensorPreset WHERE Id=:preset");
        $stmt->bindValue(':preset', $_POST['sensorco2' . $p . 'preset']);
        $stmt->execute();
    }

    // Delete CO2 sensors
    if (isset($_POST['Delete' . $p . 'CO2Sensor'])) {
        $stmt = $db->prepare("DELETE FROM CO2Sensor WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_co2_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidallrestart CO2");
    }
}


/*
 *
 * Pressure Sensors
 *
 */

for ($p = 0; $p < count($sensor_press_id); $p++) {

    // Add Press Conditional statement
    if (isset($_POST['AddPress' . $p . 'Conditional'])) {
        $stmt = $db->prepare("INSERT INTO PressSensorConditional (Id, Name, Sensor, State, Condition, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On) VALUES(:id, :name, :sensor, 0, :condition, :direction, :setpoint, :period, :relay, :relaystate, :relaysecondson)");
        $stmt->bindValue(':id', uniqid(), SQLITE3_TEXT);
        $stmt->bindValue(':name', $_POST['conditionpress' . $p . 'name'], SQLITE3_TEXT);
        $stmt->bindValue(':sensor', $p, SQLITE3_INTEGER);
        $stmt->bindValue(':condition', $_POST['conditionpress' . $p . 'condition'], SQLITE3_TEXT);
        $stmt->bindValue(':direction', (int)$_POST['conditionpress' . $p . 'direction'], SQLITE3_INTEGER);
        $stmt->bindValue(':setpoint', (float)$_POST['conditionpress' . $p . 'setpoint'], SQLITE3_FLOAT);
        $stmt->bindValue(':period', (int)$_POST['conditionpress' . $p . 'period'], SQLITE3_INTEGER);
        $stmt->bindValue(':relay', (int)$_POST['conditionpress' . $p . 'relay'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaystate', (int)$_POST['conditionpress' . $p . 'relaystate'], SQLITE3_INTEGER);
        $stmt->bindValue(':relaysecondson', (int)$_POST['conditionpress' . $p . 'relaysecondson'], SQLITE3_INTEGER);
        $stmt->execute();
    }

    if (isset($conditional_press_id[$p])) {
        for ($z = 0; $z < count($conditional_press_id[$p]); $z++) {
            // Delete Press Conditional Statement
            if (isset($_POST['DeletePress' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("DELETE FROM PressSensorConditional WHERE Id=:id");
                $stmt->bindValue(':id', $conditional_press_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            // Turn Press Conditional Statements On/Off
            if (isset($_POST['TurnOnPress' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE PressSensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 1);
                $stmt->bindValue(':id', $conditional_press_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }

            if (isset($_POST['TurnOffPress' . $p . '-' . $z . 'Conditional'])) {
                $stmt = $db->prepare("UPDATE PressSensorConditional SET State=:state WHERE Id=:id");
                $stmt->bindValue(':state', 0);
                $stmt->bindValue(':id', $conditional_press_id[$p][$z], SQLITE3_TEXT);
                $stmt->execute();

                shell_exec("$mycodo_client --sqlreload -1");
            }
        }
    }

    // Check for errors
    if ((isset($_POST['ChangePress' . $p . 'TempOR']) && (int)$_POST['ChangePress' . $p . 'TempOR'] == 0) ||
        ($pid_press_temp_or[$p] == 0 && isset($_POST['Change' . $p . 'PressSensorOverwrite'])) ||
        ($pid_press_temp_or[$p] == 0 && isset($_POST['Change' . $p . 'PressSensorLoad']) && $_POST['sensorpress' . $p . 'preset'] != 'default')) {

        if ((float)$_POST['SetPress' . $p . 'TempSetDir'] == 0 && ((int)$_POST['SetPress' . $p . 'TempRelayLow'] < 1 || (int)$_POST['SetPress' . $p . 'TempRelayHigh'] < 1)) {
            $sensor_error = 'Error: If "PID Regulate" is set to Both, "Up Relay" and "Down Relay" is required to be set.';
        } else if ((float)$_POST['SetPress' . $p . 'TempSetDir'] == 1 && (int)$_POST['SetPress' . $p . 'TempRelayLow'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Up, "Up Relay" is required to be set.';
        } else if ((float)$_POST['SetPress' . $p . 'TempSetDir'] == -1 && (int)$_POST['SetPress' . $p . 'TempRelayHigh'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Down, "Down Relay" is required to be set.';
        }
    }

    if ((isset($_POST['ChangePress' . $p . 'PressOR']) && (int)$_POST['ChangePress' . $p . 'PressOR'] == 0) ||
        ($pid_press_press_or[$p] == 0 && isset($_POST['Change' . $p . 'PressSensorOverwrite'])) ||
        ($pid_press_press_or[$p] == 0 && isset($_POST['Change' . $p . 'PressSensorLoad']) && $_POST['sensorpress' . $p . 'preset'] != 'default')) {

        if ((float)$_POST['SetPress' . $p . 'PressSetDir'] == 0 && ((int)$_POST['SetPress' . $p . 'PressRelayLow'] < 1 || (int)$_POST['SetPress' . $p . 'PressRelayHigh'] < 1)) {
            $sensor_error = 'Error: If "PID Regulate" is set to Both, "Up Relay" and "Down Relay" is required to be set.';
        } else if ((float)$_POST['SetPress' . $p . 'PressSetDir'] == 1 && (int)$_POST['SetPress' . $p . 'PressRelayLow'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Up, "Up Relay" is required to be set.';
        } else if ((float)$_POST['SetPress' . $p . 'PressSetDir'] == -1 && (int)$_POST['SetPress' . $p . 'PressRelayHigh'] < 1) {
            $sensor_error = 'Error: If "PID Regulate" is set to Down, "Down Relay" is required to be set.';
        }
    }

    if (isset($_POST['Change' . $p . 'PressSensorOverwrite'])) {
        $re = '/^\d+(?:,\d+)*$/';
        if (($_POST['SetPress' . $p . 'TempRelaysUp'] != '0' and
            (!ctype_digit($_POST['SetPress' . $p . 'TempRelaysUp']) and !preg_match($re, $_POST['SetPress' . $p . 'TempRelaysUp']))) or
            ($_POST['SetPress' . $p . 'TempRelaysUp'] == '') or
            ($_POST['SetPress' . $p . 'TempRelaysDown'] != '0' and
            (!ctype_digit($_POST['SetPress' . $p . 'TempRelaysDown']) and !preg_match($re, $_POST['SetPress' . $p . 'TempRelaysDown']))) or
            ($_POST['SetPress' . $p . 'TempRelaysDown'] == '')) {
            $sensor_error = 'Error: Graph Relays must contain digits separated by commas or be set to 0.';
        } else if (($_POST['SetPress' . $p . 'PressRelaysUp'] != '0' and
            (!ctype_digit($_POST['SetPress' . $p . 'PressRelaysUp']) and !preg_match($re, $_POST['SetPress' . $p . 'PressRelaysUp']))) or
            ($_POST['SetPress' . $p . 'PressRelaysUp'] == '') or
            ($_POST['SetPress' . $p . 'PressRelaysDown'] != '0' and
            (!ctype_digit($_POST['SetPress' . $p . 'PressRelaysDown']) and !preg_match($re, $_POST['SetPress' . $p . 'PressRelaysDown']))) or
            ($_POST['SetPress' . $p . 'PressRelaysDown'] == '')) {
            $sensor_error = 'Error: Graph Relays must contain digits separated by commas or be set to 0.';
        }
    }


    // If no errors encountered in the form data, proceed
    if (!isset($sensor_error)) {

        // Set Temperature PID override on or off
        if (isset($_POST['ChangePress' . $p . 'TempOR'])) {

            $stmt = $db->prepare("UPDATE PressSensor SET Temp_OR=:pressor WHERE Id=:id");
            $stmt->bindValue(':pressor', (int)$_POST['ChangePress' . $p . 'TempOR'], SQLITE3_INTEGER);
            $stmt->bindValue(':id', $sensor_press_id[$p], SQLITE3_TEXT);
            $stmt->execute();
            if ((int)$_POST['ChangePress' . $p . 'TempOR']) {
                shell_exec("$mycodo_client --pidstop PressTemp $p");
                shell_exec("$mycodo_client --sqlreload -1");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
                shell_exec("$mycodo_client --pidstart PressTemp $p");
            }
        }

        // Set Pressure sensor PID override on or off
        if (isset($_POST['ChangePress' . $p . 'PressOR'])) {

            $stmt = $db->prepare("UPDATE PressSensor SET Press_OR=:pressor WHERE Id=:id");
            $stmt->bindValue(':pressor', (int)$_POST['ChangePress' . $p . 'PressOR'], SQLITE3_INTEGER);
            $stmt->bindValue(':id', $sensor_press_id[$p], SQLITE3_TEXT);
            $stmt->execute();
            if ((int)$_POST['ChangePress' . $p . 'PressOR']) {
                shell_exec("$mycodo_client --pidstop PressPress $p");
                shell_exec("$mycodo_client --sqlreload -1");
            } else {
                shell_exec("$mycodo_client --sqlreload -1");
                shell_exec("$mycodo_client --pidstart PressPress $p");
            }
        }


        // Overwrite preset for Pressure sensor and PID variables
        if (isset($_POST['Change' . $p . 'PressSensorOverwrite'])) {

            if (isset($_POST['sensorpress' . $p . 'preset']) && $_POST['sensorpress' . $p . 'preset'] != 'default') {
                $stmt = $db->prepare("UPDATE PressSensorPreset SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, YAxis_Press_Min=:yaxis_press_min, YAxis_Press_Max=:yaxis_press_max, YAxis_Press_Tics=:yaxis_press_tics, YAxis_Press_MTics=:yaxis_press_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Press_Relays_Up=:pressrelaysup, Press_Relays_Down=:pressrelaysdown, Press_Relay_High=:pressrelayhigh, Press_Outmax_High=:pressoutmaxhigh, Press_Relay_Low=:pressrelaylow, Press_Outmax_Low=:pressoutmaxlow, Press_Set=:pressset, Press_Set_Direction=:presssetdir, Press_Period=:pressperiod, Press_P=:press, Press_I=:press, Press_D=:pressd WHERE Id=:preset");
                $stmt->bindValue(':name', $_POST['sensorpress' . $p . 'name'], SQLITE3_TEXT);
                $stmt->bindValue(':device', $_POST['sensorpress' . $p . 'device'], SQLITE3_TEXT);
                $stmt->bindValue(':pin', (int)$_POST['sensorpress' . $p . 'pin'], SQLITE3_INTEGER);
                $stmt->bindValue(':period', (int)$_POST['sensorpress' . $p . 'period'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_relay', (int)$_POST['sensorpress' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                $stmt->bindValue(':premeas_dur', (int)$_POST['sensorpress' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
                if (isset($_POST['sensorpress' . $p . 'activated'])) {
                    $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
                } else {
                    $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
                }
                if (isset($_POST['sensorpress' . $p . 'graph'])) {
                    $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
                } else {
                    $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
                }
                $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetPress' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetPress' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetPress' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetPress' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetPress' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetPress' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetPress' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetPress' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_press_min', (int)$_POST['SetPress' . $p . 'YAxisPressMin'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_press_max', (int)$_POST['SetPress' . $p . 'YAxisPressMax'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_press_tics', (int)$_POST['SetPress' . $p . 'YAxisPressTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':yaxis_press_mtics', (int)$_POST['SetPress' . $p . 'YAxisPressMTics'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaysup', $_POST['SetPress' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelaysdown', $_POST['SetPress' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
                $stmt->bindValue(':temprelayhigh', (int)$_POST['SetPress' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetPress' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':temprelaylow', (int)$_POST['SetPress' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetPress' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempset', (float)$_POST['SetPress' . $p . 'TempSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempsetdir', (float)$_POST['SetPress' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempperiod', (int)$_POST['SetPress' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':tempp', (float)$_POST['SetPress' . $p . 'Temp_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempi', (float)$_POST['SetPress' . $p . 'Temp_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':tempd', (float)$_POST['SetPress' . $p . 'Temp_D'], SQLITE3_FLOAT);
                $stmt->bindValue(':pressrelaysup', $_POST['SetPress' . $p . 'PressRelaysUp'], SQLITE3_TEXT);
                $stmt->bindValue(':pressrelaysdown', $_POST['SetPress' . $p . 'PressRelaysDown'], SQLITE3_TEXT);
                $stmt->bindValue(':pressrelayhigh', (int)$_POST['SetPress' . $p . 'PressRelayHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':pressoutmaxhigh', (int)$_POST['SetPress' . $p . 'PressOutmaxHigh'], SQLITE3_INTEGER);
                $stmt->bindValue(':pressrelaylow', (int)$_POST['SetPress' . $p . 'PressRelayLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':pressoutmaxlow', (int)$_POST['SetPress' . $p . 'PressOutmaxLow'], SQLITE3_INTEGER);
                $stmt->bindValue(':pressset', (float)$_POST['SetPress' . $p . 'PressSet'], SQLITE3_FLOAT);
                $stmt->bindValue(':presssetdir', (float)$_POST['SetPress' . $p . 'PressSetDir'], SQLITE3_INTEGER);
                $stmt->bindValue(':pressperiod', (int)$_POST['SetPress' . $p . 'PressPeriod'], SQLITE3_INTEGER);
                $stmt->bindValue(':pressp', (float)$_POST['SetPress' . $p . 'Press_P'], SQLITE3_FLOAT);
                $stmt->bindValue(':pressi', (float)$_POST['SetPress' . $p . 'Press_I'], SQLITE3_FLOAT);
                $stmt->bindValue(':pressd', (float)$_POST['SetPress' . $p . 'Press_D'], SQLITE3_FLOAT);
                $stmt->bindValue(':preset', $_POST['sensorpress' . $p . 'preset'], SQLITE3_TEXT);
                $stmt->execute();
            }

            $stmt = $db->prepare("UPDATE PressSensor SET Name=:name, Device=:device, Pin=:pin, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, YAxis_Press_Min=:yaxis_press_min, YAxis_Press_Max=:yaxis_press_max, YAxis_Press_Tics=:yaxis_press_tics, YAxis_Press_MTics=:yaxis_press_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Press_Relays_Up=:pressrelaysup, Press_Relays_Down=:pressrelaysdown, Press_Relay_High=:pressrelayhigh, Press_Outmax_High=:pressoutmaxhigh, Press_Relay_Low=:pressrelaylow, Press_Outmax_Low=:pressoutmaxlow, Press_Set=:pressset, Press_Set_Direction=:presssetdir, Press_Period=:pressperiod, Press_P=:pressp, Press_I=:pressi, Press_D=:pressd WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_press_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $_POST['sensorpress' . $p . 'name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $_POST['sensorpress' . $p . 'device'], SQLITE3_TEXT);
            if ($_POST['sensorpress' . $p . 'device'] != "BMP085-180") {
                $stmt->bindValue(':pin', (int)$_POST['sensorpress' . $p . 'pin'], SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':pin', 0, SQLITE3_INTEGER);
            }
            $stmt->bindValue(':period', (int)$_POST['sensorpress' . $p . 'period'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_relay', (int)$_POST['sensorpress' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_dur', (int)$_POST['sensorpress' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
            if (isset($_POST['sensorpress' . $p . 'activated'])) {
                $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
            }
            if (isset($_POST['sensorpress' . $p . 'graph'])) {
                $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
            } else {
                $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
            }
            $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetPress' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetPress' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetPress' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetPress' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetPress' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetPress' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetPress' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetPress' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_min', (int)$_POST['SetPress' . $p . 'YAxisPressMin'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_max', (int)$_POST['SetPress' . $p . 'YAxisPressMax'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_tics', (int)$_POST['SetPress' . $p . 'YAxisPressTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_mtics', (int)$_POST['SetPress' . $p . 'YAxisPressMTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaysup', $_POST['SetPress' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelaysdown', $_POST['SetPress' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelayhigh', (int)$_POST['SetPress' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetPress' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', (int)$_POST['SetPress' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetPress' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', (float)$_POST['SetPress' . $p . 'TempSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', (float)$_POST['SetPress' . $p . 'TempSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', (int)$_POST['SetPress' . $p . 'TempPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', (float)$_POST['SetPress' . $p . 'Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', (float)$_POST['SetPress' . $p . 'Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', (float)$_POST['SetPress' . $p . 'Temp_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':pressrelaysup', $_POST['SetPress' . $p . 'PressRelaysUp'], SQLITE3_TEXT);
            $stmt->bindValue(':pressrelaysdown', $_POST['SetPress' . $p . 'PressRelaysDown'], SQLITE3_TEXT);
            $stmt->bindValue(':pressrelayhigh', (int)$_POST['SetPress' . $p . 'PressRelayHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressoutmaxhigh', (int)$_POST['SetPress' . $p . 'PressOutmaxHigh'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressrelaylow', (int)$_POST['SetPress' . $p . 'PressRelayLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressoutmaxlow', (int)$_POST['SetPress' . $p . 'PressOutmaxLow'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressset', (float)$_POST['SetPress' . $p . 'PressSet'], SQLITE3_FLOAT);
            $stmt->bindValue(':presssetdir', (float)$_POST['SetPress' . $p . 'PressSetDir'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressperiod', (int)$_POST['SetPress' . $p . 'PressPeriod'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressp', (float)$_POST['SetPress' . $p . 'Press_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':pressi', (float)$_POST['SetPress' . $p . 'Press_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':pressd', (float)$_POST['SetPress' . $p . 'Press_D'], SQLITE3_FLOAT);
            $stmt->execute();   

            $reload = 1;
            if ($pid_press_temp_or[$p] == 0 &&
                ($pid_press_temp_relay_high[$p] != (int)$_POST['SetPress' . $p . 'TempRelayHigh'] ||
                $pid_press_temp_outmax_high[$p] != (int)$_POST['SetPress' . $p . 'TempOutmaxHigh'] ||
                $pid_press_temp_relay_low[$p] != (int)$_POST['SetPress' . $p . 'TempRelayLow'] ||
                $pid_press_temp_outmax_low[$p] != (int)$_POST['SetPress' . $p . 'TempOutmaxLow'] ||
                $pid_press_temp_set[$p] != (float)$_POST['SetPress' . $p . 'TempSet'] ||
                $pid_press_temp_set_dir[$p] != (float)$_POST['SetPress' . $p . 'TempSetDir'] ||
                $pid_press_temp_period[$p] != (int)$_POST['SetPress' . $p . 'TempPeriod'] ||
                $pid_press_temp_p[$p] != (float)$_POST['SetPress' . $p . 'Temp_P'] ||
                $pid_press_temp_i[$p] != (float)$_POST['SetPress' . $p . 'Temp_I'] ||
                $pid_press_temp_d[$p] != (float)$_POST['SetPress' . $p . 'Temp_D'])) {
                shell_exec("$mycodo_client --pidrestart PressTemp $p");
                $reload = 0;
            }
            if ($pid_press_press_or[$p] == 0 &&
                ($pid_press_press_relay_high[$p] != (int)$_POST['SetPress' . $p . 'PressRelayHigh'] ||
                $pid_press_press_outmax_high[$p] != (int)$_POST['SetPress' . $p . 'PressOutmaxHigh'] ||
                $pid_press_press_relay_low[$p] != (int)$_POST['SetPress' . $p . 'PressRelayLow'] ||
                $pid_press_press_outmax_low[$p] != (int)$_POST['SetPress' . $p . 'PressOutmaxLow'] ||
                $pid_press_press_set[$p] != (float)$_POST['SetPress' . $p . 'PressSet'] ||
                $pid_press_press_set_dir[$p] != (float)$_POST['SetPress' . $p . 'PressSetDir'] ||
                $pid_press_press_period[$p] != (int)$_POST['SetPress' . $p . 'PressPeriod'] ||
                $pid_press_press_p[$p] != (float)$_POST['SetPress' . $p . 'Press_P'] ||
                $pid_press_press_i[$p] != (float)$_POST['SetPress' . $p . 'Press_I'] ||
                $pid_press_press_d[$p] != (float)$_POST['SetPress' . $p . 'Press_D'])) {
                shell_exec("$mycodo_client --pidrestart PressPress $p");
                $reload = 0;
            }
            if ($reload) {
                shell_exec("$mycodo_client --sqlreload -1");
            }
        }

        // Save Pressure sensor and PID variables to a new preset
        if (isset($_POST['Change' . $p . 'PressSensorNewPreset'])) {
            if (in_array($_POST['sensorpress' . $p . 'presetname'], $sensor_press_preset)) {
                $name = $_POST['sensorpress' . $p . 'presetname'];
                $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
            } else {
                if (isset($_POST['sensorpress' . $p . 'presetname']) && $_POST['sensorpress' . $p . 'presetname'] != '') {

                    $stmt = $db->prepare("INSERT INTO PressSensorPreset (Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Press_Min, YAxis_Press_Max, YAxis_Press_Tics, YAxis_Press_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Press_Relays_Up, Press_Relays_Down, Press_Relay_High, Press_Outmax_High, Press_Relay_Low, Press_Outmax_Low, Press_Set, Press_Set_Direction, Press_Period, Press_P, Press_I, Press_D) VALUES(:preset, :name, :pin, :device, :period, :premeas_relay, :premeas_dur, :activated, :graph, :yaxis_relay_min, :yaxis_relay_max, :yaxis_relay_tics, :yaxis_relay_mtics, :yaxis_temp_min, :yaxis_temp_max, :yaxis_temp_tics, :yaxis_temp_mtics, :yaxis_press_min, :yaxis_press_max, :yaxis_press_tics, :yaxis_press_mtics, :temprelaysup, :temprelaysdown, :temprelayhigh, :tempoutmaxhigh, :temprelaylow, :tempoutmaxlow, :tempset, :tempsetdir, :tempperiod, :tempp, :tempi, :tempd, :pressrelaysup, :pressrelaysdown, :pressrelayhigh, :pressoutmaxhigh, :pressrelaylow, :pressoutmaxlow, :pressset, :presssetdir, :pressperiod, :pressp, :pressi, :pressd)");
                    $stmt->bindValue(':preset', $_POST['sensorpress' . $p . 'presetname'], SQLITE3_TEXT);
                    $stmt->bindValue(':name', $_POST['sensorpress' . $p . 'name'], SQLITE3_TEXT);
                    $stmt->bindValue(':device', $_POST['sensorpress' . $p . 'device'], SQLITE3_TEXT);
                    $stmt->bindValue(':pin', (int)$_POST['sensorpress' . $p . 'pin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':period', (int)$_POST['sensorpress' . $p . 'period'], SQLITE3_INTEGER);
                    $stmt->bindValue(':premeas_relay', (int)$_POST['sensorpress' . $p . 'premeasure_relay'], SQLITE3_INTEGER);
                    $stmt->bindValue(':premeas_dur', (int)$_POST['sensorpress' . $p . 'premeasure_dur'], SQLITE3_INTEGER);
                    if (isset($_POST['sensorpress' . $p . 'activated'])) {
                        $stmt->bindValue(':activated', 1, SQLITE3_INTEGER);
                    } else {
                        $stmt->bindValue(':activated', 0, SQLITE3_INTEGER);
                    }
                    if (isset($_POST['sensorpress' . $p . 'graph'])) {
                        $stmt->bindValue(':graph', 1, SQLITE3_INTEGER);
                    } else {
                        $stmt->bindValue(':graph', 0, SQLITE3_INTEGER);
                    }
                    $stmt->bindValue(':yaxis_relay_min', (int)$_POST['SetPress' . $p . 'YAxisRelayMin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_max', (int)$_POST['SetPress' . $p . 'YAxisRelayMax'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_tics', (int)$_POST['SetPress' . $p . 'YAxisRelayTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_relay_mtics', (int)$_POST['SetPress' . $p . 'YAxisRelayMTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_min', (int)$_POST['SetPress' . $p . 'YAxisTempMin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_max', (int)$_POST['SetPress' . $p . 'YAxisTempMax'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_tics', (int)$_POST['SetPress' . $p . 'YAxisTempTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_temp_mtics', (int)$_POST['SetPress' . $p . 'YAxisTempMTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_press_min', (int)$_POST['SetPress' . $p . 'YAxisPressMin'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_press_max', (int)$_POST['SetPress' . $p . 'YAxisPressMax'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_press_tics', (int)$_POST['SetPress' . $p . 'YAxisPressTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':yaxis_press_mtics', (int)$_POST['SetPress' . $p . 'YAxisPressMTics'], SQLITE3_INTEGER);
                    $stmt->bindValue(':temprelaysup', $_POST['SetPress' . $p . 'TempRelaysUp'], SQLITE3_TEXT);
                    $stmt->bindValue(':temprelaysdown', $_POST['SetPress' . $p . 'TempRelaysDown'], SQLITE3_TEXT);
                    $stmt->bindValue(':temprelayhigh', (int)$_POST['SetPress' . $p . 'TempRelayHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempoutmaxhigh', (int)$_POST['SetPress' . $p . 'TempOutmaxHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':temprelaylow', (int)$_POST['SetPress' . $p . 'TempRelayLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempoutmaxlow', (int)$_POST['SetPress' . $p . 'TempOutmaxLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempset', (float)$_POST['SetPress' . $p . 'TempSet'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempsetdir', (float)$_POST['SetPress' . $p . 'TempSetDir'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempperiod', (int)$_POST['SetPress' . $p . 'TempPeriod'], SQLITE3_INTEGER);
                    $stmt->bindValue(':tempp', (float)$_POST['SetPress' . $p . 'Temp_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempi', (float)$_POST['SetPress' . $p . 'Temp_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':tempd', (float)$_POST['SetPress' . $p . 'Temp_D'], SQLITE3_FLOAT);
                    $stmt->bindValue(':pressrelaysup', $_POST['SetPress' . $p . 'PressRelaysUp'], SQLITE3_TEXT);
                    $stmt->bindValue(':pressrelaysdown', $_POST['SetPress' . $p . 'PressRelaysDown'], SQLITE3_TEXT);
                    $stmt->bindValue(':pressrelayhigh', (int)$_POST['SetPress' . $p . 'PressRelayHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':pressoutmaxhigh', (int)$_POST['SetPress' . $p . 'PressOutmaxHigh'], SQLITE3_INTEGER);
                    $stmt->bindValue(':pressrelaylow', (int)$_POST['SetPress' . $p . 'PressRelayLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':pressoutmaxlow', (int)$_POST['SetPress' . $p . 'PressOutmaxLow'], SQLITE3_INTEGER);
                    $stmt->bindValue(':pressset', (float)$_POST['SetPress' . $p . 'PressSet'], SQLITE3_FLOAT);
                    $stmt->bindValue(':presssetdir', (float)$_POST['SetPress' . $p . 'PressSetDir'], SQLITE3_INTEGER);
                    $stmt->bindValue(':pressperiod', (int)$_POST['SetPress' . $p . 'PressPeriod'], SQLITE3_INTEGER);
                    $stmt->bindValue(':pressp', (float)$_POST['SetPress' . $p . 'Press_P'], SQLITE3_FLOAT);
                    $stmt->bindValue(':pressi', (float)$_POST['SetPress' . $p . 'Press_I'], SQLITE3_FLOAT);
                    $stmt->bindValue(':pressd', (float)$_POST['SetPress' . $p . 'Press_D'], SQLITE3_FLOAT);
                    $stmt->execute();
                } else {
                    $sensor_error = 'Error: You must enter a name to create a new preset.';
                }
            }
        }
    }


    // Load Pressure sensor and PID variables from preset
    if (isset($_POST['Change' . $p . 'PressSensorLoad']) && $_POST['sensorpress' . $p . 'preset'] != 'default') {

        $stmt = $db->prepare('SELECT * FROM PressSensorPreset WHERE Id=:preset');
        $stmt->bindValue(':preset', $_POST['sensorpress' . $p . 'preset']);
        $result = $stmt->execute();
        $exist = $result->fetchArray();

        // Id exists, change values to preset
        if ($exist != False) {

            $stmt = $db->prepare('SELECT Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Press_Min, YAxis_Press_Max, YAxis_Press_Tics, YAxis_Press_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Press_Relays_Up, Press_Relays_Down, Press_Relay_High, Press_Outmax_High, Press_Relay_Low, Press_Outmax_Low, Press_Set, Press_Set_Direction, Press_Period, Press_P, Press_I, Press_D FROM PressSensorPreset WHERE Id=:preset');
            $stmt->bindValue(':preset', $_POST['sensorpress' . $p . 'preset']);
            $result = $stmt->execute();
            $row = $result->fetchArray();

            $stmt = $db->prepare("UPDATE PressSensor SET Name=:name, Pin=:pin, Device=:device, Period=:period, Pre_Measure_Relay=:premeas_relay, Pre_Measure_Dur=:premeas_dur, Activated=:activated, Graph=:graph, YAxis_Relay_Min=:yaxis_relay_min, YAxis_Relay_Max=:yaxis_relay_max, YAxis_Relay_Tics=:yaxis_relay_tics, YAxis_Relay_MTics=:yaxis_relay_mtics, YAxis_Temp_Min=:yaxis_temp_min, YAxis_Temp_Max=:yaxis_temp_max, YAxis_Temp_Tics=:yaxis_temp_tics, YAxis_Temp_MTics=:yaxis_temp_mtics, YAxis_Press_Min=:yaxis_press_min, YAxis_Press_Max=:yaxis_press_max, YAxis_Press_Tics=:yaxis_press_tics, YAxis_Press_MTics=:yaxis_press_mtics, Temp_Relays_Up=:temprelaysup, Temp_Relays_Down=:temprelaysdown, Temp_Relay_High=:temprelayhigh, Temp_Outmax_High=:tempoutmaxhigh, Temp_Relay_Low=:temprelaylow, Temp_Outmax_Low=:tempoutmaxlow, Temp_OR=:tempor, Temp_Set=:tempset, Temp_Set_Direction=:tempsetdir, Temp_Period=:tempperiod, Temp_P=:tempp, Temp_I=:tempi, Temp_D=:tempd, Press_Relays_Up=:pressrelaysup, Press_Relays_Down=:pressrelaysdown, Press_Relay_High=:pressrelayhigh, Press_Outmax_High=:pressoutmaxhigh, Press_Relay_Low=:pressrelaylow, Press_Outmax_Low=:pressoutmaxlow, Press_OR=:pressor, Press_Set=:pressset, Press_Set_Direction=:presssetdir, Press_Period=:pressperiod, Press_P=:pressp, Press_I=:pressi, Press_D=:pressd WHERE Id=:id");
            $stmt->bindValue(':id', $sensor_press_id[$p], SQLITE3_TEXT);
            $stmt->bindValue(':name', $row['Name'], SQLITE3_TEXT);
            $stmt->bindValue(':device', $row['Device'], SQLITE3_TEXT);
            $stmt->bindValue(':pin', $row['Pin'], SQLITE3_INTEGER);
            $stmt->bindValue(':period', $row['Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_relay', $row['Pre_Measure_Relay'], SQLITE3_INTEGER);
            $stmt->bindValue(':premeas_dur', $row['Pre_Measure_Dur'], SQLITE3_INTEGER);
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
            $stmt->bindValue(':yaxis_relay_min', $row['YAxis_Relay_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_max', $row['YAxis_Relay_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_tics', $row['YAxis_Relay_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_relay_mtics', $row['YAxis_Relay_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_min', $row['YAxis_Temp_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_max', $row['YAxis_Temp_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_tics', $row['YAxis_Temp_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_temp_mtics', $row['YAxis_Temp_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_min', $row['YAxis_Press_Min'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_max', $row['YAxis_Press_Max'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_tics', $row['YAxis_Press_Tics'], SQLITE3_INTEGER);
            $stmt->bindValue(':yaxis_press_mtics', $row['YAxis_Press_MTics'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaysup', $row['Temp_Relays_Up'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelaysdown', $row['Temp_Relays_Down'], SQLITE3_TEXT);
            $stmt->bindValue(':temprelayhigh', $row['Temp_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxhigh', $row['Temp_Outmax_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':temprelaylow', $row['Temp_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempoutmaxlow', $row['Temp_Outmax_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempor', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':tempset', $row['Temp_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempsetdir', $row['Temp_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempperiod', $row['Temp_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':tempp', $row['Temp_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempi', $row['Temp_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':tempd', $row['Temp_D'], SQLITE3_FLOAT);
            $stmt->bindValue(':pressrelaysup', $row['Press_Relays_Up'], SQLITE3_TEXT);
            $stmt->bindValue(':pressrelaysdown', $row['Press_Relays_Down'], SQLITE3_TEXT);
            $stmt->bindValue(':pressrelayhigh', $row['Press_Relay_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressoutmaxhigh', $row['Press_Outmax_High'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressrelaylow', $row['Press_Relay_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressoutmaxlow', $row['Press_Outmax_Low'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressor', 1, SQLITE3_INTEGER);
            $stmt->bindValue(':pressset', $row['Press_Set'], SQLITE3_FLOAT);
            $stmt->bindValue(':presssetdir', $row['Press_Set_Direction'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressperiod', $row['Press_Period'], SQLITE3_INTEGER);
            $stmt->bindValue(':pressp', $row['Press_P'], SQLITE3_FLOAT);
            $stmt->bindValue(':pressi', $row['Press_I'], SQLITE3_FLOAT);
            $stmt->bindValue(':pressd', $row['Press_D'], SQLITE3_FLOAT);
            $stmt->execute();

            if ($pid_press_temp_or[$p] == 0) {
                shell_exec("$mycodo_client --pidrestart PressTemp $p");
            }
            if ($pid_press_press_or[$p] == 0) {
                shell_exec("$mycodo_client --pidrestart PressPress $p");
            }
            if  ($pid_press_temp_or[$p] != 0 or $pid_press_press_or[$p] != 0) {
                shell_exec("$mycodo_client --sqlreload -1");
            }
        } else {
            $sensor_error = 'Error: Something went wrong. The preset you selected doesn\'t exist.';
        }
    }

    // Rename Pressure preset
    if (isset($_POST['Change' . $p . 'PressSensorRenamePreset']) && $_POST['sensorpress' . $p . 'preset'] != 'default') {
        if (in_array($_POST['sensorpress' . $p . 'presetname'], $sensor_press_preset)) {
            $name = $_POST['sensorpress' . $p . 'presetname'];
            $sensor_error = "Error: The preset name '$name' is already in use. Use a different name.";
        } else {
            $stmt = $db->prepare("UPDATE PressSensorPreset SET Id=:presetnew WHERE Id=:presetold");
            $stmt->bindValue(':presetold', $_POST['sensorpress' . $p . 'preset'], SQLITE3_TEXT);
            $stmt->bindValue(':presetnew', $_POST['sensorpress' . $p . 'presetname'], SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    // Delete Pressure preset
    if (isset($_POST['Change' . $p . 'PressSensorDelete']) && $_POST['sensorpress' . $p . 'preset'] != 'default') {
        $stmt = $db->prepare("DELETE FROM PressSensorPreset WHERE Id=:preset");
        $stmt->bindValue(':preset', $_POST['sensorpress' . $p . 'preset']);
        $stmt->execute();
    }

    // Delete Pressure sensors
    if (isset($_POST['Delete' . $p . 'PressSensor'])) {
        $stmt = $db->prepare("DELETE FROM PressSensor WHERE Id=:id");
        $stmt->bindValue(':id', $sensor_press_id[$p], SQLITE3_TEXT);
        $stmt->execute();

        shell_exec("$mycodo_client --pidallrestart Press");
    }
}


/*
 *
 * Camera
 *
 */

// Change camera still image settings
if (isset($_POST['ChangeStill'])) {
    $stmt = $db->prepare("UPDATE CameraStill SET Relay=:relay, Timestamp=:timestamp, Display_Last=:displaylast, Cmd_Pre=:cmdpre, Cmd_Post=:cmdpost, Extra_Parameters=:extra");
    $stmt->bindValue(':relay', (int)$_POST['Still_Relay'], SQLITE3_INTEGER);
    $stmt->bindValue(':timestamp', (int)$_POST['Still_Timestamp'], SQLITE3_INTEGER);
    $stmt->bindValue(':displaylast', (int)$_POST['Still_DisplayLast'], SQLITE3_INTEGER);
    $cmd_pre = SQLite3::escapeString($_POST['Still_Cmd_Pre']);
    $cmd_post = SQLite3::escapeString($_POST['Still_Cmd_Post']);
    $stmt->bindValue(':cmdpre', $cmd_pre, SQLITE3_TEXT);
    $stmt->bindValue(':cmdpost', $cmd_post, SQLITE3_TEXT);
    $stmt->bindValue(':extra', $_POST['Still_Extra_Parameters'], SQLITE3_TEXT);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload -1");
}

// Change camera video stream settings
if (isset($_POST['ChangeStream'])) {
    $stmt = $db->prepare("UPDATE CameraStream SET Relay=:relay, Cmd_Pre=:cmdpre, Cmd_Post=:cmdpost, Extra_Parameters=:extra");
    $stmt->bindValue(':relay', (int)$_POST['Stream_Relay'], SQLITE3_INTEGER);
    $cmd_pre = SQLite3::escapeString($_POST['Stream_Cmd_Pre']);
    $cmd_post = SQLite3::escapeString($_POST['Stream_Cmd_Post']);
    $stmt->bindValue(':cmdpre', $cmd_pre, SQLITE3_TEXT);
    $stmt->bindValue(':cmdpost', $cmd_post, SQLITE3_TEXT);
    $stmt->bindValue(':extra', $_POST['Stream_Extra_Parameters'], SQLITE3_TEXT);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload -1");
}

// Change camera timelapse settings
if (isset($_POST['ChangeTimelapse'])) {
    $stmt = $db->prepare("UPDATE CameraTimelapse SET Relay=:relay, Path=:path, Prefix=:prefix, File_Timestamp=:timestamp, Display_Last=:displaylast, Cmd_Pre=:cmdpre, Cmd_Post=:cmdpost, Extra_Parameters=:extra");
    $stmt->bindValue(':relay', (int)$_POST['Timelapse_Relay'], SQLITE3_INTEGER);
    $stmt->bindValue(':path', $_POST['Timelapse_Path'], SQLITE3_TEXT);
    $stmt->bindValue(':prefix', $_POST['Timelapse_Prefix'], SQLITE3_TEXT);
    $stmt->bindValue(':timestamp', (int)$_POST['Timelapse_Timestamp'], SQLITE3_INTEGER);
    $stmt->bindValue(':displaylast', (int)$_POST['Timelapse_DisplayLast'], SQLITE3_INTEGER);
    $cmd_pre = SQLite3::escapeString($_POST['Timelapse_Cmd_Pre']);
    $cmd_post = SQLite3::escapeString($_POST['Timelapse_Cmd_Post']);
    $stmt->bindValue(':cmdpre', $cmd_pre, SQLITE3_TEXT);
    $stmt->bindValue(':cmdpost', $cmd_post, SQLITE3_TEXT);
    $stmt->bindValue(':extra', $_POST['Timelapse_Extra_Parameters'], SQLITE3_TEXT);
    $stmt->execute();
    shell_exec("$mycodo_client --sqlreload -1");
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
    if ($still_cmd_pre != '') shell_exec($still_cmd_pre);

    if ($still_relay > 0) {
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

    if ($still_cmd_post != '') shell_exec($still_cmd_post);
    shell_exec("rm -f $lock_raspistill");
}

// Start video stream
if (isset($_POST['start-stream']) && !file_exists($lock_raspistill) && !file_exists($lock_mjpg_streamer) && !file_exists($lock_timelapse)) {
    shell_exec("touch $lock_mjpg_streamer");
    if ($stream_cmd_pre != '') shell_exec($stream_cmd_pre);

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

    if ($stream_cmd_post != '') shell_exec($stream_cmd_post);
    shell_exec("rm -f $lock_mjpg_streamer");
    sleep(1);
}

// Start time-lapse
if (isset($_POST['start-timelapse'])) {
    if (isset($_POST['timelapse_duration']) && isset($_POST['timelapse_runtime']) && !file_exists($lock_raspistill) && !file_exists($lock_mjpg_streamer) && !file_exists($lock_timelapse)) {
        shell_exec("touch $lock_timelapse");
        if ($still_cmd_pre != '') shell_exec($still_cmd_pre);

        if ($timelapse_relay) {
            shell_exec("touch $lock_timelapse_light");
            if ($relay_trigger[$timelapse_relay-1] == 1) $trigger = 1;
            else $trigger = 0;
        } else $trigger = 0;

        if ($timelapse_timestamp) $timestamp = substr(`date +"%Y%m%d%H%M%S"`, 0, -1);
        else $timelapse = 0;

        $duration = $_POST['timelapse_duration'] * 60 * 1000;
        $timeout = $_POST['timelapse_runtime'] * 60 * 1000;

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

    if ($timelapse_cmd_post != '') shell_exec($timelapse_cmd_post);
    shell_exec("rm -f $lock_timelapse");
    sleep(1);
}


/*
 *
 * Miscelaneous
 *
 */

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
    shell_exec("$mycodo_client --sqlreload -1");
}

// Change interface settings
if (isset($_POST['ChangeInterface'])) {
    $stmt = $db->prepare("UPDATE Misc SET Refresh_Time=:refreshtime, Enable_Max_Amps=:enablemaxamps, Max_Amps=:maxamps");
    $stmt->bindValue(':refreshtime', (int)$_POST['refresh_time'], SQLITE3_INTEGER);
    $stmt->bindValue(':enablemaxamps', (int)$_POST['enable_max_amps'], SQLITE3_INTEGER);
    $stmt->bindValue(':maxamps', (float)$_POST['max_amps'], SQLITE3_FLOAT);
    $stmt->execute();
}

// Request sensor read and log write
 if (isset($_POST['WriteSensorLog'])) {
    shell_exec("$mycodo_client --writetlog 0");
    shell_exec("$mycodo_client --writehtlog 0");
    shell_exec("$mycodo_client --writeco2log 0");
}

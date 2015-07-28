<?php
/*
*  functions.php - Mycodo functions
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

// Instruct mycodo.py daemon to reload a specific PID controller
function pid_reload($mycodo_client, $controller, $pid) {
    shell_exec("$mycodo_client --pidstop $controller $pid");
    shell_exec("$mycodo_client --sqlreload 0");
    shell_exec("$mycodo_client --pidstart $controller $pid");
}


/*
 * Logging
 */

// Concatenate sensor and relay log files (to TempFS) to ensure the latest data is being used
function concatenate_logs($type) {
    switch($type) {
        case 't':
            `cat /var/www/mycodo/log/sensor-t.log /var/www/mycodo/log/sensor-t-tmp.log > /var/tmp/sensor-t.log`;
            break;
        case 'ht':
            `cat /var/www/mycodo/log/sensor-ht.log /var/www/mycodo/log/sensor-ht-tmp.log > /var/tmp/sensor-ht.log`;
            break;
        case 'co2':
            `cat /var/www/mycodo/log/sensor-co2.log /var/www/mycodo/log/sensor-co2-tmp.log > /var/tmp/sensor-co2.log`;
            break;
        case 'relay':
            `cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log > /var/tmp/relay.log`;
            break;
        case 'daemon':
            `cat /var/www/mycodo/log/daemon.log /var/www/mycodo/log/daemon-tmp.log > /var/tmp/daemon.log`;
            break;
        case 'all':
            `cat /var/www/mycodo/log/sensor-t.log /var/www/mycodo/log/sensor-t-tmp.log > /var/tmp/sensor-t.log`;
            `cat /var/www/mycodo/log/sensor-ht.log /var/www/mycodo/log/sensor-ht-tmp.log > /var/tmp/sensor-ht.log`;
            `cat /var/www/mycodo/log/sensor-co2.log /var/www/mycodo/log/sensor-co2-tmp.log > /var/tmp/sensor-co2.log`;
            `cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log > /var/tmp/relay.log`;
            break;
    }
}

// Display Log tab SQL database tables, names, and variables
function view_sql_db($sqlite_db) {
    $db = new SQLite3($sqlite_db);
    print "Table: Numbers<br>Relays HTSensors CO2Sensors Timers<br>";
    $results = $db->query('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
    }
    print "<br>Table: Relays<br>Id Name Pin Trigger<br>";
    $results = $db->query('SELECT Id, Name, Pin, Trigger FROM Relays');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
    }
    print "<br>Table: HTSensor<br>Id Name Pin Device Period Activated Graph Temp_Relay Temp_OR Temp_Set Temp_P Temp_I Temp_D Hum_Relay Hum_OR Hum_Set Hum_P Hum_I Hum_D<br>";
    $results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_P, Hum_I, Hum_D FROM HTSensor');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . " " . $row[13] . " " . $row[14] . " " . $row[15] . " " . $row[16] . " " . $row[17] . " " . $row[18] . "<br>";
    }
    print "<br>Table: CO2Sensor<br>Id Name Pin Device Period Activated Graph CO2_Relay CO2_OR CO2_Set CO2_P CO2_I CO2_D<br>";
    $results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay, CO2_OR, CO2_Set, CO2_P, CO2_I, CO2_D FROM CO2Sensor');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . "<br>";
    }
    print "<br>Table: Timers<br>";
    print "Id Name State Relay DurationOn DurationOff<br>";
    $results = $db->query('SELECT Id, Name, State, Relay, DurationOn, DurationOff FROM Timers');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . "<br>";
    }
    print "<br>Table: SMTP<br>";
    print "Host SSL Port User Pass Email_From Email_To<br>";
    $results = $db->query('SELECT Host, SSL, Port, User, Pass, Email_From, Email_To FROM SMTP');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] ."<br>";
    }
    print "<br>Table: Misc<br>";
    print "Camera_Relay Dismiss_Notification<br>";
    $results = $db->query('SELECT Camera_Relay, Dismiss_Notification FROM Misc');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . "<br>";
    }
}


/*
 * Graphing
 */

// Generate and display graphs on the Main tab
function generate_graphs($mycodo_client, $graph_id, $graph_type, $graph_time_span, $sensor_t_num, $sensor_t_graph, $sensor_ht_num, $sensor_ht_graph, $sensor_co2_num, $sensor_co2_graph) {
    // Main preset: Display graphs of past day and week
    if ($graph_time_span == 'default') {

        if (array_sum($sensor_t_graph)) {
            $sensor_t_log_file_tmp = "/var/www/mycodo/log/sensor-t-tmp.log";
            $sensor_t_log_file = "/var/www/mycodo/log/sensor-t.log";
            $sensor_t_log_generate = "/var/tmp/sensor-t-logs-default.log";
            system("cat $sensor_t_log_file $sensor_t_log_file_tmp > $sensor_t_log_generate");

            for ($n = 1; $n <= $sensor_t_num; $n++) {
                if ($sensor_t_graph[$n] == 1) {
                    if (!file_exists("/var/www/mycodo/images/graph-tdefaultdefault-$graph_id-$n.png")) {
                        shell_exec("$mycodo_client --graph t $graph_type $graph_time_span $graph_id $n");
                    }
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=t';
                    echo "&sensornumber=$n";
                    echo '&graphtype=default';
                    echo '&graphspan=default';
                    echo "&id=$graph_id>";
                    echo '</div>';

                    if ($n != $sensor_t_num || array_sum($sensor_ht_graph) || array_sum($sensor_co2_graph)) {
                        echo '<hr class="fade"/>';
                    }
                }
            }
            unlink($sensor_t_log_generate);
        }

        if (array_sum($sensor_ht_graph)) {
            $sensor_ht_log_file_tmp = "/var/www/mycodo/log/sensor-ht-tmp.log";
            $sensor_ht_log_file = "/var/www/mycodo/log/sensor-ht.log";
            $sensor_ht_log_generate = "/var/tmp/sensor-ht-logs-default.log";
            system("cat $sensor_ht_log_file $sensor_ht_log_file_tmp > $sensor_ht_log_generate");

            for ($n = 1; $n <= $sensor_ht_num; $n++) {
                if ($sensor_ht_graph[$n] == 1) {
                    if (!file_exists("/var/www/mycodo/images/graph-htdefaultdefault-$graph_id-$n.png")) {
                        shell_exec("$mycodo_client --graph ht $graph_type $graph_time_span $graph_id $n");
                    }
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=ht';
                    echo "&sensornumber=$n";
                    echo '&graphtype=default';
                    echo '&graphspan=default';
                    echo "&id=$graph_id>";
                    echo '</div>';

                    if ($n != $sensor_ht_num || array_sum($sensor_co2_graph)) {
                        echo '<hr class="fade"/>';
                    }
                }
            }
            unlink($sensor_ht_log_generate);
        }

        if (array_sum($sensor_co2_graph)) {
            $sensor_co2_log_file_tmp = "/var/www/mycodo/log/sensor-co2-tmp.log";
            $sensor_co2_log_file = "/var/www/mycodo/log/sensor-co2.log";
            $sensor_co2_log_generate = "/var/tmp/sensor-co2-logs-default.log";
            system("cat $sensor_co2_log_file $sensor_co2_log_file_tmp > $sensor_co2_log_generate");

            for ($n = 1; $n <= $sensor_co2_num; $n++) {
                if ($sensor_co2_graph[$n] == 1) {
                    if (!file_exists("/var/www/mycodo/images/graph-co2defaultdefault-$graph_id-$n.png")) {
                        shell_exec("$mycodo_client --graph co2 $graph_time_span default $graph_id $n");
                    }
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=co2';
                    echo "&sensornumber=$n";
                    echo '&graphspan=default';
                    echo '&graphtype=default';
                    echo "&id=$graph_id>";
                    echo '</div>';

                    if ($n != $sensor_co2_num) {
                        echo '<hr class="fade"/>';
                    }
                }
            }
            unlink($sensor_co2_log_generate);
        }

    } else if ($graph_type == 'combined') { // Combined preset: Generate combined graphs
        if (!file_exists("/var/www/mycodo/images/graph-xcombined$graph_time_span-$graph_id-0.png")) {
            shell_exec("$mycodo_client --graph x $graph_type $graph_time_span $graph_id 0");
        }
        echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                echo 'sensortype=x';
                echo '&sensornumber=0';
                echo "&graphspan=$graph_time_span";
                echo "&graphtype=$graph_type";
                echo "&id=$graph_id>";
                echo '</div>';
    } else if ($graph_type == 'separate') { // Combined preset: Generate separate graphs

        if (array_sum($sensor_t_graph)) {
            $sensor_t_log_file_tmp = "/var/www/mycodo/log/sensor-t-tmp.log";
            $sensor_t_log_file = "/var/www/mycodo/log/sensor-t.log";
            $sensor_t_log_generate = "/var/tmp/sensor-t-logs-separate.log";
            system("cat $sensor_t_log_file $sensor_t_log_file_tmp > $sensor_t_log_generate");

            for ($n = 1; $n <= $sensor_t_num; $n++ ) {
                if ($sensor_t_graph[$n] == 1) {
                    if (!file_exists("/var/www/mycodo/images/graph-tseparate$graph_time_span-$graph_id-$n.png")) {
                        shell_exec("$mycodo_client --graph t $graph_type $graph_time_span $graph_id $n");
                    }
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=t';
                    echo "&sensornumber=$n";
                    echo "&graphspan=$graph_time_span";
                    echo "&graphtype=$graph_type";
                    echo "&id=$graph_id>";
                    echo '</div>';

                    if ($n != $sensor_t_num || array_sum($sensor_ht_graph) || array_sum($sensor_co2_graph)) {
                        echo '<hr class="fade"/>';
                    }
                } 
            }
            unlink($sensor_t_log_generate);
        }

        if (array_sum($sensor_ht_graph)) {
            $sensor_ht_log_file_tmp = "/var/www/mycodo/log/sensor-ht-tmp.log";
            $sensor_ht_log_file = "/var/www/mycodo/log/sensor-ht.log";
            $sensor_ht_log_generate = "/var/tmp/sensor-ht-logs-separate.log";
            system("cat $sensor_ht_log_file $sensor_ht_log_file_tmp > $sensor_ht_log_generate");

            for ($n = 1; $n <= $sensor_ht_num; $n++ ) {
                if ($sensor_ht_graph[$n] == 1) {
                    if (!file_exists("/var/www/mycodo/images/graph-htseparate$graph_time_span-$graph_id-$n.png")) {
                        shell_exec("$mycodo_client --graph ht $graph_type $graph_time_span $graph_id $n");
                    }
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=ht';
                    echo "&sensornumber=$n";
                    echo "&graphspan=$graph_time_span";
                    echo "&graphtype=$graph_type";
                    echo "&id=$graph_id>";
                    echo '</div>';

                    if ($n != $sensor_ht_num || array_sum($sensor_co2_graph)) {
                        echo '<hr class="fade"/>';
                    }
                }
            }
            unlink($sensor_ht_log_generate);
        }

        if (array_sum($sensor_co2_graph)) {
            $sensor_co2_log_file_tmp = "/var/www/mycodo/log/sensor-co2-tmp.log";
            $sensor_co2_log_file = "/var/www/mycodo/log/sensor-co2.log";
            $sensor_co2_log_generate = "/var/tmp/sensor-co2-logs-separate.log";
            system("cat $sensor_co2_log_file $sensor_co2_log_file_tmp > $sensor_co2_log_generate");
            
            for ($n = 1; $n <= $sensor_co2_num; $n++ ) {
                if ($sensor_co2_graph[$n] == 1) {
                    if (!file_exists("/var/www/mycodo/images/graph-co2separate$graph_time_span-$graph_id-$n.png")) {
                        shell_exec("$mycodo_client --graph co2 $graph_type $graph_time_span $graph_id $n");
                    }
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=co2';
                    echo "&sensornumber=$n";
                    echo "&graphspan=$graph_time_span";
                    echo "&graphtype=$graph_type";
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
                if ($n != $sensor_co2_num) {
                    echo '<hr class="fade"/>';
                }
            }
            unlink($sensor_co2_log_generate);
        }
    }
}

// Create new graph ID. Instructs a new graph to be generated
function set_new_graph_id() {
    $unique_id = uniqid();
    setcookie('graph_id', $unique_id, time() + (86400 * 10), "/" );
    $_COOKIE['graph_id'] = $unique_id;
    return $unique_id;
}


function get_graph_cookie($name) {
    switch($name) {
        case 'id': // Check if cookie exists with properly-formatted graph ID
            if (isset($_COOKIE['graph_id'])) {
                if (ctype_alnum($_COOKIE['graph_id']) &&
                    !isset($_GET['Refresh'])) { // Generate graph if auto-refresh is on
                    return $_COOKIE['graph_id'];
                }
            }
            return set_new_graph_id();
        case 'type': // Check if cookie exists for graph type
            if (isset($_COOKIE['graph_type'])) {
                if ($_COOKIE['graph_type'] == 'combined' || $_COOKIE['graph_type'] == 'separate') {
                    return $_COOKIE['graph_type'];
                }
            }
            setcookie('graph_type', 'default', time() + (86400 * 10), "/" );
            $_COOKIE['graph_type'] = 'default';
            return $_COOKIE['graph_type'];
        case 'span': // Check if cookie exists for graph time span
            if (isset($_COOKIE['graph_span'])) {
                if ($_COOKIE['graph_span'] == '1h' || $_COOKIE['graph_span'] == '6h' ||
                    $_COOKIE['graph_span'] == '1d' || $_COOKIE['graph_span'] == '3d' ||
                    $_COOKIE['graph_span'] == '1w' || $_COOKIE['graph_span'] == '1m' ||
                    $_COOKIE['graph_span'] == '3m') {
                    return $_COOKIE['graph_span'];
                }
            }
            setcookie('graph_span', 'default', time() + (86400 * 10), "/" );
            $_COOKIE['graph_span'] = 'default';
            return $_COOKIE['graph_span'];
    }
}

// Display Graphs tab form tpo generate a graph with a custom time span
function displayform() { ?>
    <form action="?tab=custom<?php if (isset($_GET['page'])) echo "&page=" . $_GET['page']; ?>" method="POST">
    <div style="padding: 10px 0 0 15px;">
        <div style="display: inline-block; padding-right:0.5em;">
            <div style="padding-bottom: 5px; text-align: right;">Start: <?php DateSelector("start"); ?></div>
            <div style="text-align: right;">End: <?php DateSelector("end"); ?></div>
        </div>
        <div style="display: inline-block; padding-right:0.5em; vertical-align: top;">
            <div style="display: inline-block; padding-right:0.5em;">
                <select name="custom_type">
                    <option value="Separate" <?php
                        if (isset($_POST['custom_type'])) {
                            if ($_POST['custom_type'] == 'Separate') echo 'selected="selected"';
                        }
                        ?>>Separate</option>
                    <option value="Combined" <?php
                        if (isset($_POST['custom_type'])) {
                            if ($_POST['custom_type'] == 'Combined') echo 'selected="selected"';
                        }
                        ?>>Combined</option>
                </select>
            </div>
            <div style="display: inline-block; padding-right:0.5em;">
                Width: <input type="text" value="900" maxlength=4 size=4 name="graph-width" title="Width of the generated graph"> px (4000 max)
            </div>
            <div style="display: inline-block; padding-right:0.5em;">
                Show Key: <input type="hidden" name="key" value="0" /><input type="checkbox" id="key" name="key" value="1"<?php if (isset($_POST['key'])) if ($_POST['key'] == 1) echo ' checked'; ?> title="Generate graph with legend/key."/>
            </div>
        </div>
        <div style="display: inline-block;">
            <input type="submit" name="SubmitDates" value="Generate">
        </div>
    </div>
    </form>
    <?php
}

// Graphs tab date selection inputs
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
        echo ">" . $monthName[$currentMonth] . "</OPTION>\n";
    }
    echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Day>\n";
    for($currentDay=1; $currentDay <= 31; $currentDay++) {
        echo "<OPTION VALUE=\"$currentDay\"";
        if(intval(date( "d", $useDate))==$currentDay) echo " SELECTED";
        echo ">$currentDay</OPTION>\n";
    }
    echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Year>\n";
    $startYear = date("Y", $useDate);
    for($currentYear = $startYear-5; $currentYear <= $startYear+5; $currentYear++) {
        echo "<OPTION VALUE=\"$currentYear\"";
        if(date("Y", $useDate) == $currentYear) echo " SELECTED";
        echo ">$currentYear</OPTION>\n";
    }
    echo "</SELECT>&nbsp;&nbsp;&nbsp;";

    echo "<SELECT NAME=" . $inName . "Hour>\n";
    for($currentHour=0; $currentHour <= 23; $currentHour++) {
        if($currentHour < 10) echo "<OPTION VALUE=\"0$currentHour\"";
        else echo "<OPTION VALUE=\"$currentHour\"";
        if(intval(date("H", $useDate)) == $currentHour) echo " SELECTED";
        if($currentHour < 10) echo ">0$currentHour</OPTION>\n";
        else echo ">$currentHour</OPTION>\n";
    }
    echo "</SELECT> : ";

    echo "<SELECT NAME=" . $inName . "Minute>\n";
    for($currentMinute=0; $currentMinute <= 59; $currentMinute++) {
        if($currentMinute < 10) echo "<OPTION VALUE=\"0$currentMinute\"";
        else echo "<OPTION VALUE=\"$currentMinute\"";
        if(intval(date( "i", $useDate)) == $currentMinute) echo " SELECTED";
        if($currentMinute < 10) echo ">0$currentMinute</OPTION>\n";
        else echo ">$currentMinute</OPTION>\n";
    }
    echo "</SELECT>";
}

// Delete all graph images except for the last 40 created
function delete_graphs() {
    $dir = "/var/log/mycodo/images/";
    if (is_dir($dir)) {
        if ($dh = opendir($dir)) {
            $files = array();
            while (($file = readdir($dh)) !== false) {
                $files[$dir . $file] = filemtime($dir . $file);
            }
            closedir($dh);
        }
        // Sort by timestamp (integer) from oldest to newest
        asort($files, SORT_NUMERIC);
        // Loop over all but the 40 newest files and delete them
        // Only need the array keys (filenames) since we don't care about
        // timestamps now the array is in order
        $files = array_keys($files);
        for ($i = 0; $i < (count($files) - 40); $i++) {
            if (!is_dir($files[$i])) unlink($files[$i]);
        }
    }
}


/*
 * Miscellaneous
 */

function is_positive_integer($str) {
    return (is_numeric($str) && $str > 0 && $str == round($str));
}
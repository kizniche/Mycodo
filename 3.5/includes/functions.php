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

/*
 * Logging
 */

// Concatenate sensor and relay log files (to TempFS) to ensure the latest data is being used
function concatenate_logs() {
    `cat /var/www/mycodo/log/sensor-t.log /var/www/mycodo/log/sensor-t-tmp.log > /var/tmp/sensor-t.log`;
    `cat /var/www/mycodo/log/sensor-ht.log /var/www/mycodo/log/sensor-ht-tmp.log > /var/tmp/sensor-ht.log`;
    `cat /var/www/mycodo/log/sensor-co2.log /var/www/mycodo/log/sensor-co2-tmp.log > /var/tmp/sensor-co2.log`;
    `cat /var/www/mycodo/log/sensor-press.log /var/www/mycodo/log/sensor-press-tmp.log > /var/tmp/sensor-press.log`;
    `cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log > /var/tmp/relay.log`;
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
function generate_graphs($mycodo_client, $graph_id, $graph_type, $graph_time_span, $sensor_t_graph, $sensor_ht_graph, $sensor_co2_graph, $sensor_press_graph) {

    $sensor_t_log_file_tmp = "/var/www/mycodo/log/sensor-t-tmp.log";
    $sensor_t_log_file = "/var/www/mycodo/log/sensor-t.log";
    $sensor_t_log_generate = "/var/tmp/sensor-t-logs-combined.log";

    $sensor_ht_log_file_tmp = "/var/www/mycodo/log/sensor-ht-tmp.log";
    $sensor_ht_log_file = "/var/www/mycodo/log/sensor-ht.log";
    $sensor_ht_log_generate = "/var/tmp/sensor-ht-logs-combined.log";

    $sensor_co2_log_file_tmp = "/var/www/mycodo/log/sensor-co2-tmp.log";
    $sensor_co2_log_file = "/var/www/mycodo/log/sensor-co2.log";
    $sensor_co2_log_generate = "/var/tmp/sensor-co2-logs-combined.log";

    $sensor_press_log_file_tmp = "/var/www/mycodo/log/sensor-press-tmp.log";
    $sensor_press_log_file = "/var/www/mycodo/log/sensor-press.log";
    $sensor_press_log_generate = "/var/tmp/sensor-press-logs-combined.log";

    // Main preset: Display graphs of past day and week
    if ($graph_time_span == 'default') {
        if (sizeof(glob("/var/www/mycodo/images/*default*$graph_id*")) == 0) {
            shell_exec("$mycodo_client --graph default $graph_id 0 0 0 0");
        }
        $first = 0;
        if (array_sum($sensor_t_graph)) {
            for ($n = 0; $n < count($sensor_t_graph); $n++) {
                if ($sensor_t_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=t';
                    echo "&sensornumber=$n";
                    echo '&graphtype=default';
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
            }
        }
        if (array_sum($sensor_ht_graph)) {
            for ($n = 0; $n < count($sensor_ht_graph); $n++) {
                if ($sensor_ht_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=ht';
                    echo "&sensornumber=$n";
                    echo '&graphtype=default';
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
            }
        }
        if (array_sum($sensor_co2_graph)) {
            for ($n = 0; $n < count($sensor_co2_graph); $n++) {
                if ($sensor_co2_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=co2';
                    echo "&sensornumber=$n";
                    echo '&graphtype=default';
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
            }
        }
        if (array_sum($sensor_press_graph)) {
            for ($n = 0; $n < count($sensor_press_graph); $n++) {
                if ($sensor_press_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=press';
                    echo "&sensornumber=$n";
                    echo '&graphtype=default';
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
            }
        }
    } else if ($graph_type == 'combined') {
        if (sizeof(glob("/var/www/mycodo/images/*combined*$graph_id*")) == 0) {
            shell_exec("$mycodo_client --graph combined $graph_id $graph_time_span 0 0 0");
        }
        $first = 0;
        if (array_sum($sensor_t_graph) || array_sum($sensor_ht_graph)) {
            if ($first) echo '<hr class="fade"/>';
            else $first = 1;
            echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
            echo 'sensortype=temp';
            echo "&graphspan=$graph_time_span";
            echo "&graphtype=$graph_type";
            echo "&id=$graph_id>";
            echo '</div>';
        }
        if (array_sum($sensor_ht_graph)) {
            if ($first) echo '<hr class="fade"/>';
            else $first = 1;
            echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
            echo 'sensortype=hum';
            echo "&graphspan=$graph_time_span";
            echo "&graphtype=$graph_type";
            echo "&id=$graph_id>";
            echo '</div>';
        }
        if (array_sum($sensor_co2_graph)) {
            if ($first) echo '<hr class="fade"/>';
            else $first = 1;
            echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
            echo 'sensortype=co2';
            echo "&graphspan=$graph_time_span";
            echo "&graphtype=$graph_type";
            echo "&id=$graph_id>";
            echo '</div>';
        }
        if (array_sum($sensor_press_graph)) {
            if ($first) echo '<hr class="fade"/>';
            else $first = 1;
            echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
            echo 'sensortype=press';
            echo "&graphspan=$graph_time_span";
            echo "&graphtype=$graph_type";
            echo "&id=$graph_id>";
            echo '</div>';
        }
    } else if ($graph_type == 'separate') {
        if (sizeof(glob("/var/www/mycodo/images/*separate*$graph_id*")) == 0) {
            shell_exec("$mycodo_client --graph $graph_type $graph_id $graph_time_span 0 0 0");
        }
        $first = 0;
        if (array_sum($sensor_t_graph)) {
            for ($n = 0; $n < count($sensor_t_graph); $n++ ) {
                if ($sensor_t_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=t';
                    echo "&sensornumber=$n";
                    echo "&graphspan=$graph_time_span";
                    echo "&graphtype=$graph_type";
                    echo "&id=$graph_id>";
                    echo '</div>';
                } 
            }
        }
        if (array_sum($sensor_ht_graph)) {
            for ($n = 0; $n < count($sensor_ht_graph); $n++ ) {
                if ($sensor_ht_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=ht';
                    echo "&sensornumber=$n";
                    echo "&graphspan=$graph_time_span";
                    echo "&graphtype=$graph_type";
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
            }
        }
        if (array_sum($sensor_co2_graph)) {
            for ($n = 0; $n < count($sensor_co2_graph); $n++) {
                if ($sensor_co2_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=co2';
                    echo "&sensornumber=$n";
                    echo "&graphspan=$graph_time_span";
                    echo "&graphtype=$graph_type";
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
            }
        }
        if (array_sum($sensor_press_graph)) {
            for ($n = 0; $n < count($sensor_press_graph); $n++) {
                if ($sensor_press_graph[$n] == 1) {
                    if ($first) echo '<hr class="fade"/>';
                    else $first = 1;
                    echo '<div style="padding: 1em 0 3em 0;"><img class="main-image" style="max-width:100%;height:auto;" src=image.php?';
                    echo 'sensortype=press';
                    echo "&sensornumber=$n";
                    echo "&graphspan=$graph_time_span";
                    echo "&graphtype=$graph_type";
                    echo "&id=$graph_id>";
                    echo '</div>';
                }
            }
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
                if ($_COOKIE['graph_span'] == '1h' || $_COOKIE['graph_span'] == '3h' ||
                    $_COOKIE['graph_span'] == '6h' || $_COOKIE['graph_span'] == '12h' ||
                    $_COOKIE['graph_span'] == '1d' || $_COOKIE['graph_span'] == '3d' ||
                    $_COOKIE['graph_span'] == '1w' || $_COOKIE['graph_span'] == '2w' ||
                    $_COOKIE['graph_span'] == '1m' || $_COOKIE['graph_span'] == '3m' ||
                    $_COOKIE['graph_span'] == '6m') {
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
                <select style="height: 3em;" name="custom_type">
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
        </div>
        <div style="display: inline-block; padding-right:0.5em; vertical-align: top;">
            <div style="adding-right:0.5em;">
                Width: <input type="text" value="<?php if (isset($_POST['graph-width']) && $_POST['graph-width'] != '') echo $_POST['graph-width']; else echo '950';?>" maxlength=4 size=4 name="graph-width" title="Width of the generated graph"> px (4000 max)
            </div>
        </div>
        <div style="display: inline-block; padding-right:0.5em; vertical-align: top;">
            <button type="submit" name="SubmitDates" value="Generate">Generate<br>Graph</button>
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
    if ($useDate == 0) $useDate = Time();

    echo "<SELECT NAME=" . $inName . "Month>\n";
    for ($currentMonth = 1; $currentMonth <= 12; $currentMonth++) {
        echo "<OPTION VALUE=\"" . intval($currentMonth) . "\"";
        if (isset($_POST['startMonth']) && isset($_POST['endMonth'])) {
            if (isset($_POST['startMonth']) && $inName == "start" && $currentMonth == $_POST['startMonth']) echo " SELECTED";
            else if (isset($_POST['endMonth']) && $inName == "end" && $currentMonth == $_POST['endMonth']) echo " SELECTED";
        } else if (intval(date( "m", $useDate)) == $currentMonth) echo " SELECTED";
        echo ">" . $monthName[$currentMonth] . "</OPTION>\n";
    }
    echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Day>\n";
    for ($currentDay=1; $currentDay <= 31; $currentDay++) {
        echo "<OPTION VALUE=\"$currentDay\"";
        if (isset($_POST['startDay']) && isset($_POST['endDay'])) {
            if (isset($_POST['startDay']) && $inName == "start" && $currentDay == $_POST['startDay']) echo " SELECTED";
            else if (isset($_POST['endDay']) && $inName == "end" && $currentDay == $_POST['endDay']) echo " SELECTED";
        } else if (intval(date( "d", $useDate)) == $currentDay) echo " SELECTED";
        echo ">$currentDay</OPTION>\n";
    }
    echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Year>\n";
    $startYear = date("Y", $useDate);
    for ($currentYear = $startYear-5; $currentYear <= $startYear+5; $currentYear++) {
        echo "<OPTION VALUE=\"$currentYear\"";
        if (isset($_POST['startYear']) && isset($_POST['endYear'])) {
            if (isset($_POST['startYear']) && $inName == "start" && $currentYear == $_POST['startYear']) echo " SELECTED";
            else if (isset($_POST['endYear']) && $inName == "end" && $currentYear == $_POST['endYear']) echo " SELECTED";
        } else if (date("Y", $useDate) == $currentYear) echo " SELECTED";
        echo ">$currentYear</OPTION>\n";
    }
    echo "</SELECT>&nbsp;&nbsp;&nbsp;";

    echo "<SELECT NAME=" . $inName . "Hour>\n";
    for ($currentHour=0; $currentHour <= 23; $currentHour++) {
        if ($currentHour < 10) echo "<OPTION VALUE=\"0$currentHour\"";
        else echo "<OPTION VALUE=\"$currentHour\"";
        if (isset($_POST['startHour']) && isset($_POST['endHour'])) {
            if (isset($_POST['startHour']) && $inName == "start" && $currentHour == $_POST['startHour']) echo " SELECTED";
            else if (isset($_POST['endHour']) && $inName == "end" && $currentHour == $_POST['endHour']) echo " SELECTED";
        } else if (intval(date("H", $useDate)) == $currentHour) echo " SELECTED";
        if ($currentHour < 10) echo ">0$currentHour</OPTION>\n";
        else echo ">$currentHour</OPTION>\n";
    }
    echo "</SELECT> : ";

    echo "<SELECT NAME=" . $inName . "Minute>\n";
    for ($currentMinute=0; $currentMinute <= 59; $currentMinute++) {
        if ($currentMinute < 10) echo "<OPTION VALUE=\"0$currentMinute\"";
        else echo "<OPTION VALUE=\"$currentMinute\"";
        if (isset($_POST['startMinute']) && isset($_POST['endMinute'])) {
            if (isset($_POST['startMinute']) && $inName == "start" && $currentMinute == $_POST['startMinute']) echo " SELECTED";
            else if (isset($_POST['endMinute']) && $inName == "end" && $currentMinute == $_POST['endMinute']) echo " SELECTED";
        } else if (intval(date( "i", $useDate)) == $currentMinute) echo " SELECTED";
        if ($currentMinute < 10) echo ">0$currentMinute</OPTION>\n";
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

function makeThumbnail($updir, $img) {
    $thumbnail_width = 150;
    $thumbnail_height = 150;
    $thumb_prefix = "thumb";
    $arr_image_details = getimagesize("$updir" . "$img");
    $original_width = $arr_image_details[0];
    $original_height = $arr_image_details[1];
    if ($original_width > $original_height) {
        $new_width = $thumbnail_width;
        $new_height = (int)($original_height * $new_width / $original_width);
    } else {
        $new_height = $thumbnail_height;
        $new_width = (int)($original_width * $new_height / $original_height);
    }
    if ($arr_image_details[2] == 1) {
        $imgt = "ImageGIF";
        $imgcreatefrom = "ImageCreateFromGIF";
    }
    if ($arr_image_details[2] == 2) {
        $imgt = "ImageJPEG";
        $imgcreatefrom = "ImageCreateFromJPEG";
    }
    if ($arr_image_details[2] == 3) {
        $imgt = "ImagePNG";
        $imgcreatefrom = "ImageCreateFromPNG";
    }
    if ($imgt) {
        $old_image = $imgcreatefrom("$updir" . "$img");
        $new_image = imagecreatetruecolor($new_width, $new_height);
        imagecopyresized($new_image, $old_image, 0, 0, 0, 0, $new_width, $new_height, $original_width, $original_height);
        $imgt($new_image, "$updir" . "$thumb_prefix" . "$img");
    }
}

function is_positive_integer($str) {
    return (is_numeric($str) && $str > 0 && $str == round($str));
}

function update_check($install_path, $update_check) {
    exec("$install_path/cgi-bin/mycodo-wrapper updatecheck 2>&1", $update_check_output, $update_check_return);

    if ($update_check_return) {
        exec("echo '1' > $update_check");
    } else {
        exec("echo '0' > $update_check");
    }
}

function endswith($string, $test) {
    $strlen = strlen($string);
    $testlen = strlen($test);
    if ($testlen > $strlen) return false;
    return substr_compare($string, $test, $strlen - $testlen, $testlen) === 0;
}
<?php
/*
*  mycodo.php - The Mycodo web control interface (front-end)
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

$version = "3.5.61";

######### Start Edit Configure #########

$install_path = "/var/www/mycodo";
$lock_path = "/var/lock";
$gpio_path = "/usr/local/bin/gpio";

########## End Edit Configure ##########

$mycodo_client = $install_path . "/cgi-bin/mycodo-client.py";
$still_exec = $install_path . "/cgi-bin/camera-still.sh";
$stream_exec = $install_path . "/cgi-bin/camera-stream.sh";
$timelapse_exec = $install_path . "/cgi-bin/camera-timelapse.sh";
$mycodo_db = $install_path . "/config/mycodo.db";

$daemon_log = $install_path . "/log/daemon.log";
$auth_log = $install_path . "/log/auth.log";
$sensor_ht_log = $install_path . "/log/sensor-ht.log";
$sensor_co2_log = $install_path . "/log/sensor-co2.log";
$relay_log = $install_path . "/log/relay.log";

$images = $install_path . "/images";
$lock_daemon = $lock_path . "/mycodo/daemon.lock";
$lock_raspistill = $lock_path . "/mycodo_raspistill";
$lock_mjpg_streamer = $lock_path . "/mycodo_mjpg_streamer";
$lock_mjpg_streamer_relay = $lock_path . "/mycodo-stream-light";
$lock_timelapse = $lock_path . "/mycodo_time_lapse";
$lock_timelapse_light = $lock_path . "/mycodo-timelapse-light";

require($install_path . "/includes/functions.php"); // Mycodo functions
require($install_path . "/includes/database.php"); // Initial SQL database load to variables

// Output an error if the user guest attempts to submit certain forms
if ($_SERVER['REQUEST_METHOD'] == 'POST' && $_SESSION['user_name'] == 'guest' &&
    !isset($_POST['Graph']) && !isset($_POST['login'])) {
    $output_error = 'guest';
} else if ($_SERVER['REQUEST_METHOD'] == 'POST' && $_SESSION['user_name'] != 'guest') {
    // Only non-guest users may perform these actions
    require($install_path . "/includes/restricted.php"); // Configuration changes
    require($install_path . "/includes/database.php"); // Reload SQLite database
}
require($install_path . "/includes/public.php"); // Handle remaining forms
// Retrieve graph-generation variables (must come after running public.php)
$graph_id = get_graph_cookie('id');
$graph_type = get_graph_cookie('type');
$graph_time_span = get_graph_cookie('span');

delete_graphs(); // Delete graph image files if quantity exceeds 20 (delete oldest)
?>
<!doctype html>
<html lang="en" class="no-js">
<head>
    <title>Mycodo</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex">
    <link rel="stylesheet" href="css/fonts.css" type="text/css">
    <link rel="stylesheet" href="css/reset.css" type="text/css">
    <link rel="stylesheet" href="css/style.css" type="text/css">
    <script src="js/modernizr.js"></script>
    <script type="text/javascript">
        function open_legend() {
            window.open("image.php?span=legend-small","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=250, height=300");
        }
        function open_legend_full() {
            window.open("image.php?span=legend-full","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=820, height=550");
        }
    </script>
    <?php
        if (isset($_GET['r']) && ($_GET['r'] == 1)) echo '<META HTTP-EQUIV="refresh" CONTENT="90">';
    ?>
</head>
<body>
<div class="cd-tabs">
<?php
// Display general error that occurred (top of page)
if (isset($output_error)) {
    switch ($output_error) {
        case "guest":
            echo '<span class="error">You cannot perform that task as a guest</span>';
            break;
    }
    $output_error = NULL;
}
?>
<!-- Begin Header -->
<div class="main-wrapper">
    <div class="header">
        <div style="float: left;">
            <div>
                v<?php echo $version; ?>
            </div>
            <div>
                User: <?php echo $_SESSION['user_name']; ?>
            </div>
            <div>
                <a href="index.php?action=logout">Log Out</a>
            </div>
        </div>
    </div>
    <div class="header">
        <div style="float: left;">
            <div style="padding-bottom: 0.1em;"><?php
                if (file_exists($lock_daemon)) echo '<input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On" name="daemon_change" value="0"> Daemon';
                else echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="daemon_change" value="1"> Daemon';
                ?></div>
            <div style="padding-bottom: 0.1em;"><?php
                if (file_exists($lock_mjpg_streamer)) {
                    echo '<input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="" value="0">';
                } else {
                    echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0">';
                }
                ?> Stream</div>
            <div style="padding-bottom: 0.1em;"><?php
                if (file_exists($lock_timelapse)) { // Check if timelapse is running, delete lockfile if not
                    $timelapse_running = shell_exec("ps aux | grep [r]aspistill | grep -Eo 'timelapse'");
                    if ($timelapse_running == NULL) unlink($lock_timelapse);
                }

                if (file_exists($lock_timelapse)) {
                    echo '<input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="" value="0">';
                } else {
                    echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0">';
                }
                ?> Timelapse</div>
        </div>
        <div style="float: left;">
            <div><?php
                if (isset($_GET['r'])) {
                    ?><div style="display:inline-block; vertical-align:top;"><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On" name="" value="0">
                    </div>
                    <div style="display:inline-block; padding-left: 0.3em;">
                        <div>Refresh <span style="font-size: 0.7em">(<?php echo $tab; ?>)</span></div>
                    </div><?php
                } else {
                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0"> Refresh<?php
                }
            ?></div>
        </div>
    </div>
    <div style="float: left; vertical-align:top; height: 4.5em; padding: 1em 0.8em 0 0.3em;">
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;">Time now: <?php echo $time_now; ?></div>
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;">Last read: <?php echo $time_last; ?></div>
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;"><?php echo `uptime | grep -ohe 'load average[s:][: ].*' `; ?></div>
    </div>
    <?php
    // Display brief Temp sensor and PID data in header
    for ($i = 1; $i <= $sensor_t_num; $i++) {
        if ($sensor_t_activated[$i] == 1) { ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'T' , $i , ': ' , $sensor_t_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php
                            echo 'Now<br><span title="' , number_format((float)$t_temp_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$t_temp_c[$i], 1, '.', '') , '&deg;C</span>';
                        ?></td>
                        <td style="font-size: 0.8em;"><?php
                            echo 'Set<br><span title="' , number_format((float)$settemp_t_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$pid_t_temp_set[$i], 1, '.', '') , '&deg;C</span>';
                        ?></td>
                    </tr>
                </table>
            </div><?php
        }
    }
    // Display brief Temp/Hum sensor and PID data in header
    for ($i = 1; $i <= $sensor_ht_num; $i++) {
        if ($sensor_ht_activated[$i] == 1) { ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'HT' , $i , ': ' , $sensor_ht_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php
                            echo 'Now<br><span title="' , number_format((float)$ht_temp_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$ht_temp_c[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , number_format((float)$hum[$i], 1, '.', '') , '%';
                        ?></td>
                        <td style="font-size: 0.8em;"><?php
                            echo 'Set<br><span title="' , number_format((float)$settemp_ht_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$pid_ht_temp_set[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , number_format((float)$pid_ht_hum_set[$i], 1, '.', '') , '%';
                        ?></td>
                    </tr>
                </table>
            </div><?php
        }
    }
    // Display brief CO2 sensor and PID data in header
    for ($i = 1; $i <= $sensor_co2_num; $i++) {
        if ($sensor_co2_activated[$i] == 1) {
            ?><div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'CO<sub>2</sub>' , $i , ': ' , $sensor_co2_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php echo 'Now<br>' , $co2[$i]; ?></td>
                        <td style="font-size: 0.8em;"><?php echo 'Set<br>' , $pid_co2_set[$i]; ?></td>
                    </tr>
                </table>
            </div><?php
        }
    }
    ?>
</div>
<!-- End Header -->
<!-- Begin Tab Navigation -->
<div style="clear: both; padding-top: 15px;"></div>
    <nav>
        <ul class="cd-tabs-navigation">
            <li><a data-content="graph" <?php
                if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'graph')) {
                    echo 'class="selected"';
                } ?> href="#0">Graph</a></li>
            <li><a data-content="sensor" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'sensor') {
                    echo 'class="selected"';
                } ?> href="#0">Sensor</a></li>
            <li><a data-content="custom" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'custom') {
                    echo 'class="selected"';
                } ?> href="#0">Custom</a></li>
            <li><a data-content="camera" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'camera') {
                    echo 'class="selected"';
                } ?> href="#0">Camera</a></li>
            <li><a data-content="data" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'data') {
                    echo 'class="selected"';
                } ?> href="#0">Data</a></li>
            <li><a data-content="settings" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'settings') {
                    echo 'class="selected"';
                } ?> href="#0">Settings</a></li>
        </ul>
    </nav>
    <ul class="cd-tabs-content">
        <li data-content="graph" <?php
            if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'graph')) {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($graph_error)) {
                echo '<div style="color: red;">' . $graph_error . '</div>';
            }
            ?>

            <form action="?tab=graph<?php
            if (isset($_GET['page'])) {
                echo '&page=' , $_GET['page'];
            }
            if (isset($_GET['Refresh']) || isset($_POST['Refresh'])) {
                echo '&Refresh=1';
            }
            if (isset($_GET['r'])) {
                echo '&r=' , $_GET['r'];
            } ?>" method="POST">
            <div>
                <div style="padding-top: 0.5em;">
                    <div style="float: left; padding: 0 1.5em 1em 0.5em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">Auto Refresh</div>
                        <div style="text-align: center;"><?php
                            if (isset($_GET['r']) && $_GET['r'] == 1) {
                                if (empty($page)) {
                                    echo '<a href="?tab=graph">OFF</a> | <span class="on">ON</span>';
                                } else {
                                    echo '<a href="?tab=graph&page=' , $page , '">OFF</a> | <span class="on">ON</span>';
                                }
                            } else {
                                if (empty($page)) {
                                    echo '<span class="off">OFF</span> | <a href="?tab=graph&Refresh=1&r=1">ON</a>';
                                } else {
                                    echo '<span class="off">OFF</span> | <a href="?tab=graph&page=' , $page , '&Refresh=1&r=1">ON</a>';
                                }
                            }
                        ?>
                        </div>
                    </div>
                    <div style="float: left; padding: 0 2em 1em 0.5em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">Refresh</div>
                        <div>
                            <div style="float: left; padding-right: 0.1em;">
                                <input type="button" onclick='location.href="?tab=graph<?php
                                if (isset($_GET['page'])) {
                                    if ($_GET['page']) {
                                        echo '&page=' , $page;
                                    }
                                }
                                if (isset($_GET['r'])) {
                                    if ($_GET['r'] == 1) {
                                        echo '&r=1';
                                    }
                                } ?>"' value="Page">
                            </div>
                            <div style="float: left;">
                                <input type="submit" name="WriteSensorLog" value="Sensors" title="Reread all sensors and write logs">
                            </div>
                        </div>
                    </div>
                    <div style="float: left; padding: 0.2em 0 1em 0.5em">
                        <div style="float: left; padding-right: 0.5em;">
                            <table>
                                <tr>
                                    <td>
                                        <input type="radio" name="graph_type" value="separate" <?php
                                        if ($graph_time_span != 'default' && $graph_type == 'separate') {
                                            echo 'checked'; 
                                        }
                                        ?>>
                                    </td>
                                    <td>
                                        Separate
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <input type="radio" name="graph_type" value="combined" <?php 
                                        if ($graph_time_span != 'default' && $graph_type == 'combined') {
                                            echo 'checked'; 
                                        }
                                        ?>>
                                    </td>
                                    <td>
                                        Combined
                                    </td>
                                </tr>
                            </table>
                        </div>
                        <div style="float: left; padding-right: 0.5em;">
                            Time Span
                            <br>
                            <select name="graph_time_span">
                                <option value="default" <?php if ($graph_time_span == 'default') echo 'selected="selected"'; ?>>Day/Week</option>
                                <option value="1h" <?php if ($graph_time_span == '1h') echo 'selected="selected"'; ?>>1 Hour</option>
                                <option value="6h" <?php if ($graph_time_span == '6h') echo 'selected="selected"'; ?>>6 Hours</option>
                                <option value="1d" <?php if ($graph_time_span == '1d') echo 'selected="selected"'; ?>>1 Day</option>
                                <option value="3d" <?php if ($graph_time_span == '3d') echo 'selected="selected"'; ?>>3 Days</option>
                                <option value="1w" <?php if ($graph_time_span == '1w') echo 'selected="selected"'; ?>>1 Week</option>
                                <option value="1m" <?php if ($graph_time_span == '1m') echo 'selected="selected"'; ?>>1 Month</option>
                                <option value="3m" <?php if ($graph_time_span == '3m') echo 'selected="selected"'; ?>>3 Months</option>
                            </select>
                        </div>
                        <div style="float: left; padding-top: 0.9em;">
                            <input type="submit" name="Graph" value="Generate Graph">
                        </div>
                    </div>
                </div>

                <div style="clear: both;"></div>

                <div>
                    <?php
                    // Generate and display Main tab graphs
                    generate_graphs($mycodo_client, $graph_id, $graph_type, $graph_time_span, $sensor_t_num, $sensor_t_graph, $sensor_ht_num, $sensor_ht_graph, $sensor_co2_num, $sensor_co2_graph);

                    // If any graphs are to be displayed, show links to the legends
                    if (array_sum($sensor_t_graph) + array_sum($sensor_ht_graph) + array_sum($sensor_co2_graph)) { ?>
                        <div style="width: 100%; padding: 1em 0 0 0; text-align: center;">
                            <div style="text-align: center; padding-top: 0.5em;">
                                <a href="https://github.com/kizniche/Mycodo" target="_blank">Mycodo on GitHub</a>
                            </div>
                        </div>
                    <?php
                    } else { ?>
                        <div style="width: 100%; padding: 2em 0 0 0; text-align: center;">
                            There are currently 0 sensors activated for graphing.
                            <br>Sensors can be activated for logging and graphing from the Sensor tab.
                        </div>
                    <?php
                    }
                    ?>
            </div>
            </div>
            </form>

        </li>

        <li data-content="sensor" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'sensor') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($sensor_error)) {
                echo '<div style="color: red;">' . $sensor_error . '</div>';
            }
            ?>

            <form action="?tab=sensor<?php
                if (isset($_GET['page'])) {
                    echo '&page=' , $_GET['page'];
                }
                if (isset($_GET['r'])) {
                    echo '&r=' , $_GET['r'];
                }
                ?>" method="POST">
            <div style="padding-top: 0.5em;">
                <?php
                    if ($relay_num == 0) {
                        echo '<div style="color: red; padding: 0.5em 0 1em 0.5em; font-size: 0.9em;">Attention: There are 0 Relays configured. Change this in the Settings before activating a PID.</div>';
                    }
                ?>
                <div style="float: left; padding: 0 1.5em 1em 0.5em;">
                    <div style="text-align: center; padding-bottom: 0.2em;">Auto Refresh</div>
                    <div style="text-align: center;"><?php
                        if (isset($_GET['r'])) {
                            if ($_GET['r'] == 1) {
                                echo '<a href="?tab=sensor">OFF</a> | <span class="on">ON</span>';
                            } else {
                                echo '<span class="off">OFF</span> | <a href="?tab=sensor&?r=1">ON</a>';
                            }
                        } else {
                            echo '<span class="off">OFF</span> | <a href="?tab=sensor&r=1">ON</a>';
                        }
                    ?>
                    </div>
                </div>
                <div style="float: left; padding: 0 2em 1em 0.5em;">
                    <div style="text-align: center; padding-bottom: 0.2em;">Refresh</div>
                    <div>
                        <div style="float: left; padding-right: 0.1em;">
                            <input type="submit" name="Refresh" value="Page" title="Refresh page">
                        </div>
                        <div style="float: left;">
                            <input type="submit" name="WriteSensorLog" value="Sensors" title="Reread all sensors and write logs">
                        </div>
                    </div>
                </div>

                <div style="float: left; margin: 0 0.5em; padding: 1.2em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoTSensors" value="Set">
                        <select name="numtsensors">
                            <option value="0"<?php
                                if ($sensor_t_num == 0) {
                                    echo ' selected="selected"';
                                } ?>>0</option>
                            <option value="1"<?php
                                if ($sensor_t_num == 1) {
                                    echo ' selected="selected"';
                                } ?>>1</option>
                            <option value="2"<?php
                                if ($sensor_t_num == 2) {
                                    echo ' selected="selected"';
                                } ?>>2</option>
                            <option value="3"<?php
                                if ($sensor_t_num == 3) {
                                    echo ' selected="selected"';
                                } ?>>3</option>
                            <option value="4"<?php
                                if ($sensor_t_num == 4) {
                                    echo ' selected="selected"';
                                } ?>>4</option>
                        </select>
                    </div>
                    <div class="config-title">T Sensors</div>
                    <div style="clear: both;"></div>
                </div>

                <div style="float: left; margin: 0 0.5em; padding: 1.2em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoHTSensors" value="Set">
                        <select name="numhtsensors">
                            <option value="0"<?php
                                if ($sensor_ht_num == 0) {
                                    echo ' selected="selected"';
                                } ?>>0</option>
                            <option value="1"<?php
                                if ($sensor_ht_num == 1) {
                                    echo ' selected="selected"';
                                } ?>>1</option>
                            <option value="2"<?php
                                if ($sensor_ht_num == 2) {
                                    echo ' selected="selected"';
                                } ?>>2</option>
                            <option value="3"<?php
                                if ($sensor_ht_num == 3) {
                                    echo ' selected="selected"';
                                } ?>>3</option>
                            <option value="4"<?php
                                if ($sensor_ht_num == 4) {
                                    echo ' selected="selected"';
                                } ?>>4</option>
                        </select>
                    </div>
                    <div class="config-title">HT Sensors</div>
                    <div style="clear: both;"></div>
                </div>

                <div style="float: left; margin: 0 0.5em; padding: 1.2em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoCo2Sensors" value="Set">
                        <select name="numco2sensors">
                            <option value="0"<?php
                                if ($sensor_co2_num == 0) {
                                    echo ' selected="selected"';
                                } ?>>0</option>
                            <option value="1"<?php
                                if ($sensor_co2_num == 1) {
                                    echo ' selected="selected"';
                                } ?>>1</option>
                        </select>
                    </div>
                    <div class="config-title">CO<sub>2</sub> Sensors</div>
                    <div style="clear: both;"></div>
                </div>

            </div>

            <div style="clear: both;"></div>

            <?php
            if ($relay_num != 0) { ?>
                <div style="padding: 0.5em 0 0.5em 3em;">
                <div style="padding: 0.5em 0 0.5em 0;">Relays</div>
                <div style="padding-left: 0.2em;">
                <table class="relay-display">
                    <tr>
                        <td style="padding-bottom: 0.3em;">No.</td>
                        <td>Name</td>
                        <td>Pin</td>
                        <td>Signal On</td>
                        <td>Current State</td>
                    </tr>
                <?php
                $results = $db->query('SELECT Id, Name, Pin, Trigger FROM Relays');
                for ($i = 1; $i <= $relay_num; $i++) {
                    $read = "$gpio_path -g read $relay_pin[$i]";
                    $row = $results->fetchArray();
                    echo '<tr><td>' , $row[0] , '</td><td>' , $row[1] , '</td><td>' , $row[2] , '</td><td>' , $row[3] , '</td><td>';
                    if ((shell_exec($read) == 1 && $relay_trigger[$i] == 0) || (shell_exec($read) == 0 && $relay_trigger[$i] == 1)) {
                        echo '<span style="color: red;">Off</span>';
                    } else {
                        echo '<span style="color: green;">On</span>';
                    }
                    echo '</td></tr>';
                }
                echo '</table></div></div><div style="clear: both;"></div>';
            }
            ?>
           

            <div style="width: 54em; padding-left: 1.5em; padding-top: 2em;">
                
                <?php if ($sensor_t_num > 0) { ?>
                <div class="sensor-title">Temperature Sensors</div>
                <div style="padding-bottom: 1.5em;">
                    <?php
                    for ($i = 1; $i <= $sensor_t_num; $i++) {
                    ?>
                    <div style="width: 54em; border: 0.7em solid #EBEBEB; border-top: 0;">
                        <table class="pid" style="width: 100%;">
                        <tr class="shade">
                            <td>Sensor<br>No.</td>
                            <td>Sensor<br>Name</td>
                            <td>Sensor<br>Device</td>
                            <?php 
                            if ($sensor_t_device[$i] == 'DS18B20') {
                                echo '<td align=center>Serial No<br>28-xxx</td>';
                            } else {
                                echo '<td align=center>GPIO<br>Pin</td>';
                            }
                            ?>
                            <td>Log Interval<br>(seconds)</td>
                            <td>Activate<br>Logging</td>
                            <td>Activate<br>Graphing</td>
                            <td rowspan="2" style="padding: 0 2em;">
                                <input style="height: 2.5em;" type="submit" name="Change<?php echo $i; ?>TSensor" value="Save">
                            </td>
                        </tr>
                        <tr class="shade" style="height: 2.5em;">
                            <td class="shade" style="vertical-align: middle;" align=center>
                                <?php echo $i; ?>
                            </td>
                            <td>
                                <input style="width: <?php if ($sensor_t_device[$i] == 'DS18B20') echo '6em'; else echo '10em'; ?>;" type="text" value="<?php echo $sensor_t_name[$i]; ?>" maxlength=12 size=10 name="sensort<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 6.5em;" name="sensort<?php echo $i; ?>device">
                                    <option<?php
                                        if ($sensor_t_device[$i] == 'DS18B20') {
                                            echo ' selected="selected"';
                                        } ?> value="DS18B20">DS18B20</option>
                                    <option<?php
                                        if ($sensor_t_device[$i] == 'Other') {
                                            echo ' selected="selected"';
                                        } ?> value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <?php 
                                if ($sensor_t_device[$i] == 'DS18B20') {
                                    echo '<input style="width: 7em;" type="text" value="' , $sensor_t_pin[$i] . '" maxlength=12 name="sensort' , $i , 'pin" title="This is the serial number found at /sys/bus/w1/devices/28-x where x is the serial number of your connected DS18B20."/>';
                                } else {
                                    echo '<input style="width: 3em;" type="number" min="0" max="40" value="' , $sensor_t_pin[$i] , '" maxlength=2 name="sensort' , $i , 'pin" title="This is the GPIO pin connected to the temperature sensor"/>';
                                }
                                ?>
                                
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_t_period[$i]; ?>" name="sensort<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
                            </td>
                            <td>
                                <input type="checkbox" name="sensort<?php echo $i; ?>activated" value="1" <?php if ($sensor_t_activated[$i] == 1) echo 'checked'; ?>>
                            </td>
                            <td>
                                <input type="checkbox" name="sensort<?php echo $i; ?>graph" value="1" <?php if ($sensor_t_graph[$i] == 1) echo 'checked'; ?>>
                            </td>
                        </tr>
                    </table>

                    <table class="pid" style="width: 100%; margin-top: 0.1em;">
                        <tr class="shade">
                            <td style="text-align: left;">Regulation</td>
                            <td>Current<br>State</td>
                            <td>PID<br>Set Point</td>
                            <td>PID<br>Regulate</td>
                            <td>PID<br>Buffer</td>
                            <td>Interval<br>(seconds)</td>
                            <td>Relay<br>No.</td>
                            <td>P</td>
                            <td>I</td>
                            <td>D</td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td rowspan=2 style="text-align: left;">Temperature</td>
                            <td rowspan=2 class="onoff">
                                <?php
                                if ($pid_t_temp_or[$i] == 1) {
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="ChangeT<?php echo $i; ?>TempOR" value="0"> | <button style="width: 3em;" type="submit" name="ChangeT<?php echo $i; ?>TempOR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="ChangeT<?php echo $i; ?>TempOR" value="1"> | <button style="width: 3em;" type="submit" name="ChangeT<?php echo $i; ?>TempOR" value="1">OFF</button>
                                <?php
                                }
                                ?>
                            </td>
                            <td rowspan=2>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_set[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>TempSet" title="This is the desired temperature in °C."/> °C
                            </td>
                            <td rowspan=2>
                                <select style="width: 5em;" name="SetT<?php echo $i; ?>TempSetDir" title="Which direction should the PID regulate. 'Up' will ensure the temperature is regulated above a certain temperature. 'Down' will ensure the temperature is regulates below a certain point. 'Both' will ensure the temperature is regulated both up and down to maintain a specific temperature."/>
                                    <option value="0"<?php
                                        if ($pid_t_temp_set_dir[$i] == 0) {
                                            echo ' selected="selected"';
                                        } ?>>Both</option>
                                    <option value="1"<?php
                                        if ($pid_t_temp_set_dir[$i] == 1) {
                                            echo ' selected="selected"';
                                        } ?>>Up</option>
                                    <option value="-1"<?php
                                        if ($pid_t_temp_set_dir[$i] == -1) {
                                            echo ' selected="selected"';
                                        } ?>>Down</option>
                                </select>
                            </td>
                            <td rowspan=2>
                                <input style="width: 3em;" type="number" step="any" value="<?php echo $pid_t_temp_set_buf[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>TempSetBuf" title="This is the zone surounding the Set Point that the PID controller will not activate relays (i.e. regulation is paused). For example, if the Set Point is 30°C and the Buffer is 3°C, the Relay High will only activate once the temperature rises above 33°C to lower the temperature and the Relay Low will only activate once the temperature falls below 27°C."/> °C
                            </td>
                            <td rowspan=2>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_t_temp_period[$i]; ?>" name="SetT<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/>
                            </td>
                            <td>
                                ▼ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_t_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature. When the measured temperature reaches the upper set buffer (Upper Buffer = Set Point + Buffer) then the PID controller will modulate this relay until the temperature falls below it."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_p_high[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_P_High" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_i_high[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_I_High" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_d_high[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_D_High" title="This is the Derivative value of the PID"/>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                ▲ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_t_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature. When the measured temperature reaches the lower set buffer (Lower Buffer = Set Point - Buffer) then the PID controller will modulate this relay until the temperature rises above it."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_p_low[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_P_Low" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_i_low[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_I_Low" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_d_low[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_D_low" title="This is the Derivative value of the PID"/>
                            </td>
                        </tr>
                    </table>
                    </div>
                    <div style="padding-bottom: <?php if ($i == $sensor_t_num) echo '2'; else echo '1'; ?>em;">
                    <?php
                    }
                    ?>
                </div>
                <?php
                }
                ?>

                <?php if ($sensor_ht_num > 0) { ?>
                <div class="sensor-title">Humidity/Temperature Sensors</div>
                <div style="margin-bottom: 1.5em;">
                    <?php
                    for ($i = 1; $i <= $sensor_ht_num; $i++) {
                    ?>
                    <div style="width: 54em; border: 0.7em solid #EBEBEB; border-top: 0;">
                        <table class="pid" style="width: 100%;">
                            <tr class="shade">
                                <td>Sensor<br>No.</td>
                                <td>Sensor<br>Name</td>
                                <td>Sensor<br>Device</td>
                                <td>GPIO<br>Pin</td>
                                <td>Log Interval<br>(seconds)</td>
                                <td>Activate<br>Logging</td>
                                <td>Activate<br>Graphing</td>
                                <td rowspan=2 style="padding: 0 1.5em;">
                                    <input style="height: 2.5em;" type="submit" name="Change<?php echo $i; ?>HTSensor" value="Save">
                                </td>
                            </tr>
                            <tr class="shade" style="height: 2.5em;">
                                <td class="shade" style="vertical-align: middle;">
                                    <?php echo $i; ?>
                                </td>
                                <td>
                                    <input style="width: 10em;" type="text" value="<?php echo $sensor_ht_name[$i]; ?>" maxlength=12 size=10 name="sensorht<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                                </td>
                                <td>
                                    <select style="width: 6.5em;" name="sensorht<?php echo $i; ?>device">
                                        <option<?php
                                            if ($sensor_ht_device[$i] == 'DHT11') {
                                                echo ' selected="selected"';
                                            } ?> value="DHT11">DHT11</option>
                                        <option<?php
                                            if ($sensor_ht_device[$i] == 'DHT22') {
                                                echo ' selected="selected"';
                                            } ?> value="DHT22">DHT22</option>
                                        <option<?php
                                            if ($sensor_ht_device[$i] == 'AM2302') {
                                                echo ' selected="selected"';
                                            } ?> value="AM2302">AM2302</option>
                                        <option<?php
                                            if ($sensor_ht_device[$i] == 'Other') {
                                                echo ' selected="selected"';
                                            } ?> value="Other">Other</option>
                                    </select>
                                </td>
                                <td>
                                    <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_ht_pin[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>pin" title="This is the GPIO pin connected to the DHT sensor"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_ht_period[$i]; ?>" name="sensorht<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
                                </td>
                                <td>
                                    <input type="checkbox" name="sensorht<?php echo $i; ?>activated" value="1" <?php if ($sensor_ht_activated[$i] == 1) echo 'checked'; ?>>
                                </td>
                                <td>
                                    <input type="checkbox" name="sensorht<?php echo $i; ?>graph" value="1" <?php if ($sensor_ht_graph[$i] == 1) echo 'checked'; ?>>
                                </td>
                            </tr>
                        </table>

                        <table class="pid" style="width: 100%; margin-top: 0.1em;">
                            <tr class="shade">
                                <td style="text-align: left;">Regulation</td>
                                <td>Current<br>State</td>
                                <td>PID<br>Set Point</td>
                                <td>PID<br>Regulate</td>
                                <td>PID<br>Buffer</td>
                                <td>Interval<br>(seconds)</td>
                                <td>Relay<br>No.</td>
                                <td>P</td>
                                <td>I</td>
                                <td>D</td>
                            </tr>
                            <tr style="height: 2.5em;">
                                <td rowspan=2 style="text-align: left;">Temperature</td>
                                <td rowspan=2 class="onoff">
                                    <?php
                                    if ($pid_ht_temp_or[$i] == 1) {
                                        ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="ChangeHT<?php echo $i; ?>TempOR" value="0"> | <button style="width: 3em;" type="submit" name="ChangeHT<?php echo $i; ?>TempOR" value="0">ON</button>
                                        <?php
                                    } else {
                                        ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="ChangeHT<?php echo $i; ?>TempOR" value="1"> | <button style="width: 3em;" type="submit" name="ChangeHT<?php echo $i; ?>TempOR" value="1">OFF</button>
                                    <?php
                                    }
                                    ?>
                                </td>
                                <td rowspan=2>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_set[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>TempSet" title="This is the desired temperature in °C."/> °C
                                </td>
                                <td rowspan=2>
                                    <select style="width: 5em;" name="SetHT<?php echo $i; ?>TempSetDir" title="Which direction should the PID regulate. 'Up' will ensure the temperature is regulated above a certain temperature. 'Down' will ensure the temperature is regulates below a certain point. 'Both' will ensure the temperature is regulated both up and down to maintain a specific temperature."/>
                                        <option value="0"<?php
                                            if ($pid_ht_temp_set_dir[$i] == 0) {
                                                echo ' selected="selected"';
                                            } ?>>Both</option>
                                        <option value="1"<?php
                                            if ($pid_ht_temp_set_dir[$i] == 1) {
                                                echo ' selected="selected"';
                                            } ?>>Up</option>
                                        <option value="-1"<?php
                                            if ($pid_ht_temp_set_dir[$i] == -1) {
                                                echo ' selected="selected"';
                                            } ?>>Down</option>
                                    </select>
                                </td>
                                <td rowspan=2>
                                    <input style="width: 3em;" type="number" step="any" value="<?php echo $pid_ht_temp_set_buf[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>TempSetBuf" title="This is the zone surounding the Set Point that the PID controller will not activate relays (i.e. regulation is paused). For example, if the Set Point is 30°C and the Buffer is 3°C, the Relay High will only activate once the temperature rises above 33°C, to lower the temperature, and the Relay Low will only activate once the temperature falls below 27°C, to increase the temperature."/> °C
                                </td>
                                <td rowspan=2>
                                    <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_ht_temp_period[$i]; ?>" name="SetHT<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/>
                                </td>

                                <td>
                                    ▼ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_ht_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature. When the measured temperature reaches the upper set buffer (Upper Buffer = Set Point + Buffer) then the PID controller will modulate this relay until the temperature falls below it."/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_p_high[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_P_High" title="This is the Proportional value of the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_i_high[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_I_High" title="This is the Integral value of the the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_d_high[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_D_High" title="This is the Derivative value of the PID"/>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    ▲ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_ht_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature. When the measured temperature reaches the lower set buffer (Lower Buffer = Set Point - Buffer) then the PID controller will modulate this relay until the temperature rises above it."/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_p_low[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_P_Low" title="This is the Proportional value of the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_i_low[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_I_Low" title="This is the Integral value of the the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_d_low[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_D_Low" title="This is the Derivative value of the PID"/>
                                </td>
                                
                            </tr>
                            <tr style="height: 2.5em;">
                                <td rowspan=2 style="text-align: left;">Humidity</td>
                                <td rowspan=2 class="onoff">
                                    <?php
                                    if ($pid_ht_hum_or[$i] == 1) {
                                        ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="ChangeHT<?php echo $i; ?>HumOR" value="0"> | <button style="width: 3em;" type="submit" name="ChangeHT<?php echo $i; ?>HumOR" value="0">ON</button>
                                        <?php
                                    } else {
                                        ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="ChangeHT<?php echo $i; ?>HumOR" value="1"> | <button style="width: 3em;" type="submit" name="ChangeHT<?php echo $i; ?>HumOR" value="1">OFF</button>
                                    <?php
                                    }
                                    ?>
                                </td>
                                <td rowspan=2>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_set[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>HumSet" title="This is the desired relative humidity in percent."/> %
                                </td>
                                <td rowspan=2>
                                    <select style="width: 5em;" name="SetHT<?php echo $i; ?>HumSetDir" title="Which direction should the PID regulate. 'Up' will ensure the humidity is regulated above a certain humidity. 'Down' will ensure the humidity is regulates below a certain point. 'Both' will ensure the humidity is regulated both up and down to maintain a specific humidity."/>
                                        <option value="0"<?php
                                            if ($pid_ht_hum_set_dir[$i] == 0) {
                                                echo ' selected="selected"';
                                            } ?>>Both</option>
                                        <option value="1"<?php
                                            if ($pid_ht_hum_set_dir[$i] == 1) {
                                                echo ' selected="selected"';
                                            } ?>>Up</option>
                                        <option value="-1"<?php
                                            if ($pid_ht_hum_set_dir[$i] == -1) {
                                                echo ' selected="selected"';
                                            } ?>>Down</option>
                                    </select>
                                </td>
                                <td rowspan=2>
                                    <input style="width: 3em;" type="number" step="any" value="<?php echo $pid_ht_hum_set_buf[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>HumSetBuf" title="This is the zone surounding the Set Point that the PID controller will not activate relays (i.e. regulation is paused). For example, if the Set Point is 60% and the Buffer is 5%, the Relay High will only activate once the humidity rises above 65%, to lower the humidity, and the Relay Low will only activate once the humidity falls below 55%, to raise the humidity."/> %
                                </td>
                                <td rowspan=2>
                                    <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_ht_hum_period[$i]; ?>" name="SetHT<?php echo $i; ?>HumPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another humidity reading and applying the PID"/>
                                </td>
                                <td>
                                    ▼ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_ht_hum_relay_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumRelayHigh" title="This relay is used to decrease humidity. When the measured humidity reaches the upper set buffer (Upper Buffer = Set Point + Buffer) then the PID controller will modulate this relay until the humidity falls below it."/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_p_high[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_P_High" title="This is the Proportional value of the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_i_high[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_I_High" title="This is the Integral value of the the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_d_high[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_D_High" title="This is the Derivative value of the PID"/>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    ▲ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_ht_hum_relay_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumRelayLow" title="This relay is used to increase humidity. When the measured humidity reaches the lower set buffer (Lower Buffer = Set Point - Buffer) then the PID controller will modulate this relay until the humidity rises above it."/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_p_low[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_P_Low" title="This is the Proportional value of the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_i_low[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_I_Low" title="This is the Integral value of the the PID"/>
                                </td>
                                <td>
                                    <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_d_low[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_D_Low" title="This is the Derivative value of the PID"/>
                                </td>
                            </tr>
                        </table>
                    </div>
                    <div style="margin-bottom: <?php if ($i == $sensor_ht_num) echo '2'; else echo '1'; ?>em;"></div>
                    <?php
                    }
                    ?>
                </div>
                <?php
                }
                ?>

                <?php if ($sensor_co2_num > 0) { ?>
                <div class="sensor-title">CO<sub>2</sub> Sensors</div>
                <div>
                    <?php
                    for ($i = 1; $i <= $sensor_co2_num; $i++) {
                    ?>
                    <div style="width: 54em; border: 0.7em solid #EBEBEB; border-top: 0;">
                    <table class="pid" style="width: 100%;">
                        <tr class="shade">
                            <td>Sensor<br>No.</td>
                            <td>Sensor<br>Name</td>
                            <td>Sensor<br>Device</td>
                            <td>GPIO<br>Pin</td>
                            <td>Log Interval<br>(seconds)</td>
                            <td>Activate<br>Logging</td>
                            <td>Activate<br>Graphing</td>
                            <td rowspan="2" style="padding: 0 2em;">
                                <input style="height: 2.5em;" type="submit" name="Change<?php echo $i; ?>Co2Sensor" value="Save">
                            </td>
                        </tr>
                        <tr class="shade" style="height: 2.5em;">
                            <td align=center class="shade" style="vertical-align: middle;">
                                <?php echo $i; ?>
                            </td>
                            <td>
                                <input style="width: 7em;" type="text" value="<?php echo $sensor_co2_name[$i]; ?>" maxlength=12 size=10 name="sensorco2<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 6.5em;" name="sensorco2<?php echo $i; ?>device">
                                    <option<?php
                                        if ($sensor_co2_device[$i] == 'K30') {
                                            echo ' selected="selected"';
                                        } ?> value="K30">K30</option>
                                    <option<?php
                                        if ($sensor_co2_device[$i] == 'Other') {
                                            echo ' selected="selected"';
                                        } ?> value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <?php
                                if ($sensor_co2_device[$i] == 'K30') {
                                ?>
                                    Tx/Rx
                                <?php
                                } else {
                                ?>
                                    <input type="number" value="<?php echo $sensor_co2_pin[$i]; ?>" maxlength=2 size=1 name="sensorco2<?php echo $i; ?>pin" title="This is the GPIO pin connected to the CO2 sensor"/>
                                <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_co2_period[$i]; ?>" name="sensorco2<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
                            </td>
                            <td>
                                <input type="checkbox" name="sensorco2<?php echo $i; ?>activated" value="1" <?php if ($sensor_co2_activated[$i] == 1) echo 'checked'; ?>>
                            </td>
                            <td>
                                <input type="checkbox" name="sensorco2<?php echo $i; ?>graph" value="1" <?php if ($sensor_co2_graph[$i] == 1) echo 'checked'; ?>>
                            </td>
                        </tr>
                    </table>

                    <table class="pid" style="width: 100%; margin-top: 0.1em;">
                        <tr class="shade">
                            <td style="text-align: left;">Regulation</td>
                            <td>Current<br>State</td>
                            <td>PID<br>Set Point</td>
                            <td>PID<br>Regulate</td>
                            <td>PID<br>Buffer</td>
                            <td>Interval<br>(seconds)</td>
                            <td>Relay<br>No.</td>
                            <td>P</td>
                            <td>I</td>
                            <td>D</td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td rowspan=2 style="text-align: left;">CO<sub>2</sub></td>
                            <td rowspan=2 class="onoff">
                                <?php
                                if ($pid_co2_or[$i] == 1) {
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>Co2OR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>Co2OR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>Co2OR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>Co2OR" value="1">OFF</button>
                                    <?php
                                }
                                ?>
                            </td>
                            <td rowspan=2>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_set[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>Co2Set" title="This is the desired CO2 concentration in ppm."/> ppm
                            </td>
                            <td rowspan=2>
                                <select style="width: 5em;" name="Set<?php echo $i; ?>CO2SetDir" title="Which direction should the PID regulate. 'Up' will ensure the CO2 is regulated above a certain CO2. 'Down' will ensure the CO2 is regulates below a certain point. 'Both' will ensure the CO2 is regulated both up and down to maintain a specific CO2."/>
                                    <option value="0"<?php
                                        if ($pid_co2_set_dir[$i] == 0) {
                                            echo ' selected="selected"';
                                        } ?>>Both</option>
                                    <option value="1"<?php
                                        if ($pid_co2_set_dir[$i] == 1) {
                                            echo ' selected="selected"';
                                        } ?>>Up</option>
                                    <option value="-1"<?php
                                        if ($pid_co2_set_dir[$i] == -1) {
                                            echo ' selected="selected"';
                                        } ?>>Down</option>
                                </select>
                            </td>
                            <td rowspan=2>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_set_buf[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>Co2SetBuf" title="This is the zone surounding the Set Point that the PID controller will not activate relays (i.e. regulation is paused). For example, if the Set Point is 2000 ppm and the Buffer is 250 ppm, the Relay High will only activate once the CO2 rises above 2250 ppm, to lower the CO2, and the Relay Low will only activate once the CO2 falls below 1750, to increase the CO2."/> ppm
                            </td>
                            <td rowspan=2>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_co2_period[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2Period" title="This is the number of seconds to wait after the relay has been turned off before taking another CO2 reading and applying the PID"/>
                            </td>
                            <td>
                                ▼ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_co2_relay_high[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>Co2RelayHigh" title="This relay is used to decrease CO2. When the measured CO2 reaches the upper set buffer (Upper Buffer = Set Point + Buffer) then the PID controller will modulate this relay until the CO2 falls below it."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_p_high[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_P_High" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_i_high[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_I_High" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_d_high[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_D_High" title="This is the Derivative value of the PID"/>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                ▲ <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_co2_relay_low[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>Co2RelayLow" title="This relay is used to increase CO2. When the measured CO2 reaches the lower set buffer (Lower Buffer = Set Point - Buffer) then the PID controller will modulate this relay until the CO2 rises above it."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_p_low[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_P_Low" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_i_low[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_I_Low" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_d_low[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_D_Low" title="This is the Derivative value of the PID"/>
                            </td>
                        </tr>
                    </table>
                    </div>
                    <div style="margin-bottom: <?php if ($i == $sensor_ht_num) echo '2'; else echo '1'; ?>em;"></div>
                    <?php
                    }
                    ?>
                </div>
                <?php
                }
                ?>
            </div>
        </form>
        </li>

        <li data-content="custom" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'custom') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($custom_error)) {
                echo '<div style="color: red;">' . $custom_error . '</div>';
            }
            ?>

            <?php
            /* DateSelector*Author: Leon Atkinson */
            if (isset($_POST['SubmitDates']) and $_SESSION['user_name'] != 'guest') {
                
                concatenate_logs('all');

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

                    if ($_POST['custom_type'] == 'Combined') {

                        $cus_graph = '/var/tmp/plot-cus-combined.gnuplot';
                        $f = fopen($cus_graph, "w");

                        fwrite($f, "set terminal png size $graph_width,1600\n");
                        fwrite($f, "set xdata time\n");
                        fwrite($f, "set timefmt \"%Y %m %d %H %M %S\"\n");
                        fwrite($f, "set output \"$images/graph-custom-combined-$id2-0.png\"\n");
                        fwrite($f, "set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]\n");
                        fwrite($f, "set format x \"%H:%M\\n%m/%d\"\n");
                        fwrite($f, "set yrange [0:100]\n");
                        fwrite($f, "set y2range [0:35]\n");
                        fwrite($f, "set my2tics 10\n");
                        fwrite($f, "set ytics 10\n");
                        fwrite($f, "set y2tics 5\n");
                        fwrite($f, "set style line 11 lc rgb '#808080' lt 1\n");
                        fwrite($f, "set border 3 back ls 11\n");
                        fwrite($f, "set tics nomirror\n");
                        fwrite($f, "set style line 12 lc rgb '#808080' lt 0 lw 1\n");
                        fwrite($f, "set grid xtics ytics back ls 12\n");
                        fwrite($f, "set style line 1 lc rgb '#7164a3' pt 0 ps 1 lt 1 lw 2\n");
                        fwrite($f, "set style line 2 lc rgb '#599e86' pt 0 ps 1 lt 1 lw 2\n");
                        fwrite($f, "set style line 3 lc rgb '#c3ae4f' pt 0 ps 1 lt 1 lw 2\n");
                        fwrite($f, "set style line 4 lc rgb '#c3744f' pt 0 ps 1 lt 1 lw 2\n");
                        fwrite($f, "set style line 5 lc rgb '#91180B' pt 0 ps 1 lt 1 lw 1\n");
                        fwrite($f, "set style line 6 lc rgb '#582557' pt 0 ps 1 lt 1 lw 1\n");
                        fwrite($f, "set style line 7 lc rgb '#04834C' pt 0 ps 1 lt 1 lw 1\n");
                        fwrite($f, "set style line 8 lc rgb '#DC32E6' pt 0 ps 1 lt 1 lw 1\n");
                        fwrite($f, "set style line 9 lc rgb '#957EF9' pt 0 ps 1 lt 1 lw 1\n");
                        fwrite($f, "set style line 10 lc rgb '#CC8D9C' pt 0 ps 1 lt 1 lw 1\n");
                        fwrite($f, "set style line 11 lc rgb '#717412' pt 0 ps 1 lt 1 lw 1\n");
                        fwrite($f, "set style line 12 lc rgb '#0B479B' pt 0 ps 1 lt 1 lw 1\n");

                        fwrite($f, "set multiplot layout 4, 1 title \"Combined Sensor Data - $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"\n");

                        if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                        else fwrite($f, "unset key\n");
                        fwrite($f, "set title \"Combined Temperatures\"\n");
                        fwrite($f, "plot \"<awk '\\$10 == 1' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T1\" w lp ls 1 axes x1y2, ");
                        fwrite($f, "\"<awk '\\$10 == 2' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T2\" w lp ls 2 axes x1y2, ");
                        fwrite($f, "\"<awk '\\$10 == 3' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T3\" w lp ls 3 axes x1y2, ");
                        fwrite($f, "\"<awk '\\$10 == 4' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T4\" w lp ls 4 axes x1y2\n");

                        if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                        else fwrite($f, "unset key\n");
                        fwrite($f, "set title \"Combined Humidities\"\n");
                        fwrite($f, "plot \"<awk '\\$10 == 1' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH1\" w lp ls 1 axes x1y1, ");
                        fwrite($f, "\"<awk '\\$10 == 2' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH2\" w lp ls 2 axes x1y1, ");
                        fwrite($f, "\"<awk '\\$10 == 3' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH3\" w lp ls 3 axes x1y1, ");
                        fwrite($f, "\"<awk '\\$10 == 4' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH4\" w lp ls 4 axes x1y1\n");

                        if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                        else fwrite($f, "unset key\n");
                        fwrite($f, "set title \"Combined CO2s\"\n");
                        fwrite($f, "plot \"<awk '\\$15 == 1' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"CO21\" w lp ls 1 axes x1y1, ");
                        fwrite($f, "\"<awk '\\$15 == 2' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"CO22\" w lp ls 2 axes x1y1, ");
                        fwrite($f, "\"<awk '\\$15 == 3' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"CO23\" w lp ls 3 axes x1y1, ");
                        fwrite($f, "\"<awk '\\$15 == 4' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"CO24\" w lp ls 4 axes x1y1\n");

                        if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left top\n");
                        else fwrite($f, "unset key\n");
                        fwrite($f, "set title \"Relay Run Time\"\n");
                        fwrite($f, "plot \"$relay_log\" u 1:7 index 0 title \"$relay_name[1]\" w impulses ls 5 axes x1y1, ");
                        fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[2]\" w impulses ls 6 axes x1y1, ");
                        fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[3]\" w impulses ls 7 axes x1y1, ");
                        fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[4]\" w impulses ls 8 axes x1y1, ");
                        fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[5]\" w impulses ls 9 axes x1y1, ");
                        fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[6]\" w impulses ls 10 axes x1y1, ");
                        fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[7]\" w impulses ls 11 axes x1y1, ");
                        fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[8]\" w impulses ls 12 axes x1y1\n");
                        fwrite($f, "unset multiplot\n");

                        fclose($f);
                        $cmd = "gnuplot $cus_graph";
                        exec($cmd);
                        unlink($cus_graph);

                        echo '<div style="width: 100%; text-align: center; padding: 1em 0 3em 0;"><img src=image.php?';
                        echo 'graphtype=custom-combined';
                        echo '&id=' , $id2;
                        echo '&sensornumber=0>';
                        echo '</div>';
                    } else if ($_POST['custom_type'] == 'Separate') {
                        
                        for ($n = 1; $n <= $sensor_t_num; $n++) {
                            if ($sensor_t_graph[$n] == 1) {

                                $cus_graph = "/var/tmp/plot-cus-t-separate-$n.gnuplot";
                                $f = fopen($cus_graph, "w");

                                fwrite($f, "set terminal png size $graph_width,490\n");
                                fwrite($f, "set xdata time\n");
                                fwrite($f, "set timefmt \"%Y %m %d %H %M %S\"\n");
                                fwrite($f, "set output \"$images/graph-t-custom-separate-$id2-$n.png\"\n");
                                fwrite($f, "set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]\n");
                                fwrite($f, "set format x \"%H:%M\\n%m/%d\"\n");
                                fwrite($f, "set yrange [0:100]\n");
                                fwrite($f, "set y2range [0:35]\n");
                                fwrite($f, "set my2tics 10\n");
                                fwrite($f, "set ytics 10\n");
                                fwrite($f, "set y2tics 5\n");
                                fwrite($f, "set style line 11 lc rgb '#808080' lt 1\n");
                                fwrite($f, "set border 3 back ls 11\n");
                                fwrite($f, "set tics nomirror\n");
                                fwrite($f, "set style line 12 lc rgb '#808080' lt 0 lw 1\n");
                                fwrite($f, "set grid xtics ytics back ls 12\n");
                                fwrite($f, "set style line 1 lc rgb '#FF3100' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 2 lc rgb '#0772A1' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 3 lc rgb '#00B74A' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 4 lc rgb '#91180B' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 5 lc rgb '#582557' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 6 lc rgb '#04834C' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 7 lc rgb '#DC32E6' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 8 lc rgb '#957EF9' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 9 lc rgb '#CC8D9C' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 10 lc rgb '#717412' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 11 lc rgb '#0B479B' pt 0 ps 1 lt 1 lw 1\n");
                                if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                                else fwrite($f, "unset key\n");
                                fwrite($f, "set title \"Sensor $n: $sensor_t_name[$n]: $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"\n");
                                fwrite($f, "plot \"<awk '\\$10 == $n' /var/tmp/sensor-t.log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"T\" w lp ls 2 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, ");
                                fwrite($f, "\"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[1]\" w impulses ls 4 axes x1y1, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[2]\" w impulses ls 5 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[3]\" w impulses ls 6 axes x1y1, ");
                                fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[4]\" w impulses ls 7 axes x1y1, ");
                                fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[5]\" w impulses ls 8 axes x1y1, ");
                                fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[6]\" w impulses ls 9 axes x1y1, ");
                                fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[7]\" w impulses ls 10 axes x1y1, ");
                                fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[8]\" w impulses ls 11 axes x1y1");

                                fclose($f);
                                $cmd = "gnuplot $cus_graph";
                                exec($cmd);
                                unlink($cus_graph);

                                echo '<div style="width: 100%; text-align: center; padding: 1em 0 3em 0;"><img src=image.php?';
                                echo 'graphtype=custom-separate';
                                echo '&sensortype=t';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                            if ($n != $sensor_ht_num || ($n == $sensor_ht_num && array_sum($sensor_co2_graph))) { echo '<hr class="fade"/>'; }
                        }

                        for ($n = 1; $n <= $sensor_ht_num; $n++) {
                            if ($sensor_ht_graph[$n] == 1) {

                                $cus_graph = "/var/tmp/plot-cus-ht-separate-$n.gnuplot";
                                $f = fopen($cus_graph, "w");

                                fwrite($f, "set terminal png size $graph_width,490\n");
                                fwrite($f, "set xdata time\n");
                                fwrite($f, "set timefmt \"%Y %m %d %H %M %S\"\n");
                                fwrite($f, "set output \"$images/graph-ht-custom-separate-$id2-$n.png\"\n");
                                fwrite($f, "set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]\n");
                                fwrite($f, "set format x \"%H:%M\\n%m/%d\"\n");
                                fwrite($f, "set yrange [0:100]\n");
                                fwrite($f, "set y2range [0:35]\n");
                                fwrite($f, "set my2tics 10\n");
                                fwrite($f, "set ytics 10\n");
                                fwrite($f, "set y2tics 5\n");
                                fwrite($f, "set style line 11 lc rgb '#808080' lt 1\n");
                                fwrite($f, "set border 3 back ls 11\n");
                                fwrite($f, "set tics nomirror\n");
                                fwrite($f, "set style line 12 lc rgb '#808080' lt 0 lw 1\n");
                                fwrite($f, "set grid xtics ytics back ls 12\n");
                                fwrite($f, "set style line 1 lc rgb '#FF3100' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 2 lc rgb '#0772A1' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 3 lc rgb '#00B74A' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 4 lc rgb '#91180B' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 5 lc rgb '#582557' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 6 lc rgb '#04834C' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 7 lc rgb '#DC32E6' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 8 lc rgb '#957EF9' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 9 lc rgb '#CC8D9C' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 10 lc rgb '#717412' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 11 lc rgb '#0B479B' pt 0 ps 1 lt 1 lw 1\n");
                                if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                                else fwrite($f, "unset key\n");
                                fwrite($f, "set title \"Sensor $n: $sensor_ht_name[$n]: $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"\n");
                                fwrite($f, "plot \"<awk '\\$10 == $n' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"T\" w lp ls 2 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, ");
                                fwrite($f, "\"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[1]\" w impulses ls 4 axes x1y1, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[2]\" w impulses ls 5 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[3]\" w impulses ls 6 axes x1y1, ");
                                fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[4]\" w impulses ls 7 axes x1y1, ");
                                fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[5]\" w impulses ls 8 axes x1y1, ");
                                fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[6]\" w impulses ls 9 axes x1y1, ");
                                fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[7]\" w impulses ls 10 axes x1y1, ");
                                fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[8]\" w impulses ls 11 axes x1y1");

                                fclose($f);
                                $cmd = "gnuplot $cus_graph";
                                exec($cmd);
                                unlink($cus_graph);

                                echo '<div style="width: 100%; text-align: center; padding: 1em 0 3em 0;"><img src=image.php?';
                                echo 'graphtype=custom-separate';
                                echo '&sensortype=ht';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                            if ($n != $sensor_ht_num || ($n == $sensor_ht_num && array_sum($sensor_co2_graph))) { echo '<hr class="fade"/>'; }
                        }

                        for ($n = 1; $n <= $sensor_co2_num; $n++) {
                            if ($sensor_co2_graph[$n] == 1) {

                                $cus_graph = "/var/tmp/plot-cus-co2-separate-$n.gnuplot";
                                $f = fopen($cus_graph, "w");

                                fwrite($f, "set terminal png size $graph_width,490\n");
                                fwrite($f, "set xdata time\n");
                                fwrite($f, "set timefmt \"%Y %m %d %H %M %S\"\n");
                                fwrite($f, "set output \"$images/graph-co2-custom-separate-$id2-$n.png\"\n");
                                fwrite($f, "set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]\n");
                                fwrite($f, "set format x \"%H:%M\\n%m/%d\"\n");
                                fwrite($f, "set yrange [0:100]\n");
                                fwrite($f, "set y2range [0:35]\n");
                                fwrite($f, "set my2tics 10\n");
                                fwrite($f, "set ytics 10\n");
                                fwrite($f, "set y2tics 5\n");
                                fwrite($f, "set style line 11 lc rgb '#808080' lt 1\n");
                                fwrite($f, "set border 3 back ls 11\n");
                                fwrite($f, "set tics nomirror\n");
                                fwrite($f, "set style line 12 lc rgb '#808080' lt 0 lw 1\n");
                                fwrite($f, "set grid xtics ytics back ls 12\n");
                                fwrite($f, "set style line 1 lc rgb '#FF3100' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 2 lc rgb '#0772A1' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 3 lc rgb '#00B74A' pt 0 ps 1 lt 1 lw 2\n");
                                fwrite($f, "set style line 4 lc rgb '#91180B' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 5 lc rgb '#582557' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 6 lc rgb '#04834C' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 7 lc rgb '#DC32E6' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 8 lc rgb '#957EF9' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 9 lc rgb '#CC8D9C' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 10 lc rgb '#717412' pt 0 ps 1 lt 1 lw 1\n");
                                fwrite($f, "set style line 11 lc rgb '#0B479B' pt 0 ps 1 lt 1 lw 1\n");
                                if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                                else fwrite($f, "unset key\n");
                                fwrite($f, "set title \"Sensor $n: $sensor_co2_name[$n]: $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"\n");
                                fwrite($f, "plot \"<awk '\\$10 == $n' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, ");
                                fwrite($f, "\"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[1]\" w impulses ls 4 axes x1y1, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[2]\" w impulses ls 5 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[3]\" w impulses ls 6 axes x1y1, ");
                                fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[4]\" w impulses ls 7 axes x1y1, ");
                                fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[5]\" w impulses ls 8 axes x1y1, ");
                                fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[6]\" w impulses ls 9 axes x1y1, ");
                                fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[7]\" w impulses ls 10 axes x1y1, ");
                                fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[8]\" w impulses ls 11 axes x1y1\n");

                                fclose($f);
                                $cmd = "gnuplot $cus_graph";
                                exec($cmd);
                                unlink($cus_graph);

                                echo '<div style="width: 100%; text-align: center; padding: 1em 0 3em 0;"><img src=image.php?';
                                echo 'graphtype=custom-separate';
                                echo '&sensortype=co2';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                            if ($n != $sensor_co2_num) { echo '<hr class="fade"/>'; }
                        }
                    }
                }
            } else if (isset($_POST['SubmitDates']) and $_SESSION['user_name'] == 'guest') {
                displayform();
                echo '<div>Guest access has been revoked for graph generation.';
            } else displayform();
            ?>
        </li>

        <li data-content="camera" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'camera') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($camera_error)) {
                echo '<div style="color: red;">' . $camera_error . '</div>';
            }
            ?>

            <form action="?tab=camera" method="POST">
            <div style="float: left; padding: 0.5em;">
                <button name="CaptureStill" type="submit" value="">Capture Still</button>
            </div>

            <div style="clear: both;"></div>

            <div>
                <div style="float: left; padding: 0.5em;">
                    <?php
                    if (!file_exists($lock_timelapse)) {
                        echo '<button name="start-timelapse" type="submit" value="">Start</button>';
                    } else {
                        echo '<button name="stop-timelapse" type="submit" value="">Stop</button>';
                    }
                    ?>
                </div>
                <div style="float: left; font-weight: bold; padding: 0.8em 1em 0.5em 0;">
                    Timelapse <?php
                    if (!file_exists($lock_timelapse)) {
                        echo '(<span class="off">OFF</span>)';
                    } else {
                        echo '(<span class="on">ON</span>)';
                    }
                    ?>
                </div>
                <div style="float: left; padding: 0.65em 0.5em 0 0.5em;">
                    Duration: <input style="width: 4em;" type="number" value="60" max="99999" min="1" name="timelapse_duration"> min
                </div>
                <div style="float: left; padding: 0.65em 0.5em 0 0.5em;">
                   Run time: <input style="width: 4em;" type="number" value="600" max="99999" min="1" name="timelapse_runtime"> min
                </div>
            </div>

            <div style="clear: both;"></div>

            <div>
                <div style="float: left; padding: 0.5em;">
                    <?php
                    if (!file_exists($lock_mjpg_streamer)) {
                        echo '<button name="start-stream" type="submit" value="">Start</button>';
                    } else {
                        echo '<button name="stop-stream" type="submit" value="">Stop</button>';
                    }
                    ?>
                </div>
                <div style="float: left; font-weight: bold; padding: 0.8em 1em 0.5em 0;">
                    Video Stream <?php
                    if (!file_exists($lock_mjpg_streamer)) {
                        echo '(<span class="off">OFF</span>)';
                    } else {
                        echo '(<span class="on">ON</span>)';
                    }
                    ?>
                </div>
            </div>

            </form>

            <div style="clear: both;"></div>

            <div style="padding-top:1em;"></div>
            <center>

            <?php
            $timelapse_dir = (count(glob("$timelapse_path/*")) === 0) ? 'Empty' : 'Not empty';

            if (file_exists($lock_timelapse) || ($timelapse_display_last && $timelapse_dir == 'Not empty')) {
                echo '
                <div style="padding-bottom: 0.5em;">
                    Timelapse
                </div>
                ';

                if (file_exists($lock_timelapse)) {
                    $duration = `ps aux | grep '[r]aspistill' | grep timelapse | grep -oP "(?<=--timelapse )[^ ]+"`;
                    $duration = $duration / 1000 / 60;
                    $runtime = `ps aux | grep '[r]aspistill' | grep timelapse | grep -oP "(?<=--timeout )[^ ]+"`;
                    $runtime = $runtime / 1000 / 60;
                    echo "Duration: $duration min<br>";
                    echo "Run Time: $runtime min<br>";

                    $start_time = filemtime($lock_timelapse);
                    echo 'Start Time: ' , date("F d Y H:i:s", $start_time) , '<br>';
                }

                
                if ($timelapse_dir == 'Not empty') {
                    $files = scandir($timelapse_path, SCANDIR_SORT_DESCENDING);
                    $newest_file = $files[0];
                    $latest_file = filectime("$timelapse_path/$newest_file");
                    echo 'Latest File: ' , date("F d Y H:i:s", $latest_file) , '<br>';
                    echo '
                    <div style="padding-bottom: 2em;">
                        <img src=image.php?span=cam-timelapse>
                    </div>
                    ';
                } else if (file_exists($lock_timelapse)) {
                    echo '
                    <div style="padding: 0.5em 0 1.5em 0;">
                        Waiting for first timelapse image to be captured.
                    </div>
                    ';
                }
            }
            ?>

            <?php
                if (file_exists($lock_mjpg_streamer)) {
                    echo '
                    <div style="padding-bottom: 0.5em;">
                        Video Stream
                    </div>
                    <div style="padding-bottom: 2em;">
                        <img src="stream.php">
                    </div>
                    ';
                }

                if ($_SESSION['user_name'] != 'guest') {
                    $cam_stills_path = $install_path . '/camera-stills';
                    $cam_stills_dir = (count(glob("$cam_stills_path/*")) === 0) ? 'Empty' : 'Not empty';
                    if ($cam_stills_dir == 'Not empty' && (isset($_POST['CaptureStill']) || $still_display_last)) {
                        echo '
                        <div style="padding-bottom: 0.5em;">
                            Still Image
                        </div>
                        ';

                        $files = scandir($cam_stills_path, SCANDIR_SORT_DESCENDING);
                        $newest_file = $files[0];
                        $latest_file = filemtime("$cam_stills_path/$newest_file");
                        echo 'Latest File: ' , date("F d Y H:i:s", $latest_file) , '<br>';

                        echo '
                        <div style="padding-bottom: 2em;">
                            <img src=image.php?span=cam-still>
                        </div>
                        ';
                    }
                }
            ?>
            </center>
        </li>

        <li data-content="data" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'data') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($data_error)) {
                echo '<div style="color: red;">' . $data_error . '</div>';
            }
            ?>

            <div style="padding: 10px 0 0 15px;">
                <div style="padding-bottom: 15px;">
                    <form action="?tab=data<?php
                        if (isset($_GET['page'])) {
                            echo '&page=' , $_GET['page'];
                        } ?>" method="POST">
                        Lines: <input type="text" maxlength=8 size=8 name="Lines" />
                        <input type="submit" name="TSensor" value="T Sensor">
                        <input type="submit" name="HTSensor" value="HT Sensor">
                        <input type="submit" name="Co2Sensor" value="Co2 Sensor">
                        <input type="submit" name="Relay" value="Relay">
                        <input type="submit" name="Users" value="Users">
                        <input type="submit" name="Login" value="Login">
                        <input type="submit" name="Daemon" value="Daemon">
                        <input type="submit" name="Database" value="Database">
                    </form>
                </div>
                <div style="font-family: monospace;">
                    <pre><?php
                        if(isset($_POST['TSensor'])) {
                            concatenate_logs('t');
                            $log = '/var/tmp/sensor-t.log';

                            echo 'Year Mo Day Hour Min Sec Tc Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            unlink($log);
                        }
                        if(isset($_POST['HTSensor'])) {
                            concatenate_logs('ht');
                            $log = '/var/tmp/sensor-ht.log';

                            echo 'Year Mo Day Hour Min Sec Tc RH DPc Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            unlink($log);
                        }

                        if(isset($_POST['Co2Sensor'])) {
                            concatenate_logs('co2');
                            $log = '/var/tmp/sensor-co2.log';

                            echo 'Year Mo Day Hour Min Sec Co2 Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            unlink($log);
                        }

                        if(isset($_POST['Relay'])) {
                            concatenate_logs('relay');
                            $log = '/var/tmp/relay.log';

                            echo 'Year Mo Day Hour Min Sec R1Sec R2Sec R3Sec R4Sec R5Sec R6Sec R7Sec R8Sec<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            unlink($log);
                        }
                        if(isset($_POST['Users']) && $_SESSION['user_name'] != 'guest') {
                            echo 'User Email Password_Hash<br> <br>';
                            $db = new SQLite3("./config/users.db");
                            $results = $db->query('SELECT user_name, user_email, user_password_hash FROM users');
                            while ($row = $results->fetchArray()) {
                                echo $row[0] , ' ' , $row[1] , ' ' , $row[2] , '<br>';
                            }
                        }
                        if(isset($_POST['Login']) && $_SESSION['user_name'] != 'guest') {
                            echo 'Time, Type of auth, user, IP, Hostname, Referral, Browser<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $auth_log`;
                            } else {
                                echo `tail -n 30 $auth_log`;
                            }
                        }
                        if(isset($_POST['Daemon'])) {
                            concatenate_logs('daemon');
                            $log = '/var/tmp/daemon.log';

                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            unlink($log);
                        }
                        if(isset($_POST['Database'])) {
                            echo '<pre>';
                            exec('sqlite3 ' . $mycodo_db . ' .dump', $output); print_r($output);
                            echo '</pre>';
                        }
                    ?>
                    </pre>
                </div>
            </div>
        </li>

        <li data-content="settings" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'settings') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($settings_error)) {
                echo '<div style="color: red;">' . $settings_error . '</div>';
            }
            ?>

            <?php if ($this->feedback) echo $this->feedback; ?>

            <div class="advanced" style="padding-top: 1em;">
                <form action="?tab=settings" method="POST">
                <div style="padding: 1em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoRelays" value="Set">
                        <select name="numrelays">
                            <option value="0" <?php if ($relay_num == 0) echo 'selected="selected"'; ?>>0</option>
                            <option value="1" <?php if ($relay_num == 1) echo 'selected="selected"'; ?>>1</option>
                            <option value="2" <?php if ($relay_num == 2) echo 'selected="selected"'; ?>>2</option>
                            <option value="3" <?php if ($relay_num == 3) echo 'selected="selected"'; ?>>3</option>
                            <option value="4" <?php if ($relay_num == 4) echo 'selected="selected"'; ?>>4</option>
                            <option value="5" <?php if ($relay_num == 5) echo 'selected="selected"'; ?>>5</option>
                            <option value="6" <?php if ($relay_num == 6) echo 'selected="selected"'; ?>>6</option>
                            <option value="7" <?php if ($relay_num == 7) echo 'selected="selected"'; ?>>7</option>
                            <option value="8" <?php if ($relay_num == 8) echo 'selected="selected"'; ?>>8</option>
                        </select>
                    </div>
                    <div class="config-title">Relays</div>
                    <div style="clear: both;"></div>
                </div>

                <?php
                if ($relay_num > 0) {
                ?>
            
                <div>
                    <table class="relays">
                        <tr>
                            <td align=center class="table-header">&nbsp;<br>Relay</td>
                            <td class="table-header">&nbsp;<br>Name</td>
                            <td align=center class="table-header">State<br><img style="height: 0.95em; vertical-align: middle;" src="/mycodo/img/off.jpg" alt="Off" title="Off"> = off</td>
                            <td align=center class="table-header">Seconds<br>On</td>
                            <td align=center class="table-header">GPIO<br>Pin</td>
                            <td align=center class="table-header">Signal<br>ON</td>
                            <td align=center class="table-header"></td>
                        </tr>
                        <?php for ($i = 1; $i <= $relay_num; $i++) {
                            $read = "$gpio_path -g read $relay_pin[$i]";
                        ?>
                        <tr>
                            <td align=center>
                                <?php echo $i; ?>
                            </td>
                            <td>
                                <input style="width: 10em;" type="text" value="<?php echo $relay_name[$i]; ?>" maxlength=13 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i; ?>"/>
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
                                 [<input style="width: 4em;" type="number" min="1" max="99999" name="sR<?php echo $i; ?>" title="Number of seconds to turn this relay on"/><input type="submit" name="<?php echo $i; ?>secON" value="ON">]
                            </td>
                            <td align=center>
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $relay_pin[$i]; ?>" name="relay<?php echo $i; ?>pin" title="GPIO pin using BCM numbering, connected to relay <?php echo $i; ?>"/>
                            </td>
                            <td align=center>
                                <select style="width: 65px;" title="Does this relay activate with a LOW (0-volt) or HIGH (5-volt) signal?" name="relay<?php echo $i; ?>trigger">
                                    <option<?php
                                        if ($relay_trigger[$i] == 1) {
                                            echo ' selected="selected"';
                                        } ?> value="1">HIGH</option>
                                    <option<?php
                                        if ($relay_trigger[$i] == 0) {
                                            echo ' selected="selected"';
                                        } ?> value="0">LOW</option>
                                </select>
                            </td>
                            <td>
                                <input type="submit" name="Mod<?php echo $i; ?>Relay" value="Set">
                            </td>
                        </tr>
                        <?php
                        } ?>
                    </table>
                </div>
            <?php
            }
            ?>
            </form>
            </div>

            <div class="advanced">
                <form action="?tab=settings" method="POST">
                <div style="padding-bottom: 1em; font-weight: bold;">
                    <input type="submit" name="ChangeNoTimers" value="Set">
                    <select name="numtimers">
                        <option value="0" <?php if ($timer_num == 1) echo 'selected="selected"'; ?>>0</option>
                        <option value="1" <?php if ($timer_num == 1) echo 'selected="selected"'; ?>>1</option>
                        <option value="2" <?php if ($timer_num == 2) echo 'selected="selected"'; ?>>2</option>
                        <option value="3" <?php if ($timer_num == 3) echo 'selected="selected"'; ?>>3</option>
                        <option value="4" <?php if ($timer_num == 4) echo 'selected="selected"'; ?>>4</option>
                        <option value="5" <?php if ($timer_num == 5) echo 'selected="selected"'; ?>>5</option>
                        <option value="6" <?php if ($timer_num == 6) echo 'selected="selected"'; ?>>6</option>
                        <option value="7" <?php if ($timer_num == 7) echo 'selected="selected"'; ?>>7</option>
                        <option value="8" <?php if ($timer_num == 8) echo 'selected="selected"'; ?>>8</option>
                    </select>
                    <strong>Timers</strong>
                </div>
                <?php
                if ($timer_num > 0) {
                ?>
                <div>
                    <table class="relays">
                        <tr>
                            <td align=center class="table-header">Timer</td>
                            <td class="table-header">Name</td>
                            <th align=center class="table-header">State</th>
                            <td align=center class="table-header">Relay</td>
                            <td align=center class="table-header">On (sec)</td>
                            <td align=center class="table-header">Off (sec)</td>
                            <td align=center class="table-header"></td>
                        </tr>
                        <?php
                        for ($i = 1; $i <= $timer_num; $i++) {
                        ?>
                        <tr>
                            <td align="center">
                                <?php echo $i; ?>
                            </td>
                            <td>
                                <input style="width: 10em;" type="text" value="<?php echo $timer_name[$i]; ?>" maxlength=13 name="Timer<?php echo $i; ?>Name" title="This is the relay name for timer <?php echo $i; ?>"/>
                            </td>
                            <?php
                            if ($timer_state[$i] == 0) {
                            ?>
                                <td class="onoff">
                                    <nobr><input type="image" style="height: 0.95em; vertical-align: middle;" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="Timer<?php echo $i; ?>StateChange" value="0"> | <button style="width: 3em;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="1">ON</button></nobr>
                                </td>
                            <?php
                            } else {
                            ?>
                                <td class="onoff">
                                    <nobr><input type="image" style="height: 0.95em;" src="/mycodo/img/on.jpg" alt="On" title="On" name="Timer<?php echo $i; ?>StateChange" value="1"> | <button style="width: 3em;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="0">OFF</button></nobr>
                                </td>
                            <?php
                            }
                            ?>
                            <td>
                                <input  style="width: 3em;" type="number" min="0" max="8" value="<?php echo $timer_relay[$i]; ?>" maxlength=1 size=1 name="Timer<?php echo $i; ?>Relay" title="This is the relay number for timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input style="width: 5em;" type="number" min="1" max="99999" value="<?php echo $timer_duration_on[$i]; ?>" name="Timer<?php echo $i; ?>On" title="This is On duration of timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input style="width: 5em;" type="number" min="0" max="99999" value="<?php echo $timer_duration_off[$i]; ?>" name="Timer<?php echo $i; ?>Off" title="This is Off duration for timer <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <input type="submit" name="ChangeTimer<?php echo $i; ?>" value="Set">
                            </td>
                        </tr>
                        <?php
                        }
                        ?>
                    </table>
                </div>
                <?php
                }
                ?>
            </form>
            </div>

            <div class="advanced">
                <form method="post" action="?tab=settings" name="debug">
                <div style="font-weight: bold; padding: 0.5em 0;">
                    Debugging
                </div>
                <div class="adv">
                    Display Debugging Information <input type="hidden" name="debug" value="0" /><input type="checkbox" id="debug" name="debug" value="1"<?php if (isset($_COOKIE['debug'])) if ($_COOKIE['debug'] == True) echo ' checked'; ?> title="Display debugging information at the bottom of every page."/>
                </div>
                <div class="adv">
                    <input type="submit" value="Save">
                </div>
                </form>
            </div>

            <div class="advanced">
                <form method="post" action="?tab=settings" name="smtp">
                <div style="font-weight: bold; padding: 0.5em 0;">
                    Camera: Still Capture
                </div>
                <div class="adv">
                    Relay (0 to disable) <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $still_relay; ?>" maxlength=4 size=1 name="Still_Relay" title="A relay can be set to activate during the still image capture."/>
                </div>
                <div class="adv">
                    Add timestamp to image <input type="hidden" name="Still_Timestamp" value="0" /><input type="checkbox" id="Still_Timestamp" name="Still_Timestamp" value="1"<?php if ($still_timestamp) echo ' checked'; ?> title="Add a timestamp to the captured image."/>
                </div>
                <div class="adv">
                    Always display last still image <input type="hidden" name="Still_DisplayLast" value="0" /><input type="checkbox" id="Still_DisplayLast" name="Still_DisplayLast" value="1"<?php if ($still_display_last) echo ' checked'; ?> title="Always display the last image acquired or only after clicking 'Capture Still'."/>
                </div>
                <div class="adv">
                    Extra parameters for camera (raspistill) <input style="width: 22em;" type="text" value="<?php echo $still_extra_parameters; ?>" maxlength=200 name="Still_Extra_Parameters" title=""/>
                </div>
                <div class="adv">
                    <button name="ChangeStill" type="submit" value="">Save</button>
                </div>
                </form>
            </div>

            <div class="advanced">
                <form method="post" action="?tab=settings" name="smtp">
                <div style="font-weight: bold; padding: 0.5em 0;">
                    Camera: Video Stream
                </div>
                <div class="adv">
                    Relay (0 to disable) <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $stream_relay; ?>" maxlength=4 size=1 name="Stream_Relay" title="A relay can be set to activate during the video stream. Enable/disable on the camera tab."/>
                </div>
                <div class="adv">
                    Extra parameters for camera (raspistill) <input style="width: 22em;" type="text" value="<?php echo $stream_extra_parameters; ?>" maxlength=200 name="Stream_Extra_Parameters" title=""/>
                </div>
                <div class="adv">
                    <button name="ChangeStream" type="submit" value="">Save</button>
                </div>
                </form>
            </div>

            <div class="advanced">
                <form method="post" action="?tab=settings" name="smtp">
                <div style="font-weight: bold; padding: 0.5em 0;">
                    Camera: Timelapse
                </div>
                <div class="adv">
                    Relay (0 to disable) <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $timelapse_relay; ?>" maxlength=4 size=1 name="Timelapse_Relay" title="A relay can be set to activate during a timelapse capture. Enable/disable on the camera tab."/>
                </div>
                <div class="adv">
                    Photo save path <input style="width: 19em;" type="text" value="<?php echo $timelapse_path; ?>" maxlength=50 name="Timelapse_Path" title=""/>
                </div>
                <div class="adv">
                    Photo filename prefix <input style="width: 7em;" type="text" value="<?php echo $timelapse_prefix; ?>" maxlength=20 name="Timelapse_Prefix" title=""/>
                </div>
                <div class="adv">
                    Use start time in filename <input type="hidden" name="" value="0" /><input type="checkbox" id="" name="Timelapse_Timestamp" value="1"<?php if ($timelapse_timestamp) echo ' checked'; ?> title=""/>
                </div>
                <div class="adv">
                    Always display last timelapse image <input type="hidden" name="Timelapse_DisplayLast" value="0" /><input type="checkbox" id="Timelapse_DisplayLast" name="Timelapse_DisplayLast" value="1"<?php if ($timelapse_display_last) echo ' checked'; ?> title="Always display the last timelapse image or only while a timelapse is running."/>
                </div>
                <div class="adv">
                    Extra parameters for camera (raspistill) <input style="width: 22em;" type="text" value="<?php echo $timelapse_extra_parameters; ?>" maxlength=200 name="Timelapse_Extra_Parameters" title=""/>
                </div>
                <div class="adv">
                    Enable experimental auto-exposure mode <input type="hidden" name="" value="0" /><input type="checkbox" id="" name="timelapse-auto-exp" value="1"<?php if (1) echo ' checked'; ?> title=""/>
                </div>
                <div class="adv" style="padding: 0.3em 0 0.2em 0;">
                    <?php
                    if ($timelapse_timestamp) {
                        $timelapse_tstamp = substr(`date +"%Y%m%d%H%M%S"`, 0, -1);
                        echo "Output file series: $timelapse_path/$timelapse_prefix$timelapse_tstamp-00001.jpg";
                    } else {
                        echo "Output file series: $timelapse_path/$timelapse_prefix-00001.jpg";
                    }
                     ?>
                </div>
                <div class="adv">
                    <button name="ChangeTimelapse" type="submit" value="">Save</button>
                </div>
                </form>
            </div>

            <div style="clear: both;"></div>

            <div <div class="advanced">
                <form method="post" action="?tab=settings" name="smtp">
                <div style="font-weight: bold; padding: 0.5em 0;">
                    Email Notification
                </div>
                <div class="adv">
                    <input class="smtp" type="text" value="<?php echo $smtp_host; ?>" maxlength=30 size=20 name="smtp_host" title=""/> SMTP Host
                </div>
                <div class="adv">
                    <input class="smtp" type="number" value="<?php echo $smtp_port; ?>" maxlength=30 size=20 name="smtp_port" title=""/> SMTP Port
                </div>
                <div class="adv">
                    <input class="smtp" type="text" value="<?php echo $smtp_user; ?>" maxlength=30 size=20 name="smtp_user" title=""/> User
                </div>
                <div class="adv">
                    <input class="smtp" type="password" value="<?php echo $smtp_pass; ?>" maxlength=30 size=20 name="smtp_pass" title=""/> Password
                </div>
                <div class="adv">
                    <input class="smtp" type="text" value="<?php echo $smtp_email_from; ?>" maxlength=30 size=20 name="smtp_email_from" title=""/> From
                </div>
                <div class="adv">
                    <input class="smtp" type="text" value="<?php echo $smtp_email_to; ?>" maxlength=30 size=20 name="smtp_email_to" title=""/> To
                </div>
                <div class="adv">
                    <input type="submit" name="ChangeNotify" value="Save">
                </div>
                </form>
            </div>

            <div class="advanced">
                <div style="padding-bottom: 1em;">
                    <form method="post" action="?tab=settings" name="addform">
                    <div style="font-weight: bold; padding: 0.5em 0;">
                        Add User
                    </div>
                    <div class="adv">
                        <input id="login_input_username" type="text" pattern="[a-zA-Z0-9]{2,64}" required name="user_name" /> <label for="login_input_username">Username (only letters and numbers, 2 to 64 characters)</label>
                    </div>
                    <div class="adv">
                        <input id="login_input_email" type="email" name="user_email" /> <label for="login_input_email">Email</label>
                    </div>
                    <div class="adv">
                        <input id="login_input_password_new" class="login_input" type="password" name="user_password_new" pattern=".{6,}" required autocomplete="off" /> <label for="login_input_password_new">Password (min. 6 characters)</label>
                    </div>
                    <div class="adv">
                        <input id="login_input_password_repeat" class="login_input" type="password" name="user_password_repeat" pattern=".{6,}" required autocomplete="off" /> <label for="login_input_password_repeat">Repeat password</label>
                    </div>
                    <div class="adv">
                        <input type="submit" name="register" value="Add User" />
                    </div>
                    </form>
                </div>
                <div style="padding-bottom: 1em;">
                    <form method="post" action="?tab=settings" name="changeform">
                    <div style="font-weight: bold; padding: 0.5em 0;">
                        Change Password
                    </div>
                    <div class="adv">
                        <input id="login_input_username" type="text" pattern="[a-zA-Z0-9]{2,64}" required name="user_name" /> <label for="login_input_username">Username</label>
                    </div>
                    <div class="adv">
                        <input id="login_input_password_new" class="login_input" type="password" name="new_password" pattern=".{6,}" required autocomplete="off" /> <label for="login_input_password_new">New Password (min. 6 characters)</label>
                    </div>
                    <div class="adv">
                        <input id="login_input_password_repeat" class="login_input" type="password" name="new_password_repeat" pattern=".{6,}" required autocomplete="off" /> <label for="login_input_password_repeat">Repeat New password</label>
                    </div>
                    <div class="adv">
                        <input type="submit" name="changepassword" value="Change Password" />
                    </div>
                    </form>
                </div>
                <div>
                    <form method="post" action="?tab=settings" name="delform">
                    <div style="font-weight: bold; padding: 0.5em 0;">
                        Delete User
                    </div>
                    <div class="adv">
                        <input id="login_input_username" type="text" pattern="[a-zA-Z0-9]{2,64}" required name="user_name" />
                        <label for="login_input_username">Username</label>
                    </div>
                        <div class="adv">
                        <input type="submit" name="deleteuser" value="Delete User" />
                    </div>
                    </form>
                </div>
            </div>
            <div style="padding-top: 3em;"></div>
        </li>
    </ul> <!-- cd-tabs-content -->

    <?php
    if (isset($_COOKIE['debug']) && $_COOKIE['debug'] == True) {
        ?>
        <div style="padding: 4em 0 2em 2em;">
            <div style="padding-bottom: 1em; font-weight: bold; font-size: 1.5em;">
                Debug Information
            </div>
            <div style="padding-bottom: 2em;">
                <div style="padding: 1em 0; font-weight: bold; font-size: 1.2em;">
                    PHP Profile
                </div>
                <?php 
                    SimpleProfiler::stop_profile();
                    $profile = SimpleProfiler::get_profile();
                    $total = 0.0;
                    echo '
                    <table class="debug-profiler">
                    <tr>
                    <td>
                    Event
                    </td>
                    <td>
                    Event (seconds)
                    </td>
                    <td>
                    Up to event
                    </td>
                    <td>
                    Including event
                    </td>
                    </tr>';
                    foreach($profile as $array => $next) {
                        echo '
                        <tr>
                        <td style="padding-top: 0.5em; text-align: left; font-weight: bold;">
                        ' , $array , '
                        </td>
                        </tr>';
                        foreach($next as $key => $value) {
                            if ($key == "") $key = "-------->";
                            $pre = $total;
                            $total += $value;
                            echo '
                            <tr style="border-bottom:1pt solid black;">
                            <td style="">
                            ' , $key , '
                            </td>
                            <td>
                            ' , number_format($value, 10) , '
                            </td>
                            <td>
                            ' , number_format($pre, 10) , '
                            </td>
                            <td>
                            ' , number_format($total, 10) , '
                            </td>
                            </tr>';
                        }
                    }
                    echo '
                    <tr>
                    <td colspan="4" style="font-weight: bold; font-size: 1.3em;">
                    Total: ' , number_format($total, 10) , '
                    </td>
                    </tr>
                    </table>';
                    echo '<p style="padding: 2em 0 1em 0; font-weight: bold;">Raw Profile<p>
                    <pre>';
                    print_r($profile);
                    echo '</pre>
                    <br>';
                    ?>
                </pre>
            </div>
            <div style="padding-bottom: 2em;">
                <div style="padding: 1em 0; font-weight: bold; font-size: 1.2em;">
                    Cookies
                </div>
                <pre><?php print_r($_COOKIE); ?></pre>
            </div>
            <div style="padding-bottom: 2em;">
                <div style="padding: 1em 0; font-weight: bold; font-size: 1.2em;">
                    Session
                </div>
                <pre><?php print_r($_SESSION); ?></pre>
            </div>
            <div style="padding-bottom: 2em;">
                <div style="padding: 1em 0; font-weight: bold; font-size: 1.2em;">
                    Server
                </div>
                <pre><?php print_r($_SERVER); ?></pre>
            </div>
        </div>
    <?php
    }
    ?>

</div> <!-- cd-tabs -->

<script src="js/jquery-2.1.1.js"></script>
<script src="js/main.js"></script> <!-- Resource jQuery -->

</body>
</html>
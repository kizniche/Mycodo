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

$version = "3.5.69";

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
$user_db = $install_path . "/config/users.db";

$daemon_log = $install_path . "/log/daemon.log";
$auth_log = $install_path . "/log/auth.log";
$sensor_ht_log = $install_path . "/log/sensor-ht.log";
$sensor_co2_log = $install_path . "/log/sensor-co2.log";
$sensor_press_log = $install_path . "/log/sensor-press.log";
$relay_log = $install_path . "/log/relay.log";

$images = $install_path . "/images";
$lock_daemon = $lock_path . "/mycodo/daemon.lock";
$lock_raspistill = $lock_path . "/mycodo_raspistill";
$lock_mjpg_streamer = $lock_path . "/mycodo_mjpg_streamer";
$lock_mjpg_streamer_relay = $lock_path . "/mycodo-stream-light";
$lock_timelapse = $lock_path . "/mycodo_time_lapse";
$lock_timelapse_light = $lock_path . "/mycodo-timelapse-light";

if (!file_exists($mycodo_db)) exit("Mycodo database does not exist. Run '/var/www/mycodo/setup-database.py -i' to create required database.");
require($install_path . "/includes/database.php"); // Initial SQL database load to variables

require($install_path . "/includes/functions.php"); // Mycodo functions

// Output an error if the user guest attempts to submit certain forms
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    if ($_SESSION['user_name'] == 'guest' && !isset($_POST['Graph']) && !isset($_POST['login'])) {
        $output_error = 'guest';
    } else if ($_SESSION['user_name'] != 'guest') {
        // Only non-guest users may perform these actions
        require($install_path . "/includes/database.php"); // Reload SQLite database
        require($install_path . "/includes/restricted.php"); // Configuration changes
        require($install_path . "/includes/database.php"); // Reload SQLite database
    }
} else {
    if ((isset($_GET['r']) && $_GET['r'] == 1) && 
        (isset($_GET['tab']) && $_GET['tab'] == 'graph')) set_new_graph_id();
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
    if (isset($_GET['r']) && ($_GET['r'] == 1)) {
        echo '<META HTTP-EQUIV="refresh" CONTENT="' , $refresh_time , '">';
    }
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
                ?> Time-lapse</div>
        </div>
        <div style="float: left;">
            <div><?php
                if (isset($_GET['r'])) {
                    ?><div style="display:inline-block; vertical-align:top;"><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On" name="" value="0">
                    </div>
                    <div style="display:inline-block; padding-left: 0.3em;">
                        <div>Refresh<br><span style="font-size: 0.7em">(<?php echo $_GET['tab']; ?>)</span></div>
                    </div><?php
                } else {
                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0"> Refresh<?php
                }
            ?></div>
        </div>
    </div>
    <div style="float: left; vertical-align:top; height: 4.5em; padding: 1em 0.8em 0 0.3em;">
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;">Time now: <?php echo $time_now; ?></div>
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;">Last read: <?php echo $time_last; ?></div>
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;"><?php echo `uptime | grep -ohe 'load average[s:][: ].*' `; ?></div>
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;">CPU: <?php echo '<span title="' , number_format((float)$pi_temp_cpu_f, 1, '.', '') , '&deg;F">' , $pi_temp_cpu_c , '&deg;C</span> GPU: <span title="' , number_format((float)$pi_temp_gpu_f, 1, '.', '') , '&deg;F">' , $pi_temp_gpu_c , '&deg;C</span>'; ?></div>
    </div>
    <?php
    // Display brief Temp sensor and PID data in header
    for ($i = 0; $i < count($sensor_t_id); $i++) {
        if ($sensor_t_activated[$i] == 1) {
            if (isset($t_temp_f[$i])) {
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'T' , $i+1 , ': ' , $sensor_t_name[$i]; ?></td>
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
            } else {
                echo '<div class="header">T' , $i+1 , ':<br>Wait for<br>1st read</div>';
            }
        }
    }
    // Display brief Temp/Hum sensor and PID data in header
    for ($i = 0; $i < count($sensor_ht_id); $i++) {
        if ($sensor_ht_activated[$i] == 1) { 
            if (isset($ht_temp_f[$i])) {
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'HT' , $i+1 , ': ' , $sensor_ht_name[$i]; ?></td>
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
            } else {
                echo '<div class="header">HT' , $i+1 , ':<br>Wait for<br>1st read</div>';
            }
        }
    }
    // Display brief CO2 sensor and PID data in header
    for ($i = 0; $i < count($sensor_co2_id); $i++) {
        if ($sensor_co2_activated[$i] == 1) {
            if (isset($co2[$i])) {
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'CO<sub>2</sub>' , $i+1 , ': ' , $sensor_co2_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php echo 'Now<br>' , $co2[$i]; ?></td>
                        <td style="font-size: 0.8em;"><?php echo 'Set<br>' , $pid_co2_set[$i]; ?></td>
                    </tr>
                </table>
            </div><?php
            } else {
                echo '<div class="header">CO<sub>2</sub>' , $i+1 , ':<br>Wait for<br>1st read</div>';
            }
        }
    }
    // Display brief Press sensor and PID data in header
    for ($i = 0; $i < count($sensor_press_id); $i++) {
        if ($sensor_press_activated[$i] == 1) { 
            if (isset($press_temp_f[$i])) {
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'P' , $i+1 , ': ' , $sensor_press_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php
                            echo 'Now<br><span title="' , number_format((float)$press_temp_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$press_temp_c[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , (int)$press[$i] , ' Pa';
                        ?></td>
                        <td style="font-size: 0.8em;"><?php
                            echo 'Set<br><span title="' , number_format((float)$settemp_press_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$pid_press_temp_set[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , (int)$pid_press_press_set[$i] , ' Pa';
                        ?></td>
                    </tr>
                </table>
            </div><?php
            } else {
                echo '<div class="header">Press' , $i+1 , ':<br>Wait for<br>1st read</div>';
            }
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
                echo '<div class="error">Error: ' . $graph_error . '</div>';
            }
            ?>

            <form action="?tab=graph<?php
            if (isset($_GET['page'])) {
                echo '&page=' , $_GET['page'];
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
                                echo '<a href="?tab=graph">OFF</a> | <span class="on">ON</span>';
                            } else {
                                echo '<span class="off">OFF</span> | <a href="?tab=graph&r=1">ON</a>';
                            }
                        ?>
                        </div>
                    </div>
                    <div style="float: left; padding: 0 2em 1em 0.5em;">
                        <div style="float: left; padding-right: 0.1em;">
                            <input type="submit" name="Refresh" value="Refresh&#10;Page" title="Refresh page">
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
                                <option value="12h" <?php if ($graph_time_span == '12h') echo 'selected="selected"'; ?>>12 Hours</option>
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
                    if ((isset($sensor_t_graph) && array_sum($sensor_t_graph)) ||
                        (isset($sensor_ht_graph) && array_sum($sensor_ht_graph)) ||
                        (isset($sensor_co2_graph) && array_sum($sensor_co2_graph)) ||
                        (isset($sensor_press_graph) && array_sum($sensor_press_graph))) {

                        generate_graphs($mycodo_client, $graph_id, $graph_type, $graph_time_span, $sensor_t_graph, $sensor_ht_graph, $sensor_co2_graph, $sensor_press_graph);
                        ?>
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
                echo '<div class="error">Error: ' . $sensor_error . '</div>';
            }
            ?>

            <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
            <div style="padding-top: 0.5em;">
                <?php
                    if (count($relay_id) == 0) {
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
                    <div style="float: left; padding-right: 0.1em;">
                        <input type="submit" name="Refresh" value="Refresh&#10;Page" title="Refresh page">
                    </div>
                </div>

                <div style="float: left; margin: 0 0.5em; padding: 0 0.5em;">
                    <div style="clear: both;"></div>
                    <div class="config-title">T Sensors</div>
                    <div style="padding-right: 0.6em;">
                        <input style="width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddTSensorsNumber" title="Add this number of temperature sensors"/> <input type="submit" name="AddTSensors" value="Add">
                    </div>
                </div>

                <div style="float: left; margin: 0 0.5em; padding: 0 0.5em;">
                    <div style="clear: both;"></div>
                    <div class="config-title">HT Sensors</div>
                    <div style="padding-right: 0.6em;">
                        <input style="width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddHTSensorsNumber" title="Add this number of humidity/temperature sensors"/> <input type="submit" name="AddHTSensors" value="Add">
                    </div>
                </div>

                <div style="float: left; margin: 0 0.5em; padding: 0 0.5em;">
                    <div style="clear: both;"></div>
                    <div class="config-title">CO<sub>2</sub> Sensors</div>
                    <div style="padding-right: 0.6em;">
                        <input style="width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddCO2SensorsNumber" title="Add this number of CO2 sensors"/> <input type="submit" name="AddCO2Sensors" value="Add">
                    </div>
                </div>

                <div style="float: left; margin: 0 0.5em; padding: 0 0.5em;">
                    <div style="clear: both;"></div>
                    <div class="config-title">Pressure</sub> Sensors</div>
                    <div style="padding-right: 0.6em;">
                        <input style="width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddPressSensorsNumber" title="Add this number of pressure sensors"/> <input type="submit" name="AddPressSensors" value="Add">
                    </div>
                </div>

            </div>
            </form>

            <div style="clear: both;"></div>

            <?php
            if (count($relay_id) != 0) { ?>
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
                for ($i = 0; $i < count($relay_id); $i++) {
                    $read = "$gpio_path -g read $relay_pin[$i]";
                    $row = $results->fetchArray();
                    echo '<tr><td>' , $i+1 , '</td><td>' , $row[1] , '</td><td>' , $row[2] , '</td><td>' , $row[3] , '</td><td>';
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
           

            <div style="width: 54em; padding-left: 0.5em; padding-top: 2em;">
                
                <?php if (count($sensor_t_id) > 0) { ?>
                <div class="sensor-title">Temperature Sensors</div>
                <div style="padding-bottom: 1.5em;">
                    <?php
                    for ($i = 0; $i < count($sensor_t_id); $i++) {
                    ?>
                    <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                    <table class="sensor" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td>T Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_t_id[$i]; ?>)</span></td>
                            <td>Sensor<br>Name</td>
                            <td>Sensor<br>Device</td>
                            <?php 
                            if ($sensor_t_device[$i] == 'DS18B20') {
                                echo '<td align=center>Serial No<br>28-xxx</td>';
                            } else {
                                echo '<td align=center>GPIO<br>Pin</td>';
                            }
                            ?>
                            <td>Log<br>Interval</td>
                            <td>Pre<br>Relay</td>
                            <td>Pre<br>Duration</td>
                            <td>Log</td>
                            <td>Graph</td>
                            <td rowspan=2 style="padding: 0 0.5em;">
                                <div style="padding: 0.2em 0">
                                    Presets: <select style="width: 9em;" name="sensort<?php echo $i; ?>preset">
                                        <option value="default">default</option>
                                        <?php
                                        for ($z = 0; $z < count($sensor_t_preset); $z++) {
                                            echo '<option value="' . $sensor_t_preset[$z] . '">' . $sensor_t_preset[$z] . '</option>';
                                        }
                                        ?>
                                    </select>
                                    
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input type="submit" name="Change<?php echo $i; ?>TSensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_ht_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>TSensorOverwrite" value="Overwrite" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>TSensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_t_preset) == 0) echo ' disabled'; ?>>
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensort<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>TSensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>TSensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                                </div>
                            </td>
                        </tr>
                        <tr class="shade" style="height: 2.5em;">
                            <td class="shade" style="vertical-align: middle;">
                                <button type="submit" name="Delete<?php echo $i; ?>TSensor" title="Delete Sensor">Delete<br>Sensor</button>
                            </td>
                            <td>
                                <input style="width: <?php if ($sensor_t_device[$i] == 'DS18B20') echo '6em'; else echo '10em'; ?>;" type="text" value="<?php echo $sensor_t_name[$i]; ?>" maxlength=12 size=10 name="sensort<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 6.5em;" name="sensort<?php echo $i; ?>device">
                                    <option<?php
                                        if ($sensor_t_device[$i] == 'Other') {
                                            echo ' selected="selected"';
                                        } ?> value="Other">Other</option>
                                    <option<?php
                                        if ($sensor_t_device[$i] == 'DS18B20') {
                                            echo ' selected="selected"';
                                        } ?> value="DS18B20">DS18B20</option>
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
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_t_period[$i]; ?>" name="sensort<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_t_premeasure_relay[$i]; ?>" maxlength=2 size=1 name="sensort<?php echo $i; ?>premeasure_relay" title="This is the relay that will turn on prior to the sensor measurement, for the duration specified by Pre Duration (0 to disable)"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_t_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensort<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relaywill run before the sensor measurement is obtained"/> sec
                            </td>
                            <td>
                                <input type="checkbox" title="Enable this sensor to record measurements to the log file?" name="sensort<?php echo $i; ?>activated" value="1" <?php if ($sensor_t_activated[$i] == 1) echo 'checked'; ?>>
                            </td>
                            <td>
                                <input type="checkbox" title="Enable graphs to be generated from the sensor log data?" name="sensort<?php echo $i; ?>graph" value="1" <?php if ($sensor_t_graph[$i] == 1) echo 'checked'; ?>>
                            </td>
                        </tr>
                    </table>
                    <table class="pid" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td style="text-align: left;">Regulation</td>
                            <td>Current<br>State</td>
                            <td>PID<br>Set Point</td>
                            <td>PID<br>Regulate</td>
                            <td>Sensor Read<br>Interval</td>
                            <td>Up<br>Relay</td>
                            <td>Up<br>Max</td>
                            <td>Down<br>Relay</td>
                            <td>Down<br>Max</td>
                            <td>K<sub>p</sub></td>
                            <td>K<sub>i</sub></td>
                            <td>K<sub>d</sub></td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td style="text-align: left;">Temperature</td>
                            <td class="onoff">
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
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_set[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>TempSet" title="This is the desired temperature in °C."/> °C
                            </td>
                            <td>
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
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_t_temp_period[$i]; ?>" name="SetT<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_t_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_t_temp_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempOutmaxLow" title="This is the maximum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_t_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_t_temp_outmax_high[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempOutmaxHigh" title="This is the maximum number of seconds the relay used to decrease temperature is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_p[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_P" title="This is the Proportional gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_i[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_I" title="This is the Integral gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_t_temp_d[$i]; ?>" maxlength=4 size=1 name="SetT<?php echo $i; ?>Temp_D" title="This is the Derivative gain of the PID controller"/>
                            </td>
                        </tr>
                    </table>
                    <form>
                    <div style="margin-bottom: <?php if ($i == count($sensor_t_id)) echo '2'; else echo '1'; ?>em;"></div>
                    <?php
                    }
                    ?>
                </div>
                <?php
                }
                ?>

                <?php if (count($sensor_ht_id) > 0) { ?>
                <div class="sensor-title">Humidity/Temperature Sensors</div>
                <div style="margin-bottom: 1.5em;">
                    <?php
                    for ($i = 0; $i < count($sensor_ht_id); $i++) {
                    ?>
                    <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                    <table class="sensor" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td>HT Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_ht_id[$i]; ?>)</span></td>
                            <td>Sensor<br>Name</td>
                            <td>Sensor<br>Device</td>
                            <td>GPIO<br>Pin</td>
                            <td>Log<br>Interval</td>
                            <td>Pre<br>Relay</td>
                            <td>Pre<br>Duration</td>
                            <td>Log</td>
                            <td>Graph</td>
                            <td rowspan=2 style="padding: 0 0.5em;">
                                <div style="padding: 0.2em 0">
                                    Presets: <select style="width: 9em;" name="sensorht<?php echo $i; ?>preset">
                                        <option value="default">default</option>
                                        <?php
                                        for ($z = 0; $z < count($sensor_ht_preset); $z++) {
                                            echo '<option value="' . $sensor_ht_preset[$z] . '">' . $sensor_ht_preset[$z] . '</option>';
                                        }
                                        ?>
                                    </select>
                                    
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input type="submit" name="Change<?php echo $i; ?>HTSensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_ht_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>HTSensorOverwrite" value="Overwrite" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>HTSensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_ht_preset) == 0) echo ' disabled'; ?>>
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensorht<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>HTSensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>HTSensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                                </div>
                            </td>
                        </tr>
                        <tr class="shade" style="height: 2.5em;">
                            <td class="shade" style="vertical-align: middle;">
                                <button type="submit" name="Delete<?php echo $i; ?>HTSensor" title="Delete Sensor">Delete<br>Sensor</button>
                            </td>
                            <td>
                                <input style="width: 6.5em;" type="text" value="<?php echo $sensor_ht_name[$i]; ?>" maxlength=12 size=10 name="sensorht<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
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
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_ht_pin[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>pin" title="This is the GPIO pin connected to the HT sensor"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_ht_period[$i]; ?>" name="sensorht<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_ht_premeasure_relay[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>premeasure_relay" title="This is the relay that will turn on prior to the sensor measurement, for the duration specified by Pre Duration (0 to disable)"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_ht_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relaywill run before the sensor measurement is obtained"/> sec
                            </td>
                            <td>
                                <input type="checkbox" title="Enable this sensor to record measurements to the log file?" name="sensorht<?php echo $i; ?>activated" value="1" <?php if ($sensor_ht_activated[$i] == 1) echo 'checked'; ?>>
                            </td>
                            <td>
                                <input type="checkbox" title="Enable graphs to be generated from the sensor log data?" name="sensorht<?php echo $i; ?>graph" value="1" <?php if ($sensor_ht_graph[$i] == 1) echo 'checked'; ?>>
                            </td>
                        </tr>
                    </table>
                    <table class="pid" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td style="text-align: left;">Regulation</td>
                            <td>Current<br>State</td>
                            <td>PID<br>Set Point</td>
                            <td>PID<br>Regulate</td>
                            <td>Sensor Read<br>Interval</td>
                            <td>Up<br>Relay</td>
                            <td>Up<br>Max</td>
                            <td>Down<br>Relay</td>
                            <td>Down<br>Max</td>
                            <td>K<sub>p</sub></td>
                            <td>K<sub>i</sub></td>
                            <td>K<sub>d</sub></td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td style="text-align: left;">Temperature</td>
                            <td class="onoff">
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
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_set[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>TempSet" title="This is the desired temperature in °C."/> °C
                            </td>
                            <td>
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
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_ht_temp_period[$i]; ?>" name="SetHT<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_temp_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempOutmaxLow" title="This is the maximum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_temp_outmax_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempOutmaxHigh" title="This is the maximum number of seconds the relay used to decrease temperature is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_p[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_P" title="This is the Proportional gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_i[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_I" title="This is the Integral gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_temp_d[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Temp_D" title="This is the Derivative gain of the PID controller"/>
                            </td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td style="text-align: left;">Humidity</td>
                            <td class="onoff">
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
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_set[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>HumSet" title="This is the desired relative humidity in percent."/> %
                            </td>
                            <td>
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
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_ht_hum_period[$i]; ?>" name="SetHT<?php echo $i; ?>HumPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another humidity reading and applying the PID"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_hum_relay_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumRelayLow" title="This relay is used to increase humidity."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_hum_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumOutmaxLow" title="This is the maximum number of seconds the relay used to increase humidity is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_hum_relay_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumRelayHigh" title="This relay is used to decrease humidity."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_hum_outmax_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumOutmaxHigh" title="This is the maximum number of seconds the relay used to decrease humidity is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_p[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_P" title="This is the Proportional gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_i[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_I" title="This is the Integral gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_ht_hum_d[$i]; ?>" maxlength=4 size=1 name="SetHT<?php echo $i; ?>Hum_D" title="This is the Derivative gain of the PID controller"/>
                            </td>
                        </tr>
                    </table>
                    </form>
                    <div style="margin-bottom: <?php if ($i == count($sensor_ht_id)) echo '2'; else echo '1'; ?>em;"></div>
                    <?php
                    }
                    ?>
                </div>
                <?php
                }
                ?>

                <?php if (count($sensor_co2_id) > 0) { ?>
                <div class="sensor-title">CO<sub>2</sub> Sensors</div>
                <div>
                    <?php
                    for ($i = 0; $i < count($sensor_co2_id); $i++) {
                    ?>
                    <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                    <table class="sensor" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td>CO<sub>2</sub> Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_co2_id[$i]; ?>)</span></td>
                            <td>Sensor<br>Name</td>
                            <td>Sensor<br>Device</td>
                            <td>GPIO<br>Pin</td>
                            <td>Log<br>Interval</td>
                            <td>Pre<br>Relay</td>
                            <td>Pre<br>Duration</td>
                            <td>Log</td>
                            <td>Graph</td>
                            <td rowspan=2 style="padding: 0 0.5em;">
                                <div style="padding: 0.2em 0">
                                    Presets: <select style="width: 9em;" name="sensorco2<?php echo $i; ?>preset">
                                        <option value="default">default</option>
                                        <?php
                                        for ($z = 0; $z < count($sensor_co2_preset); $z++) {
                                            echo '<option value="' . $sensor_co2_preset[$z] . '">' . $sensor_co2_preset[$z] . '</option>';
                                        }
                                        ?>
                                    </select>
                                    
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input type="submit" name="Change<?php echo $i; ?>CO2SensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_co2_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>CO2SensorOverwrite" value="Overwrite" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>CO2SensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_co2_preset) == 0) echo ' disabled'; ?>>
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensorco2<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>CO2SensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>CO2SensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                                </div>
                            </td>
                        </tr>
                        <tr class="shade" style="height: 2.5em;">
                            <td class="shade" style="vertical-align: middle;">
                                <button type="submit" name="Delete<?php echo $i; ?>CO2Sensor" title="Delete Sensor">Delete<br>Sensor</button>
                            </td>
                            <td>
                                <input style="width: 7em;" type="text" value="<?php echo $sensor_co2_name[$i]; ?>" maxlength=12 size=10 name="sensorco2<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 6.5em;" name="sensorco2<?php echo $i; ?>device">
                                    <option<?php
                                        if ($sensor_co2_device[$i] == 'Other') {
                                            echo ' selected="selected"';
                                        } ?> value="Other">Other</option>
                                    <option<?php
                                        if ($sensor_co2_device[$i] == 'K30') {
                                            echo ' selected="selected"';
                                        } ?> value="K30">K30</option>
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
                                    <input style="width: 4em;" type="number" value="<?php echo $sensor_co2_pin[$i]; ?>" maxlength=2 size=1 name="sensorco2<?php echo $i; ?>pin" title="This is the GPIO pin connected to the CO2 sensor"/>
                                <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_co2_period[$i]; ?>" name="sensorco2<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_co2_premeasure_relay[$i]; ?>" maxlength=2 size=1 name="sensorco2<?php echo $i; ?>premeasure_relay" title="This is the relay that will turn on prior to the sensor measurement, for the duration specified by Pre Duration (0 to disable)"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_co2_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensorco2<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relaywill run before the sensor measurement is obtained"/> sec
                            </td>
                            <td>
                                <input type="checkbox" title="Enable this sensor to record measurements to the log file?" name="sensorco2<?php echo $i; ?>activated" value="1" <?php if ($sensor_co2_activated[$i] == 1) echo 'checked'; ?>>
                            </td>
                            <td>
                                <input type="checkbox" title="Enable graphs to be generated from the sensor log data?" name="sensorco2<?php echo $i; ?>graph" value="1" <?php if ($sensor_co2_graph[$i] == 1) echo 'checked'; ?>>
                            </td>
                        </tr>
                    </table>
                    <table class="pid" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td style="text-align: left;">Regulation</td>
                            <td>Current<br>State</td>
                            <td>PID<br>Set Point</td>
                            <td>PID<br>Regulate</td>
                            <td>Sensor Read<br>Interval</td>
                            <td>Up<br>Relay</td>
                            <td>Up<br>Max</td>
                            <td>Down<br>Relay</td>
                            <td>Down<br>Max</td>
                            <td>K<sub>p</sub></td>
                            <td>K<sub>i</sub></td>
                            <td>K<sub>d</sub></td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td style="text-align: left;">CO<sub>2</sub></td>
                            <td class="onoff">
                                <?php
                                if ($pid_co2_or[$i] == 1) {
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>CO2OR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>CO2OR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>CO2OR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>CO2OR" value="1">OFF</button>
                                    <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_set[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>CO2Set" title="This is the desired CO2 concentration in ppmv."/> ppmv
                            </td>
                            <td>
                                <select style="width: 5em;" name="SetCO2<?php echo $i; ?>CO2SetDir" title="Which direction should the PID regulate. 'Up' will ensure the CO2 is regulated above a certain CO2. 'Down' will ensure the CO2 is regulates below a certain point. 'Both' will ensure the CO2 is regulated both up and down to maintain a specific CO2."/>
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
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_co2_period[$i]; ?>" maxlength=4 size=1 name="SetCO2<?php echo $i; ?>CO2Period" title="This is the number of seconds to wait after the relay has been turned off before taking another CO2 reading and applying the PID"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_co2_relay_low[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2RelayLow" title="This relay is used to increase CO2."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_co2_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2OutmaxLow" title="This is the maximum number of seconds the relay used to increase CO2 is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_co2_relay_high[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2RelayHigh" title="This relay is used to decrease CO2."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_co2_outmax_high[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2OutmaxHigh" title="This is the maximum number of seconds the relay used to decrease CO2 is permitted to turn on for (0 to disable)."/>
                            </td>
                            
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_p[$i]; ?>" maxlength=5 size=1 name="SetCO2<?php echo $i; ?>CO2_P" title="This is the Proportional gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_i[$i]; ?>" maxlength=5 size=1 name="SetCO2<?php echo $i; ?>CO2_I" title="This is the Integral gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_d[$i]; ?>" maxlength=5 size=1 name="SetCO2<?php echo $i; ?>CO2_D" title="This is the Derivative gain of the PID controller"/>
                            </td>
                        </tr>
                    </table>
                    </form>
                    <div style="margin-bottom: <?php if ($i == count($sensor_co2_id)) echo '2'; else echo '1'; ?>em;"></div>
                    <?php
                    }
                    ?>
                </div>
                <?php
                }
                ?>

               <?php if (count($sensor_press_id) > 0) { ?>
                <div class="sensor-title">Pressure Sensors</div>
                <div style="margin-bottom: 1.5em;">
                    <?php
                    for ($i = 0; $i < count($sensor_press_id); $i++) {
                    ?>
                    <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                    <table class="sensor" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td>Press Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_press_id[$i]; ?>)</span></td>
                            <td>Sensor<br>Name</td>
                            <td>Sensor<br>Device</td>
                            <td>GPIO<br>Pin</td>
                            <td>Log<br>Interval</td>
                            <td>Pre<br>Relay</td>
                            <td>Pre<br>Duration</td>
                            <td>Log</td>
                            <td>Graph</td>
                            <td rowspan=2 style="padding: 0 0.5em;">
                                <div style="padding: 0.2em 0">
                                    Presets: <select style="width: 9em;" name="sensorpress<?php echo $i; ?>preset">
                                        <option value="default">default</option>
                                        <?php
                                        for ($z = 0; $z < count($sensor_press_preset); $z++) {
                                            echo '<option value="' . $sensor_press_preset[$z] . '">' . $sensor_press_preset[$z] . '</option>';
                                        }
                                        ?>
                                    </select>
                                    
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input type="submit" name="Change<?php echo $i; ?>PressSensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_press_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>PressSensorOverwrite" value="Overwrite" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>PressSensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_press_preset) == 0) echo ' disabled'; ?>>
                                </div>
                                <div style="padding: 0.2em 0">
                                    <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensorpress<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>PressSensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>PressSensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                                </div>
                            </td>
                        </tr>
                        <tr class="shade" style="height: 2.5em;">
                            <td class="shade" style="vertical-align: middle;">
                                <button type="submit" name="Delete<?php echo $i; ?>PressSensor" title="Delete Sensor">Delete<br>Sensor</button>
                            </td>
                            <td>
                                <input style="width: 6.5em;" type="text" value="<?php echo $sensor_press_name[$i]; ?>" maxlength=12 size=10 name="sensorpress<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 6.5em;" name="sensorpress<?php echo $i; ?>device">
                                    <option<?php
                                        if ($sensor_press_device[$i] == 'BMP085-180') {
                                            echo ' selected="selected"';
                                        } ?> value="BMP085-180">BMP085/180</option>
                                    <option<?php
                                        if ($sensor_press_device[$i] == 'Other') {
                                            echo ' selected="selected"';
                                        } ?> value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <?php
                                if ($sensor_press_device[$i] == 'BMP085-180') {
                                ?>
                                I<sup>2</sup>C
                                <?php
                                } else {
                                ?>
                                    <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_press_pin[$i]; ?>" maxlength=2 size=1 name="sensorpress<?php echo $i; ?>pin" title="This is the GPIO pin connected to the Press sensor"/>
                                <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_press_period[$i]; ?>" name="sensorpress<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_press_premeasure_relay[$i]; ?>" maxlength=2 size=1 name="sensorpress<?php echo $i; ?>premeasure_relay" title="This is the relay that will turn on prior to the sensor measurement, for the duration specified by Pre Duration (0 to disable)"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_press_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensorpress<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relaywill run before the sensor measurement is obtained"/> sec
                            </td>
                            <td>
                                <input type="checkbox" title="Enable this sensor to record measurements to the log file?" name="sensorpress<?php echo $i; ?>activated" value="1" <?php if ($sensor_press_activated[$i] == 1) echo 'checked'; ?>>
                            </td>
                            <td>
                                <input type="checkbox" title="Enable graphs to be generated from the sensor log data?" name="sensorpress<?php echo $i; ?>graph" value="1" <?php if ($sensor_press_graph[$i] == 1) echo 'checked'; ?>>
                            </td>
                        </tr>
                    </table>
                    <table class="pid" style="border: 0.7em solid #EBEBEB; border-top: 0;">
                        <tr class="shade">
                            <td style="text-align: left;">Regulation</td>
                            <td>Current<br>State</td>
                            <td>PID<br>Set Point</td>
                            <td>PID<br>Regulate</td>
                            <td>Sensor Read<br>Interval</td>
                            <td>Up<br>Relay</td>
                            <td>Up<br>Max</td>
                            <td>Down<br>Relay</td>
                            <td>Down<br>Max</td>
                            <td>K<sub>p</sub></td>
                            <td>K<sub>i</sub></td>
                            <td>K<sub>d</sub></td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td style="text-align: left;">Temperature</td>
                            <td class="onoff">
                                <?php
                                if ($pid_press_temp_or[$i] == 1) {
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="ChangePress<?php echo $i; ?>TempOR" value="0"> | <button style="width: 3em;" type="submit" name="ChangePress<?php echo $i; ?>TempOR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="ChangePress<?php echo $i; ?>TempOR" value="1"> | <button style="width: 3em;" type="submit" name="ChangePress<?php echo $i; ?>TempOR" value="1">OFF</button>
                                <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_temp_set[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>TempSet" title="This is the desired temperature in °C."/> °C
                            </td>
                            <td>
                                <select style="width: 5em;" name="SetPress<?php echo $i; ?>TempSetDir" title="Which direction should the PID regulate. 'Up' will ensure the temperature is regulated above a certain temperature. 'Down' will ensure the temperature is regulates below a certain point. 'Both' will ensure the temperature is regulated both up and down to maintain a specific temperature."/>
                                    <option value="0"<?php
                                        if ($pid_press_temp_set_dir[$i] == 0) {
                                            echo ' selected="selected"';
                                        } ?>>Both</option>
                                    <option value="1"<?php
                                        if ($pid_press_temp_set_dir[$i] == 1) {
                                            echo ' selected="selected"';
                                        } ?>>Up</option>
                                    <option value="-1"<?php
                                        if ($pid_press_temp_set_dir[$i] == -1) {
                                            echo ' selected="selected"';
                                        } ?>>Down</option>
                                </select>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_press_temp_period[$i]; ?>" name="SetPress<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_temp_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempOutmaxLow" title="This is the maximum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_temp_outmax_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempOutmaxHigh" title="This is the maximum number of seconds the relay used to decrease temperature is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_temp_p[$i]; ?>" maxlength=4 size=1 name="SetPress<?php echo $i; ?>Temp_P" title="This is the Proportional gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_temp_i[$i]; ?>" maxlength=4 size=1 name="SetPress<?php echo $i; ?>Temp_I" title="This is the Integral gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_temp_d[$i]; ?>" maxlength=4 size=1 name="SetPress<?php echo $i; ?>Temp_D" title="This is the Derivative gain of the PID controller"/>
                            </td>
                        </tr>
                        <tr style="height: 2.5em;">
                            <td style="text-align: left;">Pressure</td>
                            <td class="onoff">
                                <?php
                                if ($pid_press_press_or[$i] == 1) {
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="ChangePress<?php echo $i; ?>PressOR" value="0"> | <button style="width: 3em;" type="submit" name="ChangePress<?php echo $i; ?>PressOR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="ChangePress<?php echo $i; ?>PressOR" value="1"> | <button style="width: 3em;" type="submit" name="ChangePress<?php echo $i; ?>PressOR" value="1">OFF</button>
                                <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_press_set[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>PressSet" title="This is the desired relative pressure in percent."/> Pa
                            </td>
                            <td>
                                <select style="width: 5em;" name="SetPress<?php echo $i; ?>PressSetDir" title="Which direction should the PID regulate. 'Up' will ensure the pressure is regulated above a certain pressure. 'Down' will ensure the pressure is regulates below a certain point. 'Both' will ensure the pressure is regulated both up and down to maintain a specific pressure."/>
                                    <option value="0"<?php
                                        if ($pid_press_press_set_dir[$i] == 0) {
                                            echo ' selected="selected"';
                                        } ?>>Both</option>
                                    <option value="1"<?php
                                        if ($pid_press_press_set_dir[$i] == 1) {
                                            echo ' selected="selected"';
                                        } ?>>Up</option>
                                    <option value="-1"<?php
                                        if ($pid_press_press_set_dir[$i] == -1) {
                                            echo ' selected="selected"';
                                        } ?>>Down</option>
                                </select>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_press_press_period[$i]; ?>" name="SetPress<?php echo $i; ?>PressPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another pressure reading and applying the PID"/> sec
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_press_relay_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressRelayLow" title="This relay is used to increase pressure."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_press_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressOutmaxLow" title="This is the maximum number of seconds the relay used to increase pressure is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_press_relay_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressRelayHigh" title="This relay is used to decrease pressure."/>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_press_outmax_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressOutmaxHigh" title="This is the maximum number of seconds the relay used to decrease pressure is permitted to turn on for (0 to disable)."/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_press_p[$i]; ?>" maxlength=4 size=1 name="SetPress<?php echo $i; ?>Press_P" title="This is the Proportional gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_press_i[$i]; ?>" maxlength=4 size=1 name="SetPress<?php echo $i; ?>Press_I" title="This is the Integral gain of the PID controller"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_press_d[$i]; ?>" maxlength=4 size=1 name="SetPress<?php echo $i; ?>Press_D" title="This is the Derivative gain of the PID controller"/>
                            </td>
                        </tr>
                    </table>
                    </form>
                    <div style="margin-bottom: <?php if ($i == count($sensor_press_id)) echo '2'; else echo '1'; ?>em;"></div>
                    <?php
                    }
                    ?>
                </div>
                <?php
                }
                ?>
                
            </div>
        </li>

        <li data-content="custom" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'custom') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($custom_error)) {
                echo '<div class="error">Error: ' . $custom_error . '</div>';
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
                        $total = ((count($sensor_t_id) != 0) + (count($sensor_ht_id) != 0)*2 + (count($sensor_co2_id) != 0) + (count($sensor_press_id) != 0)*2 + 1);

                        $f = fopen($cus_graph, "w");
                        $size = $total * 350;
                        fwrite($f, "set terminal png size $graph_width,$size\n");
                        fwrite($f, "set xdata time\n");
                        fwrite($f, "set timefmt \"%Y %m %d %H %M %S\"\n");
                        fwrite($f, "set output \"$images/graph-custom-combined-$id2-0.png\"\n");
                        fwrite($f, "set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]\n");
                        fwrite($f, "set format x \"%H:%M\\n%m/%d\"\n");
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
                        
                        fwrite($f, "set multiplot layout $total, 1 title \"Combined Sensor Data - $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"\n");

                        if (count($sensor_t_id) != 0) {
                            if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                            else fwrite($f, "unset key\n");
                            fwrite($f, "set yrange [0:35]\n");
                            fwrite($f, "set ytics 5\n");
                            fwrite($f, "set mytics 2\n");
                            fwrite($f, "set title \"T Sensor: Combined Temperatures\"\n");
                            fwrite($f, "plot ");

                            for ($z = 0; $z < count($sensor_t_id); $z++) {
                                $line= $z+1;
                                fwrite($f, "\"<awk '\\$10 == " . $z . "' /var/tmp/sensor-t.log\" using 1:7 index 0 title \"T$line\" w lp ls $line axes x1y1");
                                if ($z < count($sensor_t_id)-1) fwrite($f, ", ");
                            }
                            fwrite($f, "\n");
                        }

                        if (count($sensor_ht_id) != 0) {
                            if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                            else fwrite($f, "unset key\n");
                            fwrite($f, "set yrange [0:35]\n");
                            fwrite($f, "set ytics 5\n");
                            fwrite($f, "set mytics 2\n");
                            fwrite($f, "set title \"HT Sensor: Combined Temperatures\"\n");
                            if (count($sensor_ht_id) != 0) fwrite($f, "plot ");

                            for ($z = 0; $z < count($sensor_ht_id); $z++) {
                                $line= $z+1;
                                fwrite($f, "\"<awk '\\$10 == " . $z . "' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T$line\" w lp ls $line axes x1y1");
                                if ($z < count($sensor_ht_id)-1) fwrite($f, ", ");
                            }
                            fwrite($f, "\n");

                            if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                            else fwrite($f, "unset key\n");
                            fwrite($f, "set yrange [0:100]\n");
                            fwrite($f, "set ytics 10\n");
                            fwrite($f, "set mytics 5\n");
                            fwrite($f, "set title \"HT Sensor: Combined Humidities\"\n");
                            if (count($sensor_ht_id) != 0) fwrite($f, "plot ");

                            for ($z = 0; $z < count($sensor_ht_id); $z++) {
                                $line= $z+1;
                                fwrite($f, "\"<awk '\\$10 == " . $z . "' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"H$line\" w lp ls $line axes x1y1");
                                if ($z < count($sensor_ht_id)-1) fwrite($f, ", ");
                            }
                            fwrite($f, "\n");
                        }

                        if (count($sensor_co2_id) != 0) {
                            if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                            else fwrite($f, "unset key\n");
                            fwrite($f, "set yrange [0:5000]\n");
                            fwrite($f, "set ytics 1000\n");
                            fwrite($f, "set mytics 5\n");
                            fwrite($f, "set title \"CO2 Sensor: Combined CO2s\"\n");
                            if (count($sensor_co2_id) != 0) fwrite($f, "plot ");

                            for ($z = 0; $z < count($sensor_co2_id); $z++) {
                                $line= $z+1;
                                fwrite($f, "\"<awk '\\$8 == " . $z . "' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"CO_2$line\" w lp ls $line axes x1y1");
                                if ($z < count($sensor_co2_id)-1) fwrite($f, ", ");
                            }
                            fwrite($f, "\n");
                        }

                        if (count($sensor_press_id) != 0) {
                            if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                            else fwrite($f, "unset key\n");
                            fwrite($f, "set yrange [0:35]\n");
                            fwrite($f, "set ytics 5\n");
                            fwrite($f, "set mytics 2\n");
                            fwrite($f, "set title \"Press Sensor: Combined Temperatures\"\n");
                            if (count($sensor_press_id) != 0) fwrite($f, "plot ");

                            for ($z = 0; $z < count($sensor_press_id); $z++) {
                                $line= $z+1;
                                fwrite($f, "\"<awk '\\$10 == " . $z . "' /var/tmp/sensor-press.log\" using 1:7 index 0 title \"T$line\" w lp ls $line axes x1y1");
                                if ($z < count($sensor_press_id)-1) fwrite($f, ", ");
                            }
                            fwrite($f, "\n");

                            if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left bottom\n");
                            else fwrite($f, "unset key\n");
                            fwrite($f, "set yrange [97000:99000]\n");
                            fwrite($f, "set ytics 200\n");
                            fwrite($f, "set mytics 4\n");
                            fwrite($f, "set title \"Press Sensor: Combined Pressures\"\n");
                            if (count($sensor_press_id) != 0) fwrite($f, "plot ");

                            for ($z = 0; $z < count($sensor_press_id); $z++) {
                                $line= $z+1;
                                fwrite($f, "\"<awk '\\$10 == " . $z . "' /var/tmp/sensor-press.log\" using 1:8 index 0 title \"P$line\" w lp ls $line axes x1y1");
                                if ($z < count($sensor_press_id)-1) fwrite($f, ", ");
                            }
                            fwrite($f, "\n");
                        }

                        if (isset($_POST['key']) && $_POST['key'] == 1) fwrite($f, "set key left top\n");
                        else fwrite($f, "unset key\n");
                        fwrite($f, "set yrange [-100:100]\n");
                        fwrite($f, "set ytics 25\n");
                        fwrite($f, "set mytics 5\n");
                        fwrite($f, "set xzeroaxis linetype 1 linecolor rgb '#000000' linewidth 1\n");
                        fwrite($f, "set title \"Relay Run Time\"\n");
                        fwrite($f, "plot ");

                        for ($z = 0; $z < count($relay_name); $z++) {
                            $line= $z+1;
                            $lsvalue = $z+5;
                            fwrite($f, "\"/var/tmp/relay.log\" u 1:7 index 0 title \"$relay_name[$z]\" w impulses ls $lsvalue axes x1y1");
                            if ($z < count($relay_name)-1) fwrite($f, ", ");
                        }
                        fwrite($f, "\n");
                        fwrite($f, "unset multiplot\n");

                        fclose($f);
                        $cmd = "gnuplot $cus_graph";
                        exec($cmd);
                        unlink($cus_graph);
                        unlink('/var/tmp/sensor-t.log');
                        unlink('/var/tmp/sensor-ht.log');
                        unlink('/var/tmp/sensor-co2.log');
                        unlink('/var/tmp/sensor-press.log');
                        unlink('/var/tmp/relay.log');

                        echo '<div style="width: 100%; text-align: center; padding: 1em 0 3em 0;"><img src=image.php?';
                        echo 'graphtype=custom-combined';
                        echo '&id=' , $id2;
                        echo '&sensornumber=0>';
                        echo '</div>';

                    } else if ($_POST['custom_type'] == 'Separate') {
                        
                        for ($n = 0; $n < count($sensor_t_id); $n++) {
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
                                fwrite($f, "\"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[0]\" w impulses ls 4 axes x1y1, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[1]\" w impulses ls 5 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[2]\" w impulses ls 6 axes x1y1, ");
                                fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[3]\" w impulses ls 7 axes x1y1, ");
                                fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[4]\" w impulses ls 8 axes x1y1, ");
                                fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[5]\" w impulses ls 9 axes x1y1, ");
                                fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[6]\" w impulses ls 10 axes x1y1, ");
                                fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[7]\" w impulses ls 11 axes x1y1");

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
                            if ($n != count($sensor_ht_id) || ($n == count($sensor_ht_id) && array_sum($sensor_co2_graph))) { echo '<hr class="fade"/>'; }
                        }

                        for ($n = 0; $n < count($sensor_ht_id); $n++) {
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
                                fwrite($f, "\"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[0]\" w impulses ls 4 axes x1y1, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[1]\" w impulses ls 5 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[2]\" w impulses ls 6 axes x1y1, ");
                                fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[3]\" w impulses ls 7 axes x1y1, ");
                                fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[4]\" w impulses ls 8 axes x1y1, ");
                                fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[5]\" w impulses ls 9 axes x1y1, ");
                                fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[6]\" w impulses ls 10 axes x1y1, ");
                                fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[7]\" w impulses ls 11 axes x1y1");

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
                            if ($n != count($sensor_ht_id) || ($n == count($sensor_ht_id) && array_sum($sensor_co2_graph))) { echo '<hr class="fade"/>'; }
                        }

                        for ($n = 0; $n < count($sensor_co2_id); $n++) {
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
                                fwrite($f, "set ytics 10\n");
                                fwrite($f, "set y2range [0:5000]\n");
                                fwrite($f, "set y2tics 500\n");
                                fwrite($f, "set my2tics 5\n");
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
                                fwrite($f, "plot \"<awk '\\$8 == $n' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"CO_2\" w lp ls 1 axes x1y2, ");
                                fwrite($f, "\"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[0]\" w impulses ls 4 axes x1y1, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[1]\" w impulses ls 5 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[2]\" w impulses ls 6 axes x1y1, ");
                                fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[3]\" w impulses ls 7 axes x1y1, ");
                                fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[4]\" w impulses ls 8 axes x1y1, ");
                                fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[5]\" w impulses ls 9 axes x1y1, ");
                                fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[6]\" w impulses ls 10 axes x1y1, ");
                                fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[7]\" w impulses ls 11 axes x1y1\n");

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
                            if ($n != count($sensor_co2_id)) { echo '<hr class="fade"/>'; }
                        }

                        for ($n = 0; $n < count($sensor_press_id); $n++) {
                            if ($sensor_press_graph[$n] == 1) {

                                $cus_graph = "/var/tmp/plot-cus-press-separate-$n.gnuplot";
                                $f = fopen($cus_graph, "w");

                                fwrite($f, "set terminal png size $graph_width,490\n");
                                fwrite($f, "set xdata time\n");
                                fwrite($f, "set timefmt \"%Y %m %d %H %M %S\"\n");
                                fwrite($f, "set output \"$images/graph-press-custom-separate-$id2-$n.png\"\n");
                                fwrite($f, "set xrange [\"$yearb $monb $dayb $hourb $minb 00\":\"$yeare $mone $daye $houre $mine 00\"]\n");
                                fwrite($f, "set format x \"%H:%M\\n%m/%d\"\n");
                                fwrite($f, "set yrange [97000:99000]\n");
                                fwrite($f, "set y2range [0:35]\n");
                                fwrite($f, "set mytics 4\n");
                                fwrite($f, "set my2tics 10\n");
                                fwrite($f, "set ytics 200\n");
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
                                fwrite($f, "set title \"Sensor $n: $sensor_press_name[$n]: $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"\n");
                                fwrite($f, "plot \"<awk '\\$10 == $n' /var/tmp/sensor-press.log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"T\" w lp ls 2 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, ");
                                fwrite($f, "\"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[0]\" w impulses ls 4 axes x1y1, ");
                                fwrite($f, "\"\" using 1:8 index 0 title \"$relay_name[1]\" w impulses ls 5 axes x1y1, ");
                                fwrite($f, "\"\" using 1:9 index 0 title \"$relay_name[2]\" w impulses ls 6 axes x1y1, ");
                                fwrite($f, "\"\" using 1:10 index 0 title \"$relay_name[3]\" w impulses ls 7 axes x1y1, ");
                                fwrite($f, "\"\" using 1:11 index 0 title \"$relay_name[4]\" w impulses ls 8 axes x1y1, ");
                                fwrite($f, "\"\" using 1:12 index 0 title \"$relay_name[5]\" w impulses ls 9 axes x1y1, ");
                                fwrite($f, "\"\" using 1:13 index 0 title \"$relay_name[6]\" w impulses ls 10 axes x1y1, ");
                                fwrite($f, "\"\" using 1:14 index 0 title \"$relay_name[7]\" w impulses ls 11 axes x1y1");

                                fclose($f);
                                $cmd = "gnuplot $cus_graph";
                                exec($cmd);
                                unlink($cus_graph);

                                echo '<div style="width: 100%; text-align: center; padding: 1em 0 3em 0;"><img src=image.php?';
                                echo 'graphtype=custom-separate';
                                echo '&sensortype=press';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                            if ($n != count($sensor_press_id) || $n == count($sensor_press_id)) {
                                echo '<hr class="fade"/>'; }
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
                echo '<div class="error">Error: ' . $camera_error . '</div>';
            }
            ?>

            <form action="?tab=camera<?php
            if (isset($_GET['page'])) {
                echo '&page=' , $_GET['page'];
            }
            if (isset($_GET['r'])) {
                echo '&r=' , $_GET['r'];
            } ?>" method="POST">

            <div style="float: left; padding-top: 0.5em;">
                <div style="float: left; padding: 0 1.5em 1em 0.5em;">
                    <div style="text-align: center; padding-bottom: 0.2em;">Auto Refresh</div>
                    <div style="text-align: center;"><?php
                        if (isset($_GET['r']) && $_GET['r'] == 1) {
                            echo '<a href="?tab=camera">OFF</a> | <span class="on">ON</span>';
                        } else {
                            echo '<span class="off">OFF</span> | <a href="?tab=camera&r=1">ON</a>';
                        }
                    ?>
                    </div>
                </div>
                <div style="float: left; padding: 0 2em 1em 0.5em;">
                    <div style="float: left; padding-right: 0.1em;">
                        <input type="submit" name="Refresh" value="Refresh&#10;Page" title="Refresh page">
                    </div>
                </div>
            </div>

            <div>
                <div style="float: left; padding: 1em 1.5em;">
                    <button name="CaptureStill" type="submit" value="">Capture Still</button>
                </div>

                <div style="float: left; padding: 1em 1.5em;">
                    <div>
                        <?php
                        if (!file_exists($lock_mjpg_streamer)) {
                            echo '<button name="start-stream" type="submit" value="">Start</button>';
                        } else {
                            echo '<button name="stop-stream" type="submit" value="">Stop</button>';
                        }
                        ?> Video Stream <?php
                        if (!file_exists($lock_mjpg_streamer)) {
                            echo '(<span class="off">OFF</span>)';
                        } else {
                            echo '(<span class="on">ON</span>)';
                        }
                        ?>
                    </div>
                </div>

                <div style="float: left; padding: 1em 1.5em;">
                    <div>
                        <?php
                        if (!file_exists($lock_timelapse)) {
                            echo '<button name="start-timelapse" type="submit" value="">Start</button>';
                        } else {
                            echo '<button name="stop-timelapse" type="submit" value="">Stop</button>';
                        }
                        ?> Time-lapse <?php
                        if (!file_exists($lock_timelapse)) {
                            echo '(<span class="off">OFF</span>)';
                        } else {
                            echo '(<span class="on">ON</span>)';
                        }
                        ?>
                    </div>
                    <div style="padding: 0.65em 0.5em 0 0.5em;">Duration: <input style="width: 4em;" type="number" value="60" max="99999" min="1" name="timelapse_duration"> min</div>
                    <div style="padding: 0.65em 0.5em 0 0.5em;">Run time: <input style="width: 4em;" type="number" value="600" max="99999" min="1" name="timelapse_runtime"> min</div>
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
                echo '<div class="error">Error: ' . $data_error . '</div>';
            }
            ?>

            <div style="padding: 10px 0 0 15px;">
                <div style="padding-bottom: 15px;">
                    <form action="?tab=data<?php
                        if (isset($_GET['page'])) {
                            echo '&page=' , $_GET['page'];
                        } ?>" method="POST">
                        Lines: <input type="text" maxlength=8 size=8 name="Lines" />
                        <input type="submit" name="TSensor" value="T">
                        <input type="submit" name="HTSensor" value="HT">
                        <input type="submit" name="Co2Sensor" value="CO2">
                        <input type="submit" name="PressSensor" value="Press">
                        <input type="submit" name="Relay" value="Relay">
                        <input type="submit" name="Login" value="Login">
                        <input type="submit" name="Daemon" value="Daemon">
                        <input type="submit" name="Users" value="User Database">
                        <input type="submit" name="Database" value="Mycodo Database">
                        <input type="submit" name="Update" value="Update Log">
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

                            echo 'Year Mo Day Hour Min Sec CO<sub>2</sub> Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            unlink($log);
                        }

                        if(isset($_POST['PressSensor'])) {
                            concatenate_logs('press');
                            $log = '/var/tmp/sensor-press.log';

                            echo 'Year Mo Day Hour Min Sec Tc Press Alt Sensor<br> <br>';
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
                            echo exec('file ' . $user_db); 
                            echo '<br>&nbsp;<br>User Email Password_Hash<br> <br>';
                            $db = new SQLite3($user_db);
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
                        if(isset($_POST['Update'])) {
                            $log = '/var/www/mycodo/log/update.log';

                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                        }
                        if(isset($_POST['Database'])) {
                            echo exec('file ' . $mycodo_db); 
                            echo '<br>&nbsp;<br><pre>';
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
                echo '<div class="error">' . $settings_error . '</div>';
            }
            ?>

            <?php if ($this->feedback) echo $this->feedback; ?>

            <div class="advanced" style="padding-top: 1em;">
                <form action="?tab=settings" method="POST">


                <div style="margin: 0 0.5em 1em 0.5em; padding: 0 0.5em;">
                    <input style="width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddRelaysNumber" title="Add Sensors"/> <input type="submit" name="AddRelays" value="Add"> Relays
                </div>

                
                <div style="clear: both"></div>

                <?php
                if (count($relay_id) > 0) {
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
                            <td align=center class="table-header">Startup<br>State</td>
                            <td align=center class="table-header"></td>
                        </tr>
                        <?php for ($i = 0; $i < count($relay_id); $i++) {
                            $read = "$gpio_path -g read $relay_pin[$i]";
                        ?>
                        <tr>
                            <td align=center>
                                <?php echo $i+1; ?>
                            </td>
                            <td>
                                <input style="width: 10em;" type="text" value="<?php echo $relay_name[$i]; ?>" maxlength=13 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i+1; ?>"/>
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
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $relay_pin[$i]; ?>" name="relay<?php echo $i; ?>pin" title="GPIO pin using BCM numbering, connected to relay <?php echo $i+1; ?>"/>
                            </td>
                            <td align=center>
                                <select style="width: 65px;" title="Does this relay activate with a LOW (0-volt) or HIGH (5-volt) signal?" name="relay<?php echo $i; ?>trigger">
                                    <option<?php
                                        if ($relay_trigger[$i] == 1) {
                                            echo ' selected="selected"';
                                        } ?> value="1">High</option>
                                    <option<?php
                                        if ($relay_trigger[$i] == 0) {
                                            echo ' selected="selected"';
                                        } ?> value="0">Low</option>
                                </select>
                            </td>
                            <td align=center>
                                <select style="width: 65px;" title="Should the relay be On or Off at startup?" name="relay<?php echo $i; ?>startstate">
                                    <option<?php
                                        if ($relay_start_state[$i] == 1) {
                                            echo ' selected="selected"';
                                        } ?> value="1">On</option>
                                    <option<?php
                                        if ($relay_start_state[$i] == 0) {
                                            echo ' selected="selected"';
                                        } ?> value="0">Off</option>
                                </select>
                            </td>
                            <td>
                                <input type="submit" name="Mod<?php echo $i; ?>Relay" value="Set"> <button type="submit" name="Delete<?php echo $i; ?>Relay" title="Delete">Delete</button>
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
                <div style="margin: 0 0.5em 1em 0.5em; padding: 0 0.5em;">
                    <input style="width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddTimersNumber" title="Add Sensors"/> <input type="submit" name="AddTimers" value="Add"> Timers
                </div>
                <div style="clear: both"></div>

                <?php
                if (count($timer_id) > 0) {
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
                        for ($i = 0; $i < count($timer_id); $i++) {
                        ?>
                        <tr>
                            <td align="center">
                                <?php echo $i+1; ?>
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
                                <input type="submit" name="ChangeTimer<?php echo $i; ?>" value="Set"> <button type="submit" name="Delete<?php echo $i; ?>Timer" title="Delete">Delete</button>
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
                <table>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            System Update
                        </td>
                    </tr>
                    <form action="?tab=settings" method="post">
                        <tr>
                        <td class="setting-text">
                            Check if there is an update avaialble for Mycodo 
                        </td>
                        <td class="setting-value">
                            <button name="UpdateCheck" type="submit" value="" title="Check if there is a newer version of Mycodo on github.">Check for Update</button>
                        </td>
                    </tr>
                    </form>
                    <form action="?tab=settings" method="post" onsubmit="return confirm('Confirm that you would like to begin the update process now. If not, click Cancel.')">
                    <tr>
                        <td class="setting-text">
                            Update Mycodo to the latest version on <a href="https://github.com/kizniche/Mycodo" target="_blank">github</a>
                        </td>
                        <td class="setting-value">
                            <button name="UpdateMycodo" type="submit" value="" title="Update the mycodo system to the latest version on github.">Update Mycodo</button>
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Daemon
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Stop Daemon
                        </td>
                        <td class="setting-value">
                            <button name="DaemonStop" type="submit" value="" title="Stop the mycodo daemon from running or kill a daemon that has had a segmentation fault.">Stop Daemon</button>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Start Daemon
                        </td>
                        <td class="setting-value">
                            <button name="DaemonStart" type="submit" value="" title="Start the mycodo daemon in normal mode (if no other instance is currently running).">Start Daemon</button>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Restart Daemon
                        </td>
                        <td class="setting-value">
                            <button name="DaemonRestart" type="submit" value="" title="Stop and start the mycodo daemon in normal mode.">Restart Daemon</button>
                        </td>
                    </tr>
                    </form>
                    <form action="?tab=settings" method="post" onsubmit="return confirm('Confirm that you would like to run the daemon in debug mode. If not, click Cancel.')">
                    <tr>
                        <td class="setting-text">
                            Restart Daemon in Debug Mode (use with caution, produces large logs)
                        </td>
                        <td class="setting-value">
                            <button name="DaemonDebug" type="submit" value="" title="Stop and start the mycodo daemon in debug mode (verbose log messages, temporary files are not deleted). You should probably not enable this unless you know what you're doing.">Restart Daemon in Debug Mode</button>
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Web Interface
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Display Debugging Information
                        </td>
                        <td class="setting-value">
                            <input type="hidden" name="debug" value="0" /><input type="checkbox" id="debug" name="debug" value="1"<?php if (isset($_COOKIE['debug'])) if ($_COOKIE['debug'] == True) echo ' checked'; ?> title="Display debugging information at the bottom of every page."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Automatic refresh rate (seconds)
                        </td>
                        <td class="setting-value">
                            <input style="width: 4em;" type="number" min="1" max="999999" value="<?php echo $refresh_time; ?>" maxlength=4 size=1 name="refresh_time" title="The number of seconds between automatic page refreshing."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <button name="ChangeInterface" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Camera: Still Capture
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Relay to activate during capture (0 to disable)
                        </td>
                        <td class="setting-value">
                    <input style="width: 4em;" type="number" min="0" max="30" value="<?php echo $still_relay; ?>" maxlength=4 size=1 name="Still_Relay" title="A relay can be set to activate during the still image capture."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Add timestamp to image
                        </td>
                        <td class="setting-value">
                    <input type="hidden" name="Still_Timestamp" value="0" /><input type="checkbox" id="Still_Timestamp" name="Still_Timestamp" value="1"<?php if ($still_timestamp) echo ' checked'; ?> title="Add a timestamp to the captured image."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Always display last still image on Camera tab
                        </td>
                        <td class="setting-value">
                    <input type="hidden" name="Still_DisplayLast" value="0" /><input type="checkbox" id="Still_DisplayLast" name="Still_DisplayLast" value="1"<?php if ($still_display_last) echo ' checked'; ?> title="Always display the last image acquired or only after clicking 'Capture Still'."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Command to execute before capture
                        </td>
                        <td class="setting-value">
                    <input style="width: 18em;" type="text" value="<?php echo $still_cmd_pre; ?>" maxlength=100 name="Still_Cmd_Pre" title="Command to be executed before the image capture. If your command is longer than 100 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Command to execute after capture
                        </td>
                        <td class="setting-value">
                    <input style="width: 18em;" type="text" value="<?php echo $still_cmd_post; ?>" maxlength=100 name="Still_Cmd_Post" title="Command to be executed after the image capture. If your command is longer than 100 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Extra parameters for camera (raspistill)
                        </td>
                        <td class="setting-value">
                    <input style="width: 18em;" type="text" value="<?php echo $still_extra_parameters; ?>" maxlength=200 name="Still_Extra_Parameters"/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <button name="ChangeStill" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Camera: Video Stream
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Relay to activate during capture (0 to disable)
                        </td>
                        <td class="setting-value">
                            <input style="width: 4em;" type="number" min="0" max="30" value="<?php echo $stream_relay; ?>" maxlength=4 size=1 name="Stream_Relay" title="A relay can be set to activate during the video stream."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Command to execute before starting stream
                        </td>
                        <td class="setting-value">
                    <input style="width: 18em;" type="text" value="<?php echo $stream_cmd_pre; ?>" maxlength=100 name="Stream_Cmd_Pre" title="Command to be executed before the stream has started. If your command is longer than 100 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Command to execute after stopping stream
                        </td>
                        <td class="setting-value">
                    <input style="width: 18em;" type="text" value="<?php echo $stream_cmd_post; ?>" maxlength=100 name="Stream_Cmd_Post" title="Command to be executed after the stream has been stopped. If your command is longer than 100 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Extra parameters for camera (raspistill)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $stream_extra_parameters; ?>" maxlength=200 name="Stream_Extra_Parameters" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <button name="ChangeStream" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Camera: Time-lapse
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Relay to activate during capture (0 to disable)
                        </td>
                        <td class="setting-value">
                            <input style="width: 4em;" type="number" min="0" max="30" value="<?php echo $timelapse_relay; ?>" maxlength=4 size=1 name="Timelapse_Relay" title="A relay can be set to activate during a timelapse capture."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Photo save path
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $timelapse_path; ?>" maxlength=50 name="Timelapse_Path" title=""/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Photo filename prefix
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $timelapse_prefix; ?>" maxlength=20 name="Timelapse_Prefix" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Time-lapse start time in filename
                        </td>
                        <td class="setting-value">
                            <input type="hidden" name="Timelapse_Timestamp" value="0" /><input type="checkbox" id="" name="Timelapse_Timestamp" value="1"<?php if ($timelapse_timestamp) echo ' checked'; ?> title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Always display last time-lapse image on Camera tab
                        </td>
                        <td class="setting-value">
                            <input type="hidden" name="Timelapse_DisplayLast" value="0" /><input type="checkbox" id="Timelapse_DisplayLast" name="Timelapse_DisplayLast" value="1"<?php if ($timelapse_display_last) echo ' checked'; ?> title="Always display the last timelapse image or only while a timelapse is running."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Command to execute before capture
                        </td>
                        <td class="setting-value">
                    <input style="width: 18em;" type="text" value="<?php echo $timelapse_cmd_pre; ?>" maxlength=100 name="Timelapse_Cmd_Pre" title="Command to be executed before capture. If your command is longer than 100 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Command to execute after capture
                        </td>
                        <td class="setting-value">
                    <input style="width: 18em;" type="text" value="<?php echo $timelapse_cmd_post; ?>" maxlength=100 name="Timelapse_Cmd_Post" title="Command to be executed after capture. If your command is longer than 100 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."/> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Extra parameters for camera (raspistill)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $timelapse_extra_parameters; ?>" maxlength=200 name="Timelapse_Extra_Parameters" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Enable experimental auto-exposure mode (currently not enabled)
                        </td>
                        <td class="setting-value">
                            <input type="hidden" name="" value="0" /><input type="checkbox" id="" name="timelapse-auto-exp" value="1"<?php if (1) echo ' checked'; ?> title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-value">
                            <?php
                    if ($timelapse_timestamp) {
                        $timelapse_tstamp = substr(`date +"%Y%m%d%H%M%S"`, 0, -1);
                        echo 'Output file series: ' , $timelapse_path , '/' , $timelapse_prefix , $timelapse_tstamp , '-00001.jpg';
                    } else {
                        echo 'Output file series: ' , $timelapse_path , '/' , $timelapse_prefix , '00001.jpg';
                    }
                     ?>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <button name="ChangeTimelapse" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Email Notification
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            SMTP Host
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="text" value="<?php echo $smtp_host; ?>" maxlength=30 size=20 name="smtp_host" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            SMTP Port
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="number" value="<?php echo $smtp_port; ?>" maxlength=30 size=20 name="smtp_port" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            User
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="text" value="<?php echo $smtp_user; ?>" maxlength=30 size=20 name="smtp_user" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Password
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="password" value="<?php echo $smtp_pass; ?>" maxlength=30 size=20 name="smtp_pass" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            From
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="text" value="<?php echo $smtp_email_from; ?>" maxlength=30 size=20 name="smtp_email_from" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            To
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="text" value="<?php echo $smtp_email_to; ?>" maxlength=30 size=20 name="smtp_email_to" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <input type="submit" name="ChangeNotify" value="Save">
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Add User
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Username (only letters and numbers, 2 to 64 characters)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" pattern="[a-zA-Z0-9]{2,64}" required name="user_name" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Email
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="email" name="user_email" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Password (min. 6 characters)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" class="login_input" type="password" name="user_password_new" pattern=".{6,}" required autocomplete="off" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Repeat password
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" class="login_input" type="password" name="user_password_repeat" pattern=".{6,}" required autocomplete="off" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <input type="submit" name="register" value="Add User" />
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Change Password
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Username
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" pattern="[a-zA-Z0-9]{2,64}" required name="user_name" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Password (min. 6 characters)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" class="login_input" type="password" name="new_password" pattern=".{6,}" required autocomplete="off" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Repeat New password
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" class="login_input" type="password" name="new_password_repeat" pattern=".{6,}" required autocomplete="off" /> <label for="login_input_password_repeat">
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <input type="submit" name="changepassword" value="Change Password" />
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Change Email
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Username
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" pattern="[a-zA-Z0-9]{2,64}" required name="user_name" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            New Email
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" class="login_input" type="email" name="user_email" required />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <input type="submit" name="changeemail" value="Change Email" />
                        </td>
                    </tr>
                    </form>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-title">
                            Delete User
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Username
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" pattern="[a-zA-Z0-9]{2,64}" required name="user_name" />
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-save">
                            <input type="submit" name="deleteuser" value="Delete User" />
                        </td>
                    </tr>
                    </form>
                </table>
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
                    $grand_total = 0.0;
                    foreach($profile as $array => $next) {
                        foreach($next as $key => $value) {
                            $grand_total += $value;
                        }
                    }
                    $step_total = 0.0;
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
                        <td>
                            Percentage
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
                            $pre = $step_total;
                            $step_total += $value;
                            echo '
                            <tr style="border-bottom:1pt solid black;">
                                <td style="">
                                    ' , $key , '
                                </td>
                                <td>
                                    ' , number_format($value, 6) , '
                                </td>
                                <td>
                                    ' , number_format($pre, 6) , '
                                </td>
                                <td>
                                    ' , number_format($step_total, 6) , '
                                </td>
                                <td>
                                    ' , number_format($value/$grand_total*100, 2) , '%
                                </td>
                            </tr>';
                        }
                    }
                    echo '
                    <tr>
                        <td colspan="4" style="font-weight: bold; font-size: 1.3em;">
                            Total: ' , number_format($grand_total, 10) , '
                        </td>
                    </tr>
                    </table>
                    <p style="padding: 2em 0 1em 0; font-weight: bold;">Raw Profile<p>
                    <pre>' , print_r($profile) , '</pre><br>';
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
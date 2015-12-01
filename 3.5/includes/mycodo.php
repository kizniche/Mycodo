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

$version = "3.5.92";

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
$note_db = $install_path . "/config/notes.db";
$update_check = $install_path . "/.updatecheck";

$daemon_log = $install_path . "/log/daemon.log";
$auth_log = $install_path . "/log/auth.log";
$sensor_t_log = $install_path . "/log/sensor-t.log";
$sensor_ht_log = $install_path . "/log/sensor-ht.log";
$sensor_co2_log = $install_path . "/log/sensor-co2.log";
$sensor_press_log = $install_path . "/log/sensor-press.log";
$relay_log = $install_path . "/log/relay.log";

$sensor_t_changes_log = $install_path . "/log/sensor-t-changes.log";
$sensor_ht_changes_log = $install_path . "/log/sensor-ht-changes.log";
$sensor_co2_changes_log = $install_path . "/log/sensor-co2-changes.log";
$sensor_press_changes_log = $install_path . "/log/sensor-press-changes.log";
$relay_changes_log = $install_path . "/log/relay-changes.log";
$timer_changes_log = $install_path . "/log/timer-changes.log";

$images = $install_path . "/images";
$lock_daemon = $lock_path . "/mycodo/daemon.lock";
$lock_raspistill = $lock_path . "/mycodo_raspistill";
$lock_mjpg_streamer = $lock_path . "/mycodo_mjpg_streamer";
$lock_mjpg_streamer_relay = $lock_path . "/mycodo-stream-light";
$lock_timelapse = $lock_path . "/mycodo_time_lapse";
$lock_timelapse_light = $lock_path . "/mycodo-timelapse-light";

$logged_in_user = $_SESSION['user_name'];

if (!file_exists($mycodo_db)) exit("Mycodo database does not exist. Run 'setup-database.py -i' to create required database.");

require($install_path . "/includes/database.php"); // Initial SQL database load to variables
require($install_path . "/includes/functions.php"); // Mycodo functions

// Check is there is an update (check at minimum every 24 hours)
if (!file_exists($update_check) || time()-filemtime($update_check) > 24 * 3600) {
    update_check($install_path, $update_check);
}

// Output an error if the user guest attempts to submit certain forms
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    if (($current_user_restriction == 'guest' && !isset($_POST['Graph']) && !isset($_POST['login']) && !isset($_POST['edituser'])) &&
        (isset($_POST['Login']) ||
        isset($_POST['Users']) ||
        isset($_POST['Database']) ||
        isset($_POST['DeleteBackup']) ||
        isset($_POST['RestoreBackup']) ||
        isset($_POST['UpdateCheck']) ||
        isset($_POST['UpdateMycodo']) ||
        isset($_POST['DaemonStop']) ||
        isset($_POST['DaemonStart']) ||
        isset($_POST['DaemonRestart']) ||
        isset($_POST['DaemonDebug']))) {
        $output_error = 'guest';
    } else if ($current_user_restriction != 'guest') {
        // Only non-guest users may perform these actions
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
    <title>Mycodo <?php echo $version; ?> - <?php echo $_SERVER['SERVER_NAME']; ?></title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex">
    <link rel="icon" type="image/png" href="img/favicon.png">
    <link rel="stylesheet" href="css/fonts.css" type="text/css">
    <link rel="stylesheet" href="css/reset.css" type="text/css">
    <link rel="stylesheet" href="css/style.css" type="text/css">
    <script src="js/modernizr.js"></script>
    <script src="js/jquery-2.1.4.min.js"></script>
    <script src="js/highstock.js"></script>
    <!-- Order of dependencies before highcharts-export-clientside.js is important -->
    <script src="js/modules/exporting.js"></script>
    <script src="js/modules/canvas-tools.js"></script>
    <script src="js/modules/export-csv.js"></script>
    <script src="js/modules/jspdf.min.js"></script>
    <script src="js/modules/highcharts-export-clientside.js"></script>
    <?php
    if ($current_user_theme == 'light') {
        echo '<link rel="stylesheet" href="css/theme-light.css" type="text/css">';
    } else if ($current_user_theme == 'dark') {
        echo '<link rel="stylesheet" href="css/theme-dark.css" type="text/css">
        <script src="js/themes/dark-unica.js"></script>';
    }
    ?>
    <script type="text/javascript">
        function open_legend() {
            window.open("file.php?span=legend-small","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=250, height=300");
        }
        function open_legend_full() {
            window.open("file.php?span=legend-full","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=820, height=550");
        }
    </script>
    <script>
        function submitForm(action, target) {
            document.getElementById('DynamicGraphForm').action = action;
            document.getElementById('DynamicGraphForm').target = target;
            document.getElementById('DynamicGraphForm').submit();
        }
    </script>
    <?php
    if (isset($_POST['Generate_Graph'])) {
        require($install_path . "/includes/graph.php");
    }

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
    if ($output_error == 'guest') {
        echo '<span class="error">You cannot perform that task as a guest user</span>';
    }
    $output_error = NULL;
}
if (!file_exists($lock_daemon)) {
    $check_tentacle_pi = shell_exec('/usr/bin/python -c "import tentacle_pi" 2>&1');
    if ($check_tentacle_pi != '') {
        echo '
        <span class="error">
            Daemon unable to start without tentacle_pi installed. Install with:
            <br>1. sudo apt-get install i2c-tools libi2c-dev python-dev build-essential
            <br>2. git clone --recursive https://github.com/lexruee/tentacle_pi ~/tentacle_pi
            <br>3. cd ~/tentacle_pi
            <br>4. sudo python setup.py install
        </span>';
    }
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
                User: <?php echo $logged_in_user; ?>
            </div>
            <div>
                <a href="index.php?action=logout">Log Out</a>
            </div>
        </div>
    </div>
    <div class="header">
        <div style="float: left;">
            <div style="padding-bottom: 0.1em;"><?php
                if (file_exists($lock_daemon)) {
                    echo '<img style="height: 0.9em;" src="/mycodo/img/on.png" alt="On" title="On">';
                } else {
                    echo '<img style="height: 0.9em;" src="/mycodo/img/off.png" alt="Off" title="Off">';
                }
                ?> Daemon</div>
            <div style="padding-bottom: 0.1em;"><?php
                if (file_exists($lock_mjpg_streamer)) {
                    echo '<img style="height: 0.9em;" src="/mycodo/img/on.png" alt="On" title="On">';
                } else {
                    echo '<img style="height: 0.9em;" src="/mycodo/img/off.png" alt="Off" title="Off">';
                }
                ?> Stream</div>
            <div style="padding-bottom: 0.1em;"><?php
                if (file_exists($lock_timelapse)) { // Check if timelapse is running, delete lockfile if not
                    $timelapse_running = shell_exec("ps aux | grep [r]aspistill | grep -Eo 'timelapse'");
                    if ($timelapse_running == NULL) unlink($lock_timelapse);
                }

                if (file_exists($lock_timelapse)) {
                    echo '<img style="height: 0.9em;" src="/mycodo/img/on.png" alt="On" title="On">';
                } else {
                    echo '<img style="height: 0.9em;" src="/mycodo/img/off.png" alt="Off" title="Off">';
                }
                ?> Time-lapse</div>
        </div>
        <div style="float: left;">
            <div><?php
                if (isset($_GET['r'])) {
                    ?><div style="display:inline-block; vertical-align:top;"><img style="height: 0.9em;" src="/mycodo/img/on.png" alt="On" title="On">
                    </div>
                    <div style="display:inline-block; padding-left: 0.3em;">
                        <div>Refresh<br><span style="font-size: 0.7em">(<?php echo $_GET['tab']; ?>)</span></div>
                    </div><?php
                } else {
                    ?><img style="height: 0.9em;" src="/mycodo/img/off.png" alt="Off" title="Off"> Refresh<?php
                }
            ?></div>
        </div>
    </div>
    <div style="float: left; vertical-align:top; height: 4.5em; padding: 1em 0.8em 0 0.3em;">
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;">Time now: <?php echo $time_now; ?></div>
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;">Last read: <?php echo $time_last; ?></div>
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;"><?php echo `uptime | grep -ohe 'load average[s:][: ].*' `; ?></div>
        <div style="text-align: right; padding-top: 0.1em; font-size: 0.8em;"><?php
            echo 'CPU: <span title="' , number_format((float)$pi_temp_cpu_f, 1, '.', '') , '&deg;F">' , $pi_temp_cpu_c , '&deg;C</span>';
            echo ' GPU: <span title="' , number_format((float)$pi_temp_gpu_f, 1, '.', '') , '&deg;F">' , $pi_temp_gpu_c , '&deg;C</span>';
            ?></div>
    </div>
    <?php
    // Display brief Temp sensor and PID data in header
    for ($i = 0; $i < count($sensor_t_id); $i++) {
        if ($sensor_t_activated[$i] == 1) {
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'T' , $i+1 , ': ' , $sensor_t_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <?php
                        if (isset($t_temp_f[$i])) {
                        ?>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php
                            echo 'Now<br><span title="' , number_format((float)$t_temp_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$t_temp_c[$i], 1, '.', '') , '&deg;C</span>';
                        ?></td>
                        <td style="font-size: 0.8em;"><?php
                            echo 'Set<br><span title="' , number_format((float)$settemp_t_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$pid_t_temp_set[$i], 1, '.', '') , '&deg;C</span>';
                        ?></td>
                        <?php
                        } else {
                            echo '<td>Wait for<br>1st read</td>';
                        } ?>
                    </tr>
                </table>
            </div>
            <?php
        }
    }
    // Display brief Temp/Hum sensor and PID data in header
    for ($i = 0; $i < count($sensor_ht_id); $i++) {
        if ($sensor_ht_activated[$i] == 1) { 
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'HT' , $i+1 , ': ' , $sensor_ht_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <?php
                        if (isset($ht_temp_f[$i])) {
                        ?>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php
                            echo 'Now<br><span title="' , number_format((float)$ht_temp_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$ht_temp_c[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , number_format((float)$hum[$i], 1, '.', '') , '%';
                        ?></td>
                        <td style="font-size: 0.8em;"><?php
                            echo 'Set<br><span title="' , number_format((float)$settemp_ht_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$pid_ht_temp_set[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , number_format((float)$pid_ht_hum_set[$i], 1, '.', '') , '%';
                        ?></td>
                        <?php
                        } else {
                            echo '<td>Wait for<br>1st read</td>';
                        } ?>
                    </tr>
                </table>
            </div>
            <?php
        }
    }
    // Display brief CO2 sensor and PID data in header
    for ($i = 0; $i < count($sensor_co2_id); $i++) {
        if ($sensor_co2_activated[$i] == 1) {
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'CO<sub>2</sub>' , $i+1 , ': ' , $sensor_co2_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <?php
                        if (isset($co2[$i])) {
                        ?>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php echo 'Now<br>' , $co2[$i]; ?></td>
                        <td style="font-size: 0.8em;"><?php echo 'Set<br>' , $pid_co2_set[$i]; ?></td>
                        <?php
                        } else {
                            echo '<td>Wait for<br>1st read</td>';
                        } ?>
                    </tr>
                </table>
            </div>
            <?php
        }
    }
    // Display brief Press sensor and PID data in header
    for ($i = 0; $i < count($sensor_press_id); $i++) {
        if ($sensor_press_activated[$i] == 1) {
            ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo 'P' , $i+1 , ': ' , $sensor_press_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <?php
                        if (isset($press_temp_f[$i])) {
                        ?>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php
                            echo 'Now<br><span title="' , number_format((float)$press_temp_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$press_temp_c[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , (int)$press[$i] , ' Pa';
                        ?></td>
                        <td style="font-size: 0.8em;"><?php
                            echo 'Set<br><span title="' , number_format((float)$settemp_press_f[$i], 1, '.', '') , '&deg;F">' , number_format((float)$pid_press_temp_set[$i], 1, '.', '') , '&deg;C</span>';
                            echo '<br>' , (int)$pid_press_press_set[$i] , ' Pa';
                        ?></td>
                        <?php
                        } else {
                            echo '<td>Wait for<br>1st read</td>';
                        } ?>
                    </tr>
                </table>
            </div>
            <?php
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
                echo '<div class="error">' . $graph_error . '</div>';
            }

            if (isset($_POST['Generate_Graph_Span'])) $dyn_time_span = $_POST['Generate_Graph_Span'];
            else $dyn_time_span = "1 Week";
            if (isset($_POST['Generate_Graph_Type'])) $dyn_type = $_POST['Generate_Graph_Type'];
            else $dyn_type = 'all';
            ?>

            <div>
                <div style="padding-top: 0.5em;">
                    <div style="float: left; padding: 0 2em 1em 0.5em;">
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
                    <form action="?tab=graph<?php if (isset($_GET['r'])) echo '&r=' , $_GET['r']; ?>" method="POST">
                    <div style="float: left; padding: 0 2em 1em 0;">
                        <div style="float: left; padding-right: 0.1em;">
                            <button name="Refresh" type="submit" value="">Refresh<br>Page</button>
                        </div>
                    </div>
                    <div style="float: left; padding: 0 2em 1em 0">
                        <div style="float: left; padding-right: 0.5em;">
                            <select style="height: 2.8em;" name="graph_type">
                                <option value="separate" <?php if ($graph_time_span != 'default' && $graph_type == 'separate') echo 'selected="selected"'; ?>>Separate</option>
                                <option value="combined" <?php if ($graph_time_span != 'default' && $graph_type == 'combined') echo 'selected="selected"'; ?>>Combined</option>
                            </select>
                        </div>
                        <div style="float: left; padding-right: 0.5em;">
                            <select style="height: 2.8em;" name="graph_time_span">
                                <option value="default" <?php if ($graph_time_span == 'default') echo 'selected="selected"'; ?>>Day/Week</option>
                                <option value="1h" <?php if ($graph_time_span == '1h') echo 'selected="selected"'; ?>>1 Hour</option>
                                <option value="3h" <?php if ($graph_time_span == '3h') echo 'selected="selected"'; ?>>3 Hours</option>
                                <option value="6h" <?php if ($graph_time_span == '6h') echo 'selected="selected"'; ?>>6 Hours</option>
                                <option value="12h" <?php if ($graph_time_span == '12h') echo 'selected="selected"'; ?>>12 Hours</option>
                                <option value="1d" <?php if ($graph_time_span == '1d') echo 'selected="selected"'; ?>>1 Day</option>
                                <option value="3d" <?php if ($graph_time_span == '3d') echo 'selected="selected"'; ?>>3 Days</option>
                                <option value="1w" <?php if ($graph_time_span == '1w') echo 'selected="selected"'; ?>>1 Week</option>
                                <option value="2w" <?php if ($graph_time_span == '2w') echo 'selected="selected"'; ?>>2 Weeks</option>
                                <option value="1m" <?php if ($graph_time_span == '1m') echo 'selected="selected"'; ?>>1 Month</option>
                                <option value="3m" <?php if ($graph_time_span == '3m') echo 'selected="selected"'; ?>>3 Months</option>
                                <option value="6m" <?php if ($graph_time_span == '6m') echo 'selected="selected"'; ?>>6 Months</option>
                            </select>
                        </div>
                        <div style="float: left; padding-right: 1em;">
                            <button type="submit" name="Graph" value="Generate Graph" title="Generate a server-side graph and display them as PNG images.">Static<br>Graph</button>
                        </div>
                    </div>
                    </form>

                    <div style="float: left; padding: 0 0 1em 0;">
                        <form style="float:left;" id="DynamicGraphForm" action="?tab=graph<?php if (isset($_GET['r'])) echo '&r=' , $_GET['r']; ?>" method="POST">
                        <div style="float:left; padding-right: 0.5em;">
                            <select style="height: 2.8em;" name="Generate_Graph_Span">
                                <option value="1 Hour" <?php if ($dyn_time_span == '1 Hour') echo 'selected="selected"'; ?>>1 Hour</option>
                                <option value="3 Hours" <?php if ($dyn_time_span == '3 Hours') echo 'selected="selected"'; ?>>3 Hours</option>
                                <option value="6 Hours" <?php if ($dyn_time_span == '6 Hours') echo 'selected="selected"'; ?>>6 Hours</option>
                                <option value="12 Hours" <?php if ($dyn_time_span == '12 Hours') echo 'selected="selected"'; ?>>12 Hours</option>
                                <option value="1 Day" <?php if ($dyn_time_span == '1 Day') echo 'selected="selected"'; ?>>1 Day</option>
                                <option value="3 Days" <?php if ($dyn_time_span == '3 Days') echo 'selected="selected"'; ?>>3 Days</option>
                                <option value="1 Week" <?php if ($dyn_time_span == '1 Week') echo 'selected="selected"'; ?>>1 Week</option>
                                <option value="2 Weeks" <?php if ($dyn_time_span == '2 Weeks') echo 'selected="selected"'; ?>>2 Weeks</option>
                                <option value="1 Month" <?php if ($dyn_time_span == '1 Month') echo 'selected="selected"'; ?>>1 Month</option>
                                <option value="3 Months" <?php if ($dyn_time_span == '3 Months') echo 'selected="selected"'; ?>>3 Months</option>
                                <option value="6 Months" <?php if ($dyn_time_span == '6 Months') echo 'selected="selected"'; ?>>6 Months</option>
                                <option value="1 Year" <?php if ($dyn_time_span == '1 Year') echo 'selected="selected"'; ?>>1 Year</option>
                                <option value="all" <?php if ($dyn_time_span == 'all') echo 'selected="selected"'; ?>>All Time</option>
                            </select>
                        </div>
                        <div style="float:left; padding-right: 0.5em;">
                            <select style="height: 2.8em;" name="Generate_Graph_Type">
                                <option value="all" <?php if ($dyn_type == 'all') echo 'selected="selected"'; ?>>All Sensors</option>
                                <option value="t" <?php if ($dyn_type == 't') echo 'selected="selected"'; ?>>Temperature</option>
                                <option value="ht" <?php if ($dyn_type == 'ht') echo 'selected="selected"'; ?>>Humidity</option>
                                <option value="co2" <?php if ($dyn_type == 'co2') echo 'selected="selected"'; ?>>CO2</option>
                                <option value="press" <?php if ($dyn_type == 'press') echo 'selected="selected"'; ?>>Pressure</option>
                            </select>
                        </div>
                        <div style="float:left; padding-right: 0.5em;">
                            <button type="submit" onclick="submitForm('?tab=graph<?php if (isset($_GET['r'])) echo '&r=' , $_GET['r']; ?>','_self')" name="Generate_Graph" value="all" title="Generate a client-side graph that will render in the browser. Warning: The more data you choose to use, the longer it will take to process. Choosing 'All Time' or 'All Sensors' may take a significant amount of time to process.">Dynamic<br>Graph</button>
                        </div>
                        <div style="float:left;">
                            <button type="submit" onclick="submitForm('file.php?span=graph-pop&theme=<?php echo $current_user_theme; ?>','_blank')" name="Generate_Graph" value="all" title="Same as 'Dynamic Graph' but the graph will load in a new window.">Pop<br>Out</button>
                        </div>
                        </form>
                    </div>
                </div>
                
                <div style="clear: both;"></div>

                <?php
                if (isset($_POST['Generate_Graph'])) {
                    echo '<div style="padding: 1.5em 0 1.5em 0; text-align:center;">';
                    echo '<div id="container" style="width: 100%; height: 50em;"></div>';
                    echo '</div>';
                }
                ?>

                <div style="clear: both;"></div>

                <div>
                    <?php
                    // Generate and display Main tab graphs
                    if ((isset($sensor_t_graph) && array_sum($sensor_t_graph)) ||
                        (isset($sensor_ht_graph) && array_sum($sensor_ht_graph)) ||
                        (isset($sensor_co2_graph) && array_sum($sensor_co2_graph)) ||
                        (isset($sensor_press_graph) && array_sum($sensor_press_graph))) {

                        if (!isset($_POST['Generate_Graph']) && !isset($_POST['Generate_Graph_All'])) {
                            generate_graphs($mycodo_client, $graph_id, $graph_type, $graph_time_span, $sensor_t_graph, $sensor_ht_graph, $sensor_co2_graph, $sensor_press_graph, $current_user_theme);
                        }
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
        </li>

        <li data-content="sensor" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'sensor') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($sensor_error)) {
                echo '<div class="error">' . $sensor_error . '</div>';
            }
            ?>

            <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <div style="float: left; padding: 0.5em 2em 1em 0.5em;">
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
                <div style="float: left; padding: 0.5em 2em 1em 0;">
                    <div style="float: left; padding-right: 0.1em;">
                        <button name="Refresh" type="submit" value="">Refresh<br>Page</button>
                    </div>
                </div>
            </form>

            <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <div style="float: left; margin: 0.5em 0.7em 0 0;">
                    <div style="float: left;">
                        <div>
                            <select style="height: 1.6em; width: 20em;" name="AddSensorDev">
                                <option value="RPi">Temperature: Raspberry Pi</option>
                                <option value="DS18B20">Temperature: DS18B20</option>
                                <option value="DHT11">Humidity/Temperature: DHT11</option>
                                <option value="DHT22">Humidity/Temperature: DHT22</option>
                                <option value="AM2302">Humidity/Temperature: AM2302</option>
                                <option value="AM2315">Humidity/Temperature: AM2315</option>
                                <option value="K30">Carbon Dioxide (CO2): K-30</option>
                                <option value="BMP">Pressure/Temperature: BMP085/BMP180</option>
                            </select>
                        </div>
                        <div style="padding: 0.1em 0 0 0.2em;">Sensor</div>
                    </div>
                    <div style="float: left; padding: 0 0.2em;">
                        <div>
                            <input style="width: 6em;" maxlength=12 size=10 name="AddSensorName" title="Name of the new sensor."/>
                        </div>
                        <div style="padding: 0.1em 0 0 0.2em;">Name</div>
                    </div>
                    <div style="float: left;">
                        <button type="submit" name="AddSensor" value="Add">Add<br>Sensor</button>
                    </div>
                </div>
            </form>
            
            <form action="?tab=sensor" method="POST">
                <div style="float:left; margin: 0.5em 0.7em;">
                    <div style="float:left; padding-right: 0.2em;">
                        <input style="height: 2.6em; width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddRelaysNumber" title="Add Sensors" required/>
                    </div>
                    <div style="float:left">
                        <button type="submit" name="AddRelays" value="Add">Add<br>Relays</button>
                    </div>
                </div>
            </form>

            <form action="?tab=sensor" method="POST">
                <div style="float:left; margin: 0.5em 0.7em;">
                    <div style="float:left; padding-right: 0.2em;">
                        <input style="height: 2.6em; width: 3em;" type="number" value="1" min="1" max="20" step="1" maxlength=2 name="AddTimersNumber" title="Add Sensors"  required/>
                    </div>
                    <div style="float:left">
                        <button type="submit" name="AddTimers" value="Add">Add<br>Timers</button>
                    </div>
                </div>
            </form>
                
            <div style="clear: both"></div>
            
            <?php
            if (count($relay_id) > 0) {
            ?>
                <div class="sensor-parent" style="margin-top: 2em;">
                    <form action="?tab=sensor" method="POST">
                    <table class="relays">
                        <tr>
                            <td class="table-header center middle">Relay</td>
                            <td class="table-header middle">Name</td>
                            <td colspan="2" class="table-header center" style="vertical-align: middle;">
                                On <img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On"> ~ Off <img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off"></td>
                            <td class="table-header center">Seconds<br>On</td>
                            <td class="table-header center">GPIO<br>Pin</td>
                            <td class="table-header center">Amps<br>Draw</td>
                            <td class="table-header center">Signal<br>ON</td>
                            <td class="table-header center">Startup<br>State</td>
                            <td class="table-header center"></td>
                        </tr>
                        <?php for ($i = 0; $i < count($relay_id); $i++) {
                            $read = "$gpio_path -g read $relay_pin[$i]";
                        ?>
                        <tr>
                            <td class="center">
                                <?php echo $i+1; ?>
                            </td>
                            <td>
                                <input style="width: 10em;" type="text" value="<?php echo $relay_name[$i]; ?>" maxlength=13 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i+1; ?>"/>
                            </td>
                            <?php
                                if ((shell_exec($read) == 1 && $relay_trigger[$i] == 0) || (shell_exec($read) == 0 && $relay_trigger[$i] == 1)) {
                                    ?>
                                    <td style="vertical-align: middle;">
                                        <input type="hidden" "R<?php echo $i; ?>" value="1" /><img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                    </td>
                                    <td>
                                        <button style="width: 5em;" type="submit" name="R<?php echo $i; ?>" value="1">Turn On</button>
                                    </td>
                                    <?php
                                } else {
                                    ?>
                                    <td style="vertical-align: middle;">
                                        <img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                                    </td>
                                    <td>
                                        <button style="width: 5em;" type="submit" name="R<?php echo $i; ?>" value="0">Turn Off</button>
                                    </td>
                                    <?php
                                }
                            ?>
                            <td class="center">
                                 [<input style="width: 4em;" type="number" min="1" max="99999" name="sR<?php echo $i; ?>" title="Number of seconds to turn this relay on"/><input type="submit" name="<?php echo $i; ?>secON" value="ON">]
                            </td>
                            <td class="center">
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $relay_pin[$i]; ?>" name="relay<?php echo $i; ?>pin" title="GPIO pin using BCM numbering, connected to relay <?php echo $i+1; ?>"/>
                            </td>
                            <td class="center">
                                <input style="width: 4em;" type="number" min="0" max="500" step="0.1" value="<?php echo $relay_amps[$i]; ?>" name="relay<?php echo $i; ?>amps" title="The maximum number of amps that the device connected to relay <?php echo $i+1; ?> draws. Set overall maximum allowed to be drawn from all relays in the Settings tab."/>
                            </td>
                            <td class="center">
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
                            <td class="center">
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
                            <td class="center">
                                <input type="submit" name="Mod<?php echo $i; ?>Relay" value="Set"> <button type="submit" name="Delete<?php echo $i; ?>Relay" title="Delete">Delete</button>
                            </td>
                        </tr>
                        <?php
                        } ?>
                    </table>
                    </form>

                    <table class="conditional">
                        <tr>
                            <td>
                                Conditional Statements<br/><span style="padding-top: 0.5em;font-size: 0.7em;">Note: Ensure these conditional statements don't produce conflicts with themselves or interfere with running PID controllers.</span>
                            </td>
                        </tr>
                    </table>

                    <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                    <table class="sensor-conditional">
                        <tr>
                            <td style="padding-left: 1em;">
                                Name: 
                                <input style="width: 5em;" type="text" step="any" value="" maxlength=12 size=1 name="conditionrelayname" title="Name for this relay conditional statement." required/>
                                If Relay
                                <select style="width: 3em;" name="conditionrelayifrelay" title="Select the relay to watch for whether it turns on or off.">
                                    <?php
                                    for ($n = 0; $n < count($relay_id); $n++) {
                                    echo '<option value="' . ($n+1) . '">' . ($n+1) . '</option>';
                                    } ?>
                                </select>
                                turns
                                <select style="width: 3em;" name="conditionrelayifaction" title="Select whether the relay that is watched will be watched whether it turns on or off.">
                                    <option value="on">On</option>
                                    <option value="off">Off</option>
                                </select>
                                (if on, for 
                                <input style="width: 4em;" type="number" step="any" value="0" maxlength=5 size=1 name="conditionrelayifduration" title="Check if the number of seconds the selected relay turns on for is equal to this value. If it is the same number of seconds, this statement is true. Leave at 0 if you only want to check if the relay was turned on and not necessarily if there is a duration associated with it. If 'Off' is selected in the previous field, this variable is not considered." required/>
                                sec): 
                            </td>
                            <td style="padding-bottom: 0.3em;">
                                <input type="checkbox" name="conditionrelayselrelay" value="1" checked> Turn Relay
                                <select style="width: 3em;" name="conditionrelaydorelay" title="Select the relay that will be modified based on the watched relay and watched action.">
                                    <?php
                                    for ($n = 0; $n < count($relay_id); $n++) {
                                    echo '<option value="' . ($n+1) . '">' . ($n+1) . '</option>';
                                    } ?>
                                </select>
                                <select style="width: 3em;" name="conditionrelaydoaction" title="What do you want the modified relay to do once the watched relay performs the watched action.">
                                    <option value="on">On</option>
                                    <option value="off">Off</option>
                                </select>
                                (for 
                                <input style="width: 4em;" type="number" step="any" value="0" maxlength=5 size=1 name="conditionrelaydoduration" title="The number of seconds for the modified relay to remain on. Leave at 0 to only turn the selected relay on, but not off. If 'Off' is selected in the previous field, this variable is not considered." required/>
                                sec)
                            </td>
                            <td rowspan="3" style="vertical-align:middle; padding: 0 0 0.8em 0.5em;">
                                <button type="submit" style="height:5em; width:4em;" style="height:5em;" name="AddRelayConditional" title="Save new relay conditional statement">Save</button>
                            </td>
                        </tr>
                        <tr>
                            <td></td>
                            <td style="padding-bottom: 0.3em;"><input type="checkbox" name="conditionrelayselcommand" value="1"> Execute command: <input style="width: 11em;" type="text" value="" maxlength=100 name="conditionrelaycommand" title="Command to execute in a linux shell."/></td>
                        </tr>
                        <tr>
                            <td></td>
                            <td style="padding-bottom: 1em;">
                                <input type="checkbox" name="conditionrelayselnotify" value="1"> Email <input style="width: 17em;" type="text" value="" name="conditionrelaynotify" title="These are the email addresses that will be notified. Separate multiple email addresses with commas."/>
                            </td>
                        </tr>
                    </table>
                    </form>

                    <?php
                    if (isset($conditional_relay_id) && count($conditional_relay_id) > 0) {
                    ?>
                    <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                    <table class="sensor_conditional">
                        <?php
                        for ($z = 0; $z < count($conditional_relay_id); $z++) {
                        ?>
                        <tr>
                            <td style="padding-top: 1em; padding-left: 1em; white-space: nowrap;">
                            <?php
                            echo '<button type="submit" name="DeleteRelay' . $z . 'Conditional" title="Delete conditional statement">Delete</button> ';

                            echo $z+1 . ': ' . $conditional_relay_name[$z] . ': If Relay ' . $conditional_relay_ifrelay[$z] . ' turns';

                            if ($conditional_relay_ifaction[$z] == 'on') {
                                echo ' On';
                                if ($conditional_relay_ifduration[$z] > 0) {
                                    echo ' for ' . $conditional_relay_ifduration[$z] . ' seconds:';
                                } else {
                                    echo ':';
                                }
                            } else {
                                echo ' Off:';
                            }

                        echo '</td>';

                            $first = 1;

                            if ($conditional_relay_sel_relay[$z]) {
                                if ($first) {
                                    $first = 0;
                                }
                                echo '<td style="width: 100%;">Turn Relay ' . $conditional_relay_dorelay[$z];

                                if ($conditional_relay_doaction[$z] == 'on') {
                                    echo ' On';
                                    if ($conditional_relay_doduration[$z] > 0) {
                                        echo ' for ' . $conditional_relay_doduration[$z] . ' seconds';
                                    }
                                } else {
                                    echo ' Off';
                                }
                                echo '</td>';
                            }

                            if ($conditional_relay_sel_command[$z]) {
                                if ($first) {
                                    $first = 0;
                                } else {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="padding-bottom: 0.3em;">Execute: <strong>' . htmlentities($conditional_relay_command[$z]) . '</strong></td>';
                            }

                            if ($conditional_relay_sel_notify[$z]) {
                                if (!$first) {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="width: 100%; white-space:normal;">Email <b>' . str_replace(",", ", ", $conditional_relay_notify[$z]) . '</b></td>';
                            }

                            echo '</tr>';
                        }
                    ?>
                    <tr>
                        <td style="padding-top: 1em;"></td>
                        <td></td>
                    </tr>
                    </table>
                    </form>
                    <?php
                    }
                    ?>
                </div>
            <?php
            }
            ?>

            <?php if (count($relay_id) > 0) echo '<div style="margin-bottom:1em;"></div>'; ?>
            
            <?php
            if (count($timer_id) > 0) {
            ?>
                <div style="clear: both;"></div>
                <div class="sensor-title">Timers</div>
                <div style="clear: both;"></div>

                <div class="sensor-parent">
                <form action="?tab=sensor" method="POST">
                    <table class="relays">
                        <tr>
                            <td class="table-header center middle">Timer</td>
                            <td class="table-header middle">Name</td>
                            <td class="table-header center middle">Status</td>
                            <td class="table-header center middle">Activate</td>
                            <td class="table-header center middle">Relay</td>
                            <td class="table-header center middle">On (sec)</td>
                            <td class="table-header center middle">Off (sec)</td>
                            <td class="table-header"></td>
                        </tr>
                        <?php
                        for ($i = 0; $i < count($timer_id); $i++) {
                        ?>
                        <tr>
                            <td class="center">
                                <?php echo $i+1; ?>
                            </td>
                            <td>
                                <input style="width: 10em;" type="text" value="<?php echo $timer_name[$i]; ?>" maxlength=13 name="Timer<?php echo $i; ?>Name" title="This is the relay name for timer <?php echo $i; ?>"/>
                            </td>
                            <?php
                            if ($timer_state[$i] == 0) {
                            ?>
                                <td  class="center" style="vertical-align:middle;">
                                    <img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                </td>
                                <td class="center">
                                    <button style="width: 5em;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="1">Turn On</button></nobr>
                                </td>
                            <?php
                            } else {
                            ?>
                                <td  class="center" style="vertical-align:middle;">
                                    <img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                                </td>
                                <td class="center">
                                    <button style="width: 5em;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="0">Turn Off</button></nobr>
                                </td>
                            <?php
                            }
                            ?>
                            <td class="center">
                                <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $timer_relay[$i]; ?>" maxlength=1 size=1 name="Timer<?php echo $i; ?>Relay" title="This is the relay number for timer <?php echo $i; ?>"/>
                            </td>
                            <td class="center">
                                <input style="width: 5em;" type="number" min="1" max="99999" value="<?php echo $timer_duration_on[$i]; ?>" name="Timer<?php echo $i; ?>On" title="This is On duration of timer <?php echo $i; ?>"/>
                            </td>
                            <td class="center">
                                <input style="width: 5em;" type="number" min="0" max="99999" value="<?php echo $timer_duration_off[$i]; ?>" name="Timer<?php echo $i; ?>Off" title="This is Off duration for timer <?php echo $i; ?>"/>
                            </td>
                            <td class="center">
                                <input type="submit" name="ChangeTimer<?php echo $i; ?>" value="Set"> <button type="submit" name="Delete<?php echo $i; ?>Timer" title="Delete">Delete</button>
                            </td>
                        </tr>
                        <?php
                        }
                        ?>
                    </table>
                </form>
                </div>
            <?php
            }
            ?>
            
            <?php if (count($sensor_t_id) > 0) { ?>
            <div style="clear: both;"></div>
            <div class="sensor-title">Temperature Sensors</div>
            <div style="clear: both;"></div>
            <?php
            for ($i = 0; $i < count($sensor_t_id); $i++) {
            ?>
                
            <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
            <div class="sensor-parent">
                <table class="sensor">
                    <tr>
                        <td>T Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_t_id[$i]; ?>)</span></td>
                        <td>Sensor<br>Name</td>
                        <td>Sensor<br>Device</td>
                        <?php 
                        if ($sensor_t_device[$i] == 'RPi') {
                            echo '<td>Sensor<br>Type</td>';
                        } else if ($sensor_t_device[$i] == 'DS18B20') {
                            echo '<td>Serial No<br>28-xxx</td>';
                        } else {
                            echo '<td>GPIO<br>Pin</td>';
                        }
                        ?>
                        <td>Log<br>Interval</td>
                        <td>Pre<br>Relay</td>
                        <td>Pre<br>Duration</td>
                        <td>Log</td>
                        <td>Graph</td>
                        <td style="padding: 0.2 0.5em;">
                            Presets: <select style="width: 7em;" name="sensort<?php echo $i; ?>preset">
                                <option value="default">default</option>
                                <?php
                                for ($z = 0; $z < count($sensor_t_preset); $z++) {
                                    echo '<option value="' . $sensor_t_preset[$z] . '">' . $sensor_t_preset[$z] . '</option>';
                                }
                                ?>
                            </select>
                        </td>
                    </tr>
                    <tr style="height: 2.5em;">
                        <td style="vertical-align: middle;">
                            <button type="submit" name="Delete<?php echo $i; ?>TSensor" title="Delete Sensor">Delete<br>Sensor</button>
                        </td>
                        <td>
                            <input style="width: <?php if ($sensor_t_device[$i] == 'DS18B20') echo '6em'; else echo '10em'; ?>;" type="text" value="<?php echo $sensor_t_name[$i]; ?>" maxlength=12 size=10 name="sensort<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                        </td>
                        <td>
                            <select style="width: 7em;" name="sensort<?php echo $i; ?>device">
                                <option<?php
                                    if ($sensor_t_device[$i] == 'Other') {
                                        echo ' selected="selected"';
                                    } ?> value="Other">Other</option>
                                <option<?php
                                    if ($sensor_t_device[$i] == 'RPi') {
                                        echo ' selected="selected"';
                                    } ?> value="RPi">Raspberry Pi</option>
                                <option<?php
                                    if ($sensor_t_device[$i] == 'DS18B20') {
                                        echo ' selected="selected"';
                                    } ?> value="DS18B20">DS18B20</option>
                            </select>
                        </td>
                        <td>
                            <?php 
                            if ($sensor_t_device[$i] == 'RPi') {
                            ?>
                                <select style="width: 3.5em;" name="sensort<?php echo $i; ?>pin">
                                <option<?php
                                    if ($sensor_t_pin[$i] == 0) {
                                        echo ' selected="selected"';
                                    } ?> value="0">CPU</option>
                                <option<?php
                                    if ($sensor_t_pin[$i] == 1) {
                                        echo ' selected="selected"';
                                    } ?> value="1">GPU</option>
                            </select>
                            <?php
                            } else if ($sensor_t_device[$i] == 'DS18B20') {
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
                            <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_t_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensort<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relay will run before the sensor measurement is obtained"/> sec
                        </td>
                        <td>
                            <input type="checkbox" title="Enable this sensor to record measurements to the log file" name="sensort<?php echo $i; ?>activated" value="1" <?php if ($sensor_t_activated[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <input type="checkbox" title="Enable graphs to be generated from the sensor log data" name="sensort<?php echo $i; ?>graph" value="1" <?php if ($sensor_t_graph[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <div style="padding: 0.2em 0">
                                <input type="submit" name="Change<?php echo $i; ?>TSensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_ht_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>TSensorOverwrite" value="Save" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>TSensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_t_preset) == 0) echo ' disabled'; ?>>
                            </div>
                            <div style="padding: 0.2em 0">
                                <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensort<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>TSensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>TSensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                            </div>
                        </td>
                    </tr>
                </table>

                <table class="yaxis">
                    <tr>
                        <td rowspan=3>Graph Y-Axis<br>Range<br>&<br>Marks</td>
                        <td colspan=4>Relay</td>
                        <td colspan=4>Temperature (&deg;C)</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                    </tr>
                        <td style="padding-left: 1.5em;"    >
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_relay_min[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisRelayMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_relay_max[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisRelayMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_relay_tics[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisRelayTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_relay_mtics[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisRelayMTics" title=""/>
                        </td>
                        <td style="padding-left: 1.5em;">
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_temp_min[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisTempMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_temp_max[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisTempMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_temp_tics[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisTempTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_t_yaxis_temp_mtics[$i]; ?>" maxlength=4 size=2 name="SetT<?php echo $i; ?>YAxisTempMTics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td rowspan="2">Relays to<br>Graph</td>
                        <td colspan="4" rowspan="2" style="padding-left: 1.5em;">Separate multiple relays with<br>commas or set 0 to disable</td>
                        <td colspan="2" style="padding-left: 1.5em;">Graph Up</td>
                        <td colspan="2">Graph Down</td>
                    </tr>
                        <td colspan="2" style="padding-left: 1.5em;">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_t_temp_relays_up[$i]; ?>" maxlength=20 name="SetT<?php echo $i; ?>TempRelaysUp" title="These relays will be graphed with this sensor's condition and display above the y-axis 0."/>
                        </td>
                        <td colspan="2">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_t_temp_relays_down[$i]; ?>" maxlength=20 name="SetT<?php echo $i; ?>TempRelaysDown" title="These relays will be graphed with this sensor's condition and display below the y-axis 0."/>
                        </td>
                    </tr>
                </table>

                <table class="pid">
                    <tr>
                        <td>PID Regulation</td>
                        <td>Activate</td>
                        <td>Set Point</td>
                        <td>Regulate</td>
                        <td>Measure<br>Interval</td>
                        <td>Up<br>Relay</td>
                        <td>Up<br>Min</td>
                        <td>Up<br>Max</td>
                        <td>Down<br>Relay</td>
                        <td>Down<br>Min</td>
                        <td>Down<br>Max</td>
                        <td>K<sub>p</sub></td>
                        <td>K<sub>i</sub></td>
                        <td>K<sub>d</sub></td>
                    </tr>
                    <tr style="height: 2.5em; background-color: #FFFFFF;">
                        <td style="text-align:left; padding-left:0.5em;"><?php
                            if ($pid_t_temp_or[$i] == 1) {
                                ?><img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                <?php
                            } else {
                                ?><img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                            <?php
                            }
                            ?> Temperature
                        </td>
                        <td>
                            <?php
                            if ($pid_t_temp_or[$i] == 1) {
                                ?><button style="width: 5em;" type="submit" name="ChangeT<?php echo $i; ?>TempOR" value="0">Turn On</button>
                                <?php
                            } else {
                                ?><button style="width: 5em;" type="submit" name="ChangeT<?php echo $i; ?>TempOR" value="1">Turn Off</button>
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
                            <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_t_temp_period[$i]; ?>" name="SetT<?php echo $i; ?>TempPeriod" title="This is the number of seconds between taking a new temperature measurement and applying the PID"/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_t_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_t_temp_outmin_low[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempOutminLow" title="This is the minimum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_t_temp_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempOutmaxLow" title="This is the maximum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_t_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_t_temp_outmin_high[$i]; ?>" maxlength=1 size=1 name="SetT<?php echo $i; ?>TempOutminHigh" title="This is the minimum number of seconds the relay used to decrease temperature is permitted to turn on for (0 to disable)."/>
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
                </form>

                <table class="conditional">
                    <tr>
                        <td>
                            Conditional Statements<br/><span style="padding-top: 0.5em;font-size: 0.7em;">Note: Ensure these conditional statements don't produce conflicts with themselves or interfere with running PID controllers.</span>
                        </td>
                    </tr>
                </table>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor-conditional">
                    <tr>
                        <td style="padding-left: 1em;">
                            Name: 
                            <input style="width: 5em;" type="text" step="any" value="" maxlength=12 size=1 name="conditiont<?php echo $i; ?>name" title="" required/>
                            Every <input style="width: 4em;" type="number" step="any" value="360" maxlength=4 size=1 name="conditiont<?php echo $i; ?>period" title="" required/> sec,
                            if Temperature is
                            <select style="width: 5em;" name="conditiont<?php echo $i; ?>direction">
                                <option value="1">Above</option>
                                <option value="-1">Below</option>
                            </select>
                            <input style="width: 4em;" type="number" step="any" value="" maxlength=4 size=1 name="conditiont<?php echo $i; ?>setpoint" title="" required/>: 
                        </td>
                        <td style="padding-bottom: 0.3em;">
                            <input type="checkbox" name="conditiont<?php echo $i; ?>selrelay" value="1" checked> Turn Relay
                            <select style="width: 3em;" name="conditiont<?php echo $i; ?>relay" title="Select the relay that will be modified based on the watched action.">
                                <?php
                                for ($n = 0; $n < count($relay_id); $n++) {
                                echo '<option value="' . ($n+1) . '">' . ($n+1) . '</option>';
                                } ?>
                            </select>
                            <select style="width: 3em;" name="conditiont<?php echo $i; ?>relaystate">
                                <option value="1">On</option>
                                <option value="0">Off</option>
                            </select>
                            (for
                            <input style="width: 4em;" type="number" step="any" value="0" maxlength=4 size=1 name="conditiont<?php echo $i; ?>relaysecondson" title="The number of seconds for the relay to remain on. Leave at 0 to just turn it on or off." required/> sec)
                        </td>
                        <td rowspan="3" style="vertical-align:middle; padding: 0 0 0.8em 0.5em;">
                            <button type="submit" style="height:5em; width:4em;" name="AddT<?php echo $i; ?>Conditional" title="Save new conditional statement">Save</button>
                        </td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 0.3em;"><input type="checkbox" name="conditiont<?php echo $i; ?>selcommand" value="1"> Execute command: <input style="width: 11em;" type="text" value="" maxlength=100 name="conditiont<?php echo $i; ?>command" title="Command to execute in a linux shell."/></td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 1em;">
                            <input type="checkbox" name="conditiont<?php echo $i; ?>selnotify" value="1"> Email <input style="width: 17em;" type="text" value="" name="conditiont<?php echo $i; ?>notify" title="These are the email addresses that will be notified. Separate multiple email addresses with commas."/>
                        </td>
                    </tr>
                </table>
                </form>

                <?php
                if (isset($conditional_t_id[$i]) && count($conditional_t_id[$i]) > 0) {
                ?>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor_conditional">
                    <?php
                        for ($z = 0; $z < count($conditional_t_id[$i]); $z++) {
                    ?>
                    <tr>
                        <td style="padding-top: 1em; padding-left: 1em; white-space: nowrap;">
                            <?php
                            echo '<button type="submit" name="DeleteT' . $i . '-' . $z . 'Conditional" title="Delete conditional statement">Delete</button> ';
                            if ($conditional_t_state[$i][$z]) {
                                echo '<button style="width: 5em;" type="submit" name="TurnOffT' . $i . '-' . $z . 'Conditional" title="">Turn Off</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/on.png" alt="On" title="On"> ';
                            } else {
                                echo '<button style="width: 5em;" type="submit" name="TurnOnT' . $i . '-' . $z . 'Conditional" title="">Turn On</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/off.png" alt="Off" title="Off"> ';
                            }

                            echo $z+1 . ' ' . $conditional_t_name[$i][$z] . ': Every ' . $conditional_t_period[$i][$z] . ' sec, if the Temperature is ';

                            if ($conditional_t_direction[$i][$z] == 1) {
                                echo 'Above ';
                            } else {
                                echo 'Below ';
                            }

                            echo $conditional_t_setpoint[$i][$z] .  '&deg;C:</td>';

                            $first = 1;

                            if ($conditional_t_sel_relay[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                }
                                echo '<td style="width: 100%;">Turn Relay ' . $conditional_t_relay[$i][$z];

                                if ($conditional_t_relay_state[$i][$z]) {
                                    echo ' On';
                                    if ($conditional_t_relay_seconds_on[$i][$z] > 0) {
                                        echo ' for ' . $conditional_t_relay_seconds_on[$i][$z] . ' seconds';
                                    }
                                } else {
                                    echo ' Off';
                                } 
                                echo '</td>';
                            }

                            if ($conditional_t_sel_command[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                } else {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="padding-bottom: 0.3em;">Execute: <strong>' . htmlentities($conditional_t_command[$i][$z]) . '</strong></td>';
                            }

                            if ($conditional_t_sel_notify[$i][$z]) {
                                if (!$first) {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="width: 100%; white-space:normal;">Email <b>' . str_replace(",", ", ", $conditional_t_notify[$i][$z]) . '</b></td>';
                            }

                            echo '</tr>';
                        } 
                    ?>
                    <tr><td style="padding-top:1em;"></td><td></td></tr>
                </table>
                </form>
                <?php
                    }
                ?>

            </div>
            <div style="margin-bottom: <?php if ($i == count($sensor_t_id)) echo '2'; else echo '1'; ?>em;"></div>
            <?php
            } }
            ?>

            <?php if (count($sensor_ht_id) > 0) { ?>
            <div style="clear: both;"></div>
            <div class="sensor-title">Humidity/Temperature Sensors</div>
            <div style="clear: both;"></div>
                <?php
                for ($i = 0; $i < count($sensor_ht_id); $i++) {
                ?>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <div class="sensor-parent">
                <table class="sensor">
                    <tr>
                        <td>HT Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_ht_id[$i]; ?>)</span></td>
                        <td>Sensor<br>Name</td>
                        <td>Sensor<br>Device</td>
                        <?php
                            if ($sensor_ht_device[$i] == 'AM2315') {
                                echo '
                                <td>I<sup>2</sup>C or<br>Multiplex</td>
                                ';
                            } else {
                                echo '<td>GPIO<br>Pin</td>';
                            }
                        ?>
                        <td>Log<br>Interval</td>
                        <td>Pre<br>Relay</td>
                        <td>Pre<br>Duration</td>
                        <td>Log</td>
                        <td>Graph</td>
                        <td style="padding: 0.2 0.5em;">
                            Presets: <select style="width: 7em;" name="sensorht<?php echo $i; ?>preset">
                                <option value="default">default</option>
                                <?php
                                for ($z = 0; $z < count($sensor_ht_preset); $z++) {
                                    echo '<option value="' . $sensor_ht_preset[$z] . '">' . $sensor_ht_preset[$z] . '</option>';
                                }
                                ?>
                            </select>
                        </td>
                    </tr>
                    <tr style="height: 2.5em;">
                        <td style="vertical-align: middle;">
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
                                    if ($sensor_ht_device[$i] == 'AM2315') {
                                        echo ' selected="selected"';
                                    } ?> value="AM2315">AM2315</option>
                                <option<?php
                                    if ($sensor_ht_device[$i] == 'Other') {
                                        echo ' selected="selected"';
                                    } ?> value="Other">Other</option>
                            </select>
                        </td>
                        <td>
                            <?php
                            if ($sensor_ht_device[$i] == 'AM2315') {
                            ?>
                            <select style="width: 7em;" name="sensorht<?php echo $i; ?>pin" title="If the sensor is connected directly to the I2C, select 'Use I2C'. If the sensor is connected through an I2C multiplexer (TCA9548A), select the multiplexer address and channel.">
                                <option<?php
                                    if ($sensor_ht_pin[$i] == 0) {
                                        echo ' selected="selected"';
                                    } ?> value="0">Use I2C</option>
                                <?php
                                for ($j = 1; $j < 79; $j++) {
                                    $count_str = str_split($j);
                                    if ($j < 10) {
                                        $count_str[1] = $count_str[0];
                                        $address = 0;
                                        $channel = $count_str[1];
                                    } else {
                                        $address = $count_str[0];
                                        $channel = $count_str[1];
                                    }
                                    if ($count_str[1] > 0 && $count_str[1] < 9) {
                                        echo '<option';
                                        if ($sensor_ht_pin[$i] == $j) {
                                            echo ' selected="selected"';
                                        }
                                        echo ' value="' . $j . '">0x7' . $address . ' Ch. ' . $channel . '</option>';
                                    }
                                }
                                ?>
                            </select>
                            <?php
                            } else {
                            ?>
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_ht_pin[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>pin" title="This is the GPIO pin connected to the HT sensor"/>
                            <?php
                            }
                            ?>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_ht_period[$i]; ?>" name="sensorht<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/> sec
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_ht_premeasure_relay[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>premeasure_relay" title="This is the relay that will turn on prior to the sensor measurement, for the duration specified by Pre Duration (0 to disable)"/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_ht_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relay will run before the sensor measurement is obtained"/> sec
                        </td>
                        <td>
                            <input type="checkbox" title="Enable this sensor to record measurements to the log file" name="sensorht<?php echo $i; ?>activated" value="1" <?php if ($sensor_ht_activated[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <input type="checkbox" title="Enable graphs to be generated from the sensor log data" name="sensorht<?php echo $i; ?>graph" value="1" <?php if ($sensor_ht_graph[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <div style="padding: 0.2em 0">
                                <input type="submit" name="Change<?php echo $i; ?>HTSensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_ht_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>HTSensorOverwrite" value="Save" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>HTSensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_ht_preset) == 0) echo ' disabled'; ?>>
                            </div>
                            <div style="padding: 0.2em 0">
                                <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensorht<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>HTSensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>HTSensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                            </div>
                        </td>
                    </tr>
                </table>

                <table class="sensor">
                    <tr>
                        <td>Sensor Verification</td>
                        <td></td>
                        <td colspan="3">Temperature (&degC)</td>
                        <td colspan="3">Humidity (%)</td>
                        <td>Notification</td>
                    </tr>
                    <tr>
                        <td>Sensor must be either:</td>
                        <td>GPIO</td>
                        <td>Difference</td>
                        <td>Notify</td>
                        <td>Stop PID</td>
                        <td>Difference</td>
                        <td>Notify</td>
                        <td>Stop PID</td>
                        <td>(separate emails with commas)</td>
                    </tr>
                    <tr>
                        <td>DHT11, DHT22, AMH2302</td>
                        <td><input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_ht_verify_pin[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>verifypin" title="This is the GPIO pin connected to the HT sensor that will verify this sensor's measurement (0 to disable)"/></td>
                        <td><input style="width: 4em;" type="number" min="0" max="100" step="any" value="<?php echo $sensor_ht_verify_temp[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>verifytemp" title="This is the maximum temperature difference between the two sensors allowed before sending an alarm notification and disabling the PID for the condition with the disparity."/> &deg;C</td>
                        <td><input type="hidden" name="sensorht<?php echo $i; ?>verifytempnotify" value="0" /><input type="checkbox" id="sensorht<?php echo $i; ?>verifytempnotify" name="sensorht<?php echo $i; ?>verifytempnotify" value="1" <?php if ($sensor_ht_verify_temp_notify[$i] == 1) echo "checked"; ?>/></td>
                        <td><input type="hidden" name="sensorht<?php echo $i; ?>verifytempstop" value="0" /><input type="checkbox" id="sensorht<?php echo $i; ?>verifytempstop" name="sensorht<?php echo $i; ?>verifytempstop" value="1" <?php if ($sensor_ht_verify_temp_stop[$i] == 1) echo "checked"; ?>/></td>
                        <td><input style="width: 4em;" type="number" min="0" max="100" step="any" value="<?php echo $sensor_ht_verify_hum[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>verifyhum" title="This is the maximum humidity difference between the two sensors allowed before sending an alarm notification and disabling the PID for the condition with the disparity."/> %</td>
                        <td><input type="hidden" name="sensorht<?php echo $i; ?>verifyhumnotify" value="0" /><input type="checkbox" id="sensorht<?php echo $i; ?>verifyhumnotify" name="sensorht<?php echo $i; ?>verifyhumnotify" value="1" <?php if ($sensor_ht_verify_hum_notify[$i] == 1) echo "checked"; ?>/></td>
                        <td><input type="hidden" name="sensorht<?php echo $i; ?>verifyhumstop" value="0" /><input type="checkbox" id="sensorht<?php echo $i; ?>verifyhumstop" name="sensorht<?php echo $i; ?>verifyhumstop" value="1" <?php if ($sensor_ht_verify_hum_stop[$i] == 1) echo "checked"; ?>/></td>
                        <td><input style="width: 16em;" type="text" value="<?php echo $sensor_ht_verify_email[$i]; ?>" name="sensorht<?php echo $i; ?>verifyemail" title="These are the email addresses that will be notified if the sensor measurements diverge by the set differences"/></td>
                    </tr>
                </table>

                <table class="yaxis">
                    <tr>
                        <td rowspan=3>Graph Y-Axis<br>Range<br>&<br>Marks</td>
                        <td colspan=4>Relay</td>
                        <td colspan=4>Temperature (&degC)</td>
                        <td colspan=4>Humidity (%)</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                    </tr>
                        <td style="padding-left: 1.5em;"    >
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_relay_min[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisRelayMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_relay_max[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisRelayMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_relay_tics[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisRelayTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_relay_mtics[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisRelayMTics" title=""/>
                        </td>
                        <td style="padding-left: 1.5em;">
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_temp_min[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisTempMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_temp_max[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisTempMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_temp_tics[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisTempTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_temp_mtics[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisTempMTics" title=""/>
                        </td>
                        <td style="padding-left: 1.5em;">
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_hum_min[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisHumMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_hum_max[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisHumMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_hum_tics[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisHumTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_ht_yaxis_hum_mtics[$i]; ?>" maxlength=4 size=2 name="SetHT<?php echo $i; ?>YAxisHumMTics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td rowspan="2">Relays to<br>Graph</td>
                        <td colspan="4" rowspan="2" style="padding-left: 1.5em;">Separate multiple relays with<br>commas or set 0 to disable</td>
                        <td colspan="2" style="padding-left: 1.5em;">Graph Up</td>
                        <td colspan="2">Graph Down</td>
                        <td colspan="2" style="padding-left: 1.5em;">Graph Up</td>
                        <td colspan="2">Graph Down</td>
                    </tr>
                        <td colspan="2" style="padding-left: 1.5em;">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_ht_temp_relays_up[$i]; ?>" maxlength=20 name="SetHT<?php echo $i; ?>TempRelaysUp" title="These relays will be graphed with this sensor's condition and display above the y-axis 0."/>
                        </td>
                        <td colspan="2">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_ht_temp_relays_down[$i]; ?>" maxlength=20 name="SetHT<?php echo $i; ?>TempRelaysDown" title="These relays will be graphed with this sensor's condition and display below the y-axis 0."/>
                        </td>
                        <td colspan="2" style="padding-left: 1.5em;">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_ht_hum_relays_up[$i]; ?>" maxlength=20 name="SetHT<?php echo $i; ?>HumRelaysUp" title="These relays will be graphed with this sensor's condition and display above the y-axis 0."/>
                        </td>
                        <td colspan="2">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_ht_hum_relays_down[$i]; ?>" maxlength=20 name="SetHT<?php echo $i; ?>HumRelaysDown" title="These relays will be graphed with this sensor's condition and display below the y-axis 0."/>
                        </td>
                    </tr>
                </table>

                <table class="pid">
                    <tr>
                        <td>PID Regulation</td>
                        <td>Activate</td>
                        <td>Set Point</td>
                        <td>Regulate</td>
                        <td>Measure<br>Interval</td>
                        <td>Up<br>Relay</td>
                        <td>Up<br>Min</td>
                        <td>Up<br>Max</td>
                        <td>Down<br>Relay</td>
                        <td>Down<br>Min</td>
                        <td>Down<br>Max</td>
                        <td>K<sub>p</sub></td>
                        <td>K<sub>i</sub></td>
                        <td>K<sub>d</sub></td>
                    </tr>
                    <tr style="height: 2.5em; background-color: #FFFFFF;">
                        <td style="text-align:left; padding-left:0.5em;"><?php
                            if ($pid_ht_temp_or[$i] == 1) {
                                ?><img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                <?php
                            } else {
                                ?><img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                            <?php
                            }
                            ?> Temperature</td>
                        <td>
                            <?php
                            if ($pid_ht_temp_or[$i] == 1) {
                                ?><button style="width: 5em;" type="submit" name="ChangeHT<?php echo $i; ?>TempOR" value="0">Turn On</button>
                                <?php
                            } else {
                                ?><button style="width: 5em;" type="submit" name="ChangeHT<?php echo $i; ?>TempOR" value="1">Turn Off</button>
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
                            <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_ht_temp_period[$i]; ?>" name="SetHT<?php echo $i; ?>TempPeriod" title="This is the number of seconds between taking a new temperature measurement and applying the PID"/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_temp_outmin_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempOutminLow" title="This is the minimum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_temp_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempOutmaxLow" title="This is the maximum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_temp_outmin_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>TempOutminHigh" title="This is the minimum number of seconds the relay used to decrease temperature is permitted to turn on for (0 to disable)."/>
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
                    <tr style="height: 2.5em; background-color: #FFFFFF;">
                        <td style="text-align:left; padding-left:0.5em;"><?php
                            if ($pid_ht_hum_or[$i] == 1) {
                                ?><img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                <?php
                            } else {
                                ?><img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                            <?php
                            }
                            ?> Humidity</td>
                        <td>
                            <?php
                            if ($pid_ht_hum_or[$i] == 1) {
                                ?><button style="width: 5em;" type="submit" name="ChangeHT<?php echo $i; ?>HumOR" value="0">Turn On</button>
                                <?php
                            } else {
                                ?><button style="width: 5em;" type="submit" name="ChangeHT<?php echo $i; ?>HumOR" value="1">Turn Off</button>
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
                            <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_ht_hum_period[$i]; ?>" name="SetHT<?php echo $i; ?>HumPeriod" title="This is the number of seconds between taking a new humidity measurement and applying the PID"/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_hum_relay_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumRelayLow" title="This relay is used to increase humidity."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_hum_outmin_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumOutminLow" title="This is the minimum number of seconds the relay used to increase humidity is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_hum_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumOutmaxLow" title="This is the maximum number of seconds the relay used to increase humidity is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_ht_hum_relay_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumRelayHigh" title="This relay is used to decrease humidity."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_ht_hum_outmin_high[$i]; ?>" maxlength=1 size=1 name="SetHT<?php echo $i; ?>HumOutminHigh" title="This is the minimum number of seconds the relay used to decrease humidity is permitted to turn on for (0 to disable)."/>
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
                
                <table class="conditional">
                    <tr>
                        <td>
                            Conditional Statements<br/><span style="padding-top: 0.5em;font-size: 0.7em;">Note: Ensure these conditional statements don't produce conflicts with themselves or interfere with running PID controllers.</span>
                        </td>
                    </tr>
                </table>

                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor-conditional">
                    <tr>
                        <td style="padding-left: 1em;">
                            Name: 
                            <input style="width: 5em;" type="text" step="any" value="" maxlength=12 size=1 name="conditionht<?php echo $i; ?>name" title="" required/>
                            Every <input style="width: 4em;" type="number" step="any" value="360" maxlength=4 size=1 name="conditionht<?php echo $i; ?>period" title="" required/> sec,
                            if <select style="width: 6em;" name="conditionht<?php echo $i; ?>condition">
                                <option value="Humidity">Humidity</option>
                                <option value="Temperature">Temperature</option>
                            </select>
                            is
                            <select style="width: 5em;" name="conditionht<?php echo $i; ?>direction">
                                <option value="1">Above</option>
                                <option value="-1">Below</option>
                            </select>
                            <input style="width: 4em;" type="number" step="any" value="" maxlength=4 size=1 name="conditionht<?php echo $i; ?>setpoint" title="" required/>: 
                        </td>
                        <td style="padding-bottom: 0.3em;">
                            <input type="checkbox" name="conditionht<?php echo $i; ?>selrelay" value="1" checked> Turn Relay
                            <select style="width: 3em;" name="conditionht<?php echo $i; ?>relay" title="Select the relay that will be modified based on the watched action.">
                                <?php
                                for ($n = 0; $n < count($relay_id); $n++) {
                                echo '<option value="' . ($n+1) . '">' . ($n+1) . '</option>';
                                } ?>
                            </select>
                            <select style="width: 3em;" name="conditionht<?php echo $i; ?>relaystate">
                                <option value="1">On</option>
                                <option value="0">Off</option>
                            </select>
                            (for
                            <input style="width: 4em;" type="number" step="any" value="0" maxlength=4 size=1 name="conditionht<?php echo $i; ?>relaysecondson" title="The number of seconds for the relay to remain on. Leave at 0 to just turn it on or off." required/> sec)
                        </td>
                        <td rowspan="3" style="vertical-align:middle; padding: 0 0 0.8em 0.5em;">
                            <button type="submit" style="height:5em; width:4em;" name="AddHT<?php echo $i; ?>Conditional" title="Save new conditional statement">Save</button>
                        </td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 0.3em;"><input type="checkbox" name="conditionht<?php echo $i; ?>selcommand" value="1"> Execute command: <input style="width: 11em;" type="text" value="" maxlength=100 name="conditionht<?php echo $i; ?>command" title="Command to execute in a linux shell."/></td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 1em;">
                            <input type="checkbox" name="conditionht<?php echo $i; ?>selnotify" value="1"> Email <input style="width: 17em;" type="text" value="" name="conditionht<?php echo $i; ?>notify" title="These are the email addresses that will be notified. Separate multiple email addresses with commas."/>
                        </td>
                    </tr>
                </table>
                </form>

                <?php
                if (isset($conditional_ht_id[$i]) && count($conditional_ht_id[$i]) > 0) {
                ?>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor_conditional">
                    <?php
                        for ($z = 0; $z < count($conditional_ht_id[$i]); $z++) {
                    ?>
                    <tr>
                        <td style="padding-top: 1em; padding-left: 1em; white-space: nowrap;">
                            <?php
                            echo '<button type="submit" name="DeleteHT' . $i . '-' . $z . 'Conditional" title="Delete conditional statement">Delete</button> ';
                            if ($conditional_ht_state[$i][$z]) {
                                echo '<button style="width: 5em;" type="submit" name="TurnOffHT' . $i . '-' . $z . 'Conditional" title="">Turn Off</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/on.png" alt="On" title="On"> ';
                            } else {
                                echo '<button style="width: 5em;" type="submit" name="TurnOnHT' . $i . '-' . $z . 'Conditional" title="">Turn On</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/off.png" alt="Off" title="Off"> ';
                            }

                            echo $z+1 . ' ' . $conditional_ht_name[$i][$z] . ': Every ' . $conditional_ht_period[$i][$z] . ' sec, if the ' . $conditional_ht_condition[$i][$z] . ' is ';

                            if ($conditional_ht_direction[$i][$z] == 1) {
                                echo 'Above ';
                            } else {
                                echo 'Below ';
                            }

                            echo $conditional_ht_setpoint[$i][$z];

                            if ($conditional_ht_condition[$i][$z] == "Humidity") {
                                echo '%:';
                            } else {
                                echo '&deg;C:';
                            }

                            $first = 1;

                            if ($conditional_ht_sel_relay[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                }
                                echo '<td style="width: 100%;">Turn Relay ' . $conditional_ht_relay[$i][$z];

                                if ($conditional_ht_relay_state[$i][$z]) {
                                    echo ' On';
                                    if ($conditional_ht_relay_seconds_on[$i][$z] > 0) {
                                        echo ' for ' . $conditional_ht_relay_seconds_on[$i][$z] . ' seconds';
                                    }
                                } else {
                                    echo ' Off';
                                } 
                                echo '</td>';
                            }

                            if ($conditional_ht_sel_command[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                } else {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="padding-bottom: 0.3em;">Execute: <strong>' . htmlentities($conditional_ht_command[$i][$z]) . '</strong></td>';
                            }

                            if ($conditional_ht_sel_notify[$i][$z]) {
                                if (!$first) {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="width: 100%; white-space:normal;">Email <b>' . str_replace(",", ", ", $conditional_ht_notify[$i][$z]) . '</b></td>';
                            }

                            echo '</tr>';
                        } 
                    ?>
                    <tr>
                        <td style="padding-top:1em;"></td>
                        <td></td>
                    </tr>
                </table>
                </form>
                <?php
                    }
                ?>

                </div>
                <div style="margin-bottom: <?php if ($i == count($sensor_ht_id)) echo '2'; else echo '1'; ?>em;"></div>
                <?php
                }   }
                ?>

            <?php if (count($sensor_co2_id) > 0) { ?>
            <div style="clear: both;"></div>
            <div class="sensor-title">CO<sub>2</sub> Sensors</div>
            <div style="clear: both;"></div>
                <?php
                for ($i = 0; $i < count($sensor_co2_id); $i++) {
                ?>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <div class="sensor-parent">
                <table class="sensor">
                    <tr>
                        <td>CO<sub>2</sub> Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_co2_id[$i]; ?>)</span></td>
                        <td>Sensor<br>Name</td>
                        <td>Sensor<br>Device</td>
                        <td>GPIO<br>Pin</td>
                        <td>Log<br>Interval</td>
                        <td>Pre<br>Relay</td>
                        <td>Pre<br>Duration</td>
                        <td>Log</td>
                        <td>Graph</td>
                        <td style="padding: 0.2 0.5em;">
                            Presets: <select style="width: 7em;" name="sensorco2<?php echo $i; ?>preset">
                                <option value="default">default</option>
                                <?php
                                for ($z = 0; $z < count($sensor_co2_preset); $z++) {
                                    echo '<option value="' . $sensor_co2_preset[$z] . '">' . $sensor_co2_preset[$z] . '</option>';
                                }
                                ?>
                            </select>
                        </td>
                    </tr>
                    <tr style="height: 2.5em;">
                        <td style="vertical-align: middle;">
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
                            <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_co2_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensorco2<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relay will run before the sensor measurement is obtained"/> sec
                        </td>
                        <td>
                            <input type="checkbox" title="Enable this sensor to record measurements to the log file" name="sensorco2<?php echo $i; ?>activated" value="1" <?php if ($sensor_co2_activated[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <input type="checkbox" title="Enable graphs to be generated from the sensor log data" name="sensorco2<?php echo $i; ?>graph" value="1" <?php if ($sensor_co2_graph[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <div style="padding: 0.2em 0">
                                <input type="submit" name="Change<?php echo $i; ?>CO2SensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_co2_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>CO2SensorOverwrite" value="Save" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>CO2SensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_co2_preset) == 0) echo ' disabled'; ?>>
                            </div>
                            <div style="padding: 0.2em 0">
                                <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensorco2<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>CO2SensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>CO2SensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                            </div>
                        </td>
                    </tr>
                </table>

                <table class="yaxis">
                    <tr>
                        <td rowspan=3>Graph Y-Axis<br>Range<br>&<br>Marks</td>
                        <td colspan=4>Relay</td>
                        <td colspan=4>CO<sub>2</sub> (ppmv)</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                    </tr>
                        <td style="padding-left: 1.5em;"    >
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_relay_min[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisRelayMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_relay_max[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisRelayMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_relay_tics[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisRelayTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_relay_mtics[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisRelayMTics" title=""/>
                        </td>
                        <td style="padding-left: 1.5em;">
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_co2_min[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisCO2Min" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_co2_max[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisCO2Max" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_co2_tics[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisCO2Tics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_co2_yaxis_co2_mtics[$i]; ?>" maxlength=4 size=2 name="SetCO2<?php echo $i; ?>YAxisCO2MTics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td rowspan="2">Relays to<br>Graph</td>
                        <td colspan="4" rowspan="2" style="padding-left: 1.5em;">Separate multiple relays with<br>commas or set 0 to disable</td>
                        <td colspan="2" style="padding-left: 1.5em;">Graph Up</td>
                        <td colspan="2">Graph Down</td>
                    </tr>
                        <td colspan="2" style="padding-left: 1.5em;">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_co2_relays_up[$i]; ?>" maxlength=20 name="SetCO2<?php echo $i; ?>CO2RelaysUp" title="These relays will be graphed with this sensor's condition and display above the y-axis 0."/>
                        </td>
                        <td colspan="2">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_co2_relays_down[$i]; ?>" maxlength=20 name="SetCO2<?php echo $i; ?>CO2RelaysDown" title="These relays will be graphed with this sensor's condition and display below the y-axis 0."/>
                        </td>
                    </tr>
                </table>

                <table class="pid">
                    <tr>
                        <td>PID Regulation</td>
                        <td>Activate</td>
                        <td>Set Point</td>
                        <td>Regulate</td>
                        <td>Measure<br>Interval</td>
                        <td>Up<br>Relay</td>
                        <td>Up<br>Min</td>
                        <td>Up<br>Max</td>
                        <td>Down<br>Relay</td>
                        <td>Down<br>Min</td>
                        <td>Down<br>Max</td>
                        <td>K<sub>p</sub></td>
                        <td>K<sub>i</sub></td>
                        <td>K<sub>d</sub></td>
                    </tr>
                    <tr style="height: 2.5em; background-color: #FFFFFF;">
                        <td style="text-align:left; padding-left:0.5em;"><?php
                            if ($pid_co2_or[$i] == 1) {
                                ?><img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                <?php
                            } else {
                                ?><img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                                <?php
                            }
                            ?> CO<sub>2</sub></td>
                        <td>
                            <?php
                            if ($pid_co2_or[$i] == 1) {
                                ?><button style="width: 5em;" type="submit" name="Change<?php echo $i; ?>CO2OR" value="0">Turn On</button>
                                <?php
                            } else {
                                ?><button style="width: 5em;" type="submit" name="Change<?php echo $i; ?>CO2OR" value="1">Turn Off</button>
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
                            <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_co2_period[$i]; ?>" maxlength=4 size=1 name="SetCO2<?php echo $i; ?>CO2Period" title="This is the number of seconds between taking a new CO2 measurement and applying the PID"/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_co2_relay_low[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2RelayLow" title="This relay is used to increase CO2."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_co2_outmin_low[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2OutminLow" title="This is the minimum number of seconds the relay used to increase CO2 is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_co2_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2OutmaxLow" title="This is the maximum number of seconds the relay used to increase CO2 is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_co2_relay_high[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2RelayHigh" title="This relay is used to decrease CO2."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_co2_outmin_high[$i]; ?>" maxlength=1 size=1 name="SetCO2<?php echo $i; ?>CO2OutminHigh" title="This is the minimum number of seconds the relay used to decrease CO2 is permitted to turn on for (0 to disable)."/>
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



                <table class="conditional">
                    <tr>
                        <td>
                            Conditional Statements<br/><span style="padding-top: 0.5em;font-size: 0.7em;">Note: Ensure these conditional statements don't produce conflicts with themselves or interfere with running PID controllers.</span>
                        </td>
                    </tr>
                </table>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor-conditional">
                    <tr>
                        <td style="padding-left: 1em;">
                            Name: 
                            <input style="width: 5em;" type="text" step="any" value="" maxlength=12 size=1 name="conditionco2<?php echo $i; ?>name" title="" required/>
                            Every <input style="width: 4em;" type="number" step="any" value="360" maxlength=4 size=1 name="conditionco2<?php echo $i; ?>period" title="" required/> sec,
                            if CO<sub>2</sub> is
                            <select style="width: 5em;" name="conditionco2<?php echo $i; ?>direction">
                                <option value="1">Above</option>
                                <option value="-1">Below</option>
                            </select>
                            <input style="width: 4em;" type="number" step="any" value="" maxlength=4 size=1 name="conditionco2<?php echo $i; ?>setpoint" title="" required/>: 
                        </td>
                        <td style="padding-bottom: 0.3em;">
                            <input type="checkbox" name="conditionco2<?php echo $i; ?>selrelay" value="1" checked> Turn Relay
                            <select style="width: 3em;" name="conditionco2<?php echo $i; ?>relay" title="Select the relay that will be modified based on the watched action.">
                                <?php
                                for ($n = 0; $n < count($relay_id); $n++) {
                                echo '<option value="' . ($n+1) . '">' . ($n+1) . '</option>';
                                } ?>
                            </select>
                            <select style="width: 3em;" name="conditionco2<?php echo $i; ?>relaystate">
                                <option value="1">On</option>
                                <option value="0">Off</option>
                            </select>
                            (for
                            <input style="width: 4em;" type="number" step="any" value="0" maxlength=4 size=1 name="conditionco2<?php echo $i; ?>relaysecondson" title="The number of seconds for the relay to remain on. Leave at 0 to just turn it on or off." required/> sec)
                        </td>
                        <td rowspan="3" style="vertical-align:middle; padding: 0 0 0.8em 0.5em;">
                            <button type="submit" style="height:5em; width:4em;" name="AddCO2<?php echo $i; ?>Conditional" title="Save new conditional statement">Save</button>
                        </td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 0.3em;"><input type="checkbox" name="conditionco2<?php echo $i; ?>selcommand" value="1"> Execute command: <input style="width: 11em;" type="text" value="" maxlength=100 name="conditionco2<?php echo $i; ?>command" title="Command to execute in a linux shell."/></td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 1em;">
                            <input type="checkbox" name="conditionco2<?php echo $i; ?>selnotify" value="1"> Email <input style="width: 17em;" type="text" value="" name="conditionco2<?php echo $i; ?>notify" title="These are the email addresses that will be notified. Separate multiple email addresses with commas."/>
                        </td>
                    </tr>
                </table>
                </form>

                <?php
                if (isset($conditional_co2_id[$i]) && count($conditional_co2_id[$i]) > 0) {
                ?>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor_conditional">
                    <?php
                        for ($z = 0; $z < count($conditional_co2_id[$i]); $z++) {
                    ?>
                    <tr>
                        <td style="padding-top: 1em; padding-left: 1em; white-space: nowrap;">
                            <?php
                            echo '<button type="submit" name="DeleteCO2' . $i . '-' . $z . 'Conditional" title="Delete conditional statement">Delete</button> ';
                            if ($conditional_co2_state[$i][$z]) {
                                echo '<button style="width: 5em;" type="submit" name="TurnOffCO2' . $i . '-' . $z . 'Conditional" title="">Turn Off</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/on.png" alt="On" title="On"> ';
                            } else {
                                echo '<button style="width: 5em;" type="submit" name="TurnOnCO2' . $i . '-' . $z . 'Conditional" title="">Turn On</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/off.png" alt="Off" title="Off"> ';
                            }

                            echo $z+1 . ' ' . $conditional_co2_name[$i][$z] . ': Every ' . $conditional_co2_period[$i][$z] . ' sec, if CO<sub>2</sub> is ';

                            if ($conditional_co2_direction[$i][$z] == 1) {
                                echo 'Above ';
                            } else {
                                echo 'Below ';
                            }

                            echo $conditional_co2_setpoint[$i][$z] .  ' ppmv:</td>';

                            $first = 1;

                            if ($conditional_co2_sel_relay[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                }
                                echo '<td style="width: 100%;">Turn Relay ' . $conditional_co2_relay[$i][$z];

                                if ($conditional_co2_relay_state[$i][$z]) {
                                    echo ' On';
                                    if ($conditional_co2_relay_seconds_on[$i][$z] > 0) {
                                        echo ' for ' . $conditional_co2_relay_seconds_on[$i][$z] . ' seconds';
                                    }
                                } else {
                                    echo ' Off';
                                } 
                                echo '</td>';
                            }

                            if ($conditional_co2_sel_command[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                } else {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="padding-bottom: 0.3em;">Execute: <strong>' . htmlentities($conditional_co2_command[$i][$z]) . '</strong></td>';
                            }

                            if ($conditional_co2_sel_notify[$i][$z]) {
                                if (!$first) {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="width: 100%; white-space:normal;">Email <b>' . str_replace(",", ", ", $conditional_co2_notify[$i][$z]) . '</b></td>';
                            }

                            echo '</tr>';
                        } 
                    ?>
                    <tr><td style="padding-top:1em;"></td><td></td></tr>
                </table>
                </form>
                <?php
                    }
                ?>

                </div>
                <div style="margin-bottom: <?php if ($i == count($sensor_co2_id)) echo '2'; else echo '1'; ?>em;"></div>
                <?php
                } }
                ?>

            <?php if (count($sensor_press_id) > 0) { ?>
            <div style="clear: both;"></div>
            <div class="sensor-title">Pressure Sensors</div>
            <div style="clear: both;"></div>
                <?php
                for ($i = 0; $i < count($sensor_press_id); $i++) {
                ?>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <div class="sensor-parent">
                <table class="sensor">
                    <tr>
                        <td>Press Sensor <?php echo $i+1; ?><br><span style="font-size: 0.7em;">(<?php echo $sensor_press_id[$i]; ?>)</span></td>
                        <td>Sensor<br>Name</td>
                        <td>Sensor<br>Device</td>
                        <?php
                            if ($sensor_press_device[$i] == 'BMP085-180') {
                                echo '<td>I<sup>2</sup>C or<br>Multiplex</td>';
                            } else {
                                echo '<td>GPIO<br>Pin</td>';
                            }
                        ?>
                        <td>Log<br>Interval</td>
                        <td>Pre<br>Relay</td>
                        <td>Pre<br>Duration</td>
                        <td>Log</td>
                        <td>Graph</td>
                        <td style="padding: 0.2 0.5em;">
                            Presets: <select style="width: 7em;" name="sensorpress<?php echo $i; ?>preset">
                                <option value="default">default</option>
                                <?php
                                for ($z = 0; $z < count($sensor_press_preset); $z++) {
                                    echo '<option value="' . $sensor_press_preset[$z] . '">' . $sensor_press_preset[$z] . '</option>';
                                }
                                ?>
                            </select>
                        </td>
                    </tr>
                    <tr style="height: 2.5em;">
                        <td style="vertical-align: middle;">
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
                            <select style="width: 7em;" name="sensorpress<?php echo $i; ?>pin" title="If the sensor is connected directly to the I2C, select 'Use I2C'. If the sensor is connected through an I2C multiplexer (TCA9548A), select the multiplexer address and channel.">
                                <option<?php
                                    if ($sensor_ht_pin[$i] == 0) {
                                        echo ' selected="selected"';
                                    } ?> value="0">Use I2C</option>
                                <?php
                                for ($j = 1; $j < 79; $j++) {
                                    $count_str = str_split($j);
                                    if ($j < 10) {
                                        $count_str[1] = $count_str[0];
                                        $address = 0;
                                        $channel = $count_str[1];
                                    } else {
                                        $address = $count_str[0];
                                        $channel = $count_str[1];
                                    }
                                    if ($count_str[1] > 0 && $count_str[1] < 9) {
                                        echo '<option';
                                        if ($sensor_press_pin[$i] == $j) {
                                            echo ' selected="selected"';
                                        }
                                        echo ' value="' . $j . '">0x7' . $address . ' Ch. ' . $channel . '</option>';
                                    }
                                }
                                ?>
                            </select>
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
                            <input style="width: 4em;" type="number" min="0" max="99999" value="<?php echo $sensor_press_premeasure_dur[$i]; ?>" maxlength=2 size=1 name="sensorpress<?php echo $i; ?>premeasure_dur" title="The number of seconds the pre-measurement relay will run before the sensor measurement is obtained"/> sec
                        </td>
                        <td>
                            <input type="checkbox" title="Enable this sensor to record measurements to the log file" name="sensorpress<?php echo $i; ?>activated" value="1" <?php if ($sensor_press_activated[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <input type="checkbox" title="Enable graphs to be generated from the sensor log data" name="sensorpress<?php echo $i; ?>graph" value="1" <?php if ($sensor_press_graph[$i] == 1) echo 'checked'; ?>>
                        </td>
                        <td>
                            <div style="padding: 0.2em 0">
                                <input type="submit" name="Change<?php echo $i; ?>PressSensorLoad" value="Load" title="Load the selected preset Sensor and PID values"<?php if (count($sensor_press_preset) == 0) echo ' disabled'; ?>> <input type="submit" name="Change<?php echo $i; ?>PressSensorOverwrite" value="Save" title="Overwrite the selected saved preset (or default) sensor and PID values with those that are currently populated"> <input type="submit" name="Change<?php echo $i; ?>PressSensorDelete" value="Delete" title="Delete the selected preset"<?php if (count($sensor_press_preset) == 0) echo ' disabled'; ?>>
                            </div>
                            <div style="padding: 0.2em 0">
                                <input style="width: 5em;" type="text" value="" maxlength=12 size=10 name="sensorpress<?php echo $i; ?>presetname" title="Name of new preset to save"/> <input type="submit" name="Change<?php echo $i; ?>PressSensorNewPreset" value="New" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left"> <input type="submit" name="Change<?php echo $i; ?>PressSensorRenamePreset" value="Rename" title="Save a new preset with the currently-populated sensor and PID values, with the name from the box to the left">
                            </div>
                        </td>
                    </tr>
                </table>

                <table class="yaxis">
                    <tr>
                        <td rowspan=3>Graph Y-Axis<br>Range<br>&<br>Marks</td>
                        <td colspan=4>Relay</td>
                        <td colspan=4>Temperature (&deg;C)</td>
                        <td colspan=4>Pressure (kPa)</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                        <td style="padding-left: 1.5em;">Min</td>
                        <td>Max</td>
                        <td>Tics</td>
                        <td>mTics</td>
                    </tr>
                        <td style="padding-left: 1.5em;"    >
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_relay_min[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisRelayMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_relay_max[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisRelayMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_relay_tics[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisRelayTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_relay_mtics[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisRelayMTics" title=""/>
                        </td>
                        <td style="padding-left: 1.5em;">
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_temp_min[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisTempMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_temp_max[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisTempMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_temp_tics[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisTempTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_temp_mtics[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisTempMTics" title=""/>
                        </td>
                        <td style="padding-left: 1.5em;">
                            <input style="width: 5em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_press_min[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisPressMin" title=""/>
                        </td>
                        <td>
                            <input style="width: 5em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_press_max[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisPressMax" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_press_tics[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisPressTics" title=""/>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $sensor_press_yaxis_press_mtics[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>YAxisPressMTics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td rowspan="2">Relays to<br>Graph</td>
                        <td colspan="4" rowspan="2" style="padding-left: 1.5em;">Separate multiple relays with<br>commas or set 0 to disable</td>
                        <td colspan="2" style="padding-left: 1.5em;">Graph Up</td>
                        <td colspan="2">Graph Down</td>
                        <td colspan="2" style="padding-left: 1.5em;">Graph Up</td>
                        <td colspan="2">Graph Down</td>
                    </tr>
                        <td colspan="2" style="padding-left: 1.5em;">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_press_temp_relays_up[$i]; ?>" maxlength=20 name="SetPress<?php echo $i; ?>TempRelaysUp" title="These relays will be graphed with this sensor's condition and display above the y-axis 0."/>
                        </td>
                        <td colspan="2">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_press_temp_relays_down[$i]; ?>" maxlength=20 name="SetPress<?php echo $i; ?>TempRelaysDown" title="These relays will be graphed with this sensor's condition and display below the y-axis 0."/>
                        </td>
                        <td colspan="2" style="padding-left: 1.5em;">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_press_press_relays_up[$i]; ?>" maxlength=20 name="SetPress<?php echo $i; ?>PressRelaysUp" title="These relays will be graphed with this sensor's condition and display above the y-axis 0."/>
                        </td>
                        <td colspan="2">
                            <input style="width: 8em;" type="text" value="<?php echo $sensor_press_press_relays_down[$i]; ?>" maxlength=20 name="SetPress<?php echo $i; ?>PressRelaysDown" title="These relays will be graphed with this sensor's condition and display below the y-axis 0."/>
                        </td>
                    </tr>
                </table>

                <table class="pid">
                    <tr>
                        <td>PID Regulation</td>
                        <td>Activate</td>
                        <td>Set Point</td>
                        <td>Regulate</td>
                        <td>Measure<br>Interval</td>
                        <td>Up<br>Relay</td>
                        <td>Up<br>Min</td>
                        <td>Up<br>Max</td>
                        <td>Down<br>Relay</td>
                        <td>Down<br>Min</td>
                        <td>Down<br>Max</td>
                        <td>K<sub>p</sub></td>
                        <td>K<sub>i</sub></td>
                        <td>K<sub>d</sub></td>
                    </tr>
                    <tr style="height: 2.5em; background-color: #FFFFFF;">
                        <td style="text-align:left; padding-left:0.5em;"><?php
                            if ($pid_press_temp_or[$i] == 1) {
                                ?><img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                <?php
                            } else {
                                ?><img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                            <?php
                            }
                            ?> Temperature</td>
                        <td>
                            <?php
                            if ($pid_press_temp_or[$i] == 1) {
                                ?><button style="width: 5em;" type="submit" name="ChangePress<?php echo $i; ?>TempOR" value="0">Turn On</button>
                                <?php
                            } else {
                                ?><button style="width: 5em;" type="submit" name="ChangePress<?php echo $i; ?>TempOR" value="1">Turn Off</button>
                            <?php
                            }
                            ?>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_temp_set[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>TempSet" title="This is the desired temperature in °C."/> °C&nbsp;&nbsp;
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
                            <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_press_temp_period[$i]; ?>" name="SetPress<?php echo $i; ?>TempPeriod" title="This is the number of seconds between taking a new temperature measurement and applying the PID"/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_temp_relay_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempRelayLow" title="This relay is used to increase temperature."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_temp_outmin_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempOutminLow" title="This is the minimum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_temp_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempOutmaxLow" title="This is the maximum number of seconds the relay used to increase temperature is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_temp_relay_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempRelayHigh" title="This relay is used to decrease temperature."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_temp_outmin_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>TempOutminHigh" title="This is the minimum number of seconds the relay used to decrease temperature is permitted to turn on for (0 to disable)."/>
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
                    <tr style="height: 2.5em; background-color: #FFFFFF;">
                        <td style="text-align:left; padding-left:0.5em;"><?php
                            if ($pid_press_press_or[$i] == 1) {
                                ?><img style="height: 1em;" src="/mycodo/img/off.png" alt="Off" title="Off">
                                <?php
                            } else {
                                ?><img style="height: 1em;" src="/mycodo/img/on.png" alt="On" title="On">
                            <?php
                            }
                            ?> Pressure</td>
                        <td>
                            <?php
                            if ($pid_press_press_or[$i] == 1) {
                                ?><button style="width: 5em;" type="submit" name="ChangePress<?php echo $i; ?>PressOR" value="0">Turn On</button>
                                <?php
                            } else {
                                ?><button style="width: 5em;" type="submit" name="ChangePress<?php echo $i; ?>PressOR" value="1">Turn Off</button>
                            <?php
                            }
                            ?>
                        </td>
                        <td>
                            <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_press_press_set[$i]; ?>" maxlength=4 size=2 name="SetPress<?php echo $i; ?>PressSet" title="This is the desired relative pressure in percent."/> kPa
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
                            <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_press_press_period[$i]; ?>" name="SetPress<?php echo $i; ?>PressPeriod" title="This is the number of seconds between taking a new pressure measurement and applying the PID"/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_press_relay_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressRelayLow" title="This relay is used to increase pressure."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_press_outmin_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressOutminLow" title="This is the minimum number of seconds the relay used to increase pressure is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_press_outmax_low[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressOutmaxLow" title="This is the maximum number of seconds the relay used to increase pressure is permitted to turn on for (0 to disable)."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="30" value="<?php echo $pid_press_press_relay_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressRelayHigh" title="This relay is used to decrease pressure."/>
                        </td>
                        <td>
                            <input style="width: 3em;" type="number" min="0" max="9999" value="<?php echo $pid_press_press_outmin_high[$i]; ?>" maxlength=1 size=1 name="SetPress<?php echo $i; ?>PressOutminHigh" title="This is the minimum number of seconds the relay used to decrease pressure is permitted to turn on for (0 to disable)."/>
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


                <table class="conditional">
                    <tr>
                        <td>
                            Conditional Statements<br/><span style="padding-top: 0.5em;font-size: 0.7em;">Note: Ensure these conditional statements don't produce conflicts with themselves or interfere with running PID controllers.</span>
                        </td>
                    </tr>
                </table>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor-conditional">
                    <tr>
                        <td style="padding-left: 1em;">
                            Name: 
                            <input style="width: 5em;" type="text" step="any" value="" maxlength=12 size=1 name="conditionpress<?php echo $i; ?>name" title="" required/>
                            Every <input style="width: 4em;" type="number" step="any" value="360" maxlength=4 size=1 name="conditionpress<?php echo $i; ?>period" title="" required/> sec,
                            if <select style="width: 6em;" name="conditionpress<?php echo $i; ?>condition">
                                <option value="Pressure">Pressure</option>
                                <option value="Temperature">Temperature</option>
                            </select>
                            is
                            <select style="width: 5em;" name="conditionpress<?php echo $i; ?>direction">
                                <option value="1">Above</option>
                                <option value="-1">Below</option>
                            </select>
                            <input style="width: 4em;" type="number" step="any" value="" maxlength=4 size=1 name="conditionpress<?php echo $i; ?>setpoint" title="" required/>: 
                        </td>
                        <td style="padding-bottom: 0.3em;">
                            <input type="checkbox" name="conditionpress<?php echo $i; ?>selrelay" value="1" checked> Turn Relay
                            <select style="width: 3em;" name="conditionpress<?php echo $i; ?>relay" title="Select the relay that will be modified based on the watched action.">
                                <?php
                                for ($n = 0; $n < count($relay_id); $n++) {
                                echo '<option value="' . ($n+1) . '">' . ($n+1) . '</option>';
                                } ?>
                            </select>
                            <select style="width: 3em;" name="conditionpress<?php echo $i; ?>relaystate">
                                <option value="1">On</option>
                                <option value="0">Off</option>
                            </select>
                            (for
                            <input style="width: 4em;" type="number" step="any" value="0" maxlength=4 size=1 name="conditionpress<?php echo $i; ?>relaysecondson" title="The number of seconds for the relay to remain on. Leave at 0 to just turn it on or off." required/> sec)
                        </td>
                        <td rowspan="3" style="vertical-align:middle; padding: 0 0 0.8em 0.5em;">
                            <button type="submit" style="height:5em; width:4em;" name="AddPress<?php echo $i; ?>Conditional" title="Save new conditional statement">Save</button>
                        </td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 0.3em;"><input type="checkbox" name="conditionpress<?php echo $i; ?>selcommand" value="1"> Execute command: <input style="width: 11em;" type="text" value="" maxlength=100 name="conditionpress<?php echo $i; ?>command" title="Command to execute in a linux shell."/></td>
                    </tr>
                    <tr>
                        <td></td>
                        <td style="padding-bottom: 1em;">
                            <input type="checkbox" name="conditionpress<?php echo $i; ?>selnotify" value="1"> Email <input style="width: 17em;" type="text" value="" name="conditionpress<?php echo $i; ?>notify" title="These are the email addresses that will be notified. Separate multiple email addresses with commas."/>
                        </td>
                    </tr>
                </table>
                </form>

                <?php
                if (isset($conditional_press_id[$i]) && count($conditional_press_id[$i]) > 0) {
                ?>
                <form action="?tab=sensor<?php if (isset($_GET['r']))  echo '&r=' , $_GET['r']; ?>" method="POST">
                <table class="sensor_conditional">
                    <?php
                        for ($z = 0; $z < count($conditional_press_id[$i]); $z++) {
                    ?>
                    <tr>
                        <td style="padding-top: 1em; padding-left: 1em; white-space: nowrap;">
                            <?php
                            echo '<button type="submit" name="DeletePress' . $i . '-' . $z . 'Conditional" title="Delete conditional statement">Delete</button> ';
                            if ($conditional_press_state[$i][$z]) {
                                echo '<button style="width: 5em;" type="submit" name="TurnOffPress' . $i . '-' . $z . 'Conditional" title="">Turn Off</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/on.png" alt="On" title="On"> ';
                            } else {
                                echo '<button style="width: 5em;" type="submit" name="TurnOnPress' . $i . '-' . $z . 'Conditional" title="">Turn On</button> <img style="height: 1em; padding: 0 0.5em;" src="/mycodo/img/off.png" alt="Off" title="Off"> ';
                            }

                            echo $z+1 . ' ' . $conditional_press_name[$i][$z] . ': Every ' . $conditional_press_period[$i][$z] . ' sec, if the ' . $conditional_press_condition[$i][$z] . ' is ';

                            if ($conditional_press_direction[$i][$z] == 1) {
                                echo 'Above ';
                            } else {
                                echo 'Below ';
                            }

                            echo $conditional_press_setpoint[$i][$z];

                            if ($conditional_press_condition[$i][$z] == "Pressure") {
                                echo ' kPa:';
                            } else {
                                echo '&deg;C:';
                            }

                            echo ':</td>';

                            $first = 1;

                            if ($conditional_press_sel_relay[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                }
                                echo '<td style="width: 100%;">Turn Relay ' . $conditional_press_relay[$i][$z];

                                if ($conditional_press_relay_state[$i][$z]) {
                                    echo ' On';
                                    if ($conditional_press_relay_seconds_on[$i][$z] > 0) {
                                        echo ' for ' . $conditional_press_relay_seconds_on[$i][$z] . ' seconds';
                                    }
                                } else {
                                    echo ' Off';
                                } 
                                echo '</td>';
                            }

                            if ($conditional_press_sel_command[$i][$z]) {
                                if ($first) {
                                    $first = 0;
                                } else {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="padding-bottom: 0.3em;">Execute: <strong>' . htmlentities($conditional_press_command[$i][$z]) . '</strong></td>';
                            }

                            if ($conditional_press_sel_notify[$i][$z]) {
                                if (!$first) {
                                    echo '</tr><tr><td></td>';
                                }
                                echo '<td style="width: 100%; white-space:normal;">Email <b>' . str_replace(",", ", ", $conditional_press_notify[$i][$z]) . '</b></td>';
                            }

                            echo '</tr>';
                        } 
                    ?>
                    <tr><td style="padding-top:1em;"></td><td></td></tr>
                </table>
                </form>
                <?php
                    }
                ?>

                </div>
                <div style="margin-bottom: <?php if ($i == count($sensor_ht_id)) echo '2'; else echo '1'; ?>em;"></div>
                <?php
                } }
                ?>

        </li>

        <li data-content="custom" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'custom') {
                echo 'class="selected"';
            } ?>>

            <?php
            if (isset($custom_error)) {
                echo '<div class="error">' . $custom_error . '</div>';
            }
            ?>

            <?php
            /* DateSelector, modified from work by Leon Atkinson */
            if (isset($_POST['SubmitDates']) and $current_user_restriction != 'guest') {
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
                    $time_from = strtotime($monb . "/" . $dayb . "/" . $yearb . " " .  $hourb . ":" . $minb);
                    $time_to = strtotime($mone . "/" . $daye . "/" . $yeare . " " .  $houre . ":" . $mine);

                    if (is_positive_integer($_POST['graph-width']) and $_POST['graph-width'] <= 4000 and $_POST['graph-width']) {
                        $graph_width = $_POST['graph-width'];
                    } else {
                        $graph_width = 950;
                    }

                    $image_path = '/var/www/mycodo/images/';

                    if ($_POST['custom_type'] == 'Combined') {
                        shell_exec("$mycodo_client --graph combined $id2 x $time_from $time_to $graph_width");
                        $first = False;
                        if (array_sum($sensor_t_graph) || array_sum($sensor_ht_graph)) {
                            if ($first) echo '<hr class="fade"/>';
                            else $first = True;
                            $file_name = 'graph-temp-combined-' . $id2 . '.png';
                            echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                <img class="main-image" style="max-width:100%;height:auto;" src=file.php?';
                            echo 'graphtype=combinedcustom';
                            echo '&sensortype=temp';
                            echo '&id=' , $id2 , '>';
                            echo '</div>';
                        }

                        if (array_sum($sensor_ht_graph)) {
                            if ($first) echo '<hr class="fade"/>';
                            else $first = True;
                            $file_name = 'graph-hum-combined-' . $id2 . '.png';
                            echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                <img class="main-image" style="max-width:100%;height:auto;" src=file.php?';
                            echo 'graphtype=combinedcustom';
                            echo '&sensortype=hum';
                            echo '&id=' , $id2 , '>';
                            echo '</div>';
                        }

                        if (array_sum($sensor_co2_graph)) {
                            if ($first) echo '<hr class="fade"/>';
                            else $first = True;
                            $file_name = 'graph-co2-combined-' . $id2 . '.png';
                            echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                <img class="main-image" style="max-width:100%;height:auto;" src=file.php?';
                            echo 'graphtype=combinedcustom';
                            echo '&sensortype=co2';
                            echo '&id=' , $id2 , '>';
                            echo '</div>';
                        }

                        if (array_sum($sensor_press_graph)) {
                            if ($first) echo '<hr class="fade"/>';
                            else $first = True;
                            $file_name = 'graph-press-combined-' . $id2 . '.png';
                            echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                <img class="main-image" style="max-width:100%;height:auto;" src=file.php?';
                            echo 'graphtype=combinedcustom';
                            echo '&sensortype=press';
                            echo '&id=' , $id2 , '>';
                            echo '</div>';
                        }
                    } else if ($_POST['custom_type'] == 'Separate') {
                        shell_exec("$mycodo_client --graph separate $id2 x $time_from $time_to $graph_width");
                        $first = False;
                        for ($n = 0; $n < count($sensor_t_id); $n++) {
                            if ($sensor_t_graph[$n] == 1) {
                                if ($first) echo '<hr class="fade"/>';
                                else $first = True;
                                $file_name = 'graph-t-separate-x-' . $id2 . '-' . $n . '.png';
                                echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                    <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                    <img src=file.php?';
                                echo 'graphtype=separatecustom';
                                echo '&sensortype=t';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                        }
                        for ($n = 0; $n < count($sensor_ht_id); $n++) {
                            if ($sensor_ht_graph[$n] == 1) {
                                if ($first) echo '<hr class="fade"/>';
                                else $first = True;
                                $file_name = 'graph-ht-separate-x-' . $id2 . '-' . $n . '.png';
                                echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                    <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                    <img src=file.php?';
                                echo 'graphtype=separatecustom';
                                echo '&sensortype=ht';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                        }
                        for ($n = 0; $n < count($sensor_co2_id); $n++) {
                            if ($sensor_co2_graph[$n] == 1) {
                                if ($first) echo '<hr class="fade"/>';
                                else $first = True;
                                $file_name = 'graph-co2-separate-x-' . $id2 . '-' . $n . '.png';
                                echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                    <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                    <img src=file.php?';
                                echo 'graphtype=separatecustom';
                                echo '&sensortype=co2';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                        }
                        for ($n = 0; $n < count($sensor_press_id); $n++) {
                            if ($sensor_press_graph[$n] == 1) {
                                if ($first) echo '<hr class="fade"/>';
                                else $first = True;
                                $file_name = 'graph-press-separate-x-' . $id2 . '-' . $n . '.png';
                                echo '<div style="padding: 1em 0 1em 0; text-align: center;">
                                    <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $image_path . '" /><input type="hidden" name="file_name" value="' . $file_name . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Graph</button></form>
                                    <img src=file.php?';
                                echo 'graphtype=separatecustom';
                                echo '&sensortype=press';
                                echo '&id=' , $id2;
                                echo '&sensornumber=' , $n , '>';
                                echo '</div>';
                            }
                        }
                    }
                }
            } else if (isset($_POST['SubmitDates']) and $current_user_restriction == 'guest') {
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
                echo '<div class="error">' . $camera_error . '</div>';
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
                <div style="float: left; padding: 0 2em 1em 0.5em;">
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
                <div style="float: left; padding: 0 2em 1em 0;">
                    <div style="float: left; padding-right: 0.1em;">
                        <button name="Refresh" type="submit" value="">Refresh<br>Page</button>
                    </div>
                </div>
            </div>

            <div>
                <div style="float: left; padding: 0.5em 1.5em;">
                    <button name="CaptureStill" type="submit" value="">Capture<br>Still</button>
                </div>

                <div style="float: left; padding: 0.5em 1.5em;">
                    <div>
                        <?php
                        if (!file_exists($lock_mjpg_streamer)) {
                            echo '<button name="start-stream" type="submit" value="">Start<br>Stream</button>';
                        } else {
                            echo '<button name="stop-stream" type="submit" value="">Stop<br>Stream</button>';
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

                <div style="float: left; padding: 0.5em 1.5em;">
                    <div>
                        <?php
                        if (!file_exists($lock_timelapse)) {
                            echo '<button name="start-timelapse" type="submit" value="">Start<br>Timelapse</button>';
                        } else {
                            echo '<button name="stop-timelapse" type="submit" value="">Stop<br>Timelapse</button>';
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
                    echo 'End Time: ' , date("F d Y H:i:s", $start_time+($runtime*60)) , '<br>';
                }

                
                if ($timelapse_dir == 'Not empty') {
                    $files = scandir($timelapse_path, SCANDIR_SORT_DESCENDING);
                    $newest_file = $files[0];
                    $latest_file = filectime("$timelapse_path/$newest_file");
                    echo 'Latest File: ' , date("F d Y H:i:s", $latest_file) , '<br>';
                    echo '
                    <div style="padding: 0.5em 0 2em 0;">
                        <img src="file.php?span=cam-timelapse" style="width:100%">
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
                    <img style="width:100%;" src="file.php?span=stream">
                </div>
                ';
            }

            $cam_stills_path = $install_path . '/camera-stills/';
            $cam_stills_dir = (count(glob("$cam_stills_path*")) === 0) ? 'Empty' : 'Not empty';
            if ($cam_stills_dir == 'Not empty' && (isset($_POST['CaptureStill']) || $still_display_last)) {
                $files = scandir($cam_stills_path, SCANDIR_SORT_DESCENDING);
                $newest_file = $files[0];
                $latest_file = filemtime("$cam_stills_path/$newest_file");
                echo '
                <table class="camera-still">
                    <tr>
                        <td>
                            Still Image
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <form action="?tab=data" method="POST"><input type="hidden" name="file_path" value="' . $cam_stills_path . '" /><input type="hidden" name="file_name" value="' . $newest_file . '" /><button type="submit" name="Add_Image_Note" value="">Create Note with Image</button>
                            </form>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            Latest File: ' , date("F d Y H:i:s", $latest_file) , '
                        </td>
                    </tr>
                    </table>';
                echo '
                <div style="padding-bottom: 2em;">
                    <img style="width:100%;" src=file.php?span=cam-still>
                </div>
                ';
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
                echo '<div class="error">' . $data_error . '</div>';
            }
            ?>

            <div style="padding: 10px 0 0 15px;">
                <form action="?tab=data" method="POST">
                <table class="data-buttons">
                    <tr>
                        <td rowspan="2" class="data-buttons-rightspace" style="vertical-align:middle; text-align:center; line-height:1.6em;">
                            Last<br><input style="width: 4em;" type="text" maxlength="8" name="Lines" value="<?php if (isset($_POST['Lines']) && $_POST['Lines'] != '') echo $_POST['Lines']; else echo '30'; ?>" title="The maximum number of lines to display. Defaults to 30 if left blank."/><br>Lines
                        </td>
                        <td>
                            <button style="width:100%" type="submit" name="TSensor_Changes" value="T">T<br>Δ</button>
                        </td>
                        <td>
                            <button style="width:100%" type="submit" name="HTSensor_Changes" value="HT">HT<br>Δ</button>
                        </td>
                        <td>
                            <button style="width:100%" type="submit" name="CO2Sensor_Changes" value="CO2">CO2<br>Δ</button>
                        </td>
                        <td class="data-buttons-rightspace">
                            <button style="width:100%" type="submit" name="PressSensor_Changes" value="Press">Press<br>Δ</button>
                        </td>
                        <td>
                            <button type="submit" name="Relay_Changes" value="Relay">Relay<br>Δ</button>
                        </td>
                        <td class="data-buttons-rightspace">
                            <button type="submit" name="Timer_Changes" value="Timer">Timer<br>Δ</button>
                        </td>
                        <td>
                            <button type="submit" name="Daemon" value="Daemon">Daemon<br>Log</button>
                        </td>
                        <td>
                            <button type="submit" name="Commits" value="Update Log">Git<br>Commits</button>
                        </td>
                        <td class="data-buttons-rightspace">
                            <button style="width:100%" type="submit" name="Update" value="Update Log">Update<br>Log</button>
                        </td>
                        <td class="data-buttons-rightspace">
                            <button type="submit" name="Users" value="User Database">User<br>Database</button>
                        </td>
                        <td>
                            <button style="width:100%" type="submit" name="Notes" value="Notes">Notes<br>&nbsp;</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <button type="submit" name="TSensor" value="T">T<br>Sensor</button>
                        </td>
                        <td>
                            <button type="submit" name="HTSensor" value="HT">HT<br>Sensor</button>
                        </td>
                        <td>
                            <button type="submit" name="CO2Sensor" value="CO2">CO2<br>Sensor</button>
                        </td>
                        <td class="data-buttons-rightspace">
                            <button type="submit" name="PressSensor" value="Press">Press<br>Sensor</button>
                        </td>
                        <td>
                            <button type="submit" name="Relay" value="Relay">Relay<br>Log</button>
                        </td>
                        <td class="data-buttons-rightspace">
                            <button style="width:100%" type="submit" name="RelayUsage" value="" title="Display the relay duration and power usage statistics">Relay<br>Usage</button>
                        </td>
                        <td>
                            <button style="width:100%" type="submit" name="Login" value="Login">Login<br>Log</button>
                        </td>
                        <td>
                            <button style="width:100%" type="submit" name="Backups" value="">Backup/<br>Restore</button>
                        </td>
                        <td class="data-buttons-rightspace">
                            <button type="submit" name="Restore" value="">Restore<br>Log</button>
                        </td>
                        <td>
                            <button type="submit" name="Database" value="Mycodo Database">Mycodo<br>Database</button>
                        </td>
                    </tr>
                </table>
                </form>

                <div style="clear: both;"></div>
                <div style="font-family: monospace; padding-top:1em; white-space: normal;">
                    <?php
                        if(isset($_POST['TSensor'])) {
                            echo "<pre>Temperature Sensor Log<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S Tc Sensor\n$(cat /var/www/mycodo/log/sensor-t.log /var/www/mycodo/log/sensor-t-tmp.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S Tc Sensor\n$(cat /var/www/mycodo/log/sensor-t.log /var/www/mycodo/log/sensor-t-tmp.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['TSensor_Changes'])) {
                            echo "<pre>Temperature Sensor Changes<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S ID Name Device Pin/Ser# Period PreRelay PreDur Log Graph YRelayMin YRelayMax YRelayTics YRelayMTics YTempMin YTempMax YTempTics YTempMTics TempRelaysUp TempRelaysDown TempRelayHigh TempRelayHighMin TempRelayHighMax TempRelayLow TempRelayLowMin TempRelayLowMax TempSet TempSetDir TempPeriod TempP TempI TempD\n$(cat /var/www/mycodo/log/sensor-t-changes.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S ID Name Device Pin/Ser# Period PreRelay PreDur Log Graph YRelayMin YRelayMax YRelayTics YRelayMTics YTempMin YTempMax YTempTics YTempMTics TempRelaysUp TempRelaysDown TempRelayHigh TempRelayHighMin TempRelayHighMax TempRelayLow TempRelayLowMin TempRelayLowMax TempSet TempSetDir TempPeriod TempP TempI TempD\n$(cat /var/www/mycodo/log/sensor-t-changes.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }
                        
                        if(isset($_POST['HTSensor'])) {
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                            } else {
                                $Lines = 30;
                            }
                            echo "<pre>Temperature/Humidity Sensor Log (Last $Lines lines)<br>";
                            echo '
                                <table class="data-data">
                                    <tr>
                                        <th>Y/M/D-H:M:S</th>
                                        <th>Temperature<br>(&deg;C)</th>
                                        <th>Relative<br>Humidity<br>(%)</th>
                                        <th>DewPoint<br>(&deg;C)</th>
                                        <th>Sensor</th>
                                    </tr>
                                    <tr>
                                        <td>';
                            echo `echo "$(cat /var/www/mycodo/log/sensor-ht.log /var/www/mycodo/log/sensor-ht-tmp.log | tail -n $Lines)" | column -t | tail -n +2 | tr -s " " | sed 's/ /\<\/td\>\<td\>/g' | awk '{ print $0; }' RS='\n' ORS='</td></tr><tr><td>'`;
                            echo 'End</td></tr></table></pre>';
                        }

                        if(isset($_POST['HTSensor_Changes'])) {
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                            } else {
                                $Lines = 30;
                            }
                            echo "<pre>Temperature/Humidity Sensor Changes (Last $Lines lines)<br>";
                            echo '
                                <table class="data-data">
                                    <tr>
                                        <th>Y/M/D-H:M:S</th>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Device</th>
                                        <th>GPIO</th>
                                        <th>Period</th>
                                        <th>Pre<br>Relay</th>
                                        <th>Pre<br>Dur</th>
                                        <th>Log</th>
                                        <th>Graph</th>
                                        <th>Verify<br>Pin</th>
                                        <th>Verify<br>Temp</th>
                                        <th>Verify<br>Temp<br>Notify</th>
                                        <th>Verify<br>Temp<br>Stop</th>
                                        <th>Verify<br>Hum</th>
                                        <th>Verify<br>Hum<br>Notify</th>
                                        <th>Verify<br>Hum<br>Stop</th>
                                        <th>Verify<br>Email</th>
                                        <th>YRelay<br>Min</th>
                                        <th>YRelay<br>Max</th>
                                        <th>YRelay<br>Tics</th>
                                        <th>YRelay<br>MTics</th>
                                        <th>YTemp<br>Min</th>
                                        <th>YTemp<br>Max</th>
                                        <th>YTemp<br>Tics</th>
                                        <th>YTemp<br>MTics</th>
                                        <th>Temp<br>Relays<br>Up</th>
                                        <th>Temp<br>Relays<br>Down</th>
                                        <th>Temp<br>Relay<br>High</th>
                                        <th>Temp<br>Relay<br>High<br>Min</th>
                                        <th>Temp<br>Relay<br>High<br>Max</th>
                                        <th>Temp<br>Relay<br>Low</th>
                                        <th>Temp<br>Relay<br>Low<br>Min</th>
                                        <th>Temp<br>Relay<br>Low<br>Max</th>
                                        <th>Temp<br>Set</th>
                                        <th>Temp<br>Set<br>Dir</th>
                                        <th>Temp<br>Period</th>
                                        <th>Temp<br>K<sub>P</sub></th>
                                        <th>Temp<br>K<sub>I</sub></th>
                                        <th>Temp<br>K<sub>D</sub></th>
                                        <th>Hum<br>Relays<br>Up</th>
                                        <th>Hum<br>Relays<br>Down</th>
                                        <th>Hum<br>Relay<br>High</th>
                                        <th>Hum<br>Relay<br>High<br>Min</th>
                                        <th>Hum<br>Relay<br>High<br>Max</th>
                                        <th>Hum<br>Relay<br>Low</th>
                                        <th>Hum<br>Relay<br>Low<br>Min</th>
                                        <th>Hum<br>Relay<br>Low<br>Max</th>
                                        <th>Hum<br>Set</th>
                                        <th>Hum<br>Set<br>Dir</th>
                                        <th>Hum<br>Period</th>
                                        <th>Hum<br>K<sub>P</sub></th>
                                        <th>Hum<br>K<sub>I</sub></th>
                                        <th>Hum<br>K<sub>D</sub></th>
                                    </tr>
                                    <tr>
                                        <td>';
                            echo `echo "$(cat /var/www/mycodo/log/sensor-ht-changes.log | tail -n $Lines)" | column -t | tail -n +2 | tr -s " " | sed 's/ /\<\/td\>\<td\>/g' | awk '{ print $0; }' RS='\n' ORS='</td></tr><tr><td>'`;
                            echo 'End</td></tr></table></pre>';
                        }

                        if(isset($_POST['CO2Sensor'])) {
                            echo "<pre>CO<sub>2</sub> Sensor Log<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S CO2 Sensor\n$(cat /var/www/mycodo/log/sensor-co2.log /var/www/mycodo/log/sensor-co2-tmp.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S CO2 Sensor\n$(cat /var/www/mycodo/log/sensor-co2.log /var/www/mycodo/log/sensor-co2-tmp.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['CO2Sensor_Changes'])) {
                            echo "<pre>CO<sub>2</sub> Sensor Changes<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S ID Name Device GPIO Period PreRelay PreDur Log Graph YRelayMin YRelayMax YRelayTics YRelayMTics YCO2Min YCO2Max YCO2Tics YCO2MTics CO2RelaysUp CO2RelaysDown CO2RelayHigh CO2RelayHighMin CO2RelayHighMax CO2RelayLow CO2RelayLowMin CO2RelayLowMax CO2Set CO2SetDir CO2Period CO2P CO2I CO2D\n$(cat /var/www/mycodo/log/sensor-co2-changes.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S ID Name Device GPIO Period PreRelay PreDur Log Graph YRelayMin YRelayMax YRelayTics YRelayMTics YCO2Min YCO2Max YCO2Tics YCO2MTics CO2RelaysUp CO2RelaysDown CO2RelayHigh CO2RelayHighMin CO2RelayHighMax CO2RelayLow CO2RelayLowMin CO2RelayLowMax CO2Set CO2SetDir CO2Period CO2P CO2I CO2D\n$(cat /var/www/mycodo/log/sensor-co2-changes.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['PressSensor'])) {
                            echo "<pre>Pressure Sensor Log<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S Temperature(C) Pressure(kPa) Altitude(m) Sensor\n$(cat /var/www/mycodo/log/sensor-press.log /var/www/mycodo/log/sensor-press-tmp.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S Temperature(C) Pressure(kPa) Altitude(m) Sensor\n$(cat /var/www/mycodo/log/sensor-press.log /var/www/mycodo/log/sensor-press-tmp.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['PressSensor_Changes'])) {
                            echo "<pre>Temperature/Pressure Sensor Changes<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S ID Name Device GPIO Period PreRelay PreDur Log Graph YRelayMin YRelayMax YRelayTics YRelayMTics YTempMin YTempMax YTempTics YTempMTics TempRelaysUp TempRelaysDown TempRelayHigh TempRelayHighMin TempRelayHighMax TempRelayLow TempRelayLowMin TempRelayLowMax TempSet TempSetDir TempPeriod TempP TempI TempD PressRelaysUp PressRelaysDown PressRelayHigh PressRelayHighMin PressRelayHighMax PressRelayLow PressRelayLowMin PressRelayLowMax PressSet PressSetDir PressPeriod PressP PressI PressD\n$(cat /var/www/mycodo/log/sensor-press-changes.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S ID Name Device GPIO Period PreRelay PreDur Log Graph YRelayMin YRelayMax YRelayTics YRelayMTics YTempMin YTempMax YTempTics YTempMTics TempRelaysUp TempRelaysDown TempRelayHigh TempRelayHighMin TempRelayHighMax TempRelayLow TempRelayLowMin TempRelayLowMax TempSet TempSetDir TempPeriod TempP TempI TempD PressRelaysUp PressRelaysDown PressRelayHigh PressRelayHighMin PressRelayHighMax PressRelayLow PressRelayLowMin PressRelayLowMax PressSet PressSetDir PressPeriod PressP PressI PressD\n$(cat /var/www/mycodo/log/sensor-press-changes.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['Relay'])) {
                            echo "<pre>Relay Log<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S Sensor Relay GPIO SecondsOn\n$(cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S Sensor Relay GPIO SecondsOn\n$(cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['Relay_Changes'])) {
                            echo "<pre>Relay Changes<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S Relay Name GPIO Amps Trigger State\n$(cat /var/www/mycodo/log/relay-changes.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S Relay Name GPIO Amps Trigger State\n$(cat /var/www/mycodo/log/relay-changes.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['Timer_Changes'])) {
                            echo "<pre>Timer Changes<br> <br>";
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `echo "Y/M/D-H:M:S ID Name Relay DurationOn DurationOff\n$(cat /var/www/mycodo/log/timer-changes.log | tail -n $Lines)" | column -t`;
                            } else {
                                echo `echo "Y/M/D-H:M:S ID Name Relay DurationOn DurationOff\n$(cat /var/www/mycodo/log/timer-changes.log | tail -n 30)" | column -t`;
                            }
                            echo '</pre>';
                        }

                        if (isset($_POST['Notes']) || isset($_POST['Delete_Note']) || isset($_POST['Add_Note']) || isset($_POST['Edit_Note_Save'])) {
                            echo "Notes<br> <br>
                            <form action=\"?tab=data\" method=\"POST\" enctype=\"multipart/form-data\">
                            <table style=\"width:100%;\">
                                <tr>
                                    <td style=\"padding-bottom: 0.2em;\"><input style=\"width: 100%;\" type=\"text\" placeholder=\"Title\" maxlength=\"200\" name=\"Note_Title\"></td>
                                </tr>
                                <tr>
                                    <td colspan=\"2\">
                                        <textarea style=\"width: 40em;\" placeholder=\"Note\" rows=\"6\" maxlength=\"100000\" name=\"Note_Text\"></textarea>
                                    </td>
                                    <td style=\"vertical-align: top; height:100%; width:100%;\">
                                        <table style=\"height:100%; width:100%;\">
                                            <tr>
                                                <td style=\"padding: 0 0 0.4em 0.4em; vertical-align: top; height:1em;\">
                                                    Upload (hold Ctrl to select multiple files):
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style=\"padding-left: 0.4em; vertical-align: top;\">
                                                    <input id='upload' name=\"notes[]\" type=\"file\" multiple=\"multiple\" />
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style=\"padding: 0.4em 0 0 0.4em; vertical-align: bottom;\">
                                                    <button style=\"width:5.7em;\" type=\"submit\" name=\"Add_Note\" value=\"\">Save<br>Note</button>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    
                                </tr>
                            </table><br> <br>";

                            $ndb = new SQLite3($note_db);
                            unset($note_id);
                            $results = $ndb->query('SELECT Id, Time, User, Title, Note FROM Notes');
                            $i = 0;
                            while ($row = $results->fetchArray()) {
                                $note_id[$i] = $row[0];
                                $note_time[$i] = $row[1];
                                $note_user[$i] = $row[2];
                                $note_title[$i] = $row[3];
                                $note_note[$i] = $row[4];
                                $i++;
                            }
                            if (!isset($note_id)) $note_id = [];
                            else {
                                echo "<table class=\"notes\">
                                    <tr>
                                        <td></td>
                                        <td style=\"padding-bottom:0.5em;\">#</td>
                                        <td>Time</td>
                                        <td>User</td>
                                        <td>Note</td>
                                    </tr>";
                                for ($u = count($note_id)-1; $u >= 0; $u--) {
                                    echo "<tr>
                                        <td style=\"white-space: nowrap; border-style: solid none none none; border-width: 1px;\"><button style=\"width:5em;\" type=\"submit\" name=\"Delete_Note\" value=\"$note_id[$u]\">Delete</button> <button style=\"width:5em;\" type=\"submit\" name=\"Edit_Note\" value=\"$note_id[$u]\">Edit</button></td>
                                        <td style=\"border-style: solid none none none; border-width: 1px;\">$u</td>
                                        <td style=\"border-style: solid none none none; border-width: 1px; line-height:1.5em; white-space: nowrap;\">$note_time[$u]</td>
                                        <td style=\"border-style: solid none none none; border-width: 1px;\">$note_user[$u]</td>
                                        <td style=\"width: 100%; border-style: solid none none none; border-width: 1px; padding-bottom: 0.7em;\" colspan=\"2\" class=\"wrap\"><div style=\"padding-bottom: 0.5em; font-weight: bold;\">" . htmlspecialchars($note_title[$u]) . "</div>" . htmlspecialchars($note_note[$u]) . "</td>
                                    </tr>";

                                    unset($upload_id);
                                    $results = $ndb->query("SELECT Id, Name, File_Name, Location FROM Uploads WHERE Id='" . $note_id[$u] . "'");
                                    $i = 0;
                                    while ($row = $results->fetchArray()) {
                                        $upload_id[$i] = $row[0];
                                        $upload_name[$i] = $row[1];
                                        $upload_file_name[$i] = $row[2];
                                        $upload_location[$i] = $row[3];
                                        $i++;
                                    }
                                    if (!isset($upload_id)) $upload_id = [];
                                    else {
                                        echo "<tr><td colspan=\"4\"></td><td style=\"padding-bottom:0.5em;\">Files: ";
                                        for ($v = 0; $v < count($upload_id); $v++) {
                                            echo "<a href=\"file.php?span=ul-dl&file=$upload_file_name[$v]\">$upload_name[$v]</a>";
                                            if ($v != count($upload_id)-1) echo ", ";
                                        }
                                        echo "</td></tr>";

                                        $images = False;
                                        for ($v = 0; $v < count($upload_id); $v++) {
                                            if (endswith($upload_name[$v], '.jpg') || endswith($upload_name[$v], '.jpeg') || endswith($upload_name[$v], '.png') || endswith($upload_name[$v], '.gif')) {
                                                $images = True;
                                            }
                                        }

                                        if ($images == True) {
                                            echo "<tr><td colspan=\"4\"></td><td>";
                                        }
                                        for ($v = 0; $v < count($upload_id); $v++) {
                                            if (endswith($upload_name[$v], '.jpg') || endswith($upload_name[$v], '.jpeg')) {
                                                echo "<div style=\"float: left; padding:0.4em;\"><a target=\"_blank\" href=\"file.php?span=ul-jpg&file=$upload_file_name[$v]\"><img class=\"thumbnail\" src=\"file.php?span=ul-jpg&file=thumb$upload_file_name[$v]\"></a></div>";
                                            }
                                            if (endswith($upload_name[$v], '.png')) {
                                                echo "<div style=\"float: left; padding:0.4em;\"><a target=\"_blank\" href=\"file.php?span=ul-png&file=$upload_file_name[$v]\"><img class=\"thumbnail\" src=\"file.php?span=ul-png&file=thumb$upload_file_name[$v]\"></a></div>";
                                            }
                                            if (endswith($upload_name[$v], '.gif')) {
                                                echo "<div style=\"float: left; padding:0.4em;\"><a target=\"_blank\" href=\"file.php?span=ul-gif&file=$upload_file_name[$v]\"><img class=\"thumbnail\" src=\"file.php?span=ul-gif&file=thumb$upload_file_name[$v]\"></a></div>";
                                            }
                                        }
                                        if ($images == True) {
                                            echo "</td></tr>";
                                        }
                                    }
                                }
                                echo "</table>";
                            }
                            echo "</form>";
                        }

                        if (isset($_POST['Edit_Note']) || isset($_POST['Add_Image_Note']) || isset($_GET['displaynote'])) {
                            echo "Edit Note<br> <br>";
                            $ndb = new SQLite3($note_db);
                            unset($note_id);
                            if (isset($_GET['displaynote'])) {
                                $results = $ndb->query("SELECT Id, Time, User, Title, Note FROM Notes WHERE Id='" . $_GET['noteid'] . "'");
                            } else {
                                $results = $ndb->query("SELECT Id, Time, User, Title, Note FROM Notes WHERE Id='" . $_POST['Edit_Note'] . "'");
                            }
                            while ($row = $results->fetchArray()) {
                                $note_id = $row[0];
                                $note_time = $row[1];
                                $note_user = $row[2];
                                $note_title = $row[3];
                                $note_note = $row[4];
                            }
                            echo "<form action=\"?tab=data\" method=\"POST\" enctype=\"multipart/form-data\">
                            <table class=\"notes\">
                                <tr>
                                    <td>Time</td>
                                    <td>User</td>
                                    <td style=\"width: 100%;\"></td>
                                </tr>
                                <tr>
                                    <td><input style=\"width: 100%;\" type=\"text\" maxlength=50 name=\"Edit_Note_Time\" title=\"\" value=\"$note_time\"></td>
                                    <td><input style=\"width: 100%;\" type=\"text\" maxlength=50 name=\"Edit_Note_User\" title=\"\" value=\"$note_user\"></td>
                                    <td></td>
                                </tr>
                                <tr>
                                    <td colspan=\"2\"><input style=\"width: 100%;\" type=\"text\" maxlength=50 name=\"Edit_Note_Title\" title=\"\" value=\"$note_title\" placeholder=\"Title\"></td>
                                    <td></td>
                                </tr>
                                <tr>
                                    <td colspan=\"2\">
                                        <textarea style=\"width: 40em;\" rows=\"15\" maxlength=\"100000\" name=\"Edit_Note_Text\" title=\"\" placeholder=\"Note\">$note_note</textarea>
                                    </td>
                                    <td style=\"vertical-align: top; height:100%; width:100%;\">
                                        <table style=\"height:100%; width:100%;\">
                                            <tr>
                                                <td style=\"padding: 0 0 0.4em 0.4em; vertical-align: top; height:1em;\">
                                                    Upload (hold Ctrl to select multiple files):
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style=\"padding-left: 0.4em; vertical-align: top;\">
                                                    <input id='upload' name=\"edit_notes[]\" type=\"file\" multiple=\"multiple\" />
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style=\"padding: 0.4em 0 0 0.4em; vertical-align: bottom;\">
                                                    <button style=\"width:5.7em;\" type=\"submit\" name=\"Edit_Note_Save\" value=\"$note_id\">Save<br>Note</button>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <br>
                            <table class=\"notes\">";

                            unset($upload_id);
                            $results = $ndb->query("SELECT Id, Name, File_Name, Location FROM Uploads WHERE Id='" . $_POST['Edit_Note'] . "'");
                            $i = 0;
                            while ($row = $results->fetchArray()) {
                                $upload_id[$i] = $row[0];
                                $upload_name[$i] = $row[1];
                                $upload_file_name[$i] = $row[2];
                                $upload_location[$i] = $row[3];
                                $i++;
                            }
                            if (!isset($upload_id)) $upload_id = [];
                            else {
                                echo "<tr><td style=\"vertical-align: top;\">Files (uncheck to delete):<br>";
                                for ($v = 0; $v < count($upload_id); $v++) {
                                    echo "<div style=\"float:left; padding: 0.5em;\"><input type=\"hidden\" name=\"$v\" value=\"0\" /><input type=\"checkbox\" name=\"$v\" value=\"1\" checked> <a href=\"file.php?span=ul-dl&file=$upload_file_name[$v]\">$upload_name[$v]</a></div>";
                                }
                                echo "</td></tr>";

                                $images = False;
                                for ($v = 0; $v < count($upload_id); $v++) {
                                    if (endswith($upload_name[$v], '.jpg') || endswith($upload_name[$v], '.jpeg') || endswith($upload_name[$v], '.png') || endswith($upload_name[$v], '.gif')) {
                                        $images = True;
                                    }
                                }

                                if ($images == True) {
                                    echo "<tr><td>";
                                }
                                for ($v = 0; $v < count($upload_id); $v++) {
                                    if (endswith($upload_name[$v], '.jpg') || endswith($upload_name[$v], '.jpeg')) {
                                        echo "<div style=\"float: left; padding:0.4em;\"><a target=\"_blank\" href=\"file.php?span=ul-jpg&file=$upload_file_name[$v]\"><img class=\"thumbnail\" src=\"file.php?span=ul-jpg&file=thumb$upload_file_name[$v]\"></a></div>";
                                    }
                                    if (endswith($upload_name[$v], '.png')) {
                                        echo "<div style=\"float: left; padding:0.4em;\"><a target=\"_blank\" href=\"file.php?span=ul-png&file=$upload_file_name[$v]\"><img class=\"thumbnail\" src=\"file.php?span=ul-png&file=thumb$upload_file_name[$v]\"></a></div>";
                                    }
                                    if (endswith($upload_name[$v], '.gif')) {
                                        echo "<div style=\"float: left; padding:0.4em;\"><a target=\"_blank\" href=\"file.php?span=ul-gif&file=$upload_file_name[$v]\"><img class=\"thumbnail\" src=\"file.php?span=ul-gif&file=thumb$upload_file_name[$v]\"></a></div>";
                                    }
                                }
                                if ($images == True) {
                                    echo "</td></tr>";
                                }
                            }
                            echo "</table>
                            </form>";
                        }

                        if(isset($_POST['Login']) && $current_user_restriction != 'guest') {
                            echo '<pre>Time, Type of auth, user, IP, Hostname, Referral, Browser<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                $login_lines = `tail -n $Lines $auth_log`;
                            } else {
                                $login_lines = `tail -n 30 $auth_log`;
                            }
                            $login_lines = explode("\n", $login_lines);
                            for ($i = 0; $i < count($login_lines); $i++) {
                                echo htmlentities($login_lines[$i]) , "<br>";
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['Commits'])) {
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                $commits = `git log --oneline | head -n $Lines`;
                            } else {
                                $commits = `git log --oneline | head -n 30`;
                            }
                            echo '<pre><div style="padding: 1em 0 1.5em 0;">Note: Restoring a backup will restore all files from the backup, including databases and logs.<br>When restoring a backup, a backup of the current system will also be created.<br>Deleting a backup will delete all files of that backup.</div>';
                            $current_commit = `git rev-parse --short HEAD`;
                            $current_commit = mb_substr($current_commit, 0, 7);
                            echo "Current commit: <a style=\"color: #FF0000;\" href=\"https://github.com/kizniche/Mycodo/commit/$current_commit\" target=\"_blank\">$current_commit</a> (newest commits are at the top and the system's current commit is <span style=\"color:red;\">colored red</span>)<br> <br><strong><u>Commit</u>  <u>Description</u></strong><br>";
                            exec("$install_path/cgi-bin/mycodo-wrapper fetchorigin");
                            $commits_ahead = `git log --oneline master...origin/master`;
                            $commits_ahead = explode("\n", $commits_ahead);
                            foreach ($commits_ahead as $n => $line) {
                                $commits_ahead_id[$n] = substr($line, 0, strpos($line, ' '));
                            }
                            for ($i = 0; $i < count($commits_ahead); $i++) {
                                if ($commits_ahead[$i] != '' && $commits_ahead_id[$i] != $current_commit) {
                                    echo "<div style=\"text-indent: -5em; padding: 0.7em 0 0 5em; width: 100%; white-space: normal;\"><a class=\"commit-link\" href=\"https://github.com/kizniche/Mycodo/commit/$commits_ahead_id[$i]\" target=\"_blank\">" , htmlentities($commits_ahead[$i]) , "</a></div>";
                                }
                            }
                            $commits_list = explode("\n", $commits);
                            foreach ($commits_list as $n => $line) {
                                $commits_behind_id[$n] = substr($line, 0, strpos($line, ' '));
                            }
                            $dirs = array_filter(glob('/var/Mycodo-backups/*'), 'is_dir');
                            if (count($dirs) != 0) {
                                for ($i = 0; $i < count($dirs); $i++) {
                                    $backup_commits[$i] = mb_substr($dirs[$i], -7);
                                    $backup_dates[$i] = substr($dirs[$i], 27, 19);
                                }
                            }
                            for ($j = 0; $j < count($commits_list); $j++) {
                                if ($commits_behind_id[$j] == $current_commit) {
                                    echo "<div style=\"text-indent: -5em; padding: 0.7em 0 0 5em; width: 100%; white-space: normal;\"><a style=\"color: #FF0000;\" href=\"https://github.com/kizniche/Mycodo/commit/$commits_behind_id[$j]\" target=\"_blank\">" , htmlentities($commits_list[$j]) , "</a></div>";
                                } else {
                                    echo "<div style=\"text-indent: -5em; padding: 0.7em 0 0 5em; width: 100%; white-space: normal;\"><a class=\"commit-link\" href=\"https://github.com/kizniche/Mycodo/commit/$commits_behind_id[$j]\" target=\"_blank\">" , htmlentities($commits_list[$j]) , "</a></div>";
                                }
                                if (isset($backup_commits) && count($backup_commits) != 0) {
                                    for ($i = 0; $i < count($backup_commits); $i++) {
                                        if ($backup_commits[$i] == $commits_behind_id[$j]) {
                                            echo "<table class=\"gitcommits\">
                                                <tr>
                                                    <td>$backup_commits[$i]</td>
                                                    <td><form action=\"?tab=data";
                                                    if (isset($_GET['page'])) echo '&page=' , $_GET['page'];
                                                    echo "\" method=\"POST\" onsubmit=\"return confirm('Confirm that you would like to DELETE the $backup_dates[$i] backup of the system at commit $backup_commits[$i]. Note: This will delete all files of this backup. This cannot be undone. If you do not want to do this, click Cancel.')\"><button type=\"submit\" name=\"DeleteBackup\" value=\"$dirs[$i]\" title=\"Delete backup from $backup_dates[$i]\">Delete Backup</button></form></td>
                                                    <td><form action=\"?tab=data";
                                                    if (isset($_GET['page'])) echo '&page=' , $_GET['page'];
                                                    echo "\" method=\"POST\" onsubmit=\"return confirm('Confirm that you would like to begin the RESTORE process from the $backup_dates[$i] backup of the system at commit $backup_commits[$i]. If you do not want to do this, click Cancel.)\"><button type=\"submit\" name=\"RestoreBackup\" value=\"$dirs[$i]\" title=\"Restore backup from $backup_dates[$i]\">Restore Backup</button></form></td>
                                                    <td>Backup date: $backup_dates[$i]</td>
                                                </tr>
                                            </table>";
                                        }
                                    }
                                }
                            }
                            echo '</pre>';
                        }

                        if (isset($_POST['Backups']) || isset($_POST['CreateBackup']) || isset($_POST['DeleteBackup'])) {
                            echo '<pre><div style="padding: 1em 0 1em 0;">Note: Restoring a backup will restore all files from the backup, including databases and logs.<br>When restoring a backup, a backup of the current system will also be created.<br>Deleting a backup will delete all files of that backup.</div>';
                            echo '<div style="padding: 1em 0 1.5em 0;"><form action="?tab=data" method="POST"><button type="submit" name="CreateBackup" value="">Create New System Backup</button></form></div>';
                            $dirs = array_filter(glob('/var/Mycodo-backups/*'), 'is_dir');
                            for ($i = 0; $i < count($dirs); $i++) {
                                $backup_commits[$i] = mb_substr($dirs[$i], -7);
                                $backup_dates[$i] = substr($dirs[$i], 27, 19);
                            }
                            if (count($dirs) == 0) {
                                echo "0 backups found";
                            } else {
                                for ($i = 0; $i < count($dirs); $i++) {
                                    echo "<table class=\"gitcommits\">
                                        <tr>
                                            <td><a href=\"https://github.com/kizniche/Mycodo/commit/$backup_commits[$i]\" target=\"_blank\">$backup_commits[$i]</a></td>
                                            <td><form action=\"?tab=data\" method=\"POST\" onsubmit=\"return confirm('Confirm that you would like to DELETE the $backup_dates[$i] backup of the system at commit $backup_commits[$i]. Note: This will delete all files of this backup. This cannot be undone. If you do not want to do this, click Cancel.')\"><button type=\"submit\" name=\"DeleteBackup\" value=\"$dirs[$i]\" title=\"Delete backup from $backup_dates[$i]\">Delete Backup</button></form></td>
                                            <td><form action=\"?tab=data";
                                            if (isset($_GET['page'])) echo '&page=' , $_GET['page'];
                                            echo "\" method=\"POST\" onsubmit=\"return confirm('Confirm that you would like to begin the RESTORE process from the $backup_dates[$i] backup of the system at commit $backup_commits[$i]. If you do not want to do this, click Cancel.)\"><button type=\"submit\" name=\"RestoreBackup\" value=\"$dirs[$i]\" title=\"Restore backup from $backup_dates[$i]\">Restore Backup</button></form></td>
                                            <td>Backup date: $backup_dates[$i]</td>
                                        </tr>
                                    </table>";
                                }
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['Daemon'])) {
                            echo '<pre>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `cat /var/www/mycodo/log/daemon.log /var/www/mycodo/log/daemon-tmp.log | tail -n $Lines`;
                            } else {
                                echo `cat /var/www/mycodo/log/daemon.log /var/www/mycodo/log/daemon-tmp.log | tail -n 30`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['Update'])) {
                            $log = '/var/www/mycodo/log/update.log';
                            echo '<pre>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            echo '</pre>';
                        }

                        if(isset($_POST['Restore'])) {
                            $log = '/var/www/mycodo/log/restore.log';
                            echo '<pre>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines $log`;
                            } else {
                                echo `tail -n 30 $log`;
                            }
                            echo '</pre>';
                        }

                        if (isset($_POST['RelayUsage']) && count($relay_id) > 0) {
                        ?>Past Relay Usage
                            <div class="sensor-parent" style="margin-top: 1em;">
                                <table class="relays">
                                    <tr>
                                        <td class="table-header middle">Relay</td>
                                        <td class="table-header middle">Name</td>
                                        <td class="table-header"></td>
                                        <td class="table-header right" style="width:6em;">Hour</td>
                                        <td class="table-header right" style="width:6em;">Day</td>
                                        <td class="table-header right" style="width:6em;">Week</td>
                                        <td class="table-header right" style="width:6em;">Month<br>(Today)</td>
                                        <td class="table-header right" style="width:6em;">Month<br>(Day <?php echo $relay_stats_dayofmonth; ?>)</td>
                                        <td class="table-header right" style="width:6em;">Year</td>
                                        <td class="table-header right" style="width:6em;">Total</td>
                                    </tr>
                                    <?php 
                                    $relay_stats_seconds_on = [];
                                    $relay_stats_seconds_on_hour = [];
                                    $relay_stats_seconds_on_day = [];
                                    $relay_stats_seconds_on_week = [];
                                    $relay_stats_seconds_on_month = [];
                                    $relay_stats_seconds_on_year = [];
                                    $kwh = [];

                                    $current_year = date("Y");
                                    $current_month = date("m");
                                    $current_day = date("d");
                                    $date_ago_dayofmonth = NULL;
                                    if ($relay_stats_dayofmonth < $current_day) {
                                        $date_ago_dayofmonth = date("Y/m/d-h:i:s", mktime(date("h"), date("i"), 0, $current_month, $relay_stats_dayofmonth, $current_year));
                                    } else {
                                        if ($current_month == 1) {
                                            $date_ago_dayofmonth = date("Y/m/d-h:i:s", mktime(date("h"), date("i"), 0, 12, $relay_stats_dayofmonth, $current_year-1));
                                        } else {
                                            $date_ago_dayofmonth = date("Y/m/d-h:i:s", mktime(date("h"), date("i"), 0, $current_month-1, $relay_stats_dayofmonth, $current_year));
                                        }
                                    }

                                    for ($i = 0; $i < count($relay_id); $i++) {
                                        $read = "$gpio_path -g read $relay_pin[$i]";
                                        $date_now = substr(shell_exec("date --date=\"now\" +'%Y/%m/%d-%H:%M:%S'"), 0, -1);
                                        $date_ago = shell_exec("date --date=\"1 hour ago\" +'%Y/%m/%d-%H:%M:%S'");
                                        $relay_stats_seconds_on_hour[$i] = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                        $date_ago = shell_exec("date --date=\"1 day ago\" +'%Y/%m/%d-%H:%M:%S'");
                                        $relay_stats_seconds_on_day[$i] = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                        $date_ago = shell_exec("date --date=\"1 week ago\" +'%Y/%m/%d-%H:%M:%S'");
                                        $relay_stats_seconds_on_week[$i] = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                        $date_ago = shell_exec("date --date=\"1 month ago\" +'%Y/%m/%d-%H:%M:%S'");
                                        $relay_stats_seconds_on_month[$i] = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                        $relay_stats_seconds_on_dayofmonth[$i] = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago_dayofmonth . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                        $date_ago = shell_exec("date --date=\"1 year ago\" +'%Y/%m/%d-%H:%M:%S'");
                                        $relay_stats_seconds_on_year[$i] = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                        $relay_stats_seconds_on[$i] = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                    ?>
                                    <tr>
                                        <td class="center"><?php echo $i+1; ?></td>
                                        <td><?php echo $relay_name[$i]; ?></td>
                                        <td>Duration On (hours)</td>
                                        <td class="right"><?php printf("%.2f", $relay_stats_seconds_on_hour[$i]/3600); ?></td>
                                        <td class="right"><?php printf("%.2f", $relay_stats_seconds_on_day[$i]/3600); ?></td>
                                        <td class="right"><?php printf("%.2f", $relay_stats_seconds_on_week[$i]/3600); ?></td>
                                        <td class="right"><?php printf("%.2f", $relay_stats_seconds_on_month[$i]/3600); ?></td>
                                        <td class="right"><?php printf("%.2f", $relay_stats_seconds_on_dayofmonth[$i]/3600); ?></td>
                                        <td class="right"><?php printf("%.2f", $relay_stats_seconds_on_year[$i]/3600) ?></td>
                                        <td class="right"><?php printf("%.2f", $relay_stats_seconds_on[$i]/3600); ?></td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"></td>
                                        <td>Power Usage <?php echo "(kWh@, ",$relay_stats_volts,"V)"; ?></td>
                                        <td class="right">
                                            <?php
                                            $date_ago = shell_exec("date --date=\"1 hour ago\" +'%Y/%m/%d-%H:%M:%S'");
                                            $amps = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                            $kwh[0] = $relay_stats_volts*$relay_amps[$i]*($amps/3600)/1000;
                                            printf("%.2f", $kwh[0]);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $date_ago = shell_exec("date --date=\"1 day ago\" +'%Y/%m/%d-%H:%M:%S'");
                                            $amps = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                            $kwh[1] = $relay_stats_volts*$relay_amps[$i]*($amps/3600)/1000;
                                            printf("%.2f", $kwh[1]);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $date_ago = shell_exec("date --date=\"1 week ago\" +'%Y/%m/%d-%H:%M:%S'");
                                            $amps = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                            $kwh[2] = $relay_stats_volts*$relay_amps[$i]*($amps/3600)/1000;
                                            printf("%.2f", $kwh[2]);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $date_ago = shell_exec("date --date=\"1 month ago\" +'%Y/%m/%d-%H:%M:%S'");
                                            $amps = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                            $kwh[3] = $relay_stats_volts*$relay_amps[$i]*($amps/3600)/1000;
                                            printf("%.2f", $kwh[3]);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $amps = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago_dayofmonth . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                            $kwh[4] = $relay_stats_volts*$relay_amps[$i]*($amps/3600)/1000;
                                            printf("%.2f", $kwh[4]);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $date_ago = shell_exec("date --date=\"1 year ago\" +'%Y/%m/%d-%H:%M:%S'");
                                            $amps = (int)shell_exec("cat /var/www/mycodo/log/relay.log /var/www/mycodo/log/relay-tmp.log | awk '$0>=from&&$0<=to' from=\"" . $date_ago . "\" to=\"" . $date_now . "\" | awk '{a[$3]+=$5}END{for(i in a) {if (i == \"" . ($i+1) . "\") printf \"%.0f\",a[i]}}'");
                                            $kwh[5] = $relay_stats_volts*$relay_amps[$i]*($amps/3600)/1000;
                                            printf("%.2f", $kwh[5]);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $kwh[6] = $relay_stats_volts*$relay_amps[$i]*($relay_stats_seconds_on[$i]/3600)/1000;
                                            printf("%.2f", $kwh[6]);
                                        ?>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"></td>
                                        <td>Cost <?php echo "(",$relay_stats_currency,$relay_stats_cost,"/kWh)"; ?></td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[0]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[1]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[2]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[3]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[4]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[5]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[6]*$relay_stats_cost);
                                            ?>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 0.6em;"></td>
                                    </tr>
                                    <?php
                                    }
                                    ?>
                                    <tr>
                                        <td colspan="2">Grand Total</td>
                                        <td>Duration On (hours)</td>
                                        <td class="right">
                                            <?php
                                            $relay_stats_seconds_on_total = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $relay_stats_seconds_on_total += $relay_stats_seconds_on_hour[$j];
                                            }
                                            printf("%.2f", $relay_stats_seconds_on_total/3600);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $relay_stats_seconds_on_total = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $relay_stats_seconds_on_total += $relay_stats_seconds_on_day[$j];
                                            }
                                            printf("%.2f", $relay_stats_seconds_on_total/3600);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $relay_stats_seconds_on_total = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $relay_stats_seconds_on_total += $relay_stats_seconds_on_week[$j];
                                            }
                                            printf("%.2f", $relay_stats_seconds_on_total/3600);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $relay_stats_seconds_on_total = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $relay_stats_seconds_on_total += $relay_stats_seconds_on_month[$j];
                                            }
                                            printf("%.2f", $relay_stats_seconds_on_total/3600);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $relay_stats_seconds_on_total = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $relay_stats_seconds_on_total += $relay_stats_seconds_on_dayofmonth[$j];
                                            }
                                            printf("%.2f", $relay_stats_seconds_on_total/3600);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $relay_stats_seconds_on_total = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $relay_stats_seconds_on_total += $relay_stats_seconds_on_year[$j];
                                            }
                                            printf("%.2f", $relay_stats_seconds_on_total/3600);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            $relay_stats_seconds_on_total = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $relay_stats_seconds_on_total += $relay_stats_seconds_on[$j];
                                            }
                                            printf("%.2f", $relay_stats_seconds_on_total/3600);
                                            ?>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"></td>
                                        <td>Power Usage (kWh)</td>
                                        <td class="right">
                                        <?php
                                            $kwh[0] = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $kwh[0] += round($relay_stats_volts*$relay_amps[$j]*($relay_stats_seconds_on_hour[$j]/3600)/1000, 2);
                                            }
                                            printf("%.2f", $kwh[0]);
                                        ?>
                                        </td>
                                        <td class="right">
                                        <?php
                                            $kwh[1] = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $kwh[1] += round($relay_stats_volts*$relay_amps[$j]*($relay_stats_seconds_on_day[$j]/3600)/1000, 2);
                                            }
                                            printf("%.2f", $kwh[1]);
                                        ?>
                                        </td>
                                        <td class="right">
                                        <?php
                                            $kwh[2] = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $kwh[2] += round($relay_stats_volts*$relay_amps[$j]*($relay_stats_seconds_on_week[$j]/3600)/1000, 2);
                                            }
                                            printf("%.2f", $kwh[2]);
                                        ?>
                                        </td>
                                        <td class="right">
                                        <?php
                                            $kwh[3] = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $kwh[3] += round($relay_stats_volts*$relay_amps[$j]*($relay_stats_seconds_on_month[$j]/3600)/1000, 2);
                                            }
                                            printf("%.2f", $kwh[3]);
                                        ?>
                                        </td>
                                        <td class="right">
                                        <?php
                                            $kwh[4] = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $kwh[4] += round($relay_stats_volts*$relay_amps[$j]*($relay_stats_seconds_on_dayofmonth[$j]/3600)/1000, 2);
                                            }
                                            printf("%.2f", $kwh[4]);
                                        ?>
                                        </td>
                                        <td class="right">
                                        <?php
                                            $kwh[5] = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $kwh[5] += round($relay_stats_volts*$relay_amps[$j]*($relay_stats_seconds_on_year[$j]/3600)/1000, 2);
                                            }
                                            printf("%.2f", $kwh[5]);
                                        ?>
                                        </td>
                                        <td class="right">
                                        <?php
                                            $kwh[6] = 0;
                                            for ($j=0; $j < count($relay_id); $j++) {
                                                $kwh[6] += round($relay_stats_volts*$relay_amps[$j]*($relay_stats_seconds_on[$j]/3600)/1000, 2);
                                            }
                                            printf("%.2f", $kwh[6]);
                                        ?>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"></td>
                                        <td>Cost <?php echo "(",$relay_stats_currency,$relay_stats_cost,"/kWh)"; ?></td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[0]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[1]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[2]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[3]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[4]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[5]*$relay_stats_cost);
                                            ?>
                                        </td>
                                        <td class="right">
                                            <?php
                                            printf("%s%.2f", $relay_stats_currency, $kwh[6]*$relay_stats_cost);
                                            ?>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        <?php 
                        }

                        if (isset($_POST['Users']) && $current_user_restriction != 'guest') {
                            echo '<div style="padding: 0.5em 0 1em 0;"><pre>';
                            echo exec('file ' . $user_db); 
                            echo '<br> <br>';
                            exec('sqlite3 ' . $user_db . ' .dump', $output);
                            print_r($output);
                            echo '</pre></div>';
                        }

                        if (isset($_POST['Database']) && $current_user_restriction != 'guest') {
                            echo exec('file ' . $mycodo_db); 
                            echo '<pre><br> <br>';
                            exec('sqlite3 ' . $mycodo_db . ' .dump', $output);
                            $db = new SQLite3($mycodo_db);
                            $results = $db->query('SELECT Pass FROM SMTP');
                            while ($row = $results->fetchArray()) {
                                $email_password = $row[0];
                            }
                            print_r(str_replace($email_password,"*****",$output));
                            echo '</pre>';
                        }
                    ?>
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

            <div style="padding: 1.5em 0 0 1em;">
                <a href="manual.html" target="_blank">Mycodo 3.5 Manual</a> | <a href="https://github.com/kizniche/Mycodo" target="_blank">Mycodo on GitHub</a> | Have a problem? <a href="http://kylegabriel.com/contact" target="_blank">Contact the developer</a> or <a href="https://github.com/kizniche/Mycodo/issues" target="_blank">submit an issue</a>.
            </div>

            <div style="padding: 0.5em 1em 0 1em; width: 100%;">
                <fieldset class="settings-box">
                <legend>Update</legend>
                <table style="width: 100%;">
                    <form action="?tab=settings" method="post">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
                            Check if there is an update avaialble for Mycodo<?php
                            if (strpos(`cat /var/www/mycodo/.updatecheck`,'1') !== false) {
                                echo ' (<span style="color: red;">A newer version is available</span>)';
                            } else {
                                echo ' (<span style="color: #00AA00;">You are running the latest version</span>)';
                            }
                            ?>
                        </td>
                        <td class="setting-value">
                            <button style="width: 18em;" name="UpdateCheck" type="submit" value="" title="Check if there is a newer version of Mycodo on github.">Check for Update</button>
                        </td>
                    </tr>
                    </form>

                    <form action="?tab=settings" method="post" onsubmit="return confirm('Confirm that you would like to begin the update process now. If not, click Cancel. The update process will go on in the background for several seconds up to a minute or longer. You can check the status of the update with the Update Log in the Data Tab.')">
                    <tr>
                        <td class="setting-text">
                            Update Mycodo to the latest version on <a href="https://github.com/kizniche/Mycodo" target="_blank">GitHub</a>
                        </td>
                        <td class="setting-value">
                            <button style="width: 18em;" name="UpdateMycodo" type="submit" value="" title="Update the mycodo system to the latest version on github.">Update Mycodo</button>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>Daemon</legend>
                <table style="width: 100%;">
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
                            Stop Daemon
                        </td>
                        <td class="setting-value">
                            <button style="width: 18em;" name="DaemonStop" type="submit" value="" title="Stop the mycodo daemon from running or kill a daemon that has had a segmentation fault.">Stop Daemon</button>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Start Daemon
                        </td>
                        <td class="setting-value">
                            <button style="width: 18em;" name="DaemonStart" type="submit" value="" title="Start the mycodo daemon in normal mode (if no other instance is currently running).">Start Daemon</button>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Restart Daemon
                        </td>
                        <td class="setting-value">
                            <button style="width: 18em;" name="DaemonRestart" type="submit" value="" title="Stop and start the mycodo daemon in normal mode.">Restart Daemon</button>
                        </td>
                    </tr>
                    </form>

                    <form action="?tab=settings" method="post" onsubmit="return confirm('Confirm that you would like to run the daemon in debug mode. If not, click Cancel.')">
                    <tr>
                        <td class="setting-text">
                            Restart Daemon in Debug Mode (use with caution, produces large logs)
                        </td>
                        <td class="setting-value">
                            <button style="width: 18em;" name="DaemonDebug" type="submit" value="" title="Stop and start the mycodo daemon in debug mode (verbose log messages, temporary files are not deleted). You should probably not enable this unless you know what you're doing.">Restart Daemon in Debug Mode</button>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>System</legend>
                <table style="width: 100%;">
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
                            Maximum current draw
                        </td>
                        <td class="setting-value">
                            <input style="width: 4em;" type="number" min="1" max="500" step="0.1" value="<?php echo $max_amps; ?>" maxlength=4 size=1 name="max_amps" title="The number of amps that any combination of relays will be prevented from exceeding. Each relay must have an accurate amp draw set for this to operate properly. Ensure all relays that are connected to devices have the correct amperage set."/> amps&nbsp;&nbsp;|&nbsp;&nbsp;Enable: <input type="hidden" name="enable_max_amps" value="0" /><input type="checkbox" name="enable_max_amps" value="1"<?php if ($enable_max_amps == 1) echo ' checked'; ?> title="Prevent a combination of relays from turning on that surpass the maxmum amperage limit (set below)."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Voltage (used to calculate kiloWatt-hours (kWh) power usage)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" min="1" max="9999" step="1" value="<?php echo $relay_stats_volts; ?>" maxlength=4 size=1 name="relay_stats_volts" title="The voltage that is being controlled through the relays."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Cost per kWh
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" step="0.01" value="<?php echo $relay_stats_cost; ?>" maxlength=4 name="relay_stats_cost" title="The cost per kWh."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Currency Unit
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $relay_stats_currency; ?>" maxlength=1 name="relay_stats_currency" title="The currency unit."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Power Billing Day of the Month (for calculating kWh usage since the last bill)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" min="1" max="31" step="1" value="<?php echo $relay_stats_dayofmonth; ?>" maxlength=4 size=1 name="relay_stats_dayofmonth" title="Power usage will be calculated from this nth day of the month until the present."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align:top;">
                            Message to display on login screen
                        </td>
                        <td class="setting-value">
                            <textarea style="width: 18em;" rows="2" maxlength=500 name="login_message" title=""><?php echo $login_message; ?></textarea>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Automatic refresh rate (seconds)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" min="1" max="999999" value="<?php echo $refresh_time; ?>" maxlength=4 size=1 name="refresh_time" title="The number of seconds between automatic page refreshing."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Display Debugging Information
                        </td>
                        <td class="setting-value">
                            <input type="hidden" name="debug" value="0" /><input type="checkbox" name="debug" value="1"<?php if (isset($_COOKIE['debug'])) if ($_COOKIE['debug'] == True) echo ' checked'; ?> title="Display debugging information at the bottom of every page."/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-save">
                            <button style="width: 18em;" name="ChangeSystem" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>Combined Static Graph Generation</legend>
                <table style="width: 100%;">
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td colspan="4" class="setting-text">
                            Combined Temperatures
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_min; ?>" maxlength="6" name="combined_temp_min" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_relays_min; ?>" maxlength="6" name="combined_temp_relays_min" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_max; ?>" maxlength="6" name="combined_temp_max" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_relays_max; ?>" maxlength="6" name="combined_temp_relays_max" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_tics; ?>" maxlength="6" name="combined_temp_tics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_relays_tics; ?>" maxlength="6" name="combined_temp_relays_tics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_mtics; ?>" maxlength="6" name="combined_temp_mtics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_temp_relays_mtics; ?>" maxlength="6" name="combined_temp_relays_mtics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text" style="width: 100%;">
                            Relays to Plot Up (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_temp_relays_up; ?>" name="combined_temp_relays_up" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text">
                            Relays to Plot Down (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_temp_relays_down; ?>" name="combined_temp_relays_down" title=""/>
                        </td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <td colspan="4" class="setting-text pad-top">
                            Combined Humidities
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_min; ?>" maxlength="6" name="combined_hum_min" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_relays_min; ?>" maxlength="6" name="combined_hum_relays_min" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_max; ?>" maxlength="6" name="combined_hum_max" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_relays_max; ?>" maxlength="6" name="combined_hum_relays_max" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_tics; ?>" maxlength="6" name="combined_hum_tics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_relays_tics; ?>" maxlength="6" name="combined_hum_relays_tics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_mtics; ?>" maxlength="6" name="combined_hum_mtics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_hum_relays_mtics; ?>" maxlength="6" name="combined_hum_relays_mtics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text" style="width: 100%">
                            Relays to Plot Up (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_hum_relays_up; ?>" name="combined_hum_relays_up" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text">
                            Relays to Plot Down (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_hum_relays_down; ?>" name="combined_hum_relays_down" title=""/>
                        </td>
                    </tr>
                </table>
                    
                <table>
                    </tr>
                    <tr>
                        <td colspan="4" class="setting-text pad-top">
                            Combined CO<sub>2</sub>s
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_min; ?>" maxlength="6" name="combined_co2_min" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_relays_min; ?>" maxlength="6" name="combined_co2_relays_min" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_max; ?>" maxlength="6" name="combined_co2_max" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_relays_max; ?>" maxlength="6" name="combined_co2_relays_max" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_tics; ?>" maxlength="6" name="combined_co2_tics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_relays_tics; ?>" maxlength="6" name="combined_co2_relays_tics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_mtics; ?>" maxlength="6" name="combined_co2_mtics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_co2_relays_mtics; ?>" maxlength="6" name="combined_co2_relays_mtics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text" style="width: 100%">
                            Relays to Plot Up (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_co2_relays_up; ?>" name="combined_co2_relays_up" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text">
                            Relays to Plot Down (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_co2_relays_down; ?>" name="combined_co2_relays_down" title=""/>
                        </td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <td colspan="4" class="setting-text pad-top">
                            Combined Pressures
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_min; ?>" maxlength="6" name="combined_press_min" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Min
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_relays_min; ?>" maxlength="6" name="combined_press_relays_min" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_max; ?>" maxlength="6" name="combined_press_max" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Max
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_relays_max; ?>" maxlength="6" name="combined_press_relays_max" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_tics; ?>" maxlength="6" name="combined_press_tics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis Tics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_relays_tics; ?>" maxlength="6" name="combined_press_relays_tics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_mtics; ?>" maxlength="6" name="combined_press_mtics" title=""/>
                        </td>
                        <td class="setting-text">
                            Relay Y-Axis mTics
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="number" value="<?php echo $combined_press_relays_mtics; ?>" maxlength="6" name="combined_press_relays_mtics" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text" style="width: 100%;">
                            Relays to Plot Up (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_press_relays_up; ?>" name="combined_press_relays_up" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" class="setting-text">
                            Relays to Plot Down (0 to disable, separate multiple relays with commas)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" type="text" value="<?php echo $combined_press_relays_down; ?>" name="combined_press_relays_down" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="4" class="setting-save">
                            <button style="width: 18em;" name="ChangeCombinedSetings" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>Email Notification</legend>
                <table style="width: 100%;">
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
                            SMTP Host
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="text" value="<?php echo $smtp_host; ?>" maxlength="50" name="smtp_host" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Enable SSL (unchecked for TSL)
                        </td>
                        <td class="setting-value">
                            <input type="hidden" name="smtp_ssl" value="0" /><input type="checkbox" name="smtp_ssl" value="1"<?php if ($smtp_ssl == 1) echo ' checked'; ?> title="Enable email to be sent using SSL."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            SMTP Port (465 for SSL, 587 for TSL)
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="number" value="<?php echo $smtp_port; ?>" maxlength="6" name="smtp_port" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            User (usually full email address)
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="text" value="<?php echo $smtp_user; ?>" maxlength="50" name="smtp_user" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Password (field will always be blank, enter new password to change)
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="password" value="" maxlength="100" name="smtp_pass" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            From Email
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="text" value="<?php echo $smtp_email_from; ?>" maxlength="50" name="smtp_email_from" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Wait Time (How long to wait between sending the same notification, in seconds)
                        </td>
                        <td class="setting-value">
                            <input class="smtp" type="number" step="1" value="<?php echo $smtp_wait_time; ?>" maxlength="7" name="smtp_wait_time" title=""/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Send Test Email (save configure above, then enter recipient and click Send)
                        </td>
                        <td class="setting-value">
                            <table style="100%;">
                                <tr>
                                    <td style="width: 100%;">
                                        <input style="width: 100%;" type="text" value="" maxlength="50" name="smtp_email_test" title=""/>
                                    </td>
                                    <td>
                                        <input type="submit" name="TestNotify" value="Send">
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-save">
                            <input style="width: 18em;" type="submit" name="ChangeNotify" value="Save">
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>Camera: Still Capture</legend>
                <table style="width: 100%;">
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
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
                        <td class="setting-text" style="vertical-align: top;">
                            Command to execute before capture
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Still_Cmd_Pre" title="Command to be executed before the image capture. If your command is longer than 200 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."><?php echo htmlentities($still_cmd_pre); ?></textarea> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align: top;">
                            Command to execute after capture
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Still_Cmd_Post" title="Command to be executed after the image capture. If your command is longer than 200 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."><?php echo htmlentities($still_cmd_post); ?></textarea> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align: top;">
                            Extra parameters for camera (raspistill)
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Still_Extra_Parameters"><?php echo $still_extra_parameters; ?></textarea>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-save">
                            <button style="width: 18em;" name="ChangeStill" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>Camera: Video Stream</legend>
                <table style="width: 100%;">
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
                            Relay to activate during capture (0 to disable)
                        </td>
                        <td class="setting-value">
                            <input style="width: 4em;" type="number" min="0" max="30" value="<?php echo $stream_relay; ?>" maxlength=4 size=1 name="Stream_Relay" title="A relay can be set to activate during the video stream."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align: top;">
                            Command to execute before starting stream
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Stream_Cmd_Pre" title="Command to be executed before the stream has started. If your command is longer than 200 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."><?php echo htmlentities($stream_cmd_pre); ?></textarea> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align: top;">
                            Command to execute after stopping stream
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Stream_Cmd_Post" title="Command to be executed after the stream has been stopped. If your command is longer than 200 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."><?php echo htmlentities($stream_cmd_post); ?></textarea> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align: top;">
                            Extra parameters for camera (raspistill)
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Stream_Extra_Parameters" title=""><?php echo $stream_extra_parameters; ?></textarea>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-save">
                            <button style="width: 18em;" name="ChangeStream" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>Camera: Time-lapse</legend>
                <table style="width: 100%;">
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
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
                        <td class="setting-text" style="vertical-align: top;">
                            Command to execute before capture
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Timelapse_Cmd_Pre" title="Command to be executed before capture. If your command is longer than 200 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."><?php echo htmlentities($timelapse_cmd_pre); ?></textarea> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align: top;">
                            Command to execute after capture
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Timelapse_Cmd_Post" title="Command to be executed after capture. If your command is longer than 200 characters, consider creating a script and excuting that here. Use full paths and single-quotes instead of double-quotes."><?php echo htmlentities($timelapse_cmd_post); ?></textarea> 
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text" style="vertical-align: top;">
                            Extra parameters for camera (raspistill)
                        </td>
                        <td class="setting-value">
                            <textarea rows="2" style="width: 18em;" maxlength=200 name="Timelapse_Extra_Parameters" title=""><?php echo $timelapse_extra_parameters; ?></textarea>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-value">
                            <?php
                    if ($timelapse_timestamp) {
                        $timelapse_tstamp = substr(`date +"%Y%m%d%H%M%S"`, 0, -1);
                        echo 'Output file series: ' , $timelapse_path , '/' , $timelapse_prefix , '-' , $timelapse_tstamp , '-00001.jpg';
                    } else {
                        echo 'Output file series: ' , $timelapse_path , '/' , $timelapse_prefix , '-00001.jpg';
                    }
                     ?>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-save">
                            <button style="width: 18em;" name="ChangeTimelapse" type="submit" value="">Save</button>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <?php
                if ($current_user_restriction == 'admin') {
                ?>

                <fieldset class="settings-box">
                <legend>Add User</legend>
                <table style="width: 100%;">
                <form method="post" action="?tab=settings">
                    <tr>
                        <td class="setting-text" style="width: 100%;">
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
                            <input style="width: 18em;" type="email" name="user_email" title="The email address associated with this account. In addition to the user name, the email address may be used to log in."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Password (min. 6 characters)
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" class="login_input" type="password" name="user_password_new" pattern=".{6,}" required autocomplete="off" title="To change the password, enter the new password twice and click Save."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Repeat password
                        </td>
                        <td class="setting-value">
                            <input style="width: 18em;" class="login_input" type="password" name="user_password_repeat" pattern=".{6,}" required autocomplete="off" title="To change the password, repeat the new password to verify it was entered correctly."/>
                        </td>
                    </tr>
                    <tr>
                        <td class="setting-text">
                            Group
                        </td>
                        <td class="setting-value">
                            <select style="width: 18em;" title="" name="user_restriction" title="Select what group this user belongs to. The permissions each group has can be found in the manual.">
                                <option value="guest">Guest</option>
                                <option value="admin">Admin</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" class="setting-save">
                            <input style="width: 18em;" type="submit" name="register" value="Add User"/>
                        </td>
                    </tr>
                    </form>
                </table>
                </fieldset>

                <fieldset class="settings-box">
                <legend>User Management</legend>
                <table class="edit-user">
                <form method="post" action="?tab=settings">
                    <tr>
                        <td>User</td>
                        <td>Email</td>
                        <td>New Password</td>
                        <td>New Password Repeat</td>
                        <td>Group</td>
                        <td>Theme</td>
                    </tr>
                <?php 
                for ($i = 0; $i < count($user_name); $i++) {
                ?>
                    <tr>
                        <form method="post" action="?tab=settings">
                        <td><?php echo $user_name[$i]; ?><input type="hidden" name="user_name" value="<?php echo $user_name[$i]; ?>"></td>
                        <td>
                            <input style="width: 12.5em;" type="text" value="<?php echo $user_email[$i]; ?>" name="user_email" title="The email address associated with this account. In addition to the user name, the email address may be used to log in."/>
                        </td>
                        <td>
                            <input style="width: 12.5em;" class="login_input" type="password" name="new_password" pattern=".{6,}" autocomplete="off" title="To change the password, enter the new password twice and click Save."/>
                            </td>
                        <td>
                            <input style="width: 12.5em;" class="login_input" type="password" name="new_password_repeat" pattern=".{6,}" autocomplete="off" title="To change the password, repeat the new password to verify it was entered correctly."/>
                        </td>
                        <td>
                            <select title="" name="user_restriction" title="Select what group this user belongs to. The permissions each group has can be found in the manual.">
                                <option
                                    <?php if ($user_restriction[$i] == 'admin') {
                                        echo ' selected="selected"';
                                    } ?> value="admin">Admin</option>
                                <option
                                    <?php if ($user_restriction[$i] == 'guest') {
                                        echo ' selected="selected"';
                                    } ?> value="guest">Guest</option>
                            </select>
                        </td>
                        <td>
                            <select title="" name="user_theme" title="Select what theme to display for this user.">
                                <option
                                    <?php if ($user_theme[$i] == 'light') {
                                        echo ' selected="selected"';
                                    } ?> value="light">Light</option>
                                <option
                                    <?php if ($user_theme[$i] == 'dark') {
                                        echo ' selected="selected"';
                                    } ?> value="dark">Dark</option>
                            </select>
                        </td>
                        <td>
                            <input type="submit" name="edituser" value="Save" title="Save settings for user <?php echo $user_name[$i]; ?>" />
                        </td>
                        </form>
                        <form method="post" action="?tab=settings" onsubmit="return confirm('Confirm the deletion of user <?php echo $user_name[$i]; ?>. This cannot be undone. To keep this user, click Cancel.')">
                        <td>
                            <input type="hidden" name="user_name" value="<?php echo $user_name[$i]; ?>">
                            <button type="submit" name="deleteuser" value="<?php echo $user_name[$i]; ?>" title="Delete user <?php echo $user_name[$i]; ?>">Delete</button>
                        </td>
                        </form>
                    </tr>
                <?php
                }
                ?>
                </table>

                <?php
                } else {
                ?>
                <fieldset class="settings-box">
                <legend>User Management</legend>
                <table class="edit-user">
                    <tr>
                        <td>User</td>
                        <td>Email</td>
                        <td>New Password</td>
                        <td>New Password Repeat</td>
                        <td>Theme</td>
                    </tr>
                <?php 
                for ($i = 0; $i < count($user_name); $i++) {
                    if ($user_name[$i] == $logged_in_user) {
                ?>
                    <form method="post" action="?tab=settings">
                    <tr>
                        <td><?php echo $user_name[$i]; ?><input type="hidden" name="user_name" value="<?php echo $user_name[$i]; ?>"></td>
                        <td>
                            <input style="width: 12.5em;" type="text" value="<?php echo $user_email[$i]; ?>" name="user_email" title="The email address associated with this account. In addition to the user name, the email address may be used to log in."/>
                        </td>
                        <td>
                            <input style="width: 12.5em;" class="login_input" type="password" name="new_password" pattern=".{6,}" autocomplete="off" title="To change the password, enter the new password twice and click Save."/>
                            </td>
                        <td>
                            <input style="width: 12.5em;" class="login_input" type="password" name="new_password_repeat" pattern=".{6,}" autocomplete="off" title="To change the password, repeat the new password to verify it was entered correctly."/>
                        </td>
                        <td>
                            <select title="" name="user_theme" title="Select what theme to display for this user.">
                                <option
                                    <?php if ($user_theme[$i] == 'light') {
                                        echo ' selected="selected"';
                                    } ?> value="light">Light</option>
                                <option
                                    <?php if ($user_theme[$i] == 'dark') {
                                        echo ' selected="selected"';
                                    } ?> value="dark">Dark</option>
                            </select>
                        </td>
                        <td>
                            <input type="submit" name="edituser" value="Save" />
                        </td>
                    </tr>
                    </form>
                <?php
                    }
                }
                ?>
                </table>
                </fieldset>
                <?php
                }
                ?>
            </div>
            <div style="padding-top: 1em;"></div>
        </li>
    </ul> <!-- cd-tabs-content -->

    <?php
    if (isset($_COOKIE['debug']) && $_COOKIE['debug'] == True) {
        ?>
        <div style="clear: both;"></div>
        <div style="padding: 4em 0 2em 2em;">
            <div style="padding-bottom: 1em; font-weight: bold; font-size: 1.5em;">
                Debug Information
            </div>
            <div style="padding-bottom: 2em;">
                <div style="padding: 1em 0; font-weight: bold; font-size: 1.2em;">
                    WiringPi GPIO
                </div>
                <div style="font-family: monospace;"><pre><?php echo `gpio readall`; ?></pre></div>
            </div>
            <div style="padding-bottom: 2em;">
                <div style="padding: 1em 0; font-weight: bold; font-size: 1.2em;">
                    System
                </div>
                <div style="font-family: monospace; padding-bottom:0.5em;"><pre><?php echo `uname -a`; ?></pre></div>
                <div style="font-family: monospace; padding-bottom:0.5em;"><pre><?php echo `uptime`; ?></pre></div>
                <div style="font-family: monospace; padding-bottom:0.5em;"><pre><?php echo `lsb_release -da`; ?></pre></div>
                <div style="font-family: monospace; padding-bottom:0.5em;"><pre><?php echo `lscpu`; ?></pre></div>
                <div style="font-family: monospace; padding-bottom:0.5em;"><pre><?php echo `cat /proc/cpuinfo`; ?></pre></div>
                <div style="font-family: monospace; padding-bottom:0.5em;"><pre><?php echo `df`; ?></pre></div>
                <div style="font-family: monospace;"><pre><?php echo `free`; ?></pre></div>
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
<script src="js/main.js"></script>
</body>
</html>

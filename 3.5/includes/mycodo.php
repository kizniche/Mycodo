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

$version = "3.5.54";

######### Start Edit Configure #########

$install_path = "/var/www/mycodo";
$lock_path = "/var/lock";
$gpio_path = "/usr/local/bin/gpio";

########## End Edit Configure ##########

$mycodo_client = $install_path . "/cgi-bin/mycodo-client.py";
$still_exec = $install_path . "/cgi-bin/camera-still.sh";
$stream_exec = $install_path . "/cgi-bin/camera-stream.sh";
$timelapse_exec = $install_path . "/cgi-bin/camera-timelapse.sh";
$sqlite_db = $install_path . "/config/mycodo.db";

$daemon_log = $install_path . "/log/daemon.log";
$auth_log = $install_path . "/log/auth.log";
$sensor_ht_log = $install_path . "/log/sensor-ht.log";
$sensor_co2_log = $install_path . "/log/sensor-co2.log";
$relay_log = $install_path . "/log/relay.log";

$images = $install_path . "/images";
$lock_raspistill = $lock_path . "/mycodo_raspistill";
$lock_mjpg_streamer = $lock_path . "/mycodo_mjpg_streamer";
$lock_mjpg_streamer_light = $lock_path . "/mycodo-stream-light";
$lock_time_lapse = $lock_path . "/mycodo_time_lapse";
$lock_time_lapse_light = $lock_path . "/mycodo-timelapse-light";

$camera_error = NULL;

require_once("includes/functions.php"); // Mycodo functions
require("includes/database.php"); // Initial SQL database load to variables

// Output an error if the user guest attempts to submit certain forms
$output_error = NULL;
if ($_SERVER['REQUEST_METHOD'] == 'POST' && $_SESSION['user_name'] == 'guest' &&
    !isset($_POST['Graph']) && !isset($_POST['login'])) {
    $output_error = 'guest';
} else if ($_SERVER['REQUEST_METHOD'] == 'POST' && $_SESSION['user_name'] != 'guest') {
    // Only non-guest users may perform these actions
    require_once("includes/restricted.php"); // Configuration changes
    require("includes/database.php"); // Reload SQLite database
}
require_once("includes/public.php"); // Handle remaining forms
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
    <?php
        if (isset($_GET['r']) && ($_GET['r'] == 1)) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";
    ?>
</head>
<body>
<div class="cd-tabs">
<?php
// Display an error that occurred
if ($output_error) {
    switch ($output_error) {
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
    $output_error = False;
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
        <div style="padding-bottom: 0.1em;"><?php
            if (daemon_active()) echo '<input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="daemon_change" value="0"> Daemon';
            else echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="daemon_change" value="1"> Daemon';
            ?></div>
        <div style="padding-bottom: 0.1em;"><?php
            if (file_exists($lock_raspistill) && file_exists($lock_mjpg_streamer)) {
                echo '<input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="" value="0">';
            } else {
                echo '<input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0">';
            }
            ?> Stream</div>
        <div><?php
            if (isset($_GET['r'])) {
                ?><div style="display:inline-block; vertical-align:top;"><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="" value="0">
                </div>
                <div style="display:inline-block; padding-left: 0.3em;">
                    <div>Refresh <span style="font-size: 0.7em">(<?php echo $tab; ?>)</span></div>
                </div><?php
            } else {
                ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="" value="0"> Refresh<?php
            }
        ?></div>
    </div>
    <div style="float: left; vertical-align:top; height: 4.5em; padding: 1em 0.8em 0 0.3em;">
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;">Time now: <?php echo $time_now; ?></div>
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;">Last read: <?php echo $time_last; ?></div>
        <div style="text-align: right; padding-top: 3px; font-size: 0.9em;"><?php echo `uptime | grep -ohe 'load average[s:][: ].*' `; ?></div>
    </div>
    <?php
    // Display brief Temp/Hum sensor and PID data in header
    for ($i = 1; $i <= $sensor_ht_num; $i++) {
        if ($sensor_ht_activated[$i] == 1) { ?>
            <div class="header">
                <table>
                    <tr>
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo "HT" . $i . ": " . $sensor_ht_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php
                            echo "Now<br><span title=\"" . number_format((float)$t_f[$i], 1, '.', '') . "&deg;F\">" . number_format((float)$t_c[$i], 1, '.', '') . "&deg;C</span>";
                            echo "<br>" . number_format((float)$hum[$i], 1, '.', '') . "%";
                        ?></td>
                        <td style="font-size: 0.8em;"><?php
                            echo "Set<br><span title=\"" . number_format((float)$settemp_f[$i], 1, '.', '') ."&deg;F\">" . number_format((float)$pid_temp_set[$i], 1, '.', '') . "&deg;C</span>";
                            echo "<br>" . number_format((float)$pid_hum_set[$i], 1, '.', '') . "%";
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
                        <td colspan=2 align=center style="border-bottom:1pt solid black; font-size: 0.8em;"><?php echo "CO<sub>2</sub>" . $i . ": " . $sensor_co2_name[$i]; ?></td>
                    </tr>
                    <tr>
                        <td style="font-size: 0.8em; padding-right: 0.5em;"><?php echo "Now<br>" . $co2[$i]; ?></td>
                        <td style="font-size: 0.8em;"><?php echo "Set<br>" . $pid_co2_set[$i]; ?></td>
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
			<li><a data-content="main" <?php
                if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'main')) {
                    echo "class=\"selected\"";
                } ?> href="#0">Main</a></li>
			<li><a data-content="configure" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'config') {
                    echo "class=\"selected\"";
                } ?> href="#0">Configure</a></li>
			<li><a data-content="graph" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'graph') {
                    echo "class=\"selected\"";
                } ?> href="#0">Graphs</a></li>
			<li><a data-content="camera" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'camera') {
                    echo "class=\"selected\"";
                } ?> href="#0">Camera</a></li>
			<li><a data-content="log" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'log') {
                    echo "class=\"selected\"";
                } ?> href="#0">Log</a></li>
			<li><a data-content="advanced" <?php
                if (isset($_GET['tab']) && $_GET['tab'] == 'adv') {
                    echo "class=\"selected\"";
                } ?> href="#0">Advanced</a></li>
		</ul>
	</nav>
	<ul class="cd-tabs-content">
		<li data-content="main" <?php
            if (!isset($_GET['tab']) || (isset($_GET['tab']) && $_GET['tab'] == 'main')) {
                echo "class=\"selected\"";
            } ?>>
            <FORM action="?tab=main<?php
            if (isset($_GET['page'])) {
                echo "&page=" . $_GET['page'];
            }
            if (isset($_GET['Refresh']) || isset($_POST['Refresh'])) {
                echo "&Refresh=1";
            }
            if (isset($_GET['r'])) {
                echo "&r=" . $_GET['r'];
            } ?>" method="POST">
            <div>
                <div style="padding-top: 0.5em;">
                    <div style="float: left; padding: 0 1.5em 1em 0.5em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">Auto Refresh</div>
                        <div style="text-align: center;"><?php
                            if (isset($_GET['r']) && $_GET['r'] == 1) {
                                if (empty($page)) {
                                    echo '<a href="?tab=main">OFF</a> | <span class="on">ON</span>';
                                } else {
                                    echo '<a href="?tab=main&page=' . $page . '">OFF</a> | <span class="on">ON</span>';
                                }
                            } else {
                                if (empty($page)) {
                                    echo '<span class="off">OFF</span> | <a href="?tab=main&Refresh=1&r=1">ON</a>';
                                } else {
                                    echo '<span class="off">OFF</span> | <a href="?tab=main&page=' . $page . '&Refresh=1&r=1">ON</a>';
                                }
                            }
                        ?>
                        </div>
                    </div>
                    <div style="float: left; padding: 0 2em 1em 0.5em;">
                        <div style="text-align: center; padding-bottom: 0.2em;">Refresh</div>
                        <div>
                            <div style="float: left; padding-right: 0.1em;">
                                <input type="button" onclick='location.href="?tab=main<?php
                                if (isset($_GET['page'])) {
                                    if ($_GET['page']) {
                                        echo "&page=" . $page;
                                    }
                                }
                                if (isset($_GET['r'])) {
                                    if ($_GET['r'] == 1) {
                                        echo "&r=1";
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
                                            echo "checked"; 
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
                                            echo "checked"; 
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
                                <option value="default" <?php if ($graph_time_span == 'default') echo "selected=\"selected\""; ?>>Day/Week</option>
                                <option value="1h" <?php if ($graph_time_span == '1h') echo "selected=\"selected\""; ?>>1 Hour</option>
                                <option value="6h" <?php if ($graph_time_span == '6h') echo "selected=\"selected\""; ?>>6 Hours</option>
                                <option value="1d" <?php if ($graph_time_span == '1d') echo "selected=\"selected\""; ?>>1 Day</option>
                                <option value="3d" <?php if ($graph_time_span == '3d') echo "selected=\"selected\""; ?>>3 Days</option>
                                <option value="1w" <?php if ($graph_time_span == '1w') echo "selected=\"selected\""; ?>>1 Week</option>
                                <option value="1m" <?php if ($graph_time_span == '1m') echo "selected=\"selected\""; ?>>1 Month</option>
                                <option value="3m" <?php if ($graph_time_span == '3m') echo "selected=\"selected\""; ?>>3 Months</option>
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
                    generate_graphs($mycodo_client, $graph_id, $graph_type, $graph_time_span, $sensor_ht_num, $sensor_co2_num, $sensor_ht_graph, $sensor_co2_graph);

                    // If any graphs are to be displayed, show links to the legends
                    if (array_sum($sensor_ht_graph) + array_sum($sensor_co2_graph)) { ?>
                        <div style="width: 100%; padding: 1em 0 0 0; text-align: center;">
                            Legend: <a href="javascript:open_legend()">Brief</a> / <a href="javascript:open_legend_full()">Full</a>
                            <div style="text-align: center; padding-top: 0.5em;">
                                <a href="https://github.com/kizniche/Mycodo" target="_blank">Mycodo on GitHub</a>
                            </div>
                        </div>
                    <?php
                    } else { ?>
                        <div style="width: 100%; padding: 2em 0 0 0; text-align: center;">
                            There are currently 0 sensors activated for graphing.
                            <br>Sensors can be activated for logging and graphing in the Configure tab.
                        </div>
                    <?php
                    }
                    ?>
            </div>
            </div>
            </form>

		</li>

		<li data-content="configure" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'config') {
                echo "class=\"selected\"";
            } ?>>
            <FORM action="?tab=config<?php
                if (isset($_GET['page'])) {
                    echo "&page=" . $_GET['page'];
                }
                if (isset($_GET['r'])) {
                    echo "&r=" . $_GET['r'];
                }
                ?>" method="POST">
            <div style="padding-top: 0.5em;">
                <div style="float: left; padding: 0 1.5em 1em 0.5em;">
                    <div style="text-align: center; padding-bottom: 0.2em;">Auto Refresh</div>
                    <div style="text-align: center;"><?php
                        if (isset($_GET['r'])) {
                            if ($_GET['r'] == 1) {
                                echo "<a href=\"?tab=config\">OFF</a> | <span class=\"on\">ON</span>";
                            } else {
                                echo "<span class=\"off\">OFF</span> | <a href=\"?tab=config&?r=1\">ON</a>";
                            }
                        } else {
                            echo "<span class=\"off\">OFF</span> | <a href=\"?tab=config&r=1\">ON</a>";
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
            </div>

            <div style="clear: both;"></div>

            <div style="width: 45em; padding-left: 3em; padding-top: 1em;">
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
                    <div class="config-title">Relays</div>
                    <div style="clear: both;"></div>
                </div>

                <?php
                if ($relay_num > 0) {
                ?><div style="padding-bottom: 3em;">
                    <table class="relays">
                        <tr>
                            <td align=center class="table-header">Relay<br>No.</td>
                            <td align=center class="table-header">Relay<br>Name</td>
                            <th align=center class="table-header">Current<br>State</th>
                            <td align=center class="table-header">Seconds<br>On</td>
                            <td align=center class="table-header">GPIO<br>Pin</td>
                            <td align=center class="table-header">Trigger<br>ON</td>
                            <td align=center class="table-header"></td>
                        </tr>
                        <?php for ($i = 1; $i <= $relay_num; $i++) {
                            $read = "$gpio_path -g read $relay_pin[$i]";
                        ?>
                        <tr>
                            <td align=center>
                                <?php echo $i; ?>
                            </td>
                            <td align=center>
                                <input style="width: 10em;" type="text" value="<?php echo $relay_name[$i]; ?>" maxlength=13 size=10 name="relay<?php echo $i; ?>name" title="Name of relay <?php echo $i; ?>"/>
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
                                <input style="width: 3em;" type="number" min="1" max="40" value="<?php echo $relay_pin[$i]; ?>" name="relay<?php echo $i; ?>pin" title="GPIO pin using BCM numbering, connected to relay <?php echo $i; ?>"/>
                            </td>
                            <td align=center>
                                <select style="width: 65px;" title="Does this relay activate with a LOW (0-volt) or HIGH (5-volt) signal?" name="relay<?php echo $i; ?>trigger">
                                    <option<?php
                                        if ($relay_trigger[$i] == 1) {
                                            echo " selected=\"selected\"";
                                        } ?> value="1">HIGH</option>
                                    <option<?php
                                        if ($relay_trigger[$i] == 0) {
                                            echo " selected=\"selected\"";
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

                <div style="padding: 1em 0;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoHTSensors" value="Save ->">
                        <select name="numhtsensors">
                            <option value="0"<?php
                                if ($sensor_ht_num == 0) {
                                    echo " selected=\"selected\"";
                                } ?>>0</option>
                            <option value="1"<?php
                                if ($sensor_ht_num == 1) {
                                    echo " selected=\"selected\"";
                                } ?>>1</option>
                            <option value="2"<?php
                                if ($sensor_ht_num == 2) {
                                    echo " selected=\"selected\"";
                                } ?>>2</option>
                            <option value="3"<?php
                                if ($sensor_ht_num == 3) {
                                    echo " selected=\"selected\"";
                                } ?>>3</option>
                            <option value="4"<?php
                                if ($sensor_ht_num == 4) {
                                    echo " selected=\"selected\"";
                                } ?>>4</option>
                        </select>
                    </div>
                    <div class="config-title">Humidity & Temperature Sensors</div>
                    <div style="clear: both;"></div>
                </div>

                <?php if ($sensor_ht_num > 0) { ?>
                <div style="padding-bottom: 3em;">
                    <?php
                    for ($i = 1; $i <= $sensor_ht_num; $i++) {
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
                                <input style="width: 11em;" type="text" value="<?php echo $sensor_ht_name[$i]; ?>" maxlength=12 size=10 name="sensorht<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 80px;" name="sensorht<?php echo $i; ?>device">
                                    <option<?php
                                        if ($sensor_ht_device[$i] == 'DHT11') {
                                            echo " selected=\"selected\"";
                                        } ?> value="DHT11">DHT11</option>
                                    <option<?php
                                        if ($sensor_ht_device[$i] == 'DHT22') {
                                            echo " selected=\"selected\"";
                                        } ?> value="DHT22">DHT22</option>
                                    <option<?php
                                        if ($sensor_ht_device[$i] == 'AM2302') {
                                            echo " selected=\"selected\"";
                                        } ?> value="AM2302">AM2302</option>
                                    <option<?php
                                        if ($sensor_ht_device[$i] == 'Other') {
                                            echo " selected=\"selected\"";
                                        } ?> value="Other">Other</option>
                                </select>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="40" value="<?php echo $sensor_ht_pin[$i]; ?>" maxlength=2 size=1 name="sensorht<?php echo $i; ?>pin" title="This is the GPIO pin connected to the DHT sensor"/>
                            </td>
                            <td align=center>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_ht_period[$i]; ?>" name="sensorht<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
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

                    <div style="padding-bottom: <?php if ($i == $sensor_ht_num) echo '1'; else echo '2'; ?>em;">
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
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>TempOR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>TempOR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>TempOR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>TempOR" value="1">OFF</button>
                                <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_temp_relay[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>TempRelay" title="This is the relay connected to the heating device"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_temp_set[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>TempSet" title="This is the desired temperature"/> °C
                            </td>
                            <td align=center>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_temp_period[$i]; ?>" name="Set<?php echo $i; ?>TempPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another temperature reading and applying the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_temp_p[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_temp_i[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_temp_d[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Temp_D" title="This is the Derivative value of the PID"/>
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
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>HumOR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>HumOR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>HumOR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>HumOR" value="1">OFF</button>
                                <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_hum_relay[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>HumRelay" title="This is the relay connected to your humidifying device"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_hum_set[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>HumSet" title="This is the desired humidity"/> %
                            </td>
                            <td align=center>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_hum_period[$i]; ?>" name="Set<?php echo $i; ?>HumPeriod" title="This is the number of seconds to wait after the relay has been turned off before taking another humidity reading and applying the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_hum_p[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_hum_i[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_hum_d[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Hum_D" title="This is the Derivative value of the PID"/>
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

                <div style="padding-bottom: 1em;">
                    <div style="float: left; padding-right: 1em;">
                        <input type="submit" name="ChangeNoCo2Sensors" value="Save ->">
                        <select name="numco2sensors">
                            <option value="0"<?php
                                if ($sensor_co2_num == 0) {
                                    echo " selected=\"selected\"";
                                } ?>>0</option>
                            <option value="1"<?php
                                if ($sensor_co2_num == 1) {
                                    echo " selected=\"selected\"";
                                } ?>>1</option>
                        </select>
                    </div>
                    <div class="config-title">CO<sub>2</sub> Sensors</div>
                    <div style="clear: both;"></div>
                </div>

                <?php
                if ($sensor_co2_num > 0) {
                ?>

                <div>
                    <?php
                    for ($i = 1; $i <= $sensor_co2_num; $i++) {
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
                                <input style="width: 7em;" type="text" value="<?php echo $sensor_co2_name[$i]; ?>" maxlength=12 size=10 name="sensorco2<?php echo $i; ?>name" title="Name of area using sensor <?php echo $i; ?>"/>
                            </td>
                            <td>
                                <select style="width: 80px;" name="sensorco2<?php echo $i; ?>device">
                                    <option<?php
                                        if ($sensor_co2_device[$i] == 'K30') {
                                            echo " selected=\"selected\"";
                                        } ?> value="K30">K30</option>
                                    <option<?php
                                        if ($sensor_co2_device[$i] == 'Other') {
                                            echo " selected=\"selected\"";
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
                            <td align=center>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $sensor_co2_period[$i]; ?>" name="sensorco2<?php echo $i; ?>period" title="The number of seconds between writing sensor readings to the log"/>
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
                                    ?><input type="image" class="indicate" src="/mycodo/img/off.jpg" alt="Off" title="Off, Click to turn on." name="Change<?php echo $i; ?>Co2OR" value="0"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>Co2OR" value="0">ON</button>
                                    <?php
                                } else {
                                    ?><input type="image" class="indicate" src="/mycodo/img/on.jpg" alt="On" title="On, Click to turn off." name="Change<?php echo $i; ?>Co2OR" value="1"> | <button style="width: 3em;" type="submit" name="Change<?php echo $i; ?>Co2OR" value="1">OFF</button>
                                    <?php
                                }
                                ?>
                            </td>
                            <td>
                                <input  style="width: 3em;" type="number" min="0" max="8" value="<?php echo $pid_co2_relay[$i]; ?>" maxlength=1 size=1 name="Set<?php echo $i; ?>Co2Relay" title="This is the relay connected to the device that modulates CO2"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_set[$i]; ?>" maxlength=4 size=2 name="Set<?php echo $i; ?>Co2Set" title="This is the desired CO2 level"/> ppm
                            </td>
                            <td align=center>
                                <input style="width: 4em;" type="number" min="1" max="99999" value="<?php echo $pid_co2_period[$i]; ?>" maxlength=4 size=1 name="Set<?php echo $i; ?>Co2Period" title="This is the number of seconds to wait after the relay has been turned off before taking another CO2 reading and applying the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_p[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_P" title="This is the Proportional value of the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_i[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_I" title="This is the Integral value of the the PID"/>
                            </td>
                            <td>
                                <input style="width: 4em;" type="number" step="any" value="<?php echo $pid_co2_d[$i]; ?>" maxlength=5 size=1 name="Set<?php echo $i; ?>Co2_D" title="This is the Derivative value of the PID"/>
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

		<li data-content="graph" <?php
            if (isset($_GET['tab'])) {
                if ($_GET['tab'] == 'graph') {
                    echo "class=\"selected\"";
                }
            } ?>>
            <?php
            /* DateSelector*Author: Leon Atkinson */
            if (isset($_POST['SubmitDates']) and $_SESSION['user_name'] != 'guest') {
                
                concatenate_logs();

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
                        echo `echo "set terminal png size $graph_width,1600
                        set xdata time
                        set timefmt \"%Y %m %d %H %M %S\"
                        set output \"$images/graph-custom-combined-$id2-0.png\"
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
                        unset key
                        #set xlabel \"Date and Time\"
                        #set ylabel \"% Humidity\"
                        set multiplot layout 4, 1 title \"Combined Sensor Data - $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
                        set title \"Combined Temperatures\"
                        plot \"<awk '\\$10 == 1' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T1\" w lp ls 1 axes x1y2, \\
                        \"<awk '\\$10 == 2' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T2\" w lp ls 2 axes x1y2, \\
                        \"<awk '\\$10 == 3' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T3\" w lp ls 3 axes x1y2, \\
                        \"<awk '\\$10 == 4' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \"T4\" w lp ls 4 axes x1y2 \\
                        unset key
                        set title \"Combined Humidities\"
                        plot \"<awk '\\$10 == 1' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH1\" w lp ls 1 axes x1y1, \\
                        \"<awk '\\$10 == 2' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH2\" w lp ls 2 axes x1y1, \\
                        \"<awk '\\$10 == 3' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH3\" w lp ls 3 axes x1y1, \\
                        \"<awk '\\$10 == 4' /var/tmp/sensor-ht.log\" using 1:8 index 0 title \"RH4\" w lp ls 4 axes x1y1 \\
                        unset key
                        set title \"Combined CO2s\"
                        plot \"<awk '\\$15 == 1' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"RH1\" w lp ls 1 axes x1y1, \\
                        \"<awk '\\$15 == 2' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"RH2\" w lp ls 2 axes x1y1, \\
                        \"<awk '\\$15 == 3' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"RH3\" w lp ls 3 axes x1y1, \\
                        \"<awk '\\$15 == 4' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \"RH4\" w lp ls 4 axes x1y1 \\
                        unset key
                        set title \"Relay Run Time\"
                        plot \"$relay_log\" u 1:7 index 0 title \"$relay_name[1]\" w impulses ls 5 axes x1y1, \\
                        \"\" using 1:8 index 0 title \"$relay_name[2]\" w impulses ls 6 axes x1y1, \\
                        \"\" using 1:9 index 0 title \"$relay_name[3]\" w impulses ls 7 axes x1y1, \\
                        \"\" using 1:10 index 0 title \"$relay_name[4]\" w impulses ls 8 axes x1y1, \\
                        \"\" using 1:11 index 0 title \"$relay_name[5]\" w impulses ls 9 axes x1y1, \\
                        \"\" using 1:12 index 0 title \"$relay_name[6]\" w impulses ls 10 axes x1y1, \\
                        \"\" using 1:13 index 0 title \"$relay_name[7]\" w impulses ls 11 axes x1y1, \\
                        \"\" using 1:14 index 0 title \"$relay_name[8]\" w impulses ls 12 axes x1y1 \\
                        unset multiplot" | gnuplot`;
                        echo "<div style=\"width: 100%; text-align: center; padding: 1em 0 3em 0;\"><img src=image.php?";
                        echo "graphtype=custom-combined";
                        echo "&id=" . $id2;
                        echo "&sensornumber=0>";
                        echo "</div>";
                    } else if ($_POST['custom_type'] == 'Separate') {
                        for ($n = 1; $n <= $sensor_ht_num; $n++) {
                            if ($sensor_ht_graph[$n] == 1) {
                                echo `echo "set terminal png size $graph_width,490
                                set xdata time
                                set timefmt \"%Y %m %d %H %M %S\"
                                set output \"$images/graph-ht-custom-separate-$id2-$n.png\"
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
                                unset key
                                #set xlabel \"Date and Time\"
                                #set ylabel \"% Humidity\"
                                set title \"Sensor $n: $sensor_ht_name[$n]: $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
                                plot \"<awk '\\$10 == $n' /var/tmp/sensor-ht.log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
                                \"\" using 1:8 index 0 title \"T\" w lp ls 2 axes x1y1, \\
                                \"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, \\
                                \"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[1]\" w impulses ls 4 axes x1y1, \\
                                \"\" using 1:8 index 0 title \"$relay_name[2]\" w impulses ls 5 axes x1y1, \\
                                \"\" using 1:9 index 0 title \"$relay_name[3]\" w impulses ls 6 axes x1y1, \\
                                \"\" using 1:10 index 0 title \"$relay_name[4]\" w impulses ls 7 axes x1y1, \\
                                \"\" using 1:11 index 0 title \"$relay_name[5]\" w impulses ls 8 axes x1y1, \\
                                \"\" using 1:12 index 0 title \"$relay_name[6]\" w impulses ls 9 axes x1y1, \\
                                \"\" using 1:13 index 0 title \"$relay_name[7]\" w impulses ls 10 axes x1y1, \\
                                \"\" using 1:14 index 0 title \"$relay_name[8]\" w impulses ls 11 axes x1y1" | gnuplot`;
                                echo "<div style=\"width: 100%; text-align: center; padding: 1em 0 3em 0;\"><img src=image.php?";
                                echo "graphtype=custom-separate";
                                echo "&sensortype=ht";
                                echo "&id=" . $id2;
                                echo "&sensornumber=" . $n . ">";
                                echo "</div>";
                            }
                            if ($n != $sensor_ht_num || ($n == $sensor_ht_num && array_sum($sensor_co2_graph))) { echo "<hr class=\"fade\"/>"; }
                        }
                        for ($n = 1; $n <= $sensor_co2_num; $n++) {
                            if ($sensor_co2_graph[$n] == 1) {
                                echo `echo "set terminal png size $graph_width,490
                                set xdata time
                                set timefmt \"%Y %m %d %H %M %S\"
                                set output \"$images/graph-co2-custom-separate-$id2-$n.png\"
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
                                unset key
                                #set xlabel \"Date and Time\"
                                #set ylabel \"ppm CO2\"
                                set title \"Sensor $n: $sensor_co2_name[$n]: $monb/$dayb/$yearb $hourb:$minb - $mone/$daye/$yeare $houre:$mine\"
                                plot \"<awk '\\$10 == $n' /var/tmp/sensor-co2.log\" using 1:7 index 0 title \" RH\" w lp ls 1 axes x1y2, \\
                                \"<awk '\\$15 == $n' $relay_log\" u 1:7 index 0 title \"$relay_name[1]\" w impulses ls 4 axes x1y1, \\
                                \"\" using 1:8 index 0 title \"$relay_name[2]\" w impulses ls 5 axes x1y1, \\
                                \"\" using 1:9 index 0 title \"$relay_name[3]\" w impulses ls 6 axes x1y1, \\
                                \"\" using 1:10 index 0 title \"$relay_name[4]\" w impulses ls 7 axes x1y1, \\
                                \"\" using 1:11 index 0 title \"$relay_name[5]\" w impulses ls 8 axes x1y1, \\
                                \"\" using 1:12 index 0 title \"$relay_name[6]\" w impulses ls 9 axes x1y1, \\
                                \"\" using 1:13 index 0 title \"$relay_name[7]\" w impulses ls 10 axes x1y1, \\
                                \"\" using 1:14 index 0 title \"$relay_name[8]\" w impulses ls 11 axes x1y1" | gnuplot`;
                                echo "<div style=\"width: 100%; text-align: center; padding: 1em 0 3em 0;\"><img src=image.php?";
                                echo "graphtype=custom-separate";
                                echo "&sensortype=co2";
                                echo "&id=" . $id2;
                                echo "&sensornumber=" . $n . ">";
                                echo "</div>";
                            }
                            if ($n != $sensor_co2_num) { echo "<hr class=\"fade\"/>"; }
                        }
                    }
                    echo "<div style=\"width: 100%; text-align: center;\"><a href='javascript:open_legend()'>Brief Graph Legend</a> - <a href='javascript:open_legend_full()'>Full Graph Legend</a></div>";
                }
            } else if (isset($_POST['SubmitDates']) and $_SESSION['user_name'] == 'guest') {
                displayform();
                echo "<div>Guest access has been revoked for graph generation.";
            } else displayform();
            ?>
		</li>

		<li data-content="camera" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'camera') {
                echo "class=\"selected\"";
            } ?>>

            <?php
            if ($camera_error != NULL) {
                echo '<div style="color: red;">' . $camera_error . '</div>';
            }
            ?>

            <form action="?tab=camera" method="POST">
            <div style="float: left; padding: 0.5em;">
                Use light during capture? <input type="checkbox" name="lighton" value="1">
            </div>
            <div style="float: left; padding: 0.5em;">
                <button name="Capture" type="submit" value="">Capture Still</button>
            </div>

            <div style="clear: both;"></div>

            <div>
                <div style="float: left; padding: 0.5em;">
                    <?php
                    if (!file_exists($lock_time_lapse)) {
                        echo '<button name="start-timelapse" type="submit" value="">Start</button>';
                    } else {
                        echo '<button name="stop-timelapse" type="submit" value="">Stop</button>';
                    }
                    ?>
                </div>
                <div style="float: left; font-weight: bold; padding: 0.8em 1em 0.5em 0;">
                    Timelapse <?php
                    if (!file_exists($lock_time_lapse)) {
                        echo '(<span class="off">OFF</span>)';
                    } else {
                        echo '(<span class="on">ON</span>)';
                    }
                    ?>
                </div>
                <div style="float: left; padding: 0.5em;">
                    Duration: <input style="width: 4em;" type="number" value="60" max="99999" min="1" name="timelapse_duration"> min
                </div>
                <div style="float: left; padding: 0.5em;">
                   Run time: <input style="width: 4em;" type="number" value="600" max="99999" min="1" name="timelapse_runtime"> min (<-- Currently not working)
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
                if (file_exists($lock_mjpg_streamer)) {
                    echo '<img src="http://' . $_SERVER['HTTP_HOST'] . ':8080/?action=stream" />';
                }
                if (isset($_POST['Capture']) && $_SESSION['user_name'] != 'guest') {
                    if ($capture_output != 0) {
                        echo 'Abnormal output (possibly error): ' . $capture_output . '<br>';
                    } else {
                        echo '<p><img src=image.php?span=cam-still></p>';
                    }
                }
            ?>
            </center>
		</li>

		<li data-content="log" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'log') {
                echo "class=\"selected\"";
            } ?>>
			<div style="padding: 10px 0 0 15px;">
                <div style="padding-bottom: 15px;">
                    <FORM action="?tab=log<?php
                        if (isset($_GET['page'])) {
                            echo "&page=" . $_GET['page'];
                        } ?>" method="POST">
                        Lines: <input type="text" maxlength=8 size=8 name="Lines" />
                        <input type="submit" name="HTSensor" value="HT Sensor">
                        <input type="submit" name="Co2Sensor" value="Co2 Sensor">
                        <input type="submit" name="Relay" value="Relay">
                        <input type="submit" name="Users" value="Users">
                        <input type="submit" name="Login" value="Login">
                        <input type="submit" name="Daemon" value="Daemon">
                        <input type="submit" name="Database" value="Database">
                    </FORM>
                </div>
                <div style="font-family: monospace;">
                    <pre><?php
                        if(isset($_POST['HTSensor'])) {
                            concatenate_logs();
                            echo 'Year Mo Day Hour Min Sec Tc RH DPc Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines /var/tmp/sensor-ht.log`;
                            } else {
                                echo `tail -n 30 /var/tmp/sensor-ht.log`;
                            }
                        }

                        if(isset($_POST['Co2Sensor'])) {
                            concatenate_logs();
                            echo 'Year Mo Day Hour Min Sec Co2 Sensor<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines /var/tmp/sensor-co2.log`;
                            } else {
                                echo `tail -n 30 /var/tmp/sensor-co2.log`;
                            }
                        }

                        if(isset($_POST['Relay'])) {
                            concatenate_logs();
                            echo 'Year Mo Day Hour Min Sec R1Sec R2Sec R3Sec R4Sec R5Sec R6Sec R7Sec R8Sec<br> <br>';
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines /var/tmp/relay.log`;
                            } else {
                                echo `tail -n 30 /var/tmp/relay.log`;
                            }
                        }
                        if(isset($_POST['Users']) && $_SESSION['user_name'] != 'guest') {
                            echo 'User Email Password_Hash<br> <br>';
                            $db = new SQLite3("./config/users.db");
                            $results = $db->query('SELECT user_name, user_email, user_password_hash FROM users');
                            while ($row = $results->fetchArray()) {
                                print $row[0] . " " . $row[1] . " " . $row[2] . "<br>";
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
                            `cat /var/www/mycodo/log/daemon.log /var/www/mycodo/log/daemon-tmp.log > /var/tmp/daemon.log`;
                            if ($_POST['Lines'] != '') {
                                $Lines = $_POST['Lines'];
                                echo `tail -n $Lines /var/tmp/daemon.log`;
                            } else {
                                echo `tail -n 30 /var/tmp/daemon.log`;
                            }
                        }
                        if(isset($_POST['Database'])) {
                            view_sql_db($sqlite_db);
                        }
                    ?>
                    </pre>
                </div>
            </div>
		</li>

		<li data-content="advanced" <?php
            if (isset($_GET['tab']) && $_GET['tab'] == 'adv') {
                echo "class=\"selected\"";
            } ?>>

            <?php if ($this->feedback) echo $this->feedback; ?>

            <div style="padding:1.5em 0 0 3em;">
                <div class="adv" style="padding-bottom: 2.5em;">
                    <form action="?tab=adv" method="POST">
                    <div style="padding-bottom: 1em; font-weight: bold;">
                        <input type="submit" name="ChangeNoTimers" value="Save ->">
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
                        <strong>Timers</strong>
                    </div>
                    <?php
                    if ($timer_num > 0) {
                    ?>
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
                            <?php
                            for ($i = 1; $i <= $timer_num; $i++) {
                            ?>
                            <tr>
                                <td align="center">
                                    <?php echo $i; ?>
                                </td>
                                <td>
                                    <input style="width: 7em;" type="text" value="<?php echo $timer_name[$i]; ?>" maxlength=10 size=5 name="Timer<?php echo $i; ?>Name" title="This is the relay name for timer <?php echo $i; ?>"/>
                                </td>
                                <?php
                                if ($timer_state[$i] == 0) {
                                ?>
                                    <th colspan=2 align=right>
                                        <nobr><input type="hidden" name="Timer<?php echo $i; ?>State" value="0"><input type="image" style="height: 0.9em;" src="/mycodo/img/off.jpg" alt="Off" title="Off" name="Timer<?php echo $i; ?>StateChange" value="0"> | <button style="width: 40px;" type="submit" name="Timer<?php echo $i; ?>StateChange" value="1">ON</button></nobr>
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
                    </form>
                    <?php
                    }
                    ?>
                </div>

                <div style="clear: both;"></div>

                <div class="advanced" style="padding-bottom: 2em;">
                    <form method="post" action="?tab=adv" name="debug">
                    <div style="font-weight: bold; padding: 0.5em 0;">
                        Debugging
                    </div>
                    <div>
                        Display Debugging Information
                        <input type="hidden" name="debug" value="0" />
                        <input type="checkbox" id="debug" name="debug" value="1"<?php if (isset($_COOKIE['debug'])) if ($_COOKIE['debug'] == True) echo ' checked'; ?>/>
                        <input type="submit" value="Save">
                    </div>
                    </form>
                </div>

                <div style="clear: both;"></div>

                <div class="advanced">
                    <div style="padding-bottom: 2em;">
                        <form method="post" action="?tab=adv" name="smtp">
                        <div>
                            <div style="font-weight: bold; padding: 0.5em 0;">
                                Camera
                            </div>
                            <div class="adv">
                                Light Relay: <input style="width: 3em;" type="number" min="0" max="8" value="<?php echo $camera_relay; ?>" maxlength=4 size=1 name="lightrelay" title=""/>
                            </div>
                            <div class="adv">
                                ANother variable3
                            </div>
                            <div class="adv">
                                <button name="ChangeCamera" type="submit" value="">Save</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div style="clear: both;"></div>

                <div <div class="advanced">
                    <form method="post" action="?tab=adv" name="smtp">
                    <div style="padding-bottom: 2em;">
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
                    </div>
                    </form>
                </div>

                <div style="clear: both;"></div>

                <div class="advanced">
                    <div style="padding-bottom: 1em;">
                        <form method="post" action="?tab=adv" name="addform">
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
                        <form method="post" action="?tab=adv" name="changeform">
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
                        <form method="post" action="?tab=adv" name="delform">
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
            </div>
		</li>
	</ul> <!-- cd-tabs-content -->
</div> <!-- cd-tabs -->
<script src="js/jquery-2.1.1.js"></script>
<script src="js/main.js"></script> <!-- Resource jQuery -->
<?php
if (isset($_COOKIE['debug'])) {
    if ($_COOKIE['debug'] == True) {
        ?>
        <div style="clear: both;"></div>        
        
        <div style="padding: 4em 0 2em 2em;">
            <div style="padding-bottom: 1em; font-weight: bold; font-size: 1.5em;">
                Debug Information
            </div>
            <div style="padding-bottom: 2em;">
                <div style="padding: 1em 0; font-weight: bold; font-size: 1.2em;">
                    PHP Profile
                </div>
                <pre><?php 
                    SimpleProfiler::stop_profile();
                    print_r(SimpleProfiler::get_profile());
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
                    SQLite Database
                </div>
                <pre><?php exec('sqlite3 ' . $sqlite_db . ' .dump', $output); print_r($output); ?></pre>
            </div>
        </div>
        <?php
    }
}
?>
</body>
</html>
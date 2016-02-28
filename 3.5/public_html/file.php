<?php
/*
*  file.php - Authenticates the tranfer of files, images, and video
*              streams from protected locations.
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

####### Configure #######
$install_path = dirname(__FILE__);

$image_dir = $install_path . "/../images/";
$still_dir = $install_path . "/public_html/camera-stills/";
$timelapse_dir = $install_path . "/public_html/camera-timelapse/";
$upload_dir = $install_path . "/notes/uploads/";
$hdr_dir = $install_path . "/public_html/camera-hdr/";
$mycodo_client = $install_path . "/mycodo_core/mycodo-client.py";

require_once("includes/auth.php"); // Check authorization to view

if ($_COOKIE['login_hash'] == $user_hash) {
    if (isset($_GET['span'])) {
        switch ($_GET['span']) {
            case 'cam-still':
                header('Content-Type: image/png');
                $files = scandir($still_dir, SCANDIR_SORT_DESCENDING);
                $newest_file = $files[0];
                readfile($still_dir . $newest_file);
                break;
            case 'cam-timelapse':
                header('Content-Type: image/png');
                $files = scandir($timelapse_dir, SCANDIR_SORT_DESCENDING);
                $newest_file = $files[0];
                readfile($timelapse_dir . $newest_file);
                break;
            case 'cam-hdr':
                header('Content-Type: image/png');
                $files = scandir($still_dir, SCANDIR_SORT_DESCENDING);
                $newest_file = $files[0];
                readfile($still_dir . $newest_file);
                break;
            case 'stream':
                if ($_COOKIE['login_hash'] == $user_hash) {
                    $server = "localhost"; // camera server address
                    $port = 6926; // camera server port
                    $url = "/?action=stream"; // image url on server
                    set_time_limit(0);  
                    $fp = fsockopen($server, $port, $errno, $errstr, 30); 
                    if (!$fp) { 
                            echo "$errstr ($errno)<br>\n";   // error handling
                    } else {
                            $urlstring = "GET ".$url." HTTP/1.0\r\n\r\n"; 
                            fputs ($fp, $urlstring); 
                            while ($str = trim(fgets($fp, 4096))) 
                            header($str); 
                            fpassthru($fp); 
                            fclose($fp); 
                    }
                }
                break;
            case 'ul-png':
                header('Content-Type: image/png');
                readfile($upload_dir . $_GET['file']);
                break;
            case 'ul-jpg':
                header('Content-Type: image/jpeg');
                readfile($upload_dir . $_GET['file']);
                break;
            case 'ul-gif':
                header('Content-Type: image/gif');
                readfile($upload_dir . $_GET['file']);
                break;
            case 'ul-dl':
                $quoted = sprintf('"%s"', addcslashes(basename($upload_dir . $_GET['file']), '"\\'));
                $size   = filesize($upload_dir . $_GET['file']);
                header('Content-Description: File Transfer');
                header('Content-Type: application/octet-stream');
                header('Content-Disposition: attachment; filename=' . $quoted); 
                header('Content-Transfer-Encoding: binary');
                header('Connection: Keep-Alive');
                header('Expires: 0');
                header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
                header('Pragma: public');
                header('Content-Length: ' . $size);
                readfile($upload_dir . $_GET['file']);
                break;
            case 'graph':
                $path = '/var/tmp/' . $_GET['file'];
                header('Content-Type: text/json');
                if (filesize($path) < 16 && trim(file_get_contents($path)) == false) {
                    echo json_encode("0");
                } else {
                    echo json_encode(file_get_contents($path));
                }
                if (!isset($_COOKIE['debug'])) {
                    unlink($path);
                }
                break;
            case 'graph-pop': // Generate dynamic graph in new window with descriptive title
                $mycodo_db = $install_path . "/config/mycodo.db";
                $user_db = $install_path . "/config/users.db";
                $note_db = $install_path . "/config/notes.db";
                require($install_path . "/public_html/includes/database.php");
                require($install_path . "/public_html/includes/functions.php");
                $graph_id = get_graph_cookie('id');

                // Create page title (only create title)
                $sensor_type = $_POST['Generate_Graph_Type'];
                $sensor_span = $_POST['Generate_Graph_Span'];
                if ($sensor_span == "all") {
                    $title = "Graph ($sensor_type) All Time";
                } else {
                    if ($sensor_span == "1 Hour") $time_start = date('Y/m/d-H:i:s', strtotime('-1 hour'));
                    else if ($sensor_span == "3 Hours") $time_start = date('Y/m/d-H:i:s', strtotime('-3 hour'));
                    else if ($sensor_span == "6 Hours") $time_start = date('Y/m/d-H:i:s', strtotime('-6 hour'));
                    else if ($sensor_span == "12 Hours") $time_start = date('Y/m/d-H:i:s', strtotime('-12 hour'));
                    else if ($sensor_span == "1 Day") $time_start = date('Y/m/d-H:i:s', strtotime('-1 day'));
                    else if ($sensor_span == "3 Days") $time_start = date('Y/m/d-H:i:s', strtotime('-3 day'));
                    else if ($sensor_span == "1 Week") $time_start = date('Y/m/d-H:i:s', strtotime('-1 week'));
                    else if ($sensor_span == "2 Weeks") $time_start = date('Y/m/d-H:i:s', strtotime('-2 week'));
                    else if ($sensor_span == "1 Month") $time_start = date('Y/m/d-H:i:s', strtotime('-1 month'));
                    else if ($sensor_span == "3 Months") $time_start = date('Y/m/d-H:i:s', strtotime('-3 month'));
                    else if ($sensor_span == "6 Months") $time_start = date('Y/m/d-H:i:s', strtotime('-6 month'));
                    else if ($sensor_span == "1 Year") $time_start = date('Y/m/d-H:i:s', strtotime('-1 year'));
                    $time_end = date('Y/m/d-H:i:s');
                    $title = "Graph ($sensor_type) Past $sensor_span: $time_start - $time_end";
                }
                
                echo '
                <html lang="en" class="no-js">
                <head>
                    <title>' . $title . '</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <meta name="robots" content="noindex">
                    <link rel="icon" type="image/png" href="img/favicon.png">
                    <link rel="stylesheet" href="css/fonts.css" type="text/css">
                    <link rel="stylesheet" href="css/reset.css" type="text/css">
                    <script src="js/modernizr.js"></script>
                    <script src="js/jquery-2.1.4.min.js"></script>
                    <script src="js/highstock.js"></script>
                    <script src="js/modules/exporting.js"></script>
                    <script src="js/modules/canvas-tools.js"></script>
                    <script src="js/modules/export-csv.js"></script>
                    <script src="js/modules/jspdf.min.js"></script>
                    <script src="js/modules/highcharts-export-clientside.js"></script>';
                if ($_GET['theme'] == 'light') {
                    echo '
                    <link rel="stylesheet" href="css/theme-light.css" type="text/css">
                    ';
                } else if ($_GET['theme'] == 'dark') {
                    echo '
                    <link rel="stylesheet" href="css/theme-dark.css" type="text/css">
                    <script src="js/themes/dark-unica.js"></script>
                    ';
                }
                if (isset($_POST['Generate_Graph'])) {
                    require($install_path . "/public_html/includes/graph.php");
                }
                echo '
                </head>
                    <body>
                        <div id="container" style="width: 100%; height: 100%; "></div>
                    </body>
                </html>
                ';
            break;
            }
    } else if ($_GET['graphtype'] == 'default') {
        header('Content-Type: image/png');
        readfile($image_dir . 'graph-' . $_GET['sensortype'] . '-' . $_GET['graphtype'] . '-' . $_GET['id'] . '-' . $_GET['sensornumber'] . '.png');
    } else if ($_GET['graphtype'] == 'separate') {
        header('Content-Type: image/png');
        readfile($image_dir . 'graph-' . $_GET['sensortype'] . '-' . $_GET['graphtype'] . '-' . $_GET['graphspan'] . '-' . $_GET['id'] . '-' . $_GET['sensornumber'] . '.png');
    } else if ($_GET['graphtype'] == 'combined') {
        header('Content-Type: image/png');
        readfile($image_dir . 'graph-' . $_GET['sensortype'] . '-' . $_GET['graphtype'] . '-' . $_GET['graphspan'] . '-' . $_GET['id'] . '.png');
    } else if ($_GET['graphtype'] == 'combinedcustom') {
        header('Content-Type: image/png');
        readfile($image_dir . 'graph-' . $_GET['sensortype'] . '-combined-' . $_GET['id'] . '.png');
    } else if ($_GET['graphtype'] == 'separatecustom') {
        header('Content-Type: image/png');
        readfile($image_dir . 'graph-' . $_GET['sensortype'] . '-separate-x-' . $_GET['id'] . '-' . $_GET['sensornumber'] . '.png');
    }
}
?>  
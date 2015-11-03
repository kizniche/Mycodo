<?php
/*
*  image.php - Authenticates the tranfer of files, images, and video
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
$install_path = "/var/www/mycodo";

$image_dir = $install_path . "/images/";
$still_dir = $install_path . "/camera-stills/";
$timelapse_dir = $install_path . "/camera-timelapse/";
$upload_dir = $install_path . "/notes/uploads/";
$hdr_dir = $install_path . "/camera-hdr/";
$mycodo_client = $install_path . "/cgi-bin/mycodo-client.py";

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
                header('Content-Type: text/json');
                echo json_encode(file_get_contents('/var/tmp/' . $_GET['file']));
                break;
            case 'graph-pop':
                $mycodo_db = $install_path . "/config/mycodo.db";
                $user_db = $install_path . "/config/users.db";
                $note_db = $install_path . "/config/notes.db";
                require($install_path . "/includes/database.php"); // Initial SQL database load to variables
                require($install_path . "/includes/functions.php"); // Mycodo functions
                $graph_id = get_graph_cookie('id');
                echo '
                <html lang="en" class="no-js">
                <head>
                    <title>Pop-Out Graph</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <meta name="robots" content="noindex">
                    <link rel="icon" type="image/png" href="img/favicon.png">
                    <link rel="stylesheet" href="css/fonts.css" type="text/css">
                    <link rel="stylesheet" href="css/reset.css" type="text/css">
                    <link rel="stylesheet" href="css/style.css" type="text/css">
                    <script src="js/modernizr.js"></script>
                    <script src="js/jquery.min.js"></script>
                    <script src="js/highstock.js"></script>
                    <script src="js/modules/exporting.js"></script>
                    <script src="js/modules/canvas-tools.js"></script>
                    <script src="js/modules/export-csv.js"></script>
                    <script src="js/modules/jspdf.min.js"></script>
                    <script src="js/modules/highcharts-export-clientside.js"></script>
                ';
                if (isset($_POST['Generate_Graph'])) {
                    require($install_path . "/includes/graph.php");
                }
                echo '</head><body>';
                echo '<div id="container" style="width: 100%; height: 100%; "></div>';
                echo '</body></html>';
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
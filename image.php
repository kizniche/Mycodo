<?php
/*
*
*  image.php - displays images when image directory is protected by the web server
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$install_path = "/var/www/mycodo";


$graph_exec = $install_path . "/cgi-bin/graph.sh";
$image_dir = $install_path . "/images/";
$still_dir = $install_path . "/camera-stills/";
$hdr_dir = $install_path . "/camera-hdr/";

if (version_compare(PHP_VERSION, '5.3.7', '<')) {
    exit("Sorry, Simple PHP Login does not run on a PHP version smaller than 5.3.7 !");
} else if (version_compare(PHP_VERSION, '5.5.0', '<')) {
    require_once("libraries/password_compatibility_library.php");
}
require_once('config/config.php');
require_once('translations/en.php');
require_once('libraries/PHPMailer.php');
require_once("classes/Login.php");
$login = new Login();

if ($login->isUserLoggedIn() == true) {

    if (isset($_GET['span'])) {
        header('Content-Type: image/jpeg');
        switch ($_GET['span']) {
            case 'cam-still':
                $files = scandir($still_dir, SCANDIR_SORT_DESCENDING);
                $newest_file = $files[0];
                readfile($still_dir . $newest_file);
                break;
            case 'cam-hdr':
                $files = scandir($still_dir, SCANDIR_SORT_DESCENDING);
                $newest_file = $files[0];
                readfile($still_dir . $newest_file);
                break;
            case 'main':
                readfile($image_dir . 'graph-main-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'separate1h':
                readfile($image_dir . 'graph-separate1h-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'separate6h':
                readfile($image_dir . 'graph-separate6h-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'separate1d':
                readfile($image_dir . 'graph-separate1d-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'separate3d':
                readfile($image_dir . 'graph-separate3d-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'separate1w':
                readfile($image_dir . 'graph-separate1w-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'separate1m':
                readfile($image_dir . 'graph-separate1m-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'separate6m':
                readfile($image_dir . 'graph-separate6m-' . $_GET['mod'] . '-' . $_GET['sensor'] . '.png');
                break;
            case 'combined1h':
                readfile($image_dir . 'graph-combined1h-' . $_GET['mod'] .  '.png');
                break;
            case 'combined6h':
                readfile($image_dir . 'graph-combined6h-' . $_GET['mod'] .  '.png');
                break;
            case 'combined1d':
                readfile($image_dir . 'graph-combined1d-' . $_GET['mod'] .  '.png');
                break;
            case 'combined3d':
                readfile($image_dir . 'graph-combined3d-' . $_GET['mod'] .  '.png');
                break;
            case 'combined1w':
                readfile($image_dir . 'graph-combined1w-' . $_GET['mod'] .  '.png');
                break;
            case 'combined1m':
                readfile($image_dir . 'graph-combined1m-' . $_GET['mod'] .  '.png');
                break;
            case 'combined6m':
                readfile($image_dir . 'graph-combined6m-' . $_GET['mod'] .  '.png');
                break;
            case 'cuscom':
                readfile($image_dir . 'graph-cuscom-' . $_GET['mod'] .  '.png');
                break;
            case 'cussep':
                readfile($image_dir . 'graph-cussep-' . $_GET['mod'] .  '-' . $_GET['sensor'] . '.png');
                break;
            case 'legend':
                $id = uniqid();
                shell_exec($graph_exec . ' legend ' . $id);
                readfile($image_dir . 'graph-legend-' . $id . '.png');
                break;
            case 'legend-full':
                $id = uniqid();
                shell_exec($graph_exec . ' legend-full ' . $id);
                readfile($image_dir . 'graph-legend-full-' . $id . '.png');
                break;
            case 'main-mobile':
                readfile($image_dir . 'graph-main-mobile.png');
                break;
            case '6h-mobile':
                readfile($image_dir . 'graph-6h-' . $_GET['mod'] . '-mobile.png');
                break;
            case 'day-mobile':
                readfile($image_dir . 'graph-day-mobile.png');
                break;
        }
    }
}
?>

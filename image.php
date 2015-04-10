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
	    readfile($image_dir . 'graph-main-' . $_GET['mod'] . '.png');
	    break;
	    case 'main-mobile':
	    readfile($image_dir . 'graph-main-mobile.png');
	    break;
	    case '1h':
	    readfile($image_dir . 'graph-1h-' . $_GET['mod'] . '.png');
	    break;
	    case '6h':
	    readfile($image_dir . 'graph-6h-' . $_GET['mod'] . '.png');
	    break;
	    case '6h-mobile':
	    readfile($image_dir . 'graph-6h-' . $_GET['mod'] . '-mobile.png');
	    break;
	    case 'day':
	    readfile($image_dir . 'graph-day-' . $_GET['mod'] . '.png');
	    break;
	    case 'day-mobile':
	    readfile($image_dir . 'graph-day-mobile.png');
	    break;
	    case 'week':
	    readfile($image_dir . 'graph-week-' . $_GET['mod'] . '.png');
	    break;
	    case 'month':
	    readfile($image_dir . 'graph-month-' . $_GET['mod'] . '.png');
	    break;
	    case 'year':
	    readfile($image_dir . 'graph-year-' . $_GET['mod'] . '.png');
	    break;
	    case 'cus':
	    readfile($image_dir . 'graph-cus-' . $_GET['mod'] . '.png');
	    break;
	    case 'legend':
	    readfile($image_dir . 'graph-legend.png');
	    break;
	    case 'legend-full':
	    readfile($image_dir . 'graph-legend-full.png');
	    break;
	}
    }
}
?>

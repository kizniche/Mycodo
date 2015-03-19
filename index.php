<?php
/*
*
*  index.php - The main page of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$graph_exec = getcwd() . "/cgi-bin/graph.sh";

if (version_compare(PHP_VERSION, '5.3.7', '<')) {
    exit("Sorry, Simple PHP Login does not run on a PHP version smaller than 5.3.7 !");
} else if (version_compare(PHP_VERSION, '5.5.0', '<')) {
    require_once("libraries/password_compatibility_library.php");
}
require_once("config/db.php");
require_once("classes/Login.php");
$login = new Login();

if ($login->isUserLoggedIn() == true) {

include_once ('menu.php');

$page = isset($_GET['page']) ? $_GET['page'] : 'Main';

echo '<html><head><title>Mycodo - ' . $page . '</title>';
echo '<style type="text/css">.inactive, .active, .title, .link {padding:1px 2px 2px 15px;} .inactive {background:skyblue; font-size: 12px;} .active {background:steelblue; font-weight:bold; font-size: 12px;} .title {background:white;} .slink {background:DarkTurquoise; float: center; color: #000; font-size: 11px; font-family: verdana;} .link {background:DarkTurquoise; font-size: 12px;} .link a {color:blue;} .inactive a {text-decoration:none; color:blue;} .active a {text-decoration:none; color:white;} a:hover   {color:black;} </style>';

echo '<script type="text/javascript">
function open_chmode() {
	window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=430, height=400");
}
function open_legend() {
	window.open("image.php?span=legend","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=190, height=210");
}
function open_legend_full() {
	window.open("image.php?span=legend-full","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=600, height=385");
}
</script>';

if (isset($_GET['r'])) {
	if ($_GET['r'] == 1) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";
}

echo '</head><body bgcolor="white">';
echo '<table><tr><td width="150" valign="top">';

page_menu($page);

echo '</td><td width="830" valign="top">';

if (isset($_GET['page'])) {
	switch ($_GET['page']) {
		case 'log out':
			$_SESSION['authenticated'] = 0;
			$inputuser = $_POST['input_user'];
			$inputpassword = $_POST['input_password'];
			if ($_GET['r'] == 1) echo "<meta http-equiv='refresh' content='2;url=index.php?r=1'>";
			else echo "<meta http-equiv='refresh' content='2;url=index.php'>";
			break;
		case 'Main':
			shell_exec($graph_exec . ' dayweek');
			echo "<img src=image.php?span=main>";
			break;
		case '1 Hour':
			shell_exec($graph_exec . '  1h');
			echo "<img src=image.php?span=1h>";
			break;
		case '6 Hours':
			shell_exec($graph_exec . '  6h');
			echo "<img src=image.php?span=6h>";
			break;
		case '1 Day':
			shell_exec($graph_exec . '  day');
			echo "<img src=image.php?span=day>";
			break;
		case '1 Week':
			shell_exec($graph_exec . '  week');
			echo "<img src=image.php?span=week>";
			break;
		case '1 Month':
			shell_exec($graph_exec . '  month');
			echo "<img src=image.php?span=month>";
			break;
		case '1 Year':
			shell_exec($graph_exec . '  year');
			echo "<img src=image.php?span=year>";
			break;
		case 'All':
			shell_exec($graph_exec . ' all');
			echo "<img src=image.php?span=1h><p>
				<img src=image.php?span=6h><p>
				<img src=image.php?span=day><p>
				<img src=image.php?span=week><p>
				<img src=image.php?span=month><p>
				<img src=image.php?span=year>";
			break;
		default:
			shell_exec($graph_exec . ' dayweek');
			echo "<img src=image.php?span=main>";
			break;
	}
} else {
	shell_exec($graph_exec . ' dayweek');
	echo "<img src=image.php?span=main>";
}

echo '</td></tr></table></body></html>';

} else {
	include("views/not_logged_in.php");
}
?>

<?php
/*
*
*  index.php - The main page of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

include "auth.php";
include_once ('menu.php');

$main_path = getcwd();
$graph_data = $main_path . "/mycodo/mycodo-graph.sh";

$page = isset($_GET['page']) ? $_GET['page'] : 'Main';

echo '<html><head><title>Mycodo -' . $page . '</title>';
echo '<style type="text/css">.inactive, .active, .title, .link {padding:1px 2px 2px 15px;} .inactive {background:skyblue; font-size: 12px;} .active {background:steelblue; font-weight:bold; font-size: 12px;} .title {background:white;} .slink {background:DarkTurquoise; float: center; color: #000; font-size: 11px; font-family: verdana;} .link {background:DarkTurquoise; font-size: 12px;} .link a {color:blue;} .inactive a {text-decoration:none; color:blue;} .active a {text-decoration:none; color:white;} a:hover   {color:black;} </style>';

echo '<script type="text/javascript">';
function open_chmode() {
	window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=430, height=400");
}
function open_legend() {
	window.open("graph-legend.png","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=190, height=210");
}
function open_legend_full() {
	window.open("graph-legend-full.png","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=600, height=385");
}
echo '</script>';

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
			shell_exec($graph_data . ' dayweek');
			echo "<img src=graph-main.png>";
			break;
		case '1 Hour':
			shell_exec($graph_data . '  1h');
			echo "<img src=graph-1h.png>";
			break;
		case '6 Hours':
			shell_exec($graph_data . '  6h');
			echo "<img src=graph-6h.png>";
			break;
		case '1 Day':
			shell_exec($graph_data . '  day');
			echo "<img src=graph-day.png>";
			break;
		case '1 Week':
			shell_exec($graph_data . '  week');
			echo "<img src=graph-week.png>";
			break;
		case '1 Month':
			shell_exec($graph_data . '  month');
			echo "<img src=graph-month.png>";
			break;
		case '1 Year':
			shell_exec($graph_data . '  year');
			echo "<img src=graph-year.png>";
			break;
		case 'All':
			shell_exec($graph_data . ' all');
			echo "<img src=graph-1h.png><p>
				<img src=graph-6h.png><p>
				<img src=graph-day.png><p>
				<img src=graph-week.png><p>
				<img src=graph-month.png><p>
				<img src=graph-year.png>";
			break;
		default:
			shell_exec($graph_data . ' dayweek');
			echo "<img src=graph-main.png>";
			break;
	}
} else {
	shell_exec($graph_data . ' dayweek');
	echo "<img src=graph-main.png>";
}

echo '</td></tr></table></body></html>';
?>
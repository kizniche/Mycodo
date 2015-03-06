<?php
/*
*
*  menu.php - The navigation menu of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

$cwd = getcwd();
$sensor_log = $cwd . "/log/sensor.log";
$mycodo_exe = $cwd . "/cgi-bin/mycodo";

function menu_item($id, $title, $current) {
	$class = ($current == $id) ? "active" : "inactive";

	echo '<tr><td class=' . $class . '>';
	echo '<a href="index.php?';
	if (isset($_GET['r'])){
		if ($_GET['r'] == 1) { echo 'r=1&'; }
	}
	echo 'page=' . $id. '">' . $title . '</a></td></tr>';
}

function page_menu ($page) {
	global $sensor_log, $mycodo_exe;
	
	echo '<table width="100%"><tr><td align=center><div style="padding:1px 2px 2px 2px; float: center; color: #000; font-size: 11px; font-family: verdana;">';
	echo 'Last page refresh<br>';
	echo `date +"%Y-%m-%d %H %M %S"`;
	echo '</div></td></tr><tr bgcolor="#cccccc" cellpadding=5><td align=center>';
    echo '<div style="padding:1px 2px 2px 3px; float: center; color: #000; font-size: 11px; font-family: verdana;">';

	echo 'Last sensor read<br>';
    echo `tail -n 1 $sensor_log | cut -d' ' -f1,2,3,4,5,6`;

	echo '</div></td></tr><tr bgcolor="#cccccc" cellpadding=5><td align=right><span style="padding:1px 2px 2px 7px; display:inline; float: left; color: #000; font-size: 11px; font-family: verdana;">';

    echo '<p>T <b>' , `tail -n 1 $sensor_log | cut -d' ' -f9` , '&deg;C</b> (' ,  `tail -n 1 $sensor_log | cut -d' ' -f10` , '&deg;F)<br> ( ' , `$mycodo_exe -r | cut -d' ' -f1` , ' - ' , `$mycodo_exe -r | cut -d' ' -f2` , ' )<p>';
    echo '<p>RH <b>' , `tail -n 1 $sensor_log | cut -d' ' -f8` , '%</b> ( ' , `$mycodo_exe -r | cut -d' ' -f3` , ' - ' , `$mycodo_exe -r | cut -d' ' -f4` , ')<p>';
    $dp_c = `tail -n 1 $sensor_log | cut -d' ' -f11`;
    $dp_c = ($dp_c-32)*5/9;
    echo 'DP <b>' , round($dp_c, 1);
    echo ' &deg;C</b> (' , `tail -n 1 $sensor_log | cut -d' ' -f11` , '&deg;F)';
	echo '</span></td></tr>';
	menu_item('Main', 'Main', $page);
	menu_item('1 Hour', 'Past Hour', $page);
	menu_item('6 Hours', 'Past 6 Hours', $page);
	menu_item('1 Day', 'Past Day', $page);
	menu_item('1 Week', 'Past Week', $page);
	menu_item('1 Month', 'Past Month', $page);
	menu_item('1 Year', 'Past Year', $page);
	menu_item('All', 'All', $page);
    
	echo '<tr><td class=link>Legend: <a href="javascript:open_legend()">Brief</a> - <a href="javascript:open_legend_full()">Full</a></td></tr>
	<tr><td class=link>Ref (90s): ';
	
	if (isset($_GET['r'])) {
		if ($_GET['r'] == 1) echo '<b>On</b> / <a href="index.php?page=$page">Off</a>';
		else echo '<a href="index.php?page=$page&r=1">On</a> / <b>Off</b>';
	} else echo '<a href="index.php?page=$page&r=1">On</a> / <b>Off</b>';
	
	echo '</td></tr>';
	echo '<tr><td class=link><a href="history.php" target="_blank">Log History</a></td></tr>';
	echo '<tr><td class=link><a href="drawgraph.php" target="_blank">Custom Graph</a></td></tr>';
	echo '<tr><td class=link><a href="javascript:open_chmode()">Configuration</a></td></tr>';
	echo '<tr><td class=link><a href="index.php?page=log out">Log Out</a></td></tr>';
	echo '</td></tr></table>';
}
?>

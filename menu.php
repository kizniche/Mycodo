<?php
/*
*
*  menu.php - The navigation menu of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$cwd = getcwd();
$sensor_log = $cwd . "/log/sensor.log";
$mycodo_exe = $cwd . "/cgi-bin/mycodo";


function menu_item($id, $title, $current) {
	$class = ($current == $id) ? "active" : "inactive";

	echo '<tr><td class=' . $class . '>';
	echo '<a href="index.php?';
	if (isset($_GET['r'])){
		if ($_GET['r'] == 1) echo 'r=1&';
	}
	echo 'page=' . $id. '">' . $title . '</a></td></tr>';
}

function page_menu ($page) {
	global $sensor_log, $mycodo_exe;
	
	$t_c = `tail -n 1 $sensor_log | cut -d' ' -f9`;
	$t_f = `tail -n 1 $sensor_log | cut -d' ' -f10`;
	$t_c_max = `$mycodo_exe -r | cut -d' ' -f2`;
	$t_c_min = `$mycodo_exe -r | cut -d' ' -f1`;
	$hum = `tail -n 1 $sensor_log | cut -d' ' -f8`;
	$hum_max = `$mycodo_exe -r | cut -d' ' -f4`;
	$hum_min = `$mycodo_exe -r | cut -d' ' -f3`;
	$dp_f = `tail -n 1 $sensor_log | cut -d' ' -f11`;
    $dp_c = ($dp_f-32)*5/9;
	
	$time_now = `date +"%Y-%m-%d %H %M %S"`;
	$time_last = `tail -n 1 $sensor_log | cut -d' ' -f1,2,3,4,5,6`;
	
	echo '<table width="100%"><tr><td align=center><div style="padding:1px 2px 2px 2px; float: center; color: #000; font-size: 11px; font-family: verdana;">';
	echo 'Last page refresh<br>' , $time_now;
	echo '</div></td></tr><tr bgcolor="#cccccc" cellpadding=5><td align=center>';
    echo '<div style="padding:1px 2px 2px 3px; float: center; color: #000; font-size: 11px; font-family: verdana;">';
	echo 'Last sensor read<br>' , $time_last;
	echo '</div></td></tr><tr bgcolor="#cccccc" cellpadding=5><td align=right><span style="padding:1px 2px 2px 7px; display:inline; float: left; color: #000; font-size: 11px; font-family: verdana;">';
    echo '<p>T <b>' , $t_c , '&deg;C</b> (' , $t_f , '&deg;F)';
	echo '<br>( ' , $t_c_min , ' - ' , $t_c_max , ' )';
	echo '<p><p>RH <b>' , $hum , '%</b> ( ' , $hum_min , ' - ' , $hum_max , ')<p>';
    echo 'DP <b>' , round($dp_c, 1) , ' &deg;C</b> (' , $dp_f , '&deg;F)';
	echo '</span></td></tr>';
	menu_item('Main', 'Main', $page);
	menu_item('1 Hour', 'Past Hour', $page);
	menu_item('6 Hours', 'Past 6 Hours', $page);
	menu_item('1 Day', 'Past Day', $page);
	menu_item('1 Week', 'Past Week', $page);
	menu_item('1 Month', 'Past Month', $page);
	menu_item('1 Year', 'Past Year', $page);
	menu_item('All', 'All', $page);
    
	echo '<tr><td class=link>Legend: <a href="javascript:open_legend()">Brief</a> - <a href="javascript:open_legend_full()">Full</a>';
	echo '</td></tr><tr><td class=link>Ref (90s): ';
	
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

<?php
/*
*
*  index.php - The main page of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure #######
$cwd = getcwd();
$sensor_log = $cwd . "/log/sensor.log";
$mycodo_exe = $cwd . "/cgi-bin/mycodo";
$graph_exec = $cwd . "/cgi-bin/graph.sh";

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

	$page = isset($_GET['page']) ? $_GET['page'] : 'Main';

	global $sensor_log, $mycodo_exe;

	$t_c = `tail -n 1 $sensor_log | cut -d' ' -f9`;
	$t_f = `tail -n 1 $sensor_log | cut -d' ' -f10`;
	$t_c_max = `$mycodo_exe r | cut -d' ' -f2`;
	$t_c_min = `$mycodo_exe r | cut -d' ' -f1`;
	$hum = `tail -n 1 $sensor_log | cut -d' ' -f8`;
	$hum_max = `$mycodo_exe r | cut -d' ' -f4`;
	$hum_min = `$mycodo_exe r | cut -d' ' -f3`;
	$dp_f = `tail -n 1 $sensor_log | cut -d' ' -f11`;
	$dp_c = ($dp_f-32)*5/9;
	
	$time_now = `date +"%Y-%m-%d %H:%M:%S"`;
	$time_last = `tail -n 1 $sensor_log | cut -d' ' -f1,2,3,4,5,6`;
	$time_last[4] = '-';
	$time_last[7] = '-';
	$time_last[13] = ':';
	$time_last[16] = ':';
?>

<html>
<head>
<title>Mycodo - <?php echo $page; ?></title>
<link rel="stylesheet"  href="style.css" type="text/css" media="all" />
<script type="text/javascript">
	function open_chmode() {
		window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=430, height=400");
	}
	function open_legend() {
		window.open("image.php?span=legend","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=190, height=210");
	}
	function open_legend_full() {
		window.open("image.php?span=legend-full","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=600, height=385");
	}
</script>

<?php if (isset($_GET['r'])) {
	if ($_GET['r'] == 1) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";
} ?>

</head>
<body bgcolor="white">
<table>
<tr>
<td width="150px" valign="top">
    <table width="150px">
        <tr>
            <td align=center>
                <div style="padding:1px 2px 2px 2px; float: center; color: #000; font-size: 11px; font-family: verdana;">
                    <?php echo 'Last page refresh<br>' . $time_now; ?>
                </div>
            </td>
        </tr>
        <tr class="link" cellpadding=5>
            <td align=center>
                <div style="padding:1px 2px 2px 3px; float: center; color: #000; font-size: 11px; font-family: verdana;">
                    <?php echo 'Last sensor read<br>' , $time_last; ?>
                </div>
            </td>
        </tr>
        <tr class="link" cellpadding=5>
            <td align=right>
                <div style="padding:1px 2px 2px 7px; display:inline; float: left; color: #000; font-size: 11px; font-family: verdana; text-align: left;">
<?php
        echo'<p>T <b>' , substr($t_c, 0, -1) , '&deg;C</b> (' , substr($t_c_min, 0, -1) , ' - ' , substr($t_c_max, 0, -1) , '&deg;C)';
        echo'<br>(' , substr($t_f, 0, -1) , '&deg;F)';
        echo '<p>H <b>' , substr($hum, 0, -1) , '%</b> (' , substr($hum_min, 0, -1) , ' - ' , substr($hum_max, 0, -1) , '%)<p>';
        echo 'DP <b>' , round($dp_c, 1) , '&deg;C</b> (' , substr($dp_f, 0, -1) , '&deg;F)';
?>
                </div>
            </td>
        </tr>
<?php
	menu_item('Main', 'Main', $page);
        menu_item('1 Hour', 'Past Hour', $page);
        menu_item('6 Hours', 'Past 6 Hours', $page);
        menu_item('1 Day', 'Past Day', $page);
        menu_item('1 Week', 'Past Week', $page);
        menu_item('1 Month', 'Past Month', $page);
        menu_item('1 Year', 'Past Year', $page);
        menu_item('All', 'All', $page);
?>
        <tr>
            <td class=link>Legend: <a href="javascript:open_legend()">Brief</a> - <a href="javascript:open_legend_full()">Full</a>
            </td>
        </tr>
        <tr>
            <td class=link>Refresh (90s): 
<?php
        if (isset($_GET['r'])) {
                if ($_GET['r'] == 1) echo '<b>On</b> / <a href="index.php?page=$page">Off</a>';
                else echo '<a href="index.php?page=$page&r=1">On</a> / <b>Off</b>';
        } else echo '<a href="index.php?page=$page&r=1">On</a> / <b>Off</b>';
?>
            </td>
        </tr>
        <tr>
            <td class=link>
                <a href="camera-still.php" target="_blank">Camera Image</a>
            </td>
        </tr>
        <tr>
            <td class=link>
                <a href="camera-stream.php" target="_blank">Camera Stream</a>
            </td>
        </tr>
        <tr>
            <td class=link>
                <a href="history.php" target="_blank">Log History</a>
            </td>
        </tr>
        <tr>
            <td class=link>
                <a href="drawgraph.php" target="_blank">Custom Graph</a>
            </td>
        </tr>
        <tr>
            <td class=link>
                <a href="javascript:open_chmode()">Configuration</a>
            </td>
        </tr>
        <tr>
            <td class=link-profile>
                <div style="padding: 0px 0 5px 10px;">Logged in as: <?php echo $_SESSION['user_name']; ?><?php if ($_SESSION['user_name'] != guest) { ?></div>
                <div style="clear: both;"></div>
                <img style="float: left; padding: 5px 5px 10px 10px; width: 50px; height: 50px;" src="<?php echo $login->user_gravatar_image_tag; ?>">
                <div style="float: left; vertical-align: middle;">
                <table>
                    <tr>
                        <td class=link-profile>
                            <a href="edit.php"><?php echo WORDING_EDIT_USER_DATA; ?></a>
                        </td>
                    </tr>
                    <tr>
                        <td class=link-profile>
                            <a href="index.php?logout"><?php echo WORDING_LOGOUT; ?></a>
                        </td>
                    </tr>
                </table>
                <?php } else { ?>
                    <br><a href="index.php?logout"><?php echo WORDING_LOGOUT; ?></a></div>
                <?php } ?>
            </td>
        </tr>
    </table>
</td>
<td width="830" valign="top">

<?php
if (isset($_GET['page'])) {
	switch ($_GET['page']) {
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
			echo "<img src=image.php?span=1h><p><img src=image.php?span=6h></p><p><img src=image.php?span=day></p><p><img src=image.php?span=week></p><p><img src=image.php?span=month></p><p><img src=image.php?span=year></p>";
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

} else include("views/not_logged_in.php");

function menu_item($id, $title, $current) {
        $class = ($current == $id) ? "active" : "inactive";

        echo '<tr><td class=' . $class . '>';
	if ($current != $id) {
        	echo '<a href="index.php?';
        	if (isset($_GET['r'])){
                	if ($_GET['r'] == 1) echo 'r=1&';
        	}
        	echo 'page=' . $id. '">' . $title . '</a>';
	} else echo $title;
	echo '</td></tr>';
}
?>

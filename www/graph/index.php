<?php include "auth.php";?>
<?php
include_once ('menu.php');
$page = isset($_GET['page']) ? $_GET['page'] : 'Main';
?>
<html>
<head>
<title>Mycodo - <?=$page?></title>
<style type="text/css">
.inactive, .active, .title, .link {padding:1px 2px 2px 15px;}
.inactive {background:skyblue; font-size: 12px;}
.active {background:steelblue; font-weight:bold; font-size: 12px;}
.title {background:white;}
.slink {background:DarkTurquoise; float: center; color: #000; font-size: 11px; font-family: verdana;}
.link {background:DarkTurquoise; font-size: 12px;}
.link a {color:blue;}
.inactive a {text-decoration:none; color:blue;}
.active a {text-decoration:none; color:white;}
a:hover   {color:black;}
</style>
<script type="text/javascript">
function open_chmode()
{
	window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=430, height=400");
}
function open_legend()
{
	window.open("graph-legend.png","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=190, height=210");
}
function open_legend_full()
{
	window.open("graph-legend-full.png","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=600, height=385");
}
</script>
<?php if ($_GET['r'] == 1) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";?>
</head>
<body bgcolor="white">
<table>
<tr>
<td width="150" valign="top">
<?php page_menu($page);?>
</td>
<td width="830" valign="top">
<?php
	switch ($_GET['page']) {
		case 'log out':
			$_SESSION['authenticated'] = 0;
                        $inputuser = $_POST['input_user'];
                        $inputpassword = $_POST['input_password'];
                        if ($_GET['r'] == 1) echo "<meta http-equiv='refresh' content='2;url=index.php?r=1'>";
                        else echo "<meta http-equiv='refresh' content='2;url=index.php'>";
                        break;
		case 'Main':
                                echo `/var/www/mycodo/mycodo-graph.sh dayweek`;
                                echo "<img src=graph-main.png>";
                                break;
			case '1 Hour':
				echo `/var/www/mycodo/mycodo-graph.sh 1h`;
				echo "<img src=graph-1h.png>";
				break;
			case '6 Hours':
				echo `/var/www/mycodo/mycodo-graph.sh 6h`;
				echo "<img src=graph-6h.png>";
				break;
			case '1 Day':
				echo `/var/www/mycodo/mycodo-graph.sh day`;
				echo "<img src=graph-day.png>";
				break;
			case '1 Week':
				echo `/var/www/mycodo/mycodo-graph.sh week`;
				echo "<img src=graph-week.png>";
				break;
			case '1 Month':
				echo `/var/www/mycodo/mycodo-graph.sh month`;
				echo "<img src=graph-month.png>";
				break;
			case '1 Year':
				echo `/var/www/mycodo/mycodo-graph.sh year`;
				echo "<img src=graph-year.png>";
				break;
			case 'All':
				echo `/var/www/mycodo/mycodo-graph.sh all`;
				echo "<img src=graph-1h.png><p>
					<img src=graph-6h.png><p>
					<img src=graph-day.png><p>
					<img src=graph-week.png><p>
					<img src=graph-month.png><p>
					<img src=graph-year.png>";
				break;
			default:
                                echo `/var/www/mycodo/mycodo-graph.sh dayweek`;
                                echo "<img src=graph-main.png>";
				break;
		}?>

</td>
</tr>
</table>
</body>
</html>

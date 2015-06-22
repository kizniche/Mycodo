<?php include "auth.php";?>
<html>
<head>
<title>Kizpi</title>
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
<body>
<center>
<table bgcolor="#cccccc" cellpadding=5>
<tr>
<td>
<div style='float: center; color: #000; font-size: 13px; font-family: verdana;'>
<?php echo `date +"%Y-%m-%d %H %M %S"`;?>
<?php if ($_GET['r'] == 1) {
echo "
| <a href='index.php?r=1&id=1'>Exit</a> |
Refresh (90s): <b>On</b> / <a href='index.php'>Off</a> | 
<a href='his.php' target='_blank'>His</a> | 
<a href='drawgraph.php' target='_blank'>Draw</a> | 
<a href='javascript:open_chmode()'> Ctrl</a> | 
<a href='index.php?r=1'>Main</a> | 
<a href='index.php?r=1&id=2'>1H</a> |
<a href='index.php?r=1&id=3'>6H</a> | 
<a href='index.php?r=1&id=4'>1D</a> | 
<a href='index.php?r=1&id=5'>1W</a> | 
<a href='index.php?r=1&id=6'>1M</a> | 
<a href='index.php?r=1&id=7'>1Y</a> | 
<a href='index.php?r=1&id=8'>All</a>&nbsp;";
} else {
echo "
| <a href='index.php?id=1'>Exit</a> | 
Refresh (90s): <a href='index.php?r=1'>On</a> / <b>Off</b> | 
<a href='his.php' target='_blank'>His</a> | 
<a href='drawgraph.php' target='_blank'>Draw</a> | 
<a href='javascript:open_chmode()'> Ctrl</a> |
<a href='index.php'>Main</a> |
<a href='index.php?id=2'>1H</a> |
<a href='index.php?id=3'>6H</a> | 
<a href='index.php?id=4'>1D</a> | 
<a href='index.php?id=5'>1W</a> | 
<a href='index.php?id=6'>1M</a> | 
<a href='index.php?id=7'>1Y</a> | 
<a href='index.php?id=8'>All</a>&nbsp;"; } ?>
</div>
</td>
</tr>
<tr>
<td>
<div style='float: center; color: #000; font-size: 13px; font-family: verdana;'>
<?php
 
$sdatapath="/var/www/mycodo/PiSensorData";

echo `tail -n 1 $sdatapath | cut -d' ' -f1,2,3,4,5,6`;
echo "RHum ( " , `/var/www/mycodo/mycodo r | cut -d' ' -f4` , " - " , `/var/www/mycodo/mycodo r | cut -d' ' -f5` , "): <b>" , `tail -n 1 $sdatapath | cut -d' ' -f8` , "%</b> | ";
echo "Temp ( " , `/var/www/mycodo/mycodo r | cut -d' ' -f1` , " - " , `/var/www/mycodo/mycodo r | cut -d' ' -f2` , " - " , `/var/www/mycodo/mycodo r | cut -d' ' -f3` , "): <b>" , `tail -n 1 $sdatapath | cut -d' ' -f9`;
echo "&deg;C</b> (" , `tail -n 1 $sdatapath | cut -d' ' -f10` , "&deg;F) | ";
$dp_c = `tail -n 1 $sdatapath | cut -d' ' -f11`;
$dp_c = ($dp_c-32)*5/9;
echo "DP: <b>" , round($dp_c, 1);
echo " &deg;C</b> (" , `tail -n 1 $sdatapath | cut -d' ' -f11` , "&deg;F)";?>
</div>
</td>
</tr>
</table>
<?php 
switch ($_GET['id']) { 
case 1:
$_SESSION['authenticated'] = 0;
$inputuser = $_POST['input_user'];
$inputpassword = $_POST['input_password'];
if ($_GET['r'] == 1) echo "<meta http-equiv='refresh' content='2;url=index.php?r=1'>";
else echo "<meta http-equiv='refresh' content='2;url=index.php'>";
break;

case 2:
echo `/var/www/mycodo/mycodo-graph.sh 1h`;
echo "<img src=graph-1h.png>";
break;

case 3:
echo `/var/www/mycodo/mycodo-graph.sh 6h`;
echo "<img src=graph-6h.png>";
break;

case 4:
echo `/var/www/mycodo/mycodo-graph.sh day`; 
echo "<img src=graph-day.png>"; 
break; 

case 5: 
echo `/var/www/mycodo/mycodo-graph.sh week`;
echo "<img src=graph-week.png>";
break; 

case 6: 
echo `/var/www/mycodo/mycodo-graph.sh month`;
echo "<img src=graph-month.png>";
break; 

case 7:
echo `/var/www/mycodo/mycodo-graph.sh year`;
echo "<img src=graph-year.png>";
break;

case 8: 
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
<p>
<a href='javascript:open_legend()'>Brief Graph Legend</a> - <a href='javascript:open_legend_full()'>Full Graph Legend</a>
</center>
</body>
</html>

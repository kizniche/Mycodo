<?php include "auth.php";?>
<html>
<head>
<title>Kizpi Mobile</title>
<script type="text/javascript"> 
function open_win()
{
window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=300, height=330");
}
</script>
<?php if ($_GET['r'] == 1) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";?>
</head>
<body>
<center>
<table bgcolor="#cccccc" cellpadding=10>
<tr>
<td>
<div style='float: center; color: #000; font-size: 24px; font-family: verdana;'>
<?php echo `date +"%Y-%m-%d %H %M %S"`;?>
<?php if ($_GET['r'] == 1) {
echo "
| <a href='mobile.php?r=1&id=1'>Log Out</a> | 
Refresh (90 sec): <b>On</b> / <a href='mobile.php'>Off</a><p>
<a href='his.php' target='_blank'>History</a> | 
<a href='drawgraph.php' target='_blank'>Draw</a> | 
<a href='javascript:open_win()'> Ctrl</a> | 
<a href='mobile.php?r=1'>Main</a> | 
<a href='mobile.php?r=1&id=2'>6H</a> |  
<a href='mobile.php?r=1&id=3'>Day</a> | 
<a href='mobile.php?r=1&id=4'>Week</a> | 
<a href='mobile.php?r=1&id=5'>Month</a> | 
<a href='mobile.php?r=1&id=6'>Year</a> | 
<a href='mobile.php?r=1&id=7'>All</a>&nbsp;";
} else {
echo "
| <a href='mobile.php?id=1'>Log Out</a> | 
Refresh (90 sec): <a href='mobile.php?r=1'>On</a> / <b>Off</b><p>
<a href='his.php' target='_blank'>History</a> | 
<a href='drawgraph.php' target='_blank'>Draw</a> | 
<a href='javascript:open_win()'> Ctrl</a> |
<a href='mobile.php'>Main</a> |
<a href='mobile.php?id=2'>6H</a> | 
<a href='mobile.php?id=3'>Day</a> | 
<a href='mobile.php?id=4'>Week</a> | 
<a href='mobile.php?id=5'>Month</a> | 
<a href='mobile.php?id=6'>Year</a> | 
<a href='mobile.php?id=7'>All</a>&nbsp;"; } ?>
</div>
</td>
</tr>
<tr>
<td>
<div style='float: center; color: #000; font-size: 24px; font-family: verdana;'>
<?php 
$sdatapath="/var/www/graph/PiSensorData";

echo `tail -n 1 $sdatapath | cut -d' ' -f1,2,3,4,5,6 | perl -pe 's/(.*?)\s(.*?)\s(.*)/$1-$2-$3 $4 $5 $6/;'`,"<br>";
echo `tail -n 1 $sdatapath | cut -d' ' -f7,8 | perl -pe 's/(.*?)\s(.*?)\s(.*)/Hum: <b>$2%<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f9,10 | perl -pe 's/(.*?)\s(.*?)\s(.*)/Temp: <b>$1&deg;C \/ $2&deg;F<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f11,12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/DP: <b>$1&deg;F<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f11,12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/HI: <b>$2&deg;F<\/b>/;'`;?></u>&nbsp;
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
echo `/var/www/bin/graph 6h-mobile`;
echo "<img src=graph-6h-mobile.png>";
break;

case 3:
echo `/var/www/bin/graph day-mobile`;
echo "<img src=graph-day-mobile.png>";
break;

default:
echo `/var/www/bin/graph dayweek-mobile`;
echo "<img src=graph-main-mobile.png>";
break; 
}?>
</center>
</body>
</html>

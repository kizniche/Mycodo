<?php include "auth.php";?>
<html>
<head>
<title>Kizpi</title>
<script type="text/javascript"> 
function open_win()
{
window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=430, height=340");
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
| <a href='index.php?r=1&id=1'>Log Out</a> |
Refresh (90s): <b>On</b> / <a href='index.php'>Off</a> | 
<a href='his.php' target='_blank'>History</a> | 
<a href='drawgraph.php' target='_blank'>Draw</a> | 
<a href='javascript:open_win()'> Ctrl</a> | 
<a href='index.php?r=1'>Main</a> | 
<a href='index.php?r=1&id=2'>6H</a> | 
<a href='index.php?r=1&id=3'>Day</a> | 
<a href='index.php?r=1&id=4'>Week</a> | 
<a href='index.php?r=1&id=5'>Month</a> | 
<a href='index.php?r=1&id=6'>Year</a> | 
<a href='index.php?r=1&id=7'>All</a>&nbsp;";
} else {
echo "
| <a href='index.php?id=1'>Log Out</a> | 
Refresh (90s): <a href='index.php?r=1'>On</a> / <b>Off</b> | 
<a href='his.php' target='_blank'>History</a> | 
<a href='drawgraph.php' target='_blank'>Draw</a> | 
<a href='javascript:open_win()'> Ctrl</a> |
<a href='index.php'>Main</a> |
<a href='index.php?id=2'>6H</a> | 
<a href='index.php?id=3'>Day</a> | 
<a href='index.php?id=4'>Week</a> | 
<a href='index.php?id=5'>Month</a> | 
<a href='index.php?id=6'>Year</a> | 
<a href='index.php?id=7'>All</a>&nbsp;"; } ?>
</div>
</td>
</tr>
<tr>
<td>
<div style='float: center; color: #000; font-size: 13px; font-family: verdana;'>
<?php 
$sdatapath="/var/www/graph/PiSensorData";

echo `tail -n 1 $sdatapath | cut -d' ' -f1,2,3,4,5,6 | perl -pe 's/(.*?)\s(.*?)\s(.*)/$1-$2-$3 $4 $5 $6/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f7,8 | perl -pe 's/(.*?)\s(.*?)\s(.*)/Relative Humidity: <b>$2%<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f9,10 | perl -pe 's/(.*?)\s(.*?)\s(.*)/Temperature: <b>$1&deg;C \/ $2&deg;F<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f11,12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/Dew Point: <b>$1&deg;F<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f11,12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/Heat Index: <b>$2&deg;F<\/b>/;'`;?></u>&nbsp;
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
echo `/var/www/bin/graph 6h`;
echo "<img src=graph-6h.png>";
break;

case 3:
echo `/var/www/bin/graph day`; 
echo "<img src=graph-day.png>"; 
break; 

case 4: 
echo `/var/www/bin/graph week`;
echo "<img src=graph-week.png>";
break; 

case 5: 
echo `/var/www/bin/graph month`;
echo "<img src=graph-month.png>";
break; 

case 6:
echo `/var/www/bin/graph year`;
echo "<img src=graph-year.png>";
break;

case 7: 
echo `/var/www/bin/graph all`;
echo "<img src=graph-6h.png><p>
<img src=graph-day.png><p>
<img src=graph-week.png><p>
<img src=graph-month.png><p>
<img src=graph-year.png>";
break;

default:
echo `/var/www/bin/graph dayweek`;
echo "<img src=graph-main.png>";
break; 
}?>
</center>
</body>
</html>

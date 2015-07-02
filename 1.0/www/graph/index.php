<?php include "auth.php";?>
<html>
<head>
<?php if ($_GET['r'] == 1) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";?>
</head>
<body>
<center>
<table width=1000 bgcolor="#cccccc">
<tr>
<td>
<center>
<div style='float: center; color: #000; font-size: 11px; font-family: verdana;'>
<?php echo `date +%Y-%m-%d\ %H:%M:%S`;?>&nbsp;
<?php if ($_GET['r'] == 1) {
echo "
| <a href='index.php?r=1&id=1'>LO</a>
<a href='his.php' target='_blank'>His</a>
<a href='drawgraph.php' target='_blank'>Draw</a>
<a href=\"changemode.php\" target=\"modecng\">Ctrl</a> 
<a href='index.php?r=1'>Main</a> | 
<a href='index.php?r=1&id=2'>6H</a>
<a href='index.php?r=1&id=3'>Day</a>
<a href='index.php?r=1&id=4'>Week</a>
<a href='index.php?r=1&id=5'>Month</a>
<a href='index.php?r=1&id=6'>Year</a>
<a href='index.php?r=1&id=7'>All</a> |";
} else {
echo "
| <a href='index.php?id=1'>LO</a>
<a href='his.php' target='_blank'>His</a>
<a href='drawgraph.php' target='_blank'>Draw</a>
<a href=\"changemode.php\" target=\"modecng\">Ctrl</a>
<a href='index.php'>Main</a> | 
<a href='index.php?id=2'>6H</a>
<a href='index.php?id=3'>Day</a> 
<a href='index.php?id=4'>Week</a> 
<a href='index.php?id=5'>Month</a> 
<a href='index.php?id=6'>Year</a> 
<a href='index.php?id=7'>All</a> |"; } ?>
&nbsp; <u><?php echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 1 | perl -pe 's/(.*?)\s(.*?)\s(.*)/RH $2<\/u>/;'`;?>&nbsp;
<u><?php echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 1 | cut -d' ' -f5,6 | perl -pe 's/(.*?)\s(.*?)\s(.*)/T $1\/$2/;'`;?></u>&nbsp;&nbsp;
<u><?php echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 1 | cut -d' ' -f11,12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/HI $1/;'`;?></u>&nbsp;&nbsp;
<u><?php echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 1 | cut -d' ' -f9,10 | perl -pe 's/(.*?)\s(.*?)\s(.*)/DP $1\/$2/;'`;?></u>&nbsp;&nbsp;
<u><?php echo "M".`grep -Ih Mode /home/kiz/arduino/output/* | tail -n 1 | awk '{print $22}'`;?>
((<?php echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 1 | cut -d' ' -f3,4 | perl -pe 's/(.*?)\s(.*?)\s(.*)/H $1\/$2/;'`;?> <?php echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 1 | cut -d' ' -f12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/$1/;'`;?>)
(<?php echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 1 | cut -d' ' -f7,8 | perl -pe 's/(.*?)\s(.*?)\s(.*)/T $1\/$2/;'`;?> <?php echo `grep -h OO /home/kiz/arduino/output/* | tail -n 1 | cut -d' ' -f13 | perl -pe 's/(.*?)\s(.*?)\s(.*)/$1/;'`;?>))</u>
</div>
</center>
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
echo `/home/kiz/bin/graph-6h`;
echo "<img src=graph-6h.png>";
break;

case 3:
echo `/home/kiz/bin/graph-day`; 
echo "<img src=graph-day.png>"; 
break; 

case 4: 
echo `/home/kiz/bin/graph-week`;
echo "<img src=graph-week.png>";
break; 

case 5: 
echo `/home/kiz/bin/graph-month`;
echo "<img src=graph-month.png>";
break; 

case 6:
echo `/home/kiz/bin/graph-year`;
echo "<img src=graph-year.png>";
break;

case 7: 
echo `/home/kiz/bin/graphall`;
echo "<img src=graph-6h.png><p>
<img src=graph-day.png><p>
<img src=graph-week.png><p>
<img src=graph-month.png><p>
<img src=graph-year.png>";
break;

default:
echo `/home/kiz/bin/graph-together`;
echo "<img src=graph-main.png>";
break; 
}?>
</center>
</body>
</html>

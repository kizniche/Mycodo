<?php
function menu_item ($id, $title, $current)
{
	$class = ($current == $id) ? "active" : "inactive";
	?>
	<tr><td class=<?=$class?>>
	<a href="index.php?<?php if ($_GET['r'] == 1) echo "r=1&";?>page=<?=$id?>"><?=$title?></a>
	</td></tr>
	<?php
}

function page_menu ($page)
{
	?>
	<table width="100%">
	<tr><td align=center><div style='padding:1px 2px 2px 2px; float: center; color: #000; font-size: 11px; font-family: verdana;'>
	Last page refresh<br><?php echo `date +"%Y-%m-%d %H %M %S"`;?>
	</div></td></tr>
        <tr bgcolor="#cccccc" cellpadding=5>
        <td align=center>
        <div style='padding:1px 2px 2px 3px; float: center; color: #000; font-size: 11px; font-family: verdana;'>
	Last sensor read<br>
        <?php
        $sdatapath="/var/www/mycodo/PiSensorData";
        echo `tail -n 1 $sdatapath | cut -d' ' -f1,2,3,4,5,6`;
	?>
	</div></td></tr>
	<tr bgcolor="#cccccc" cellpadding=5>
	<td align=right><span style='padding:1px 2px 2px 7px; display:inline; float: left; color: #000; font-size: 11px; font-family: verdana;'>
	<?php
        echo "<p>T <b>" , `tail -n 1 $sdatapath | cut -d' ' -f9` , "&deg;C</b> (" ,  `tail -n 1 $sdatapath | cut -d' ' -f10` , "&deg;F)<br> ( " , `/var/www/mycodo/mycodo r | cut -d' ' -f1` , " - " , `/var/www/mycodo/mycodo r | cut -d' ' -f2` , " )<p>";
        echo "<p>RH <b>" , `tail -n 1 $sdatapath | cut -d' ' -f8` , "%</b> ( " , `/var/www/mycodo/mycodo r | cut -d' ' -f3` , " - " , `/var/www/mycodo/mycodo r | cut -d' ' -f4` , ")<p>";
        $dp_c = `tail -n 1 $sdatapath | cut -d' ' -f11`;
        $dp_c = ($dp_c-32)*5/9;
        echo "DP <b>" , round($dp_c, 1);
        echo " &deg;C</b> (" , `tail -n 1 $sdatapath | cut -d' ' -f11` , "&deg;F)";
	?></span></td></tr>
	<?php menu_item ('Main', 'Main', $page); ?>
	<?php menu_item ('1 Hour', 'Past Hour', $page); ?>
	<?php menu_item ('6 Hours', 'Past 6 Hours', $page); ?>
	<?php menu_item ('1 Day', 'Past Day', $page); ?>
	<?php menu_item ('1 Week', 'Past Week', $page); ?>
	<?php menu_item ('1 Month', 'Past Month', $page); ?>
	<?php menu_item ('1 Year', 'Past Year', $page); ?>
	<?php menu_item ('All', 'All', $page); ?>
        <tr><td class=link>Legend: <a href='javascript:open_legend()'>Brief</a> - <a href='javascript:open_legend_full()'>Full</a></td></tr>
	<tr><td class=link>Ref (90s): 
	<?php if ($_GET['r'] == 1) {
		echo "<b>On</b> / <a href='index.php?page=$page'>Off</a>";
	}
	else
	{ 
		echo "<a href='index.php?page=$page&r=1'>On</a> / <b>Off</b>";
	}
	?>
	</td></tr>
	<tr><td class=link><a href='his.php' target='_blank'>Log History</a></td></tr>
	<tr><td class=link><a href='drawgraph.php' target='_blank'>Custom Graph</a></td></tr>
	<tr><td class=link><a href='javascript:open_chmode()'>Configuration</a></td></tr>
	<tr><td class=link><a href='index.php?page=log out'>Log Out</a></td></tr>
	</td></tr></table>
	<?php
}
?>

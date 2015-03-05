<?php include "auth.php";?>
<?php
function webor($state)
{
  if ($state) {
      $editconfig = `/var/www/mycodo/mycodo r`;
      $cpiece = explode(" ", $editconfig);
      $editconfig = "/var/www/mycodo/mycodo w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " 1 " . $cpiece[5] . " " . $cpiece[6] . "\n";
      shell_exec($editconfig);
  }
  else {
      $editconfig = `/var/www/mycodo/mycodo r`;
      $cpiece = explode(" ", $editconfig);
      $editconfig = "/var/www/mycodo/mycodo w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " 0 " . $cpiece[5] . " " . $cpiece[6] . "\n";
      shell_exec($editconfig);
  }
}

  if(isset($_POST['Mode'])) {
    $ModeSet = $_POST['Mode'];
  }
  if(isset($_POST['OR'])) {
    if(isset($_POST['OR'])) $OR = $_POST['OR'];
    switch ($OR) {
      case "ON":
        webor(1);
        break;
      case "OFF":
        webor(0);
        break;
    }
  }
  if(isset($_POST['R1'])) {
    if(isset($_POST['R1'])) $R1 = $_POST['R1'];
    switch ($R1) {
      case "ON":
        echo `gpio mode 4 out`;
        echo `gpio write 4 1`;
        break;
      case "OFF":
        echo `gpio mode 4 out`;
        echo `gpio write 4 0`;
        break;
    }
  }
  if(isset($_POST['R2'])) {
    if(isset($_POST['R2'])) $R2 = $_POST['R2'];
    switch ($R2) {
      case "ON":
        echo `gpio mode 3 out`;
        echo `gpio write 3 1`;
        break;
      case "OFF":
        echo `gpio mode 3 out`;
        echo `gpio write 3 0`;
        break;
    }
  }
  if(isset($_POST['R3'])) {
    if(isset($_POST['R3'])) $R3 = $_POST['R3'];
    switch ($R3) {
      case "ON":
        echo `gpio mode 1 out`;
        echo `gpio write 1 1`;
        break;
      case "OFF":
        echo `gpio mode 1 out`;
        echo `gpio write 1 0`;
        break;
    }
  }
  if(isset($_POST['R4'])) {
    if(isset($_POST['R4'])) $R4 = $_POST['R4'];
    switch ($R4) {
      case "ON":
        echo `gpio mode 0 out`;
        echo `gpio write 0 1`;
        break;
      case "OFF":
        echo `gpio mode 0 out`;
        echo `gpio write 0 0`;
        break;
    }
  }
  if($_POST['SubmitMode']) {
    $offTemp = $_POST['offTemp'];
    $onTemp = $_POST['onTemp'];
    $hiTemp = $_POST['hiTemp'];
    $offHum = $_POST['offHum'];
    $onHum = $_POST['onHum'];
    $editconfig = `/var/www/mycodo/mycodo r`;
    $cpiece = explode(" ", $editconfig);
    $editconfig = "/var/www/mycodo/mycodo w " . $offTemp . " " . $onTemp . " " . $offHum . " " . $onHum . " " . $cpiece[4] . " " . $cpiece[5] . " " . $cpiece[6] . "\n";
    exec($editconfig);
  }
  if($_POST['SubmitMode2']) {
    $webov = $_POST['webov'];
    $tState = $_POST['tState'];
    $hState = $_POST['hState'];
    $editconfig = `/var/www/mycodo/mycodo r`;
    $cpiece = explode(" ", $editconfig);
    $editconfig = "/var/www/mycodo/mycodo w " . $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $webov . " " . $tState . " " . $hState . "\n";
    exec($editconfig);
  }
  if($_POST['1secON']) {
    $sR1 = $_POST['sR1'];
    exec(sprintf("/var/www/mycodo/mycodo-relay.sh 1 %s > /dev/null 2>&1", $sR1));
  }
  if($_POST['2secON']) {
    $sR2 = $_POST['sR2'];
    exec(sprintf("/var/www/mycodo/mycodo-relay.sh 2 %s > /dev/null 2>&1", $sR2));
  }
  if($_POST['3secON']) {
    $sR3 = $_POST['sR3'];
    exec(sprintf("/var/www/mycodo/mycodo-relay.sh 3 %s > /dev/null 2>&1", $sR3));
  }
  if($_POST['4secON']) {
    $sR4 = $_POST['sR4'];
    exec(sprintf("/var/www/mycodo/mycodo-relay.sh 4 %s > /dev/null 2>&1", $sR4));
  }
?>
<html>
<body>
<head>
<title>Relay Control and Configuration</title>
<?php if ($_GET['r'] == 1) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";?>
</head>
<body>
<center>
<table><tr><td align=center><table bgcolor="#cccccc" cellpadding=5>
<tr>
<td align=left>
<div style='float: center; color: #000; font-size: 13px; font-family: verdana;'>
<center>
<?php
echo "<table align=left><tr><td align=right>Current time: ",`date +"%Y %m %d %H %M %S"`;

// Where recent data is collected
$sdatapath="/var/www/mycodo/PiSensorData";

echo "<br>Last read: ",`tail -n 1 $sdatapath | cut -d' ' -f1,2,3,4,5,6`,"</td><td align=right><a href=\"changemode.php\">Refresh</a></td></tr></table></td></tr><tr><td>";
echo "RH: <b>" , `tail -n 1 $sdatapath | cut -d' ' -f8` , "%</b> | ";
echo "T: <b>" , `tail -n 1 $sdatapath | cut -d' ' -f9`;
echo "&deg;C / " , `tail -n 1 $sdatapath | cut -d' ' -f10` , "&deg;F</b> | ";
$dp_c = `tail -n 1 $sdatapath | cut -d' ' -f11`;
$dp_c = ($dp_c-32)*5/9;
echo "DP: <b>" , round($dp_c, 1);
echo "&deg;C / " , `tail -n 1 $sdatapath | cut -d' ' -f11` , "&deg;F</b>";?>
</center></div></td></tr></table></td></tr><tr><td align=center><table cellpadding=2>
<?php
  echo "<FORM action=\"\" method=\"POST\">";
  $sconfigpath="/var/www/mycodo/mycodo.conf";
  echo "<p><tr><td>Web Override: <b>";
  if(`/var/www/mycodo/mycodo r | cut -d' ' -f5` == 1) echo "ON";
  else echo "OFF";
  echo "</b></td><td align=left>[<input type=\"submit\" name=\"OR\" value=\"ON\"> <input type=\"submit\" name=\"OR\" value=\"OFF\">]";

  echo "</td></tr><tr><td>Relay 1 (HEPA): <b>";
  if(`/usr/local/bin/gpio read 4` == 1) echo "ON";
  else echo "OFF";
  echo "</b></td><td align=center>[<input type=\"submit\" name=\"R1\" value=\"ON\"> <input type=\"submit\" name=\"R1\" value=\"OFF\">";
  echo "] [<input type=\"text\" maxlength=3 size=3 name=\"sR1\" />sec ";
  echo "<input type=\"submit\" name=\"1secON\" value=\"ON\">]";

  echo "</td></tr><tr><td>Relay 2 (HUMI): <b>";
  if(`/usr/local/bin/gpio read 3` == 1) echo "ON";
  else echo "OFF";
  echo "</b></td><td align=center>[<input type=\"submit\" name=\"R2\" value=\"ON\"> <input type=\"submit\" name=\"R2\" value=\"OFF\">";
  echo "] [<input type=\"text\" maxlength=3 size=3 name=\"sR2\" />sec ";
  echo "<input type=\"submit\" name=\"2secON\" value=\"ON\">]";

  echo "</td></tr><tr><td>Relay 3 (CFAN): <b>";
  if(`/usr/local/bin/gpio read 1` == 1) echo "ON";
  else echo "OFF";
  echo "</b></td><td align=center>[<input type=\"submit\" name=\"R3\" value=\"ON\"> <input type=\"submit\" name=\"R3\" value=\"OFF\">]";
  echo " [<input type=\"text\" maxlength=3 size=3 name=\"sR3\" />sec ";
  echo "<input type=\"submit\" name=\"3secON\" value=\"ON\">]";

  echo "</td></tr><tr><td>Relay 4 (HEAT): <b>";
  if(`/usr/local/bin/gpio read 0` == 1) echo "ON";
  else echo "OFF";
  echo "</b></td><td align=center>[<input type=\"submit\" name=\"R4\" value=\"ON\"> <input type=\"submit\" name=\"R4\" value=\"OFF\">]";
  echo " [<input type=\"text\" maxlength=3 size=3 name=\"sR4\" />sec ";
  echo "<input type=\"submit\" name=\"4secON\" value=\"ON\">]</td></tr></table>";
  echo "<table><tr><td></td><td>MnT</td><td>MxT</td><td>MnH</td><td>MxH</td></tr>";
  echo "<tr><td><input type=\"submit\" name=\"SubmitMode\" value=\"Set\"></td>";
  echo "<td><input type=\"text\" value=\"", `cat $sconfigpath | tr '\n' ' ' | tr -d ';' | cut -d' ' -f3`, "\" maxlength=2 size=1 name=\"offTemp\" /></td>";
  echo "<td><input type=\"text\" value=\"", `cat $sconfigpath | tr '\n' ' ' | tr -d ';' | cut -d' ' -f6`, "\" maxlength=2 size=1 name=\"onTemp\" /></td>";
  echo "<td><input type=\"text\" value=\"", `cat $sconfigpath | tr '\n' ' ' | tr -d ';' | cut -d' ' -f9`, "\" maxlength=2 size=1 name=\"offHum\" /></td>";
  echo "<td><input type=\"text\" value=\"", `cat $sconfigpath | tr '\n' ' ' | tr -d ';' | cut -d' ' -f12`, "\" maxlength=2 size=1 name=\"onHum\" /></td></tr>";
  echo "<tr><td></td><td>wOV</td><td>tSta</td><td>hSta</td></tr>";
  echo "<tr><td><input type=\"submit\" name=\"SubmitMode2\" value=\"Set\"></td>";
  echo "<td><input type=\"text\" value=\"", `cat $sconfigpath | tr '\n' ' ' | tr -d ';' | cut -d' ' -f15`, "\" maxlength=2 size=1 name=\"webov\" /></td>";
  echo "<td><input type=\"text\" value=\"", `cat $sconfigpath | tr '\n' ' ' | tr -d ';' | cut -d' ' -f18`, "\" maxlength=2 size=1 name=\"tState\" /></td>";
  echo "<td><input type=\"text\" value=\"", `cat $sconfigpath | tr '\n' ' ' | tr -d ';' | cut -d' ' -f21`, "\" maxlength=2 size=1 name=\"hState\" /></td>";
  echo "</tr></table></td></tr></table></FORM><p>";
?>
</center>
</body>
</html>

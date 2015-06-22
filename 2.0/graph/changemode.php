<?php include "auth.php";?>
<?php
function webor($state)
{
  switch ($state) {
    case "1":
      $editconfig = file_get_contents('/var/www/graph/PiConfig');
      $cpiece = explode(" ", $editconfig);
      $editconfig = $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $cpiece[4] . " 1\n";
      file_put_contents('/var/www/graph/PiConfig', $editconfig);
      break;
    case "0":
      $editconfig = file_get_contents('/var/www/graph/PiConfig');
      $cpiece = explode(" ", $editconfig);
      $editconfig = $cpiece[0] . " " . $cpiece[1] . " " . $cpiece[2] . " " . $cpiece[3] . " " . $cpiece[4] . " 0\n";
      file_put_contents('/var/www/graph/PiConfig', $editconfig);
      break;
  }
}

  if(isset($_POST['Mode'])) {
    $ModeSet = $_POST['Mode'];
  }
  if(isset($_POST['OR'])) {
    if(isset($_POST['OR'])) $OR = $_POST['OR'];
    switch ($OR) {
      case "on":
        webor(1);
        break;
      case "off":
        webor(0);
        break;
    }
  }
  if(isset($_POST['R1'])) {
    if(isset($_POST['R1'])) $R1 = $_POST['R1'];
    webor(1);
    switch ($R1) {
      case "on":
        echo `gpio mode 4 out`;
        echo `gpio write 4 1`;
        break;
      case "off":
        echo `gpio mode 4 out`;
        echo `gpio write 4 0`;
        break;
    }
  }
  if(isset($_POST['R2'])) {
    if(isset($_POST['R2'])) $R2 = $_POST['R2'];
    webor(1);
    switch ($R2) {
      case "on":
        echo `gpio mode 3 out`;
        echo `gpio write 3 1`;
        break;
      case "off":
        echo `gpio mode 3 out`;
        echo `gpio write 3 0`;
        break;
    }
  }
  if(isset($_POST['R3'])) {
    if(isset($_POST['R3'])) $R3 = $_POST['R3'];
    webor(1);
    switch ($R3) {
      case "on":
        echo `gpio mode 1 out`;
        echo `gpio write 1 1`;
        break;
      case "off":
        echo `gpio mode 1 out`;
        echo `gpio write 1 0`;
        break;
    }
  }
  if(isset($_POST['R4'])) {
    if(isset($_POST['R4'])) $R4 = $_POST['R4'];
    webor(1);
    switch ($R4) {
      case "on":
        echo `gpio mode 0 out`;
        echo `gpio write 0 1`;
        break;
      case "off":
        echo `gpio mode 0 out`;
        echo `gpio write 0 0`;
        break;
    }
  }
  if($_POST['SubmitMode']) {
    $String = $_POST['String'];
    $editconfig = file_get_contents('/var/www/graph/PiConfig');
    $cpiece = explode(" ", $editconfig);
    $editconfig = $String . " " . $cpiece[5] . "\n";
    file_put_contents('/var/www/graph/PiConfig', $editconfig);
  }
  if($_POST['1secON']) {
    $sR1 = $_POST['sR1'];
    webor(1);
    exec(sprintf("/var/www/bin/RelayTimer 1 %s > /dev/null 2>&1", $sR1));
  }
  if($_POST['2secON']) {
    $sR2 = $_POST['sR2'];
    webor(1);
    exec(sprintf("/var/www/bin/RelayTimer 2 %s > /dev/null 2>&1", $sR2));
  }
  if($_POST['3secON']) {
    $sR3 = $_POST['sR3'];
    webor(1);
    exec(sprintf("/var/www/bin/RelayTimer 3 %s > /dev/null 2>&1", $sR3));
  }
  if($_POST['4secON']) {
    $sR4 = $_POST['sR4'];
    webor(1);
    exec(sprintf("/var/www/bin/RelayTimer 4 %s > /dev/null 2>&1", $sR4));
  }
?>
<html>
<body>
<head>
<?php if ($_GET['r'] == 1) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";?>
</head>
<body>
<center>
<table bgcolor="#cccccc" cellpadding=5>
<tr>
<td>
<div style='float: center; color: #000; font-size: 13px; font-family: verdana;'>
<center>
<?php echo "Current time: ",`date +%Y-%m-%d-%H:%M:%S`;
$sdatapath="/var/www/graph/PiSensorData";
echo "<br>Last read: ",`tail -n 1 $sdatapath | cut -d' ' -f1,2,3,4,5,6 | perl -pe 's/(.*?)\s(.*?)\s(.*)/$1-$2-$3 $4 $5 $6/;'`,"<br>";
echo `tail -n 1 $sdatapath | cut -d' ' -f7,8 | perl -pe 's/(.*?)\s(.*?)\s(.*)/RH: <b>$2%<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f9,10 | perl -pe 's/(.*?)\s(.*?)\s(.*)/T: <b>$1&deg;C \/ $2&deg;F<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f11,12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/DP: <b>$1&deg;F<\/b>/;'`," | ";
echo `tail -n 1 $sdatapath | cut -d' ' -f11,12 | perl -pe 's/(.*?)\s(.*?)\s(.*)/HI: <b>$2&deg;F<\/b>/;'`;?>
</center></div></td></tr></table>
<?php
  echo "<FORM action=\"\" method=\"POST\">";
  $sconfigpath="/var/www/graph/PiConfig";
  echo "<p>WebOverride is <b>";
  if(`cat $sconfigpath | cut -d' ' -f6` == 1) echo "ON";
  else echo "OFF";
  echo "</b>. Change: <input type=\"submit\" name=\"OR\" value=\"on\"> <input type=\"submit\" name=\"OR\" value=\"off\">";

  echo "<p>Relay 1 (HEPA) is <b>";
  if(`/usr/local/bin/gpio read 4` == 1) echo "ON";
  else echo "OFF";
  echo "</b>. Change: <input type=\"submit\" name=\"R1\" value=\"on\"> <input type=\"submit\" name=\"R1\" value=\"off\">";
  echo " or <input type=\"text\" maxlength=3 size=3 name=\"sR1\" /> sec ";
  echo "<input type=\"submit\" name=\"1secON\" value=\"On\">";

  echo "<p>Relay 2 (HUMI) is <b>";
  if(`/usr/local/bin/gpio read 3` == 1) echo "ON";
  else echo "OFF";
  echo "</b>. Change: <input type=\"submit\" name=\"R2\" value=\"on\"> <input type=\"submit\" name=\"R2\" value=\"off\">";
  echo " or <input type=\"text\" maxlength=3 size=3 name=\"sR2\" /> sec ";
  echo "<input type=\"submit\" name=\"2secON\" value=\"On\">";

  echo "<p>Relay 3 (CFAN) is <b>";
  if(`/usr/local/bin/gpio read 1` == 1) echo "ON";
  else echo "OFF";
  echo "</b>. Change: <input type=\"submit\" name=\"R3\" value=\"on\"> <input type=\"submit\" name=\"R3\" value=\"off\">";
  echo " or <input type=\"text\" maxlength=3 size=3 name=\"sR3\" /> sec ";
  echo "<input type=\"submit\" name=\"3secON\" value=\"On\">";

  echo "<p>Relay 4 (HEAT) is <b>";
  if(`/usr/local/bin/gpio read 0` == 1) echo "ON";
  else echo "OFF";
  echo "</b>. Change: <input type=\"submit\" name=\"R4\" value=\"on\"> <input type=\"submit\" name=\"R4\" value=\"off\">";
  echo " or <input type=\"text\" maxlength=3 size=3 name=\"sR4\" /> sec ";
  echo "<input type=\"submit\" name=\"4secON\" value=\"On\">";
  echo "<p>MinT MaxT HighT MinH MaxH<br>",`cat $sconfigpath | cut -d' ' -f1,2,3,4,5`;
  echo "<p>Set Parameters (Include spaces!): <input type=\"text\" maxlength=14 size=14 name=\"String\" /> ";
  echo "<input type=\"submit\" name=\"SubmitMode\" value=\"Set\"></FORM><p>";
?>
</center>
</body>
</html>

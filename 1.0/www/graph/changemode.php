<?php include "auth.php";?>
<HTML>
<BODY>
<?php
  if(isset($_POST['Mode'])) {
    $ModeSet = $_POST['Mode'];
    displayModeform();
    echo `/home/kiz/bin/arduino-send S$ModeSet`;
  }
  else if($_POST['SubmitMode']) {
    $SetMinMax = $_POST['SetMinMax'];
    displayModeform();
    echo `/home/kiz/bin/arduino-send R$SetMinMax`;
  }
  else displayModeform();

  function displayModeform() {
    echo "<FORM action=\"\" method=\"POST\">";
    echo "Set Mode (Clocktower override): <input type=\"submit\" name=\"Mode\" value=\"1\"> ";
    echo "<input type=\"submit\" name=\"Mode\" value=\"2\"> ";
    echo "<input type=\"submit\" name=\"Mode\" value=\"3\"> ";
    echo "<input type=\"submit\" name=\"Mode\" value=\"4\"> ";
    echo "<input type=\"submit\" name=\"Mode\" value=\"5\"> ";
    echo "<input type=\"submit\" name=\"Mode\" value=\"6\">";
    echo "<p>Status: <input type=\"submit\" name=\"Mode\" value=\"0\">";
    echo "&nbsp;&nbsp;&nbsp;Revert to clocktower: <input type=\"submit\" name=\"Mode\" value=\"7\">";
    echo "&nbsp;&nbsp;&nbsp;Display Modes: <input type=\"submit\" name=\"Mode\" value=\"8\"> ";
    echo "<p>Set Mode 5, [MinMaxHum|MinMaxHeat]: <input type=\"text\" maxlength=8 size=8 name=\"SetMinMax\" /> ";
    echo "<input type=\"submit\" name=\"SubmitMode\" value=\"Set\"></FORM><p>";
  }
?>
</BODY>
</HTML>

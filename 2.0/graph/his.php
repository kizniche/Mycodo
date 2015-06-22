<?php include "auth.php"; ?>
<html>
<head>
<META HTTP-EQUIV="refresh" CONTENT="65">
</head>
<body>
<?php

  if(isset($_POST['Lines'])) {
    $Lines = $_POST['Lines'];
    displayModeform();
    echo `tail -n $Lines /var/www/graph/PiSensorData | sed 's/$/<br>/'`;
  }
  else {
    displayModeform();
    echo `tail -n 20 /var/www/graph/PiSensorData | sed 's/$/<br>/'`;
  }

  function displayModeform() {
    echo "<FORM action=\"\" method=\"POST\">";
    echo "Lines: <input type=\"text\" maxlength=8 size=8 name=\"Lines\" /> ";
    echo "<input type=\"submit\" name=\"SubmitMode\" value=\"Set\"></FORM><p>Year Mo Day Hour Min Sec Timestamp RH T_C T_F DP HI<p>";
  }
?>
</body>
</html>

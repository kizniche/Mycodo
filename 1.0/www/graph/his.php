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
    echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n $Lines | sed 's/$/<br>/'`;
  }
  else {
    displayModeform();
    echo `grep -Ih OO /home/kiz/arduino/output/* | tail -n 34 | sed 's/$/<br>/'`;
  }

  function displayModeform() {
    echo "<FORM action=\"\" method=\"POST\">";
    echo "Lines: <input type=\"text\" maxlength=8 size=8 name=\"Lines\" /> ";
    echo "<input type=\"submit\" name=\"SubmitMode\" value=\"Set\"></FORM><p>";
  }
?>
</body>
</html>

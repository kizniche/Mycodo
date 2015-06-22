<?php
session_start();
$User1 = "guest";
$Password1 = "94vf5eg8f8d34a01a598c6a7950972c6";
$User2 = "guest2";
$Password2 = "4f2e364087944450572176ff1bfdeab6";

switch ($_GET['id']) {
case hash:
  echo "<html><head><title></title></head><body><style>body,td,input { font-family: verdana; font-size: 8pt; }</style>";
  if($error) echo "<p><b>Wrong credentials</b></p>";
  echo "<form action=\"\" method=\"post\"><table width='500' border=0><tr>";
  echo "<td>password:</td><td><input type='password' name='md5password'></td><td>";
  if($_POST['md5password']) echo md5($_POST['md5password']);
  echo "</td></tr><tr><td colspan='2'><input type='Submit' value='Get md5&raquo;' name='loginbutton'></td></tr></table></form></body></html>";
  exit;
break;

default:
  if(!$_SESSION['authenticated'])
    if($_POST['loginbutton']) {
      $inputuser = $_POST['input_user'];
      $input_Password = hashPassword($_POST['input_password']);
# Uncomment the following line, load auth.php, enter desired pass in password box, click Login to display hashed password
# echo $input_Password;
      if((!strcmp($inputuser ,$User1) && !strcmp($input_Password ,$Password1))  || (!strcmp($inputuser ,$User2) && !strcmp($input_Password ,$Password2))) {
        $_SESSION['authenticated'] = 1;
        if ($_GET['r'] == 1) header("Location:".$_SERVER[PHP_SELF]."?r=1");
        else header("Location:".$_SERVER[PHP_SELF]);
      }
      else displayform(1);
    }
    else displayform(0);
}

function hashPassword($password) {
  $salt1 = "df+-+-u87^GhuiuVcc.</#;jhdgOJeEehd>IOJ~1838HB>Ihssf\}\{jhggd";
  $salt2 = "Jq*92@/<hX S_=!`/dJhFDtay@7369chsl[\?.><tqcw>wiejrgGQF`~1112";
  //encrypt the password, rotate characters by length of original password
  $len = strlen($password);
  $password = md5($password);
  $password = rotateHEX($password,$len);
  return md5($salt1.$password.salt2);
}

function rotateHEX($string, $n) {
  //for more security, randomize this string
  $chars="abcdef1234567890";
  $str="";
  for ($i=0;$i<strlen($string);$i++)
  {
    $pos = strpos($chars,$string[$i]);
    $pos += $n;
    if ($pos>=strlen($chars))
      $pos = $pos % strlen($chars);
    $str.=$chars[$pos];
  }
  return $str;
}

function displayform($error) {
  echo "<html><head><title></title></head><body><style>body,td,input { font-family: verdana; font-size: 8pt; }</style>";
  if($error) echo "<p><b>Wrong credentials</b></p>";
  echo "<form action=\"\" method=\"post\"><table width='400' border=0><tr><td width='100'>username:</td>";
  echo "<td><input autofocus=\"\" type='text' name='input_user'></td></tr><tr><td>password:</td><td><input type='password' name='input_password'></td></tr>";
  echo "<tr><td colspan='2'><input type='Submit' value='Login&raquo;' name='loginbutton'></td></tr></table></form></body></html>";
  exit;
}
?>

<?php
/*
usage on webpage:
<img src="stream.php">
*/ 
$server = "localhost"; // camera server address
$port = 8080; // camera server port
$url = "/?action=stream"; // image url on server
set_time_limit(0);  
$fp = fsockopen($server, $port, $errno, $errstr, 30); 
if (!$fp) { 
        echo "$errstr ($errno)<br>\n";   // error handling
} else { 
        $urlstring = "GET ".$url." HTTP/1.0\r\n\r\n"; 
        fputs ($fp, $urlstring); 
        while ($str = trim(fgets($fp, 4096))) 
        header($str); 
        fpassthru($fp); 
        fclose($fp); 
} 
?>